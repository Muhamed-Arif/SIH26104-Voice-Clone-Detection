import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import joblib
import numpy as np
import pandas as pd
import soundfile as sf

from scipy.signal import periodogram
from sklearn.metrics import (
    recall_score,
    precision_score,
    f1_score,
    balanced_accuracy_score,
    confusion_matrix,
)

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = r"D:\SIH_AIML\models\voice_authenticity_balanced.joblib"
DEV_PATH = (
    r"D:\SIH_AIML\ASVspoof2019_LA\data"
    r"\validation-00000-of-00001.parquet"
)

OUTPUT_CSV = (
    r"D:\SIH_AIML\models"
    r"\threshold_analysis_2019_validation.csv"
)

OUTPUT_THRESHOLD = (
    r"D:\SIH_AIML\models"
    r"\recommended_threshold.txt"
)

# Use 12 parallel workers
WORKERS = 12


# ============================================================
# FEATURE EXTRACTION
# MUST MATCH TRAINING SCRIPT EXACTLY
# ============================================================

def extract_features(audio_dict):
    """
    Extract the same 30 features used by the baseline model.
    """

    audio_bytes = audio_dict["bytes"]

    y, sr = sf.read(
        io.BytesIO(audio_bytes),
        dtype="float32"
    )

    if y.ndim > 1:
        y = np.mean(y, axis=1)

    y = np.nan_to_num(y)

    if len(y) == 0:
        return np.zeros(30, dtype=np.float32)

    # Normalize
    y = y / (np.max(np.abs(y)) + 1e-8)

    features = []

    # --------------------------------------------------------
    # Time-domain features: 11
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Zero crossing rate: 1
    # --------------------------------------------------------

    if len(y) > 1:
        zcr = (
            np.mean(
                np.abs(
                    np.diff(
                        np.sign(y)
                    )
                )
            ) / 2
        )
    else:
        zcr = 0.0

    features.append(zcr)

    # --------------------------------------------------------
    # Spectral features: 4
    # --------------------------------------------------------

    max_samples = min(
        len(y),
        sr * 10
    )

    yy = y[:max_samples]

    if len(yy) < 2:
        return np.zeros(30, dtype=np.float32)

    freqs, power = periodogram(
        yy,
        fs=sr
    )

    power = np.maximum(
        power,
        1e-12
    )

    total_power = np.sum(power)

    if total_power <= 0:
        total_power = 1e-12

    spectral_centroid = (
        np.sum(
            freqs * power
        ) / total_power
    )

    spectral_bandwidth = np.sqrt(
        np.sum(
            (
                (freqs - spectral_centroid) ** 2
            ) * power
        ) / total_power
    )

    cumulative = np.cumsum(power)

    rolloff_index = np.searchsorted(
        cumulative,
        0.85 * cumulative[-1]
    )

    spectral_rolloff = freqs[
        min(
            rolloff_index,
            len(freqs) - 1
        )
    ]

    spectral_flatness = (
        np.exp(
            np.mean(
                np.log(power)
            )
        ) / np.mean(power)
    )

    features.extend([
        spectral_centroid,
        spectral_bandwidth,
        spectral_rolloff,
        spectral_flatness,
    ])

    # --------------------------------------------------------
    # Frequency-band energy: 5
    # --------------------------------------------------------

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
                np.sum(
                    power[mask]
                ) / total_power
            )

        else:

            energy = 0.0

        features.append(energy)

    # --------------------------------------------------------
    # Frame RMS statistics: 8
    # --------------------------------------------------------

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

        rms = np.sqrt(
            np.mean(
                frame ** 2
            ) + 1e-10
        )

        rms_values.append(rms)

        # EXACT SAME LIMIT AS TRAINING
        if len(rms_values) >= 500:
            break

    if rms_values:

        rms_values = np.asarray(
            rms_values
        )

        features.extend([
            np.mean(rms_values),
            np.std(rms_values),
            np.min(rms_values),
            np.max(rms_values),
            np.percentile(rms_values, 25),
            np.percentile(rms_values, 50),
            np.percentile(rms_values, 75),
            np.percentile(rms_values, 95),
        ])

    else:

        features.extend(
            [0.0] * 8
        )

    # --------------------------------------------------------
    # Duration: 1
    # --------------------------------------------------------

    features.append(
        len(y) / sr
    )

    result = np.asarray(
        features,
        dtype=np.float32
    )

    if result.shape != (30,):

        raise RuntimeError(
            f"Expected 30 features, "
            f"got {result.shape}"
        )

    return result


# ============================================================
# PARALLEL WORKER
# ============================================================

def process_one(index, audio):

    try:

        features = extract_features(
            audio
        )

        return (
            index,
            features,
            True,
            None
        )

    except Exception as exc:

        return (
            index,
            None,
            False,
            str(exc)
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "================================"
    )

    print(
        "THRESHOLD ANALYSIS"
    )

    print(
        "================================"
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print(
        "\nLoading model..."
    )

    artifact = joblib.load(
        MODEL_PATH
    )

    model = artifact["model"]

    expected_features = artifact[
        "feature_count"
    ]

    print(
        "Model loaded."
    )

    print(
        "Expected features:",
        expected_features
    )

    if expected_features != 30:

        raise RuntimeError(
            "Model does not expect 30 features."
        )

    # --------------------------------------------------------
    # Load validation data
    # --------------------------------------------------------

    print(
        "\nLoading validation dataset..."
    )

    df = pd.read_parquet(
        DEV_PATH
    )

    print(
        "Validation samples:",
        len(df)
    )

    print(
        "\nValidation labels:"
    )

    print(
        df["key"].value_counts()
    )

    # Keep original order.
    audio_data = df["audio"].tolist()

    y_true = (
        df["key"]
        .astype(int)
        .to_numpy()
    )

    total = len(audio_data)

    # --------------------------------------------------------
    # Parallel feature extraction
    # --------------------------------------------------------

    print(
        f"\nStarting {WORKERS}-worker "
        f"parallel feature extraction..."
    )

    features_by_index = [
        None
    ] * total

    errors = 0
    completed = 0

    with ThreadPoolExecutor(
        max_workers=WORKERS
    ) as executor:

        futures = [
            executor.submit(
                process_one,
                i,
                audio
            )
            for i, audio in enumerate(
                audio_data
            )
        ]

        for future in as_completed(
            futures
        ):

            index, features, success, error = (
                future.result()
            )

            completed += 1

            if success:

                features_by_index[index] = (
                    features
                )

            else:

                errors += 1

            if (
                completed % 500 == 0
                or completed == total
            ):

                print(
                    f"\rProcessed: "
                    f"{completed}/{total} "
                    f"({100.0 * completed / total:.1f}%) "
                    f"| errors: {errors}",
                    end="",
                    flush=True
                )

    print()

    # --------------------------------------------------------
    # Remove failed samples
    # --------------------------------------------------------

    valid_indices = [
        i
        for i, x in enumerate(
            features_by_index
        )
        if x is not None
    ]

    if not valid_indices:

        raise RuntimeError(
            "No validation features were extracted."
        )

    X = np.asarray(
        [
            features_by_index[i]
            for i in valid_indices
        ],
        dtype=np.float32
    )

    y = y_true[
        valid_indices
    ]

    print(
        "\nFeature matrix:",
        X.shape
    )

    print(
        "Successful samples:",
        len(X)
    )

    print(
        "Feature extraction errors:",
        errors
    )

    # --------------------------------------------------------
    # Get model probabilities
    # --------------------------------------------------------

    print(
        "\nCalculating AI probabilities..."
    )

    if not hasattr(
        model,
        "predict_proba"
    ):

        raise RuntimeError(
            "Model does not support predict_proba()."
        )

    prob_ai = model.predict_proba(
        X
    )[:, 1]

    # --------------------------------------------------------
    # Threshold sweep
    # --------------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "THRESHOLD RESULTS"
    )

    print(
        "================================"
    )

    print(
        "Threshold | REAL Recall | "
        "AI Recall | Balanced Acc | "
        "AI Precision | Macro F1"
    )

    results = []

    # Thresholds from 0.05 to 0.95
    thresholds = np.arange(
        0.05,
        0.951,
        0.05
    )

    for threshold in thresholds:

        predictions = (
            prob_ai >= threshold
        ).astype(int)

        real_recall = recall_score(
            y,
            predictions,
            pos_label=0,
            zero_division=0
        )

        ai_recall = recall_score(
            y,
            predictions,
            pos_label=1,
            zero_division=0
        )

        ai_precision = precision_score(
            y,
            predictions,
            pos_label=1,
            zero_division=0
        )

        balanced_acc = (
            balanced_accuracy_score(
                y,
                predictions
            )
        )

        macro_f1 = f1_score(
            y,
            predictions,
            average="macro",
            zero_division=0
        )

        results.append([
            threshold,
            real_recall,
            ai_recall,
            balanced_acc,
            ai_precision,
            macro_f1,
        ])

        print(
            f"{threshold:9.2f} | "
            f"{real_recall:11.4f} | "
            f"{ai_recall:9.4f} | "
            f"{balanced_acc:13.4f} | "
            f"{ai_precision:12.4f} | "
            f"{macro_f1:8.4f}"
        )

    # --------------------------------------------------------
    # Results dataframe
    # --------------------------------------------------------

    results_df = pd.DataFrame(
        results,
        columns=[
            "threshold",
            "real_recall",
            "ai_recall",
            "balanced_accuracy",
            "ai_precision",
            "macro_f1",
        ]
    )

    # --------------------------------------------------------
    # Select recommended threshold
    #
    # Constraint:
    # AI recall must remain >= 90%.
    #
    # Among those thresholds:
    # maximize REAL recall,
    # then balanced accuracy.
    # --------------------------------------------------------

    acceptable = results_df[
        results_df["ai_recall"] >= 0.90
    ]

    if len(acceptable) > 0:

        best = acceptable.sort_values(
            [
                "real_recall",
                "balanced_accuracy",
            ],
            ascending=False
        ).iloc[0]

    else:

        print(
            "\nWARNING: No threshold keeps "
            "AI recall >= 90%."
        )

        best = results_df.sort_values(
            "balanced_accuracy",
            ascending=False
        ).iloc[0]

    # --------------------------------------------------------
    # Best threshold details
    # --------------------------------------------------------

    best_threshold = float(
        best["threshold"]
    )

    best_predictions = (
        prob_ai >= best_threshold
    ).astype(int)

    best_matrix = confusion_matrix(
        y,
        best_predictions
    )

    print(
        "\n================================"
    )

    print(
        "RECOMMENDED THRESHOLD"
    )

    print(
        "================================"
    )

    print(
        "Threshold:",
        best_threshold
    )

    print(
        "REAL recall:",
        f"{best['real_recall']:.4f}"
    )

    print(
        "AI recall:",
        f"{best['ai_recall']:.4f}"
    )

    print(
        "Balanced accuracy:",
        f"{best['balanced_accuracy']:.4f}"
    )

    print(
        "AI precision:",
        f"{best['ai_precision']:.4f}"
    )

    print(
        "Macro F1:",
        f"{best['macro_f1']:.4f}"
    )

    print(
        "\nConfusion Matrix:"
    )

    print(
        best_matrix
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    results_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    # --------------------------------------------------------
    # Save recommended threshold
    # --------------------------------------------------------

    with open(
        OUTPUT_THRESHOLD,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            f"threshold={best_threshold}\n"
        )

        file.write(
            f"real_recall={best['real_recall']}\n"
        )

        file.write(
            f"ai_recall={best['ai_recall']}\n"
        )

        file.write(
            f"balanced_accuracy="
            f"{best['balanced_accuracy']}\n"
        )

        file.write(
            f"ai_precision="
            f"{best['ai_precision']}\n"
        )

        file.write(
            f"macro_f1={best['macro_f1']}\n"
        )

    print(
        "\nSaved:"
    )

    print(
        OUTPUT_CSV
    )

    print(
        OUTPUT_THRESHOLD
    )

    print(
        "\nThreshold analysis complete."
    )


if __name__ == "__main__":
    main()