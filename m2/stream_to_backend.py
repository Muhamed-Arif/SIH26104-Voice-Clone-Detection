"""Stream microphone audio through M2 DSP -> backend -> M1 -> risk engine."""
from __future__ import annotations

import argparse
import json
import math
import queue
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

import numpy as np

from .stream_microphone import RATE, Windows, prepare, quality


def post_json(url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(262144)
    except urllib.error.HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"Backend HTTP {exc.code}: {detail}") from exc
    except OSError as exc:
        raise RuntimeError(f"Backend unavailable: {exc}") from exc
    result = json.loads(body)
    if not isinstance(result, dict):
        raise RuntimeError("Backend returned non-object JSON")
    return result


def run(args) -> int:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Install m2/requirements.txt to enable microphone capture") from exc

    device = int(args.device) if args.device and args.device.isdigit() else args.device
    source_rate = args.sample_rate or round(sd.query_devices(device, "input")["default_samplerate"])
    if not 8000 <= source_rate <= 192000:
        raise ValueError("Unsupported microphone sample rate")

    session_id = str(uuid.uuid4())
    endpoint = args.backend_url.rstrip("/") + "/api/v1/analyze"
    pending: queue.Queue = queue.Queue(maxsize=20)
    capture = {"offset": 0, "dropped": 0}
    windows = Windows(round(source_rate * args.window), round(source_rate * args.hop))
    expected = 0
    sequence = 0
    started = time.monotonic()
    counts: dict[str, int] = {}

    def callback(indata, frames, timing, status):
        offset = capture["offset"]
        capture["offset"] += frames
        item = (offset, indata[:, 0].copy(), datetime.now(timezone.utc).isoformat(), bool(status))
        try:
            pending.put_nowait(item)
        except queue.Full:
            capture["dropped"] += 1

    print(f"Session: {session_id}")
    print(f"Backend: {endpoint}")
    print(f"Microphone sample rate: {source_rate} Hz")
    print("Press Ctrl+C to stop.\n")

    try:
        with sd.InputStream(device=device, channels=1, samplerate=source_rate, dtype="float32",
                            blocksize=max(1, round(source_rate * 0.1)), callback=callback):
            while not args.duration or time.monotonic() - started < args.duration:
                try:
                    offset, block, stamp, overflow = pending.get(timeout=0.25)
                except queue.Empty:
                    continue
                if offset != expected or overflow:
                    windows.reset(offset)
                    print("[audio gap] capture discontinuity")
                expected = offset + len(block)

                for _, chunk in windows.feed(block):
                    x = prepare(chunk, source_rate)
                    q = quality(x, args.silence_db)
                    if q["quality"] == "SILENCE" and not args.include_silence:
                        counts["SILENCE"] = counts.get("SILENCE", 0) + 1
                        print("SILENCE")
                        continue

                    sequence += 1
                    chunk_id = f"{session_id}-{sequence:06d}"
                    payload = {
                        "waveform": x.tolist(),
                        "sample_rate": RATE,
                        "chunk_id": chunk_id,
                        "quality": q["quality"],
                        "timestamp": stamp,
                        "session_id": session_id,
                    }
                    t0 = time.perf_counter()
                    try:
                        result = post_json(endpoint, payload, args.timeout)
                        latency_ms = (time.perf_counter() - t0) * 1000.0
                        risk_level = str(result.get("risk_level", "UNKNOWN"))
                        counts[risk_level] = counts.get(risk_level, 0) + 1
                        print(
                            f"{chunk_id} | P(AI)={float(result.get('synthetic_probability', 0))*100:.2f}% "
                            f"| confidence={float(result.get('confidence', 0))*100:.2f}% "
                            f"| risk={result.get('risk_score')} {risk_level} "
                            f"| action={result.get('action')} | {latency_ms:.1f} ms"
                        )
                    except Exception as exc:
                        counts["ERROR"] = counts.get("ERROR", 0) + 1
                        print(f"{chunk_id} | ERROR | {exc}")
    except KeyboardInterrupt:
        print("\nStopped by user.")

    print("\nSummary:", counts)
    print("Dropped capture blocks:", capture["dropped"])
    return 0 if counts.get("ERROR", 0) == 0 else 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backend-url", default="http://127.0.0.1:8000")
    p.add_argument("--device", help="Microphone index or name")
    p.add_argument("--sample-rate", type=int, help="Capture rate; default is device native rate")
    p.add_argument("--window", type=float, default=2.0)
    p.add_argument("--hop", type=float, default=1.0)
    p.add_argument("--duration", type=float, default=0.0, help="Seconds; 0 means until Ctrl+C")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--silence-db", type=float, default=-45.0)
    p.add_argument("--include-silence", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    if not (0.5 <= args.window <= 2.0 and 0 < args.hop <= args.window):
        raise SystemExit("Use 0.5 <= window <= 2.0 and 0 < hop <= window")
    if not all(math.isfinite(v) for v in (args.window, args.hop, args.duration, args.timeout, args.silence_db)):
        raise SystemExit("Numeric arguments must be finite")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
