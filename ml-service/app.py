from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from scipy.signal import periodogram, resample_poly

TARGET_RATE = 16000
MODEL_VERSION = "voice-authenticity-balanced-v1"
FEATURES_VERSION = "compact-acoustic-30-v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(REPO_ROOT / "models" / "voice_authenticity_balanced.joblib"))).resolve()
THRESHOLD = float(os.getenv("MODEL_THRESHOLD", "0.45"))

app = FastAPI(title="SIH26104 Voice Authenticity ML Service", version="1.0.0")
_artifact = None
_model = None
_model_error: str | None = None


class PredictRequest(BaseModel):
    waveform: list[float] = Field(..., min_length=1)
    sample_rate: int = Field(..., ge=8000, le=192000)
    chunk_id: str = Field(..., min_length=1, max_length=160)
    language: str = "English"
    quality: str | None = None
    timestamp: str | None = None


class PredictResponse(BaseModel):
    chunk_id: str
    language: str
    label: Literal[0, 1]
    label_name: Literal["REAL", "AI_GENERATED"]
    synthetic_probability: float
    confidence: float
    threshold: float
    model_version: str
    features_version: str
    model_feature_type: str
    quality_flag: Literal["model"]


def load_model():
    global _artifact, _model, _model_error
    if _model is not None:
        return _artifact, _model
    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
        artifact = joblib.load(MODEL_PATH)
        if not isinstance(artifact, dict) or "model" not in artifact:
            raise RuntimeError("Model artifact must contain a 'model' key")
        if int(artifact.get("feature_count", -1)) != 30:
            raise RuntimeError("Expected a 30-feature model artifact")
        model = artifact["model"]
        classes = list(getattr(model, "classes_", []))
        if classes and classes != [0, 1]:
            raise RuntimeError(f"Expected classes [0, 1], got {classes}")
        _artifact, _model, _model_error = artifact, model, None
        return artifact, model
    except Exception as exc:
        _model_error = str(exc)
        raise


def normalize_audio(values: list[float], source_rate: int) -> np.ndarray:
    x = np.asarray(values, dtype=np.float32)
    if x.ndim != 1 or x.size == 0 or not np.isfinite(x).all():
        raise ValueError("waveform must be a finite mono float array")
    if x.size > source_rate * 10:
        x = x[: source_rate * 10]
    if source_rate != TARGET_RATE:
        divisor = math.gcd(TARGET_RATE, source_rate)
        x = resample_poly(x, TARGET_RATE // divisor, source_rate // divisor).astype(np.float32)
    if x.size < TARGET_RATE // 2:
        raise ValueError("audio chunk must be at least 0.5 seconds")
    peak = float(np.max(np.abs(x)))
    if peak > 0:
        x = x / (peak + 1e-8)
    return np.clip(x, -1.0, 1.0)


def extract_features(x: np.ndarray, sr: int = TARGET_RATE) -> np.ndarray:
    f = [float(np.mean(x)), float(np.std(x)), float(np.min(x)), float(np.max(x)),
         float(np.mean(np.abs(x))), float(np.sqrt(np.mean(x ** 2))),
         float(np.percentile(x, 5)), float(np.percentile(x, 25)), float(np.percentile(x, 50)),
         float(np.percentile(x, 75)), float(np.percentile(x, 95))]
    f.append(float(np.mean(np.abs(np.diff(np.sign(x)))) / 2.0) if len(x) > 1 else 0.0)
    yy = x[:min(len(x), sr * 10)]
    freqs, power = periodogram(yy, fs=sr)
    power = np.maximum(power, 1e-12)
    total = float(np.sum(power)) or 1e-12
    centroid = float(np.sum(freqs * power) / total)
    bandwidth = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * power) / total))
    cumulative = np.cumsum(power)
    rolloff = float(freqs[min(int(np.searchsorted(cumulative, 0.85 * cumulative[-1])), len(freqs)-1)])
    flatness = float(np.exp(np.mean(np.log(power))) / np.mean(power))
    f.extend([centroid, bandwidth, rolloff, flatness])
    for low, high in [(0,300),(300,1000),(1000,3000),(3000,6000),(6000,12000)]:
        mask = (freqs >= low) & (freqs < high)
        f.append(float(np.sum(power[mask]) / total) if np.any(mask) else 0.0)
    frame, hop = max(1, int(sr*0.025)), max(1, int(sr*0.010))
    rms = []
    for start in range(0, len(x)-frame+1, hop):
        segment = x[start:start+frame]
        rms.append(float(np.sqrt(np.mean(segment**2)+1e-10)))
        if len(rms) >= 500:
            break
    if rms:
        r = np.asarray(rms, dtype=np.float32)
        f.extend([float(np.mean(r)), float(np.std(r)), float(np.min(r)), float(np.max(r)),
                  float(np.percentile(r,25)), float(np.percentile(r,50)), float(np.percentile(r,75)), float(np.percentile(r,95))])
    else:
        f.extend([0.0]*8)
    f.append(float(len(x)/sr))
    result = np.asarray(f, dtype=np.float32)
    if result.shape != (30,) or not np.isfinite(result).all():
        raise RuntimeError(f"Expected 30 valid features, got {result.shape}")
    return result


@app.get("/health")
def health():
    try:
        artifact, _ = load_model()
        return {"status":"ok","model_configured":True,"model_loaded":True,"model_version":MODEL_VERSION,
                "feature_count":int(artifact.get("feature_count",30)),"threshold":THRESHOLD,
                "features_version":FEATURES_VERSION,"cpu_only":True}
    except Exception:
        return {"status":"error","model_configured":MODEL_PATH.is_file(),"model_loaded":False,
                "model_version":MODEL_VERSION,"error":_model_error}


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    try:
        _, model = load_model()
        x = normalize_audio(payload.waveform, payload.sample_rate)
        probability = float(model.predict_proba(extract_features(x).reshape(1,-1))[0,1])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ML model unavailable: {exc}") from exc
    probability = max(0.0, min(1.0, probability))
    label = 1 if probability >= THRESHOLD else 0
    confidence = probability if label else 1.0 - probability
    return PredictResponse(chunk_id=payload.chunk_id, language=payload.language, label=label,
        label_name="AI_GENERATED" if label else "REAL", synthetic_probability=round(probability,6),
        confidence=round(confidence,6), threshold=THRESHOLD, model_version=MODEL_VERSION,
        features_version=FEATURES_VERSION, model_feature_type="compact_acoustic_statistics", quality_flag="model")
