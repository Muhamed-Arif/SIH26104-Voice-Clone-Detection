# M2 delivery — start here

Open **`m2/README.md`** for Windows setup and commands. For the combined M1+M2 workflow, open **`M1_M2_START_HERE.md`**.

| Item | Location in this ZIP |
|---|---|
| M1 start guide | `M1_START_HERE.md` |
| Combined M1+M2 start guide | `M1_M2_START_HERE.md` |
| M2 microphone/streaming Python | `m2/stream_microphone.py` |
| M2 robustness evaluator | `m2/robustness_evaluate.py` |
| M2 labeled WAV evaluator | `m2/evaluate.py` |
| M2 local physical acceptance | `m2/LOCAL_ACCEPTANCE_2026-09-07.md` |
| M1 `/predict` API | `ml-service/ml_service/api.py` |
| M1 preprocessing/features (`summary-v2`) | `ml-service/ml_service/preprocessing.py` |
| M1 predictor/model wrapper | `ml-service/ml_service/predictor.py`, `baseline.py` |
| M1 direct handoff gate | `ml-service/scripts/validate_model_handoff.py` |
| Default integration model | `ml-service/model_artifacts/candidate-gradient-boosting-v1.joblib` |
| Frozen baseline reference | `ml-service/model_artifacts/baseline-v2.joblib` |
| Requirements | `m2/requirements.txt`, `m2/constraints.txt`, `ml-service/requirements-ml.txt` |
| M3 payload helpers | `m2/contracts.py` |
| Tests and evidence | `m2/tests/test_m2.py`, `m2/TEST_RESULTS.md` |
| Completion status | `M1_M2_COMPLETION_STATUS.md` |

## Quick start

```powershell
powershell -ExecutionPolicy Bypass -File .\m2\setup_windows.ps1
powershell -ExecutionPolicy Bypass -File .\m2\start_m1.ps1
```

Open a second terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-m2\Scripts\Activate.ps1
python .\m2\stream_microphone.py
```

M2 engineering is implemented and physical microphone acceptance has been performed. M1 engineering is packaged with the stronger audited candidate and a strict handoff gate. The remaining limitation is **model generalization**, not M2 microphone transport: the current M1 evidence still reports misses on some external AI generators, so final classifier sign-off must be based on an independent generator-diverse test set.
