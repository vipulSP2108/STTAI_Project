#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""unseen_speaker_test.py - Unseen Speaker & Language Slice Generalization Benchmark.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Evaluates:
1. Generalization across completely held-out student participants.
2. Per-language performance slices:
   - Pure Gujarati queries
   - Pure Hindi queries
   - Pure English queries
   - Code-mixed queries
3. Generates benchmark results in model/results/unseen_speaker_benchmark.json.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from model.src.training.models import CalibratedMultilingualClassifier
from model.src.training.dataset import INTENT2ID, ID2INTENT
from model.src.evaluation.evaluate import compute_metrics

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
SPLITS_DIR = MODEL_DIR / "data" / "splits"
RESULTS_DIR = MODEL_DIR / "results"

def run_unseen_speaker_benchmark():
    print("=" * 70)
    print("OUT-OF-DOMAIN & UNSEEN SPEAKER GENERALIZATION BENCHMARK")
    print("=" * 70)

    test_file = SPLITS_DIR / "independent_test_set.json"
    test_samples = []
    if test_file.exists():
        with open(test_file, "r") as f:
            test_data = json.load(f)
        test_samples = test_data.get("samples", [])

    if not test_samples:
        print("Independent test benchmark set empty. Using Fold 1 held-out test split (strictly unseen groups/speakers).")
        fold_1_file = SPLITS_DIR / "fold_1.json"
        with open(fold_1_file, "r") as f:
            fold_data = json.load(f)
        train_samples = fold_data["train_samples"]
        test_samples = [s for s in fold_data["val_samples"] if not s.get("is_augmented", False)]
    else:
        with open(SPLITS_DIR / "fold_1.json", "r") as f:
            train_samples = json.load(f)["train_samples"]

    # Load manifest to get language mappings
    manifest_file = MODEL_DIR / "data" / "metadata" / "internal_manifest.json"
    lang_map = {}
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            for item in json.load(f).get("manifest", []):
                lang_map[item["uuid"]] = item.get("languages", ["Unknown"])

    for s in test_samples:
        if "languages" not in s:
            s["languages"] = lang_map.get(s["uuid"], ["Unknown"])

    if not test_samples:
        print("No test samples available for benchmark.")
        return

    print(f"Training Classifier on {len(train_samples)} training samples...")
    X_train = [s["transcript"] for s in train_samples]
    y_train = [INTENT2ID[s["gold_intent"]] for s in train_samples]

    clf = CalibratedMultilingualClassifier(c_reg=2.0, seed=42)
    clf.fit(X_train, y_train)

    # Evaluate overall test set
    X_test = [s["transcript"] for s in test_samples]
    y_test = [INTENT2ID[s["gold_intent"]] for s in test_samples]
    preds = clf.predict(X_test)
    overall_metrics = compute_metrics(y_test, preds)

    print(f"\nOverall Unseen Benchmark Performance:")
    print(f"Accuracy : {overall_metrics['accuracy']:.4f}")
    print(f"Macro-F1 : {overall_metrics['macro_f1']:.4f}")

    # Slice evaluation by language
    slices = defaultdict(lambda: {"y_true": [], "y_pred": []})
    for s, pred in zip(test_samples, preds):
        langs = s.get("languages", ["Unknown"])
        if len(langs) > 1:
            lang_key = "Code-Mixed"
        elif len(langs) == 1:
            lang_key = f"Pure {langs[0]}"
        else:
            lang_key = "Unknown"
        slices[lang_key]["y_true"].append(INTENT2ID[s["gold_intent"]])
        slices[lang_key]["y_pred"].append(pred)

    slice_metrics = {}
    print("\nLanguage Slice Breakdown:")
    for lang_key, data in slices.items():
        if len(data["y_true"]) >= 2:
            m = compute_metrics(data["y_true"], data["y_pred"])
            slice_metrics[lang_key] = {
                "sample_count": len(data["y_true"]),
                "accuracy": m["accuracy"],
                "macro_f1": m["macro_f1"]
            }
            print(f"  - {lang_key:<18s} (N={len(data['y_true']):2d}): Accuracy={m['accuracy']:.4f} | Macro-F1={m['macro_f1']:.4f}")

    # Save benchmark
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    bench_file = RESULTS_DIR / "unseen_speaker_benchmark.json"
    with open(bench_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_test_samples": len(test_samples),
            "overall_metrics": overall_metrics,
            "language_slices": slice_metrics
        }, f, indent=2)

    print(f"\nBenchmark saved to: {bench_file}")
    print("=" * 70)
    return overall_metrics

if __name__ == "__main__":
    run_unseen_speaker_benchmark()
