"""M2 robustness evaluator for labeled PCM WAV files against a running M1 API.

The original files are never modified. Scenarios are generated in memory:
clean, low_volume, noise_20db, telephone_8k, and quantized_8bit.
Manifest columns: path,label,language.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import math
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

from .evaluate import summarize
from .stream_microphone import API, Runner, Windows, mono, parser as stream_parser, wav_blocks


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    blocks = list(wav_blocks(path, 30.0))
    if not blocks:
        raise ValueError("WAV file is empty")
    rates = {rate for _, rate in blocks}
    if len(rates) != 1:
        raise ValueError("WAV sample rate changed while reading")
    return np.concatenate([data for data, _ in blocks]), rates.pop()


def _resample(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate:
        return mono(samples)
    divisor = math.gcd(source_rate, target_rate)
    return mono(resample_poly(mono(samples), target_rate // divisor, source_rate // divisor))


def make_variant(samples: np.ndarray, rate: int, scenario: str, seed: int = 26104) -> tuple[np.ndarray, int]:
    x = mono(samples).astype(np.float64, copy=True)
    if scenario == "clean":
        return x, rate
    if scenario == "low_volume":
        return np.clip(x * 0.25, -1, 1), rate
    if scenario == "noise_20db":
        rms = float(np.sqrt(np.mean(x * x)))
        if rms == 0:
            return x, rate
        rng = np.random.default_rng(seed)
        noise_rms = rms / (10 ** (20 / 20))
        noise = rng.normal(0.0, noise_rms, size=x.shape)
        return np.clip(x + noise, -1, 1), rate
    if scenario == "telephone_8k":
        return _resample(x, rate, 8000), 8000
    if scenario == "quantized_8bit":
        return np.clip(np.round(x * 127.0) / 127.0, -1, 1), rate
    raise ValueError(f"unknown scenario: {scenario}")


def classify_array(api: API, samples: np.ndarray, rate: int, language: str, scenario: str) -> dict:
    options = stream_parser().parse_args(["--language", language, "--api-url", api.base_url])
    log = io.StringIO()
    runner = Runner(options, log, api=api)
    window = Windows(round(rate * options.window), round(rate * options.hop))
    with contextlib.redirect_stdout(io.StringIO()):
        for offset, chunk in window.feed(samples):
            runner.process(chunk, rate, offset, f"robustness:{scenario}:{offset}")
        tail = window.tail()
        if tail is not None:
            offset, chunk = tail
            runner.process(chunk, rate, offset, f"robustness:{scenario}:{offset}")
    chunks = [json.loads(line) for line in log.getvalue().splitlines()]
    labels = [row["status"] for row in chunks if row.get("status") in ("REAL", "AI_GENERATED")]
    real, ai = labels.count("REAL"), labels.count("AI_GENERATED")
    predicted = "INCONCLUSIVE" if runner.failed or real == ai else ("REAL" if real > ai else "AI_GENERATED")
    return {"predicted": predicted, "chunks": chunks, "failed": runner.failed}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument(
        "--scenarios",
        default="clean,low_volume,noise_20db,telephone_8k,quantized_8bit",
        help="Comma-separated scenario names",
    )
    args = parser.parse_args(argv)

    scenarios = [value.strip() for value in args.scenarios.split(",") if value.strip()]
    allowed = {"clean", "low_volume", "noise_20db", "telephone_8k", "quantized_8bit"}
    if not scenarios or any(value not in allowed for value in scenarios):
        parser.error(f"scenarios must be chosen from {sorted(allowed)}")
    if not args.manifest.is_file():
        parser.error(f"manifest not found: {args.manifest}")

    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        items = list(csv.DictReader(handle))
    if not items:
        parser.error("manifest contains no rows")

    api = API(args.api_url)
    health = api.health()
    all_results: list[dict] = []
    by_scenario: dict[str, list[dict]] = {scenario: [] for scenario in scenarios}

    for item_index, item in enumerate(items, start=1):
        label = (item.get("label") or "").strip()
        language = (item.get("language") or "").strip()
        if label not in ("REAL", "AI_GENERATED") or language not in ("English", "Hindi", "Tamil"):
            parser.error("Every row needs label REAL/AI_GENERATED and language English/Hindi/Tamil")
        source = Path(item.get("path") or "")
        if not source.is_absolute():
            source = (args.manifest.parent / source).resolve()
        try:
            samples, rate = read_wav(source)
        except Exception as exc:
            for scenario in scenarios:
                row = {
                    "path": item.get("path"), "label": label, "language": language,
                    "scenario": scenario, "predicted": "INCONCLUSIVE", "error": str(exc), "chunks": [],
                }
                all_results.append(row); by_scenario[scenario].append(row)
            continue

        for scenario_index, scenario in enumerate(scenarios):
            seed = 26104 + item_index * 101 + scenario_index
            try:
                variant, variant_rate = make_variant(samples, rate, scenario, seed)
                outcome = classify_array(api, variant, variant_rate, language, scenario)
                row = {
                    "path": item.get("path"), "label": label, "language": language,
                    "scenario": scenario, "source_rate": rate, "variant_rate": variant_rate,
                    "predicted": outcome["predicted"], "error": None, "chunks": outcome["chunks"],
                }
            except Exception as exc:
                row = {
                    "path": item.get("path"), "label": label, "language": language,
                    "scenario": scenario, "predicted": "INCONCLUSIVE", "error": str(exc), "chunks": [],
                }
            all_results.append(row)
            by_scenario[scenario].append(row)

    summaries = {scenario: summarize(rows) for scenario, rows in by_scenario.items()}
    result = {
        "health": health,
        "scenarios": scenarios,
        "summary_by_scenario": summaries,
        "results": all_results,
        "note": (
            "These are deterministic software perturbations. A physical speaker replay must still be "
            "tested with a real loudspeaker, room and microphone."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(summaries, indent=2))
    print(f"Report: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
