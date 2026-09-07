import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    confusion_matrix,
    classification_report,
)

# ============================================================
# CONFIG
# ============================================================

DATA_DIR = r"D:\SIH_AIML\ASVspoof2019_LA\data"

TRAIN_PATH = os.path.join(
    DATA_DIR,
    "train-00000-of-00001.parquet"
)

DEV_PATH = os.path.join(
    DATA_DIR,
    "validation-00000-of-00001.parquet"
)

MODEL_DIR = r"D:\SIH_AIML\models"
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "voice_authenticity_balanced.joblib"
)

WORKERS = 12
SEED = 42


# ============================================================
# EXACT SAME 30-FEATURE EXTRACTOR
# ============================================================

def extract_features(audio_dict):

    y, sr = sf.read(
        io.BytesIO(audio_dict["bytes"]),
        dtype="float32"
    )

    if y.ndim > 1:
        y = np.mean(y, axis=1)

    y = np.nan_to_num(y)

    if len(y) == 0:
        return np.zeros(30, dtype=np.float32)

    y = y / (np.max(np.abs(y)) + 1e-8)

    features = []

    # 11 time-domain
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

    # 1 zero crossing
    if len(y) > 1:
        zcr = np.mean(
            np.abs(np.diff(np.sign(y)))
        ) / 2
    else:
        zcr = 0.0

    features.append(zcr)

    # 4 spectral
    yy = y[:min(len(y), sr * 10)]

    freqs, power = periodogram(
        yy,
        fs=sr
    )

    power = np.maximum(
        power,
        1e-12
    )

    total = np.sum(power)

    if total <= 0:
        total = 1e-12

    centroid = (
        np.sum(freqs * power) / total
    )

    bandwidth = np.sqrt(
        np.sum(
            ((freqs - centroid) ** 2) *
            power
        ) / total
    )

    cumulative = np.cumsum(power)

    rolloff_index = np.searchsorted(
        cumulative,
        0.85 * cumulative[-1]
    )

    rolloff = freqs[
        min(
            rolloff_index,
            len(freqs) - 1
        )
    ]

    flatness = (
        np.exp(np.mean(np.log(power))) /
        np.mean(power)
    )

    features.extend([
        centroid,
        bandwidth,
        rolloff,
        flatness,
    ])

    # 5 frequency-band energies
    bands = [
        (0, 300),
        (300, 1000),
        (1000, 3000),
        (3000, 6000),
        (6000, 12000),
    ]

    for low, high in bands:

        mask = (
            (freqs >= low) &
            (freqs < high)
        )

        if np.any(mask):
            energy = (
                np.sum(power[mask]) / total
            )
        else:
            energy = 0.0

        features.append(energy)

    # 8 RMS statistics
    frame_size = max(
        1,
        int(sr * 0.025)
    )

    hop = max(
        1,
        int(sr * 0.010)
    )

    rms_values = []

    for start in range(
        0,
        len(y) - frame_size + 1,
        hop
    ):

        frame = y[
            start:start + frame_size
        ]

        rms_values.append(
            np.sqrt(
                np.mean(frame ** 2) +
                1e-10
            )
        )

        if len(rms_values) >= 500:
            break

    if rms_values:

        rms = np.asarray(rms_values)

        features.extend([
            np.mean(rms),
            np.std(rms),
            np.min(rms),
            np.max(rms),
            np.percentile(rms, 25),
            np.percentile(rms, 50),
            np.percentile(rms, 75),
            np.percentile(rms, 95),
        ])

    else:

        features.extend([0.0] * 8)

    # 1 duration
    features.append(
        len(y) / sr
    )

    result = np.asarray(
        features,
        dtype=np.float32
    )

    if result.shape != (30,):
        raise RuntimeError(
            f"Expected 30 features, got {result.shape}"
        )

    return result


# ============================================================
# PARALLEL FEATURE EXTRACTION
# ============================================================

def extract_parallel(df, name):

    total = len(df)

    print(
        f"\n{name}: {total} samples"
    )

    X = [None] * total
    y = df["key"].astype(int).to_numpy()

    def worker(index):
        return index, extract_features(
            df.iloc[index]["audio"]
        )

    completed = 0
    errors = 0

    with ThreadPoolExecutor(
        max_workers=WORKERS
    ) as executor:

        futures = [
            executor.submit(worker, i)
            for i in range(total)
        ]

        for future in as_completed(futures):

            try:

                index, feature = future.result()
                X[index] = feature

            except Exception as exc:

                errors += 1

            completed += 1

            if (
                completed % 500 == 0
                or completed == total
            ):

                print(
                    f"\rProcessed "
                    f"{completed}/{total} "
                    f"({100*completed/total:.1f}%) "
                    f"| errors: {errors}",
                    end="",
                    flush=True
                )

    print()

    valid = [
        i
        for i, item in enumerate(X)
        if item is not None
    ]

    X_final = np.asarray(
        [X[i] for i in valid],
        dtype=np.float32
    )

    y_final = y[valid]

    print(
        f"{name} feature matrix:",
        X_final.shape
    )

    print(
        f"{name} errors:",
        errors
    )

    return X_final, y_final


# ============================================================
# LOAD TRAIN
# ============================================================

print("Loading training dataset...")

train_df = pd.read_parquet(
    TRAIN_PATH
)

print(
    "Original training labels:"
)

print(
    train_df["key"].value_counts()
)


# ============================================================
# BALANCE TRAINING DATA
# ============================================================

real_df = train_df[
    train_df["key"] == 0
].copy()

ai_df = train_df[
    train_df["key"] == 1
].copy()

n = len(real_df)

ai_df = ai_df.sample(
    n=n,
    random_state=SEED
)

balanced_df = pd.concat(
    [
        real_df,
        ai_df
    ],
    ignore_index=True
)

balanced_df = balanced_df.sample(
    frac=1.0,
    random_state=SEED
).reset_index(
    drop=True
)

print(
    "\nBalanced training labels:"
)

print(
    balanced_df["key"].value_counts()
)


# ============================================================
# EXTRACT BALANCED TRAIN FEATURES
# ============================================================

X_train, y_train = extract_parallel(
    balanced_df,
    "BALANCED TRAIN"
)


# ============================================================
# LOAD VALIDATION
# ============================================================

print(
    "\nLoading validation dataset..."
)

dev_df = pd.read_parquet(
    DEV_PATH
)

print(
    "Validation labels:"
)

print(
    dev_df["key"].value_counts()
)


# ============================================================
# EXTRACT VALIDATION FEATURES
# ============================================================

X_dev, y_dev = extract_parallel(
    dev_df,
    "VALIDATION"
)


# ============================================================
# TRAIN MODEL
# ============================================================

print(
    "\n================================"
)

print(
    "TRAINING BALANCED MODEL"
)

print(
    "================================"
)

model = HistGradientBoostingClassifier(
    max_iter=200,
    learning_rate=0.08,
    max_leaf_nodes=31,
    l2_regularization=1.0,
    random_state=SEED
)

model.fit(
    X_train,
    y_train
)

print(
    "Training complete."
)


# ============================================================
# VALIDATION
# ============================================================

probability = model.predict_proba(
    X_dev
)[:, 1]

predictions = (
    probability >= 0.50
).astype(int)

accuracy = accuracy_score(
    y_dev,
    predictions
)

balanced_accuracy = (
    balanced_accuracy_score(
        y_dev,
        predictions
    )
)

roc_auc = roc_auc_score(
    y_dev,
    probability
)

matrix = confusion_matrix(
    y_dev,
    predictions
)

report = classification_report(
    y_dev,
    predictions,
    target_names=[
        "REAL",
        "AI_GENERATED"
    ],
    zero_division=0
)

print(
    "\n================================"
)

print(
    "BALANCED MODEL - VALIDATION"
)

print(
    "================================"
)

print(
    "Threshold: 0.50"
)

print(
    "Accuracy:",
    accuracy
)

print(
    "Balanced Accuracy:",
    balanced_accuracy
)

print(
    "ROC-AUC:",
    roc_auc
)

print(
    "\nConfusion Matrix:"
)

print(
    matrix
)

print(
    "\nClassification Report:"
)

print(
    report
)


# ============================================================
# SAVE MODEL
# ============================================================

artifact = {
    "model": model,
    "feature_count": 30,
    "label_mapping": {
        0: "REAL",
        1: "AI_GENERATED"
    },
    "feature_type": "compact_acoustic_statistics",
    "training_dataset": "ASVspoof2019_LA_balanced",
    "real_training_samples": n,
    "ai_training_samples": n,
    "random_seed": SEED,
}

joblib.dump(
    artifact,
    MODEL_PATH
)

print(
    "\nMODEL SAVED:"
)

print(
    MODEL_PATH
)

print(
    "\nBalanced training complete."
)
