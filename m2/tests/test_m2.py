import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import wave
from unittest.mock import patch

import numpy as np

from m2.stream_microphone import API, Runner, Windows, mono, parser, prepare, quality, run_file, wav_blocks
from m2.contracts import backend_chunk, m1_payload

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ml-service'))
from ml_service.preprocessing import preprocess_audio, extract_features_from_waveform


def tone(rate=16000, seconds=2):
    return .2*np.sin(2*np.pi*220*np.arange(round(rate*seconds))/rate)


def prediction(payload, **changes):
    result = dict(chunk_id=payload['chunk_id'], language=payload['language'],
                  synthetic_probability=.52, confidence=.52, label=0,
                  quality_flag='model', model_version='baseline-logistic-v2', features_version='summary-v2')
    result.update(changes)
    return result


class DSPTests(unittest.TestCase):
    def test_resampling_matches_m1(self):
        for rate in (8000, 16000, 44100, 48000):
            x = tone(rate)
            actual = prepare(x, rate)
            self.assertEqual(len(actual), 32000)
            np.testing.assert_allclose(actual, preprocess_audio(x.tolist(), rate), atol=1e-12)
            np.testing.assert_allclose(extract_features_from_waveform(actual.tolist(), 16000).values,
                                       extract_features_from_waveform(x.tolist(), rate).values, atol=1e-12)

    def test_mono_and_invalid_samples(self):
        np.testing.assert_allclose(mono([[.2, .4], [.1, -.1]]), [.3, 0])
        for value in ([], [float('nan')], [float('inf')], [2.]):
            with self.assertRaises(ValueError):
                mono(value)

    def test_silence_activity_clipping(self):
        self.assertEqual(quality(np.zeros(16000))['quality'], 'SILENCE')
        self.assertEqual(quality(tone())['quality'], 'HIGH')
        self.assertEqual(quality(np.ones(16000))['quality'], 'DEGRADED')

    def test_window_overlap_and_uncovered_tail(self):
        w = Windows(4, 2)
        chunks = list(w.feed(np.arange(7)/10))
        self.assertEqual([i for i, x in chunks], [0, 2])
        np.testing.assert_allclose(chunks[1][1], [.2, .3, .4, .5])
        offset, tail = w.tail()
        self.assertEqual(offset, 6)
        np.testing.assert_allclose(tail, [.6])
        w.reset(10)
        self.assertEqual(list(w.feed([.1, .2])), [])
        chunks = list(w.feed([.3, .4]))
        self.assertEqual(chunks[0][0], 10)

    def test_wav_all_pcm_widths_and_stereo(self):
        with tempfile.TemporaryDirectory() as tmp:
            for width in (1, 2, 3, 4):
                path = Path(tmp)/f'{width}.wav'
                if width == 1:
                    raw = bytes([160, 96])*8000
                else:
                    v = 2**(width*8-3)
                    raw = (v.to_bytes(width, 'little', signed=True)+(-v).to_bytes(width, 'little', signed=True))*8000
                with wave.open(str(path), 'wb') as f:
                    f.setparams((2, width, 8000, 0, 'NONE', 'not compressed'))
                    f.writeframes(raw)
                blocks = list(wav_blocks(path, .1))
                self.assertEqual(sum(len(x) for x, r in blocks), 8000)
                self.assertTrue(all(np.allclose(x, 0) for x, r in blocks))

    def test_m3_contract(self):
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location('audio_contract', ROOT/'backend/app/schemas/audio.py')
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        chunk = backend_chunk(tone(), 16000, 'test', '2026-09-07T00:00:00+00:00')
        module.DSPAudioChunk.model_validate(chunk)
        from ml_service.schemas import PredictRequest
        PredictRequest.model_validate(m1_payload(chunk, 'Tamil'))


class RunnerTests(unittest.TestCase):
    def runner(self, **changes):
        args = parser().parse_args([])
        for key, value in changes.items():
            setattr(args, key, value)
        log = io.StringIO()
        return Runner(args, log), log

    def test_preserves_m1_label_threshold_and_no_audio_logging(self):
        runner, log = self.runner()
        runner.api.predict = lambda payload: prediction(payload)
        with contextlib.redirect_stdout(io.StringIO()):
            runner.process(tone(), 16000, 0, 'now')
        result = json.loads(log.getvalue())
        self.assertEqual(result['status'], 'REAL')  # .52 is below M1's .53966 threshold
        self.assertNotIn('waveform', result)

    def test_silence_skips_network(self):
        runner, log = self.runner()
        runner.api.predict = lambda payload: self.fail('Silence called API')
        with contextlib.redirect_stdout(io.StringIO()):
            runner.process(np.zeros(32000), 16000, 0, 'now')
        self.assertEqual(json.loads(log.getvalue())['status'], 'SILENCE')

    def test_errors_and_mock_never_real(self):
        for mode in ('error', 'mock'):
            runner, log = self.runner()
            def fake(payload):
                if mode == 'error':
                    raise OSError('offline')
                return prediction(payload, quality_flag='model_unavailable')
            runner.api.predict = fake
            with contextlib.redirect_stdout(io.StringIO()):
                runner.process(tone(), 16000, 0, 'now')
            self.assertIn(json.loads(log.getvalue())['status'], ('API_ERROR', 'INCONCLUSIVE'))
            self.assertTrue(runner.failed)

    def test_wav_entire_file_and_partial_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'input.wav'
            with wave.open(str(path), 'wb') as f:
                f.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                f.writeframes((tone(seconds=5.75)*32767).astype('<i2').tobytes())
            runner, log = self.runner(file=path)
            runner.api.predict = lambda payload: prediction(payload)
            with contextlib.redirect_stdout(io.StringIO()):
                run_file(runner)
            rows = [json.loads(line) for line in log.getvalue().splitlines()]
            self.assertEqual(len(rows), 5)
            self.assertEqual(rows[-1]['source_offset_seconds'], 5)
            self.assertEqual(rows[-1]['duration_seconds'], .75)


class HTTPTests(unittest.TestCase):
    def test_real_http_validation_and_health(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                self.send_response(200); self.end_headers()
                self.wfile.write(b'{"status":"ok","model_configured":true,"model_loaded":false}')
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200); self.end_headers()
                self.wfile.write(json.dumps(prediction(data, chunk_id='wrong')).encode())
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            api = API(f'http://127.0.0.1:{server.server_port}')
            self.assertFalse(api.health()['model_loaded'])
            with self.assertRaisesRegex(ValueError, 'chunk_id'):
                api.predict({'chunk_id':'right', 'language':'Tamil'})
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_rejects_invalid_probabilities_and_contract(self):
        api = API('unused')
        payload = {'chunk_id': 'id', 'language': 'Tamil'}
        for changes in ({'synthetic_probability':float('nan')}, {'confidence':2},
                        {'label':True}, {'features_version':'other'}, {'quality_flag':None}):
            api.request = lambda *args: prediction(payload, **changes)
            with self.assertRaises(ValueError):
                api.predict(payload)


class ModelIntegrationTests(unittest.TestCase):
    def test_bundled_baseline_through_actual_m1_api(self):
        from fastapi.testclient import TestClient
        from ml_service.api import create_app
        from ml_service.config import Settings
        from ml_service.predictor import Predictor
        with patch('ml_service.predictor._run_shadow', None):
            client = TestClient(create_app(Predictor(Settings(
                model_artifact=ROOT/'ml-service/model_artifacts/baseline-v2.joblib', allow_mock=False))))
            runner, log = RunnerTests().runner()
            def request(route, payload=None):
                response = client.get(route) if payload is None else client.post(route, json=payload)
                response.raise_for_status()
                return response.json()
            runner.api.request = request
            self.assertTrue(runner.api.health()['model_configured'])
            with contextlib.redirect_stdout(io.StringIO()):
                runner.process(tone(), 16000, 0, 'now')
            row = json.loads(log.getvalue())
            self.assertFalse(runner.failed)
            self.assertEqual(row['prediction']['model_version'], 'baseline-logistic-v2')
            self.assertEqual(row['prediction']['quality_flag'], 'model')


class EvaluationTests(unittest.TestCase):
    def test_metrics_keep_failed_files_visible(self):
        from m2.evaluate import summarize
        report = summarize([{'label':'REAL', 'predicted':'REAL'},
                            {'label':'AI_GENERATED', 'predicted':'REAL'},
                            {'label':'AI_GENERATED', 'predicted':'INCONCLUSIVE'}])
        self.assertEqual(report['classified_files'], 2)
        self.assertEqual(report['inconclusive_or_failed_files'], 1)
        self.assertEqual(report['confusion_matrix']['false_negative'], 1)
        self.assertEqual(report['accuracy_on_classified_files'], .5)

class MicrophoneSimulationTests(unittest.TestCase):
    def test_callback_queue_overflow_and_discontinuity(self):
        import queue
        import types
        from m2.stream_microphone import run_microphone
        clock = [0.0]
        real_queue = queue.Queue
        class FakeQueue(real_queue):
            def get(self, timeout=None):
                if self.empty():
                    clock[0] = 10.0
                    raise queue.Empty
                return super().get(block=False)
        class FakeStream:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def __enter__(self):
                cb = self.kwargs['callback']
                for i in range(25):
                    cb(tone(seconds=.1).reshape(-1, 1), 1600, None, i == 0)
                return self
            def __exit__(self, *args): pass
        fake = types.SimpleNamespace(InputStream=FakeStream)
        runner, log = RunnerTests().runner(sample_rate=16000, duration=1)
        runner.api.predict = lambda payload: prediction(payload)
        with patch.dict(sys.modules, {'sounddevice': fake}), patch('m2.stream_microphone.queue.Queue', FakeQueue), patch('m2.stream_microphone.time.monotonic', lambda:clock[0]), contextlib.redirect_stdout(io.StringIO()):
            run_microphone(runner)
        rows = [json.loads(x) for x in log.getvalue().splitlines()]
        self.assertTrue(any(r.get('reason') == 'capture_discontinuity' for r in rows))
        self.assertEqual(rows[-1]['dropped_blocks'], 5)
        self.assertEqual(sum(r['type'] == 'chunk' for r in rows), 1)


if __name__ == '__main__':
    unittest.main()

class RobustnessTransformTests(unittest.TestCase):
    def test_robustness_variants_are_finite_and_bounded(self):
        from m2.robustness_evaluate import make_variant
        x = tone(seconds=1)
        for scenario in ('clean', 'low_volume', 'noise_20db', 'telephone_8k', 'quantized_8bit'):
            y, rate = make_variant(x, 16000, scenario)
            self.assertTrue(len(y) > 0)
            self.assertTrue(np.isfinite(y).all())
            self.assertLessEqual(float(np.max(np.abs(y))), 1.00001)
            self.assertEqual(rate, 8000 if scenario == 'telephone_8k' else 16000)

    def test_low_volume_and_quantization_have_expected_effect(self):
        from m2.robustness_evaluate import make_variant
        x = tone(seconds=1)
        low, _ = make_variant(x, 16000, 'low_volume')
        quantized, _ = make_variant(x, 16000, 'quantized_8bit')
        self.assertAlmostEqual(float(np.max(np.abs(low))), float(np.max(np.abs(x))) * .25, places=5)
        self.assertLessEqual(len(np.unique(np.round(quantized, 8))), 256)
