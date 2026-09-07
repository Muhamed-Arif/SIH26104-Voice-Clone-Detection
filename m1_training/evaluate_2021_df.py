import os
import glob
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

import joblib
import numpy as np
from scipy.signal import periodogram
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = r"D:\SIH_AIML\models\voice_authenticity_balanced.joblib"
DATASET_DIR = r"D:\SIH_AIML\ASVspoof2021_DF_eval"

FLAC_DIR = os.path.join(
    DATASET_DIR,
    "flac"
)

METADATA = (
    r"D:\SIH_AIML\keys\DF\CM"
    r"\trial_metadata.txt"
)

RESULTS_PATH = (
    r"D:\SIH_AIML\models"
    r"\asvspoof2021_df_part00_threshold090_results.txt"
)

# Use 12 CPU workers
WORKERS = 12

# Threshold selected from 2019 validation
THRESHOLD = 0.45


# ============================================================
# FFMPEG DECODER
# ============================================================

def decode_flac(path):
    """
    Decode FLAC using FFmpeg.
    Converts audio to mono 16 kHz float32.
    """

    command = [
        "ffmpeg",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        path,
        "-f",
        "f32le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "pipe:1",
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if (
        result.returncode != 0
        or not result.stdout
    ):
        raise RuntimeError(
            "FFmpeg failed to decode audio"
        )

    audio = np.frombuffer(
        result.stdout,
        dtype=np.float32
    )

    return audio, 16000


# ============================================================
# 30-FEATURE EXTRACTOR
# SAME FEATURES USED DURING TRAINING
# ============================================================

def extract_features(path):

    y, sr = decode_flac(path)

    if y.size == 0:
        raise RuntimeError(
            "Empty audio"
        )

    y = np.nan_to_num(y)

    y = (
        y /
        (np.max(np.abs(y)) + 1e-8)
    )

    features = []

    # --------------------------------------------------------
    # 11 TIME-DOMAIN FEATURES
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
    # ZERO CROSSING RATE
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
    # SPECTRAL FEATURES
    # --------------------------------------------------------

    max_samples = min(
        len(y),
        sr * 10
    )

    yy = y[:max_samples]

    if len(yy) < 2:

        raise RuntimeError(
            "Audio too short"
        )

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

    # Spectral centroid
    centroid = (
        np.sum(
            freqs * power
        ) /
        total_power
    )

    # Spectral bandwidth
    bandwidth = np.sqrt(
        np.sum(
            (
                (freqs - centroid) ** 2
            ) * power
        ) /
        total_power
    )

    # Spectral rolloff
    cumulative = np.cumsum(
        power
    )

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

    # Spectral flatness
    flatness = (
        np.exp(
            np.mean(
                np.log(power)
            )
        ) /
        np.mean(power)
    )

    features.extend([
        centroid,
        bandwidth,
        rolloff,
        flatness,
    ])

    # --------------------------------------------------------
    # FIVE FREQUENCY-BAND ENERGY FEATURES
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
                ) /
                total_power
            )

        else:

            energy = 0.0

        features.append(
            energy
        )

    # --------------------------------------------------------
    # EIGHT RMS FEATURES
    # --------------------------------------------------------

    frame_size = int(
        sr * 0.025
    )

    hop = int(
        sr * 0.010
    )

    rms_values = []

    if len(y) >= frame_size:

        for start in range(
            0,
            len(y) - frame_size + 1,
            hop
        ):

            frame = y[
                start:
                start + frame_size
            ]

            rms = np.sqrt(
                np.mean(
                    frame ** 2
                ) +
                1e-10
            )

            rms_values.append(
                rms
            )

            # Same limit as training
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
    # DURATION
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
# WORKER FUNCTION
# ============================================================

def process_one(item):

    path, label = item

    try:

        features = extract_features(
            path
        )

        return (
            features,
            label,
            True
        )

    except Exception:

        return (
            None,
            label,
            False
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "================================"
    )

    print(
        "ASVSPOOF 2021 DF OOD EVALUATION"
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

    model = artifact[
        "model"
    ]

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
    # Show threshold
    # --------------------------------------------------------

    print(
        "\nDecision threshold:",
        THRESHOLD
    )

    print(
        "Threshold rule:"
    )

    print(
        "P(AI_GENERATED) >= 0.90"
        " -> AI_GENERATED"
    )

    print(
        "P(AI_GENERATED) <  0.90"
        " -> REAL"
    )

    # --------------------------------------------------------
    # Load metadata
    # --------------------------------------------------------

    print(
        "\nLoading metadata..."
    )

    labels = {}

    with open(
        METADATA,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            parts = (
                line.strip().split()
            )

            if len(parts) < 6:
                continue

            utterance_id = parts[1]

            label_text = (
                parts[5].lower()
            )

            if label_text == "bonafide":

                labels[
                    utterance_id
                ] = 0

            elif label_text == "spoof":

                labels[
                    utterance_id
                ] = 1

    print(
        "Metadata labels:",
        len(labels)
    )

    if len(labels) == 0:

        raise RuntimeError(
            "No labels found."
        )

    # --------------------------------------------------------
    # Find FLAC files
    # --------------------------------------------------------

    print(
        "\nScanning FLAC files..."
    )

    files = glob.glob(
        os.path.join(
            FLAC_DIR,
            "*.flac"
        )
    )

    print(
        "FLAC files found:",
        len(files)
    )

    # --------------------------------------------------------
    # Match files to labels
    # --------------------------------------------------------

    items = []

    missing_labels = 0

    for path in files:

        utterance_id = os.path.splitext(
            os.path.basename(path)
        )[0]

        if utterance_id in labels:

            items.append(
                (
                    path,
                    labels[
                        utterance_id
                    ]
                )
            )

        else:

            missing_labels += 1

    print(
        "Files with labels:",
        len(items)
    )

    print(
        "Missing labels:",
        missing_labels
    )

    # --------------------------------------------------------
    # Parallel feature extraction
    # --------------------------------------------------------

    print(
        f"\nStarting parallel evaluation "
        f"with {WORKERS} CPU workers..."
    )

    X = []
    y_true = []

    completed = 0
    errors = 0

    total = len(items)

    with ProcessPoolExecutor(
        max_workers=WORKERS
    ) as executor:

        futures = [
            executor.submit(
                process_one,
                item
            )
            for item in items
        ]

        for future in as_completed(
            futures
        ):

            features, label, success = (
                future.result()
            )

            completed += 1

            if success:

                X.append(
                    features
                )

                y_true.append(
                    label
                )

            else:

                errors += 1

            if (
                completed % 1000 == 0
                or completed == total
            ):

                percentage = (
                    completed *
                    100 /
                    total
                )

                print(
                    f"\rProcessed: "
                    f"{completed}/{total} "
                    f"({percentage:.1f}%) "
                    f"| successful: "
                    f"{len(X)} "
                    f"| errors: "
                    f"{errors}",
                    end="",
                    flush=True
                )

    print()

    # --------------------------------------------------------
    # Build feature matrix
    # --------------------------------------------------------

    if not X:

        raise RuntimeError(
            "No samples processed."
        )

    X = np.asarray(
        X,
        dtype=np.float32
    )

    y_true = np.asarray(
        y_true,
        dtype=np.int32
    )

    print(
        "\n================================"
    )

    print(
        "DATA PROCESSING SUMMARY"
    )

    print(
        "================================"
    )

    print(
        "FLAC files found:",
        len(files)
    )

    print(
        "Files with labels:",
        total
    )

    print(
        "Processed successfully:",
        len(X)
    )

    print(
        "Missing labels:",
        missing_labels
    )

    print(
        "Decode/feature errors:",
        errors
    )

    print(
        "Feature matrix:",
        X.shape
    )

    # --------------------------------------------------------
    # Model probabilities
    # --------------------------------------------------------

    print(
        "\nCalculating model probabilities..."
    )

    if not hasattr(
        model,
        "predict_proba"
    ):

        raise RuntimeError(
            "Model does not support predict_proba()."
        )

    probability = (
        model.predict_proba(X)[:, 1]
    )

    # --------------------------------------------------------
    # Apply 0.90 threshold
    # --------------------------------------------------------

    predictions = (
        probability >= THRESHOLD
    ).astype(int)

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_true,
        predictions
    )

    balanced_accuracy = (
        balanced_accuracy_score(
            y_true,
            predictions
        )
    )

    try:

        roc_auc = roc_auc_score(
            y_true,
            probability
        )

    except ValueError:

        roc_auc = None

    matrix = confusion_matrix(
        y_true,
        predictions
    )

    report = classification_report(
        y_true,
        predictions,
        target_names=[
            "REAL",
            "AI_GENERATED"
        ],
        zero_division=0
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "ASVSPOOF 2021 DF OOD RESULTS"
    )

    print(
        "================================"
    )

    print(
        "Threshold:",
        THRESHOLD
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
        (
            roc_auc
            if roc_auc is not None
            else "unavailable"
        )
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

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "ASVspoof 2021 DF Part00 "
            "OOD Evaluation\n"
        )

        file.write(
            "================================\n"
        )

        file.write(
            f"Decision threshold: "
            f"{THRESHOLD}\n"
        )

        file.write(
            f"FLAC files found: "
            f"{len(files)}\n"
        )

        file.write(
            f"Files with labels: "
            f"{total}\n"
        )

        file.write(
            f"Processed successfully: "
            f"{len(X)}\n"
        )

        file.write(
            f"Missing labels: "
            f"{missing_labels}\n"
        )

        file.write(
            f"Decode/feature errors: "
            f"{errors}\n"
        )

        file.write(
            f"Feature matrix: "
            f"{X.shape}\n"
        )

        file.write(
            f"Accuracy: "
            f"{accuracy}\n"
        )

        file.write(
            f"Balanced Accuracy: "
            f"{balanced_accuracy}\n"
        )

        file.write(
            f"ROC-AUC: "
            f"{roc_auc}\n"
        )

        file.write(
            "\nConfusion Matrix:\n"
        )

        file.write(
            str(matrix)
        )

        file.write(
            "\n\nClassification Report:\n"
        )

        file.write(
            report
        )

    print(
        "\nResults saved to:"
    )

    print(
        RESULTS_PATH
    )

    print(
        "\nEvaluation complete."
    )


if __name__ == "__main__":
    main()