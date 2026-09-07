# Member 2 — audio capture, DSP and streaming

Built for Muhamed Arif's uploaded SIH26104 repository on 7 September 2026.
Main file: `m2/stream_microphone.py`. Run commands from the extracted repository root.
This adds M2 to the supplied snapshot; it is not a newer download from GitHub.

## Start on Windows

1. Install Python 3.12 if it is not already installed. `py -0p` lists installed versions.
   Use 3.12 for this setup even if your default `py` is Python 3.14.
2. Open the extracted repository folder in VS Code, then open a PowerShell terminal.
3. Install the environment (no environment activation is needed):

```powershell
powershell -ExecutionPolicy Bypass -File .\m2\setup_windows.ps1
```

4. Start the M1 API in that terminal. The stronger audited candidate is the default integration model; the frozen baseline is still available for comparison:

```powershell
powershell -ExecutionPolicy Bypass -File .\m2\start_m1.ps1
# baseline reference only:
powershell -ExecutionPolicy Bypass -File .\m2\start_m1.ps1 -Model baseline
```

5. Open a SECOND terminal in the same repository folder:

```powershell
.\.venv-m2\Scripts\python.exe .\m2\stream_microphone.py --list-devices
.\.venv-m2\Scripts\python.exe .\m2\stream_microphone.py --language Tamil
```

Speak into the microphone. The first full window takes two seconds to collect;
subsequent overlapping windows advance every second. Stop with Ctrl+C.
If the default input is wrong, choose an input index from the device list:

```powershell
.\.venv-m2\Scripts\python.exe .\m2\stream_microphone.py --device 1 --language Tamil --duration 60
```

Microphone access must be enabled for desktop applications in Windows settings.
The capture rate defaults to the device's native rate, then each window is
converted to mono 16 kHz for M1. `--sample-rate 48000` explicitly requests a
capture rate if the device supports it.

## Test a WAV directly

```powershell
.\.venv-m2\Scripts\python.exe .\m2\stream_microphone.py --file "C:\Users\WELCOME\Downloads\SIH_Voice_Clone\SIH_Voice_Clone\dataset\OpenAI\alloy_0.wav" --language English
```

Replace the path with an actual file on your computer. Files are streamed in
small blocks, and all windows are tested rather than only the beginning.
PCM WAV 8/16/24/32 bit is supported; compressed WAV, floating-point WAV, MP3 and
FLAC need conversion to PCM WAV first. `--realtime` paces WAV windows in real time;
without it, file testing proceeds as quickly as the API responds.

For non-overlapping two-second tests, add `--hop 2`.
A file tail shorter than 0.5 seconds is logged as TOO_SHORT and is not sent.
An uncovered tail of 0.5 seconds or longer is submitted without zero padding.
The last unfinished microphone window is discarded when capture stops.

## What is implemented

- Microphone selection, native-rate capture and mono conversion.
- Two-second windows with a configurable step; bounded audio callback queue.
- Queue overflow and device discontinuity reporting; old audio is discarded,
  and partial windows are reset so separate parts of a recording are not joined.
- Polyphase resampling matched against M1 `summary-v2`; finite/sample-range validation.
- RMS, clipping fraction and frame activity measurements, with an energy silence gate.
- Strict `/predict` request and response validation; lazy-model `/health` handling.
- API timeouts and explicit error/inconclusive statuses; no fake fallback or retries.
- M1's own label is retained, including its learned decision threshold.
- Last-three-valid-window mean probability for display/logging only. It is not
  a new calibrated confidence value or a replacement classification threshold.
- JSONL result logs with session/chunk IDs, timestamps, source offsets, quality,
  model/feature versions and request latency. Raw waveform audio is not saved.
- WAV regression evaluator and M3 payload helpers.
- Automated DSP, transport, model integration and simulated capture tests.

This energy gate is not a trained voice activity detector: loud fans or music
can pass it. Noise reduction, AGC, high-pass filters and peak boosting are not
applied because changing those inputs would change the four trained features.
Coordinate any such changes with M1 and retrain/evaluate the model accordingly.

## Interpret the output

| Status | Meaning |
|---|---|
| REAL | M1 returned label 0. This is not proof of a caller's identity. |
| AI_GENERATED | M1 returned label 1. |
| SILENCE | Low energy/activity; not submitted by default. |
| TOO_SHORT | Less than 0.5 seconds; not enough audio for this client's policy. |
| INCONCLUSIVE | M1 reported unavailable/invalid/low-quality input or a mock model. |
| API_ERROR | Connection, timeout, response or contract error. |

A DEGRADED audio-quality measurement is logged alongside a valid model label;
it should reduce trust in that label. `--include-silence` bypasses the local
silence gate for diagnostics. `--silence-db -50` changes its threshold.
These are engineering defaults, not dataset-calibrated acceptance thresholds.

Logs are created under `m2/logs/`. Request p50/p95 cover the most recent 10,000
successful API responses, including the cold first prediction; they exclude
window collection and time spent in the microphone queue. At defaults, expect
at least two seconds before the first complete-window result.

## Recheck known real and AI samples

Copy `m2/sample_manifest.csv` to `m2/my_samples.csv` and replace its placeholder
paths. Relative paths are resolved from the CSV's folder. Each row needs:
`path,label,language`, with label `REAL` or `AI_GENERATED` and language English,
Hindi or Tamil. Use independent genuine speech and known generator recordings.

```powershell
.\.venv-m2\Scripts\python.exe -m m2.evaluate --manifest .\m2\my_samples.csv --output .\m2\logs\baseline_evaluation.json
```

The evaluator reports file-level majority decisions, confusion counts and
accuracy on classified files. Ties, API failures and no usable windows are
inconclusive and separately counted. This is a diagnostic aggregation rule,
not a trained call-level classifier. Silent/too-short windows are excluded.
Don't claim detection accuracy from sine waves used in software tests.

## M1 model selection and final handoff gate

This completion build keeps both artifacts:

- `candidate-gradient-boosting-v1.joblib` — default integration model because the repository audit shows materially higher AI recall and lower false negatives than baseline-v2.
- `baseline-v2.joblib` — frozen reference model for comparison.

To start the baseline explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\m2\start_m1.ps1 -Model baseline
```

To test another artifact without editing code:

```powershell
powershell -ExecutionPolicy Bypass -File .\m2\start_m1.ps1 -ModelPath .\ml-service\model_artifacts\your-model.joblib
```

Before M1 hands any model to M2 as final, run the direct artifact gate on an independent labeled challenge set:

```powershell
.\.venv-m2\Scripts\python.exe .\ml-service\scripts\validate_model_handoff.py `
  --model .\ml-service\model_artifacts\candidate-gradient-boosting-v1.joblib `
  --manifest .\m2\my_samples.csv `
  --output .\M1_dataset\handoff_gate.json
```

The gate verifies the model class mapping (`0=REAL`, `1=AI_GENERATED`), runs the same `summary-v2` production preprocessing, reports false positives/false negatives and fails when the supplied set does not meet the configured AI-recall/FPR thresholds.

For software robustness testing with the same labeled files:

```powershell
.\.venv-m2\Scripts\python.exe -m m2.robustness_evaluate `
  --manifest .\m2\my_samples.csv `
  --output .\m2\logs\robustness.json
```

The current repository evidence still reports two OpenAI `alloy` misses for the candidate. Do not hide that limitation or call the classifier universally solved until an independent generator-diverse handoff set passes.

## Member 3 handoff

`m2/contracts.py` provides `backend_chunk(...)` for the current backend's
`DSPAudioChunk`, and `m1_payload(chunk, language)` for M1's strict schema.
The microphone CLI intentionally targets the real M1 endpoint for this delivery.
Do not point `--api-url` at the backend `/analyze` endpoint: it has another schema.

Before wiring backend persistence/dashboard/alerts, Member 3 must fix:

1. `backend/app/services/ml_client.py` sends `quality` and `timestamp` to M1,
   but omits required `language`. M1 forbids extra keys, so that request is rejected.
   Send exactly waveform, sample_rate, chunk_id and language. The existing backend
   chunk schema has no language field: add and propagate it, or explicitly supply
   session language. `m1_payload` demonstrates the exact translation.
2. That client falls back to mock classifications on API errors. Production
   must propagate an unavailable/error state and respect M1 `quality_flag`;
   do not record the fallback as a real model result.
3. Validate session ownership/authentication and database configuration before
   sending real microphone audio through the backend or WebSocket route.

Backend files are preserved from the upload. Payload compatibility is tested;
PostgreSQL, authenticated WebSocket streaming, dashboard and prevention actions
were not executed or claimed complete in this M2 delivery.

Shadow scoring is now opt-in. It is disabled by default so the candidate is not scored twice when it is the active model. To run the baseline while also collecting candidate shadow results, use `start_m1.ps1 -Model baseline -EnableShadow`.

## Verify the package

```powershell
.\.venv-m2\Scripts\python.exe -m unittest discover -s m2/tests -v
```

See `m2/TEST_RESULTS.md` and `m2/LOCAL_ACCEPTANCE_2026-09-07.md` for the checks actually performed. The user completed the physical Windows microphone acceptance on 7 September 2026.

On Linux, install the system PortAudio library before microphone use, then:

```bash
python3.12 -m venv .venv-m2
.venv-m2/bin/python -m pip install -r m2/requirements.txt -r ml-service/requirements-ml.txt -c m2/constraints.txt
cd ml-service
MODEL_ARTIFACT_PATH=model_artifacts/baseline-v2.joblib ALLOW_MOCK_PREDICTOR=0 ../.venv-m2/bin/python -m uvicorn ml_service.api:app --host 127.0.0.1 --port 8001
```

In a second terminal at the repository root:

```bash
.venv-m2/bin/python m2/stream_microphone.py --language English
```
