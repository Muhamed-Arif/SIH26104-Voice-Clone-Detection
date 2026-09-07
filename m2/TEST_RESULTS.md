# M2 / M1 integration verification — 7 September 2026

## Automated checks in this completion build

- `python -m unittest discover -s m2/tests -v`: **17 tests passed** in the build environment.
- `python -m pytest ml-service/tests/test_api.py ml-service/tests/test_contract.py -q`: **9 tests passed**.
- Candidate API smoke test: the bundled `candidate-gradient-boosting-v1.joblib` loaded through the real FastAPI predictor and returned `model_version=candidate-gradient-boosting-v1`, `features_version=summary-v2`, and a valid model probability/label.
- M2 robustness-evaluator smoke test: a local HTTP M1 server was exercised with clean and telephone-8k variants; the evaluator completed and produced scenario-level reports. This verifies the software path, not model accuracy.

The suite covers:

- mono conversion and invalid sample rejection;
- 8/16/24/32-bit PCM WAV handling;
- silence/activity/clipping quality measurements;
- overlapping windows, tails and capture-gap reset;
- M2 resampling parity with M1 preprocessing;
- M3 payload schema validation;
- strict HTTP response validation;
- no deceptive model fallback;
- preservation of M1 classification decisions;
- evaluator accounting;
- simulated microphone queue overflow/discontinuity handling;
- robustness transforms for low volume, additive noise, 8-kHz telephone bandwidth and 8-bit quantization;
- model probability-column mapping by actual class values;
- rejection of invalid/non-binary model class mappings.

## Physical Windows acceptance performed by the user

See `m2/LOCAL_ACCEPTANCE_2026-09-07.md`.

Reported local results included:

- Python 3.12.10 / `.venv-m2` working;
- physical 44.1-kHz microphone capture;
- `baseline-logistic-v2` loaded through the real M1 API;
- silence correctly producing `SILENCE`;
- human speech producing live `REAL` predictions;
- zero dropped blocks in the longer reported run;
- request-latency medians between about 76 ms and 138 ms across the reported sessions.

## Model-quality boundary

Software/DSP transport passing does **not** mean the classifier is universally accurate. Existing M1 repository evidence reports:

- baseline-v2 failed all five named external AI holdouts;
- candidate-gradient-boosting-v1 improved external holdout detection to 3/5;
- two OpenAI `alloy` holdouts remained false negatives.

Therefore M1 must run `ml-service/scripts/validate_model_handoff.py` on the team's independent challenge set before final model sign-off. M2 should then run `m2/evaluate.py` and `m2/robustness_evaluate.py` on the same model.

## Dependency note

The bundled joblib estimators were serialized with scikit-learn **1.9.0**. `m2/constraints.txt` pins that version for the Windows setup. The build-environment smoke tests used an older local scikit-learn installation and emitted compatibility warnings while still passing; the user's Windows setup should use the pinned 1.9.0 environment.
