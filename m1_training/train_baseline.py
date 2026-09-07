import io
import os
import time
import joblib
import numpy as np
import pandas as pd
import soundfile as sf

from scipy.signal import periodogram
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)

BASE = r"D:\SIH_AIML\ASVspoof2019_LA\data"

TRAIN = os.path.join(BASE, "train-00000-of-00001.parquet")
DEV = os.path.join(BASE, "validation-00000-of-00001.parquet")

MODEL_DIR = r"D:\SIH_AIML\models"
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "voice_authenticity_baseline.joblib")


def extract_features(audio_dict):
    """Extract compact CPU-friendly acoustic features."""

    audio_bytes = audio_dict["bytes"]

    y, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")

    if y.ndim > 1:
        y = np.mean(y, axis=1)

    y = np.nan_to_num(y)

    if len(y) == 0:
        return np.zeros(40, dtype=np.float32)

    # Normalize
    y = y / (np.max(np.abs(y)) + 1e-8)

    features = []

    # -------------------------
    # Time-domain statistics
    # -------------------------
    features.extend([
        np.mean(y),
        np.std(y),
        np.min(y),
        np.max(y),
        np.mean(np.abs(y)),
        np.sqrt(np.mean(y ** 2)),
        np.percentile(y, 5),
        np.percentile(y, 25),
        np.percentile(y, 50),
        np.percentile(y, 75),
        np.percentile(y, 95),
    ])

    # Zero crossing rate
    zcr = np.mean(np.abs(np.diff(np.sign(y)))) / 2
    features.append(zcr)

    # -------------------------
    # Spectral features
    # -------------------------

    # Limit to reasonable analysis length
    max_samples = min(len(y), sr * 10)
    yy = y[:max_samples]

    freqs, power = periodogram(yy, fs=sr)

    power = np.maximum(power, 1e-12)

    total_power = np.sum(power)

    spectral_centroid = np.sum(freqs * power) / total_power

    spectral_bandwidth = np.sqrt(
        np.sum(((freqs - spectral_centroid) ** 2) * power)
        / total_power
    )

    cumulative = np.cumsum(power)
    rolloff_index = np.searchsorted(
        cumulative,
        0.85 * cumulative[-1]
    )

    spectral_rolloff = (
        freqs[min(rolloff_index, len(freqs) - 1)]
    )

    spectral_flatness = np.exp(
        np.mean(np.log(power))
    ) / np.mean(power)

    features.extend([
        spectral_centroid,
        spectral_bandwidth,
        spectral_rolloff,
        spectral_flatness,
    ])

    # -------------------------
    # Band energy ratios
    # -------------------------

    bands = [
        (0, 300),
        (300, 1000),
        (1000, 3000),
        (3000, 6000),
        (6000, 12000),
    ]

    for low, high in bands:
        mask = (freqs >= low) & (freqs < high)

        if np.any(mask):
            energy = np.sum(power[mask]) / total_power
        else:
            energy = 0.0

        features.append(energy)

    # -------------------------
    # Frame-level statistics
    # -------------------------

    frame_size = max(1, int(sr * 0.025))
    hop = max(1, int(sr * 0.010))

    values = []

    for start in range(0, len(y) - frame_size, hop):
        frame = y[start:start + frame_size]

        rms = np.sqrt(np.mean(frame ** 2) + 1e-10)
        values.append(rms)

        if len(values) >= 500:
            break

    if values:
        values = np.asarray(values)

        features.extend([
            np.mean(values),
            np.std(values),
            np.min(values),
            np.max(values),
            np.percentile(values, 25),
            np.percentile(values, 50),
            np.percentile(values, 75),
            np.percentile(values, 95),
        ])
    else:
        features.extend([0.0] * 8)

    # Duration
    features.append(len(y) / sr)

    return np.asarray(features, dtype=np.float32)


def process_dataset(path, name):
    df = pd.read_parquet(path)

    X = []
    y = []

    total = len(df)

    print(f"\nProcessing {name}: {total} samples")

    start = time.time()

    for i, row in enumerate(df.itertuples(index=False), 1):

        try:
            audio = row.audio
            features = extract_features(audio)

            X.append(features)
            y.append(int(row.key))

        except Exception as e:
            print(f"\nERROR at sample {i}: {e}")
            continue

        if i % 500 == 0 or i == total:
            elapsed = time.time() - start
            rate = i / max(elapsed, 1e-6)

            print(
                f"\r{i}/{total} "
                f"({100*i/total:.1f}%) "
                f"{rate:.1f} samples/sec",
                end=""
            )

    print()

    return np.asarray(X), np.asarray(y)


# ============================================================
# TRAIN
# ============================================================

X_train, y_train = process_dataset(TRAIN, "TRAIN")

print("\nTRAIN SHAPE:", X_train.shape)
print("TRAIN LABELS:", np.bincount(y_train))

# ============================================================
# VALIDATION
# ============================================================

X_dev, y_dev = process_dataset(DEV, "VALIDATION")

print("\nVALIDATION SHAPE:", X_dev.shape)
print("VALIDATION LABELS:", np.bincount(y_dev))

# ============================================================
# TRAIN MODEL
# ============================================================

print("\nTraining model...")

model = HistGradientBoostingClassifier(
    max_iter=150,
    learning_rate=0.08,
    max_leaf_nodes=31,
    l2_regularization=1.0,
    random_state=42
)

start = time.time()

model.fit(X_train, y_train)

print(
    f"Training completed in "
    f"{time.time() - start:.1f} seconds"
)

# ============================================================
# VALIDATION
# ============================================================

pred = model.predict(X_dev)
prob = model.predict_proba(X_dev)[:, 1]

print("\n==============================")
print("VALIDATION RESULTS")
print("==============================")

print(
    "Accuracy:",
    accuracy_score(y_dev, pred)
)

print(
    "Balanced Accuracy:",
    balanced_accuracy_score(y_dev, pred)
)

print(
    "ROC-AUC:",
    roc_auc_score(y_dev, prob)
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_dev, pred))

print("\nClassification Report:")
print(
    classification_report(
        y_dev,
        pred,
        target_names=[
            "REAL",
            "AI_GENERATED"
        ]
    )
)

# ============================================================
# SAVE
# ============================================================

artifact = {
    "model": model,
    "feature_count": X_train.shape[1],
    "label_mapping": {
        0: "REAL",
        1: "AI_GENERATED"
    },
    "dataset": "ASVspoof2019_LA",
    "feature_type": "compact_acoustic_statistics",
    "sample_rate": "native",
}

joblib.dump(artifact, MODEL_PATH)

print("\nMODEL SAVED:")
print(MODEL_PATH)