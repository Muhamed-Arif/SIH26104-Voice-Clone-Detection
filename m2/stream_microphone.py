"""M2 audio streaming client. Run from the repository root; see m2/README.md."""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import queue
import sys
import time
import urllib.error
import urllib.request
import uuid
import wave

import numpy as np
from scipy.signal import resample_poly

RATE = 16000


def utc_now():
    return datetime.now(timezone.utc)


def mono(samples):
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim not in (1, 2) or values.size == 0:
        raise ValueError('Audio must be a nonempty mono or frames-by-channels array')
    if not np.isfinite(values).all():
        raise ValueError('Audio contains NaN or infinity')
    if values.ndim == 2:
        values = values.mean(axis=1)
    if np.max(np.abs(values)) > 1.00001:
        raise ValueError('Audio must be normalized float samples in [-1, 1]')
    return np.clip(values, -1, 1)


def prepare(samples, source_rate):
    """Match M1 resample/normalization without denoising or gain boosting."""
    if not 8000 <= source_rate <= 192000:
        raise ValueError('Sample rate must be 8000..192000 Hz')
    values = mono(samples)
    if source_rate != RATE:
        divisor = math.gcd(RATE, source_rate)
        values = resample_poly(values, RATE // divisor, source_rate // divisor)
        target = max(1, round(len(mono(samples)) * RATE / source_rate))
        if len(values) != target:
            values = np.interp(np.linspace(0, len(values)-1, target), np.arange(len(values)), values)
    peak = np.max(np.abs(values))
    if peak > 1:
        values = values / peak
    return np.clip(values, -1, 1)


def quality(samples, floor_db=-45):
    """Energy activity gate, NOT a trained speech detector or SNR estimate."""
    x = mono(samples)
    rms = float(np.sqrt(np.mean(x*x)))
    db = 20 * math.log10(max(rms, 1e-12))
    frame_size = 320
    activity = [float(np.sqrt(np.mean(x[i:i+frame_size]**2))) >= 10**(floor_db/20)
                for i in range(0, len(x), frame_size)]
    active_ratio = sum(activity) / len(activity)
    clipping = float(np.mean(np.abs(x) >= .999))
    flag = 'SILENCE' if db < floor_db or active_ratio < .1 else 'HIGH'
    if flag != 'SILENCE' and (clipping > .01 or active_ratio < .4):
        flag = 'DEGRADED'
    return {'quality': flag, 'rms_dbfs': round(db, 2),
            'active_frame_ratio': round(active_ratio, 4),
            'clipping_ratio': round(clipping, 4)}


class Windows:
    """Sample-accurate windows. reset() prevents joining audio across capture gaps."""
    def __init__(self, size, hop):
        if not 0 < hop <= size:
            raise ValueError('hop must be positive and no greater than window')
        self.size, self.hop = size, hop
        self.buffer = np.empty(0)
        self.offset = 0
        self.last_end = 0

    def reset(self, offset=0):
        self.buffer = np.empty(0)
        self.offset = offset
        self.last_end = offset

    def feed(self, samples):
        self.buffer = np.concatenate((self.buffer, mono(samples)))
        while len(self.buffer) >= self.size:
            yield self.offset, self.buffer[:self.size].copy()
            self.last_end = self.offset + self.size
            self.buffer = self.buffer[self.hop:]
            self.offset += self.hop

    def tail(self):
        # Emit uncovered samples only, not overlap already analyzed.
        skip = max(0, self.last_end - self.offset)
        if len(self.buffer) > skip:
            return self.offset + skip, self.buffer[skip:].copy()
        return None


def wav_blocks(path, seconds):
    """Stream PCM WAV without loading a long recording into RAM."""
    with wave.open(str(path), 'rb') as wav:
        rate, channels, width = wav.getframerate(), wav.getnchannels(), wav.getsampwidth()
        if width not in (1, 2, 3, 4) or not 8000 <= rate <= 192000:
            raise ValueError('Use PCM WAV, 8/16/24/32 bit, 8000..192000 Hz')
        while raw := wav.readframes(max(1, round(rate * seconds))):
            if width == 1:
                x = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64)-128)/128
            elif width == 3:
                b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
                x = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
                x = ((x ^ 0x800000)-0x800000)/8388608
            else:
                x = np.frombuffer(raw, dtype='<i2' if width == 2 else '<i4').astype(np.float64)
                x /= 2**(8*width-1)
            yield mono(x.reshape(-1, channels)), rate


class API:
    def __init__(self, base_url, timeout=5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def request(self, route, payload=None):
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode()
        req = urllib.request.Request(self.base_url + route, data=data,
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read(65537)
                if len(raw) > 65536:
                    raise ValueError('API response exceeds 64 KiB')
                result = json.loads(raw)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'API HTTP {exc.code}: {exc.read(1024).decode(errors="replace")}') from exc
        if not isinstance(result, dict):
            raise ValueError('API returned a non-object JSON response')
        return result

    def health(self):
        h = self.request('/health')
        if h.get('status') != 'ok' or h.get('model_configured') is not True:
            raise RuntimeError('M1 has no configured model. Start M1 using m2/start_m1.ps1')
        # M1 loads lazily on the first prediction, so model_loaded=false is valid here.
        return h

    def predict(self, payload):
        result = self.request('/predict', payload)
        for key in ('chunk_id', 'language'):
            if result.get(key) != payload[key]:
                raise ValueError(f'API {key} does not match request')
        for key in ('synthetic_probability', 'confidence'):
            v = result.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
                raise ValueError(f'Invalid API {key}')
        if type(result.get('label')) is not int or result['label'] not in (0, 1):
            raise ValueError('Invalid API label')
        if result.get('features_version') != 'summary-v2':
            raise ValueError('Unexpected feature version; confirm updated contract with M1')
        if not isinstance(result.get('model_version'), str) or not result['model_version']:
            raise ValueError('Missing model version')
        if result.get('quality_flag') not in ('model', 'model_unavailable', 'low_quality_input', 'invalid_input'):
            raise ValueError('Invalid API quality_flag')
        return result


class Runner:
    def __init__(self, args, log, api=None):
        self.args, self.log = args, log
        self.api = api or API(args.api_url, args.timeout)
        self.session = str(uuid.uuid4())
        self.sequence = 0
        self.scores = deque(maxlen=3)
        self.version = None
        self.counts = {}
        self.latencies = deque(maxlen=10000)
        self.failed = False
        self.started = utc_now()

    def emit(self, record):
        self.log.write(json.dumps(record, allow_nan=False) + '\n')
        self.log.flush()
        if record.get('type') == 'chunk':
            status = record['status']
            self.counts[status] = self.counts.get(status, 0) + 1
            p = record.get('prediction', {}).get('synthetic_probability')
            detail = '' if p is None else f' | Synthetic {p*100:.2f}%'
            print(f"{record['chunk_id']} | {status}{detail}", flush=True)
        else:
            print(json.dumps(record), flush=True)

    def process(self, samples, source_rate, offset, timestamp):
        self.sequence += 1
        cid = f'{self.session}-{self.sequence:06d}'
        x = prepare(samples, source_rate)
        q = quality(x, self.args.silence_db)
        record = {'type': 'chunk', 'session_id': self.session, 'chunk_id': cid,
                  'timestamp': timestamp, 'source_offset_seconds': round(offset/source_rate, 6),
                  'sample_rate': RATE, 'duration_seconds': len(x)/RATE, **q}
        if len(x) < RATE // 2:
            record['status'] = 'TOO_SHORT'
            self.scores.clear()
        elif q['quality'] == 'SILENCE' and not self.args.include_silence:
            record['status'] = 'SILENCE'
            self.scores.clear()
        else:
            payload = {'waveform': x.tolist(), 'sample_rate': RATE,
                       'chunk_id': cid, 'language': self.args.language}
            t0 = time.perf_counter()
            try:
                result = self.api.predict(payload)
                latency = round((time.perf_counter()-t0)*1000, 2)
                self.latencies.append(latency)
                record.update(prediction=result, request_latency_ms=latency)
                if result['quality_flag'] != 'model' or result['model_version'].startswith('mock'):
                    record['status'] = 'INCONCLUSIVE'
                    self.scores.clear()
                    self.failed = True
                else:
                    # Use M1's label: its learned threshold is not necessarily 0.5.
                    record['status'] = 'AI_GENERATED' if result['label'] else 'REAL'
                    if self.version != result['model_version']:
                        self.scores.clear()
                    self.version = result['model_version']
                    self.scores.append(result['synthetic_probability'])
                    record['rolling_synthetic_probability'] = sum(self.scores)/len(self.scores)
            except (OSError, ValueError, RuntimeError) as exc:
                self.failed = True
                self.scores.clear()
                record.update(status='API_ERROR', error=str(exc))
            # No automatic retry: backend/shadow operations may have side effects.
        self.emit(record)

    def summary(self):
        self.emit({'type': 'summary', 'session_id': self.session, 'counts': self.counts,
                   'latency_sample_count': len(self.latencies), 'latency_scope': 'latest 10000 successful API responses',
                   'request_latency_p50_ms': float(np.percentile(self.latencies, 50)) if self.latencies else None,
                   'request_latency_p95_ms': float(np.percentile(self.latencies, 95)) if self.latencies else None,
                   'note': 'Latency excludes audio collection; REAL is a model output, not identity verification.'})


def run_file(runner):
    args = runner.args
    windows = None
    for block, rate in wav_blocks(args.file, .1):
        if windows is None:
            windows = Windows(round(rate*args.window), round(rate*args.hop))
        for offset, chunk in windows.feed(block):
            if args.realtime:
                target = (runner.started + timedelta(seconds=(offset+len(chunk))/rate)).timestamp()
                time.sleep(max(0, target-time.time()))
            runner.process(chunk, rate, offset, (runner.started+timedelta(seconds=offset/rate)).isoformat())
    if windows is None:
        raise ValueError('WAV file is empty')
    tail = windows.tail()
    if tail is not None:
        offset, chunk = tail
        runner.process(chunk, rate, offset, (runner.started+timedelta(seconds=offset/rate)).isoformat())


def run_microphone(runner):
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError('Install m2/requirements.txt to enable microphone capture') from exc
    args = runner.args
    device = int(args.device) if args.device and args.device.isdigit() else args.device
    rate = args.sample_rate or round(sd.query_devices(device, 'input')['default_samplerate'])
    if not 8000 <= rate <= 192000:
        raise ValueError('Unsupported microphone sample rate')
    # Callback only copies audio. All DSP, HTTP and logging run in the consumer.
    pending = queue.Queue(maxsize=20)
    capture = {'offset': 0, 'dropped': 0}
    window = Windows(round(rate*args.window), round(rate*args.hop))

    def callback(indata, frames, timing, status):
        offset = capture['offset']
        capture['offset'] += frames
        item = (offset, indata[:, 0].copy(), time.monotonic(), utc_now().isoformat(), bool(status))
        try:
            pending.put_nowait(item)
        except queue.Full:
            capture['dropped'] += 1

    expected = 0
    started = time.monotonic()
    try:
        with sd.InputStream(device=device, channels=1, samplerate=rate, dtype='float32',
                            blocksize=max(1, round(rate*.1)), callback=callback):
            runner.emit({'type': 'capture_started', 'sample_rate': rate, 'device': str(device),
                         'window_seconds': args.window, 'hop_seconds': args.hop})
            while not args.duration or time.monotonic()-started < args.duration:
                try:
                    offset, data, captured, stamp, overflow = pending.get(timeout=.2)
                except queue.Empty:
                    continue
                if time.monotonic()-captured > args.max_age:
                    window.reset(offset+len(data))
                    expected = offset+len(data)
                    runner.emit({'type': 'gap', 'reason': 'stale_audio', 'samples': len(data)})
                    runner.scores.clear()
                    continue
                if offset != expected or overflow:
                    window.reset(offset)
                    runner.scores.clear()
                    runner.emit({'type': 'gap', 'reason': 'capture_discontinuity',
                                 'missing_samples': max(0, offset-expected), 'device_status': overflow})
                expected = offset+len(data)
                for start, chunk in window.feed(data):
                    # Timestamp approximates window start using callback arrival and sample offset.
                    begin = datetime.fromisoformat(stamp) - timedelta(seconds=(offset+len(data)-start)/rate)
                    runner.process(chunk, rate, start, begin.isoformat())
    finally:
        runner.emit({'type': 'capture_stopped', 'dropped_blocks': capture['dropped'],
                     'note': 'Unfinished live window is discarded on stop.'})



def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--file', type=Path, help='Analyze PCM WAV instead of microphone')
    p.add_argument('--api-url', default='http://127.0.0.1:8001', help='M1 base URL, without /predict')
    p.add_argument('--language', choices=['English', 'Hindi', 'Tamil'], default='English')
    p.add_argument('--device', help='Microphone index or name')
    p.add_argument('--list-devices', action='store_true')
    p.add_argument('--sample-rate', type=int, help='Capture rate; default is device native rate')
    p.add_argument('--window', type=float, default=2, help='0.5..2 seconds; M1 truncates at 2 seconds')
    p.add_argument('--hop', type=float, default=1, help='Window step in seconds')
    p.add_argument('--duration', type=float, default=0, help='Live seconds; 0 until Ctrl+C')
    p.add_argument('--timeout', type=float, default=5)
    p.add_argument('--max-age', type=float, default=2, help='Discard queued live blocks older than this')
    p.add_argument('--silence-db', type=float, default=-45)
    p.add_argument('--include-silence', action='store_true', help='Diagnostic bypass of energy gate')
    p.add_argument('--realtime', action='store_true', help='Pace WAV playback at recording speed')
    p.add_argument('--log', type=Path, help='JSONL metadata/predictions only; audio is not saved')
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    numeric = (args.window, args.hop, args.duration, args.timeout, args.max_age, args.silence_db)
    if not all(math.isfinite(v) for v in numeric):
        p.error('Numeric options must be finite')
    if not .5 <= args.window <= 2 or not 0 < args.hop <= args.window:
        p.error('Use 0.5 <= window <= 2 and 0 < hop <= window')
    if args.duration < 0 or args.timeout <= 0 or args.max_age <= 0:
        p.error('duration >= 0, timeout > 0, max-age > 0 required')
    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        return 0
    path = args.log or Path('m2/logs') / f'{utc_now():%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as log:
        runner = Runner(args, log)
        try:
            runner.emit({'type': 'session_started', 'session_id': runner.session,
                         'timestamp': runner.started.isoformat(), 'language': args.language,
                         'health': runner.api.health(), 'mode': 'file' if args.file else 'microphone'})
            run_file(runner) if args.file else run_microphone(runner)
        except KeyboardInterrupt:
            print('\nStopped by user.')
        except Exception as exc:
            runner.failed = True
            runner.emit({'type': 'fatal_error', 'error': str(exc)})
        finally:
            runner.summary()
    print(f'Log: {path.resolve()}')
    return 1 if runner.failed else 0


if __name__ == '__main__':
    sys.exit(main())
