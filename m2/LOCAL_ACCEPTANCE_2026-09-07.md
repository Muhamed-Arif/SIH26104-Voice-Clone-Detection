# M2 local Windows microphone acceptance — 7 September 2026

These results are transcribed from the user's local VS Code/PowerShell runs. They verify the physical microphone path; they are not claims about universal classifier accuracy.

## Environment / model

- Python 3.12.10 in `.venv-m2`.
- M1 API running locally on port 8001.
- `model_loaded=true` with `baseline-logistic-v2` during the reported acceptance runs.
- Native microphone capture rate: 44.1 kHz.
- M2 window: 2 seconds; hop: 1 second.

## Reported runs

### Live speech run

- 7 REAL windows.
- Request latency p50: 76.23 ms.
- Request latency p95: 83.988 ms.
- Human speech was consistently returned as REAL.

### Silence + speech run

- 9 SILENCE windows.
- 3 REAL windows.
- Request latency p50: 137.62 ms.
- Request latency p95: 147.889 ms.
- Silence gate and return-to-speech behavior both worked.

### Longer silence + speech run

- 15 SILENCE windows.
- 26 REAL windows.
- Dropped blocks: 0.
- Request latency p50: 114.53 ms.
- Request latency p95: 136.585 ms.
- The stream recovered from silence and continued producing valid model responses.

## Acceptance conclusion

M2 core transport/DSP acceptance: **PASS** for physical microphone capture, live windowing, silence gating, M1 API transport, model/version receipt, latency logging and dropped-block accounting.

Separate model-quality gate: **not implied by this PASS**. Earlier direct known-AI WAV tests showed false negatives in baseline-v2, which is why M1 model validation must be handled separately with `validate_model_handoff.py`.
