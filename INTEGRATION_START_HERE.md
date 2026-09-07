# SIH26104 full-system integration — start here

This branch wires the runtime path into one flow:

`Frontend microphone / M2 microphone -> Backend /api/v1/analyze -> M1 ML /predict -> Risk Engine + DB -> Frontend result`

## What is integrated

- **Frontend:** `backend/app/static/integrated.html` captures real browser microphone audio, creates 2-second windows with a 1-second hop, resamples to 16 kHz mono, skips silence, sends chunks to the backend, and renders probability/confidence/risk/action.
- **M2 Audio/DSP:** existing `m2/stream_microphone.py` remains available; new `m2/stream_to_backend.py` sends the physical microphone through the backend so the full risk/database path is exercised.
- **M1 ML:** `ml-service/app.py` loads `models/voice_authenticity_balanced.joblib`, reproduces the 30-feature training extractor, uses threshold `0.45`, and exposes `/health` + `/predict`.
- **Backend:** real ML is enabled by default, silent mock fallback is disabled, SQLite is the zero-config local default, and `/integration-health` verifies DB + M1 together.

## Windows quick start

From the repository root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
powershell -ExecutionPolicy Bypass -File .\m2\setup_windows.ps1
powershell -ExecutionPolicy Bypass -File .\run_integrated.ps1
```

The browser opens automatically.

- Frontend: `http://127.0.0.1:8000/`
- Integration health: `http://127.0.0.1:8000/integration-health`
- Backend Swagger: `http://127.0.0.1:8000/docs`
- M1 health: `http://127.0.0.1:8001/health`

Allow microphone access in the browser and press **Start microphone**.

## Run the physical M2 microphone through the whole backend

Keep `run_integrated.ps1` running, open another PowerShell in the repository root, then run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-m2\Scripts\Activate.ps1
python -m m2.stream_to_backend
```

Expected output contains:

```text
P(AI)=... | confidence=... | risk=... LOW/MEDIUM/HIGH | action=ALLOW/ALERT/BLOCK
```

## Model contract used by this integration

- Artifact: `models/voice_authenticity_balanced.joblib`
- Labels: `0 = REAL`, `1 = AI_GENERATED`
- Feature count: 30 compact acoustic statistics
- Target inference sample rate: 16 kHz mono
- Recommended threshold from repository evidence: `0.45`
- Model version exposed by API: `voice-authenticity-balanced-v1`

## Important model-quality note

Integration success means frontend, M2 DSP, backend, M1 inference, risk engine, and persistence work together. It does **not** prove universal voice-clone detection accuracy. M1 should continue independent evaluation/retraining and only replace the artifact after it improves the agreed validation and unseen-generator metrics.
