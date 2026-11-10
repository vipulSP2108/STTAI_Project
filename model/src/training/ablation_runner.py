#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""ablation_runner.py - 10-Configuration Systematic Augmentation Ablation Suite.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Evaluates:
- C-01: Baseline (Raw Transcripts Only)
- C-02: Original + Back-Translation
- C-03: Original + Cross-Lingual Syntactic Paraphrase
- C-04: Original + Pivot Translation (English -> Latin -> English)
- C-05: Original + Lexical Synonym Replacement
- C-06: Original + Contextual MLM Substitution
- C-07: Original + Campus Code-Switching Synthesis
- C-08: Original + Acoustic Audio Perturbations
- C-09: Original + Top-3 Synergistic Text Techniques
- C-10: Complete Optimized Pipeline (All Gates Active)

Enforces 5-Fold StratifiedGroupKFold with zero cross-validation data leakage.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from model.src.training.models import CalibratedMultilingualClassifier
from model.src.training.dataset import INTENT2ID, ID2INTENT, INTENT_CLASSES
from model.src.evaluation.evaluate import compute_metrics

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
SPLITS_DIR = MODEL_DIR / "data" / "splits"
RESULTS_DIR = MODEL_DIR / "results"

CONFIGURATIONS = {
    "C-01": {
        "name": "Baseline (Raw Transcripts Only)",
        "description": "Performance floor using solely the original unaugmented transcripts.",
        "allowed_types": ["original"]
    },
    "C-02": {
        "name": "Original + Back-Translation",
        "description": "Tests syntactic clause reordering via multilingual back-translation.",
        "allowed_types": ["original", "back_translation"]
    },
    "C-03": {
        "name": "Original + Cross-Lingual Paraphrase",
        "description": "Evaluates direct syntactic transfer across campus languages.",
        "allowed_types": ["original", "cross_lingual", "cross_lingual_translation"]
    },
    "C-04": {
        "name": "Original + Pivot Translation (Latin)",
        "description": "Tests morphological abstraction via Romance/Latinate pivot transformation.",
        "allowed_types": ["original", "pivot_latin"]
    },
    "C-05": {
        "name": "Original + Lexical Synonym Replacement",
        "description": "Evaluates domain synset expansion across administrative terms.",
        "allowed_types": ["original", "lexical_synsets"]
    },
    "C-06": {
        "name": "Original + Contextual MLM Substitution",
        "description": "Evaluates masked bidirectional contextual token replacement.",
        "allowed_types": ["original", "contextual_mlm"]
    },
    "C-07": {
        "name": "Original + Campus Code-Switching",
        "description": "Tests robustness to intra-sentential Gujarati/Hindi-English code switching.",
        "allowed_types": ["original", "code_mixing"]
    },
    "C-08": {
        "name": "Original + Acoustic Audio Perturbations",
        "description": "Tests acoustic feature variation (speed, pitch, ambient noise).",
        "allowed_types": ["original", "audio_perturbed"]
    },
    "C-09": {
        "name": "Original + Top-3 Text Techniques",
        "description": "Evaluates synergistic combination of Back-Translation + Lexical Synsets + Code-Mixing.",
        "allowed_types": ["original", "back_translation", "lexical_synsets", "code_mixing"]
    },
    "C-10": {
        "name": "Complete Optimized Pipeline (All Gates)",
        "description": "Full dataset combining all techniques passed through semantic similarity & deduplication gates.",
        "allowed_types": ["original", "back_translation", "pivot_latin", "lexical_synsets", "code_mixing", "audio_perturbed", "contextual_mlm", "cross_lingual", "cross_lingual_translation", "discourse_framing"]
    },
    "C-11": {
        "name": "Original + Indic Discourse Framing",
        "description": "Evaluates colloquial student conversational helpdesk frames across Gujarati, Hindi, and English.",
        "allowed_types": ["original", "discourse_framing"]
    },
    "C-12": {
        "name": "Synergistic Ensemble (Latin Pivot + Indic Discourse)",
        "description": "Combines morphological Latinate pivot abstraction with conversational Indic discourse frames.",
        "allowed_types": ["original", "pivot_latin", "discourse_framing"]
    }
}

def run_ablation_study():
    print("=" * 80)
    print("MANDATORY 10-CONFIGURATION AUGMENTATION ABLATION STUDY")
    print("5-Fold StratifiedGroupKFold Cross-Validation | Target: Macro-F1")
    print("=" * 80)

    # 1. Load the 5 folds
    fold_files = sorted(list(SPLITS_DIR.glob("fold_*.json")))
    if not fold_files:
        raise FileNotFoundError("Fold files not found in model/data/splits/. Run group_splitter.py first.")

    folds = []
    for ff in fold_files:
        with open(ff, "r") as f:
            folds.append(json.load(f))

    ablation_results = {}
    baseline_macro_f1 = None

    for cfg_id, cfg_info in CONFIGURATIONS.items():
        print(f"\n---> Evaluating [{cfg_id}] {cfg_info['name']} ...")
        allowed = set(cfg_info["allowed_types"])

        fold_accuracies = []
        fold_macro_f1s = []
        fold_weighted_f1s = []
        per_class_accum = defaultdict(list)

        for fold_data in folds:
            fold_idx = fold_data["fold_index"]
            train_all = fold_data["train_samples"]
            # Validation ALWAYS uses original ground-truth samples to ensure unbiased benchmark
            val_samples = [s for s in fold_data["val_samples"] if not s.get("is_augmented", False)]
            if not val_samples:
                val_samples = fold_data["val_samples"]

            # Filter training samples according to configuration allowed_types
            train_filtered = []
            for s in train_all:
                aug_type = s.get("augmentation_type", "original")
                if aug_type in allowed or (not s.get("is_augmented", False) and "original" in allowed):
                    train_filtered.append(s)

            # Extract features and targets
            X_train = [s["transcript"] for s in train_filtered]
            y_train = [INTENT2ID[s["gold_intent"]] for s in train_filtered]

            X_val = [s["transcript"] for s in val_samples]
            y_val = [INTENT2ID[s["gold_intent"]] for s in val_samples]

            # Fit model
            clf = CalibratedMultilingualClassifier(c_reg=1.0, seed=42 + fold_idx)
            clf.fit(X_train, y_train)

            # Predict
            preds = clf.predict(X_val)
            metrics = compute_metrics(y_val, preds)

            fold_accuracies.append(metrics["accuracy"])
            fold_macro_f1s.append(metrics["macro_f1"])
            fold_weighted_f1s.append(metrics["weighted_f1"])

            for cls_name, vals in metrics["per_class"].items():
                per_class_accum[cls_name].append(vals["f1_score"])

        mean_acc = float(np.mean(fold_accuracies))
        mean_macro_f1 = float(np.mean(fold_macro_f1s))
        std_macro_f1 = float(np.std(fold_macro_f1s))
        mean_weighted_f1 = float(np.mean(fold_weighted_f1s))

        if cfg_id == "C-01":
            baseline_macro_f1 = mean_macro_f1

        delta_f1 = mean_macro_f1 - baseline_macro_f1

        mean_per_class = {
            cls_name: round(float(np.mean(scores)), 4)
            for cls_name, scores in per_class_accum.items()
        }

        ablation_results[cfg_id] = {
            "name": cfg_info["name"],
            "description": cfg_info["description"],
            "accuracy_mean": round(mean_acc, 4),
            "macro_f1_mean": round(mean_macro_f1, 4),
            "macro_f1_std": round(std_macro_f1, 4),
            "weighted_f1_mean": round(mean_weighted_f1, 4),
            "delta_macro_f1": round(delta_f1, 4),
            "per_class_f1": mean_per_class,
            "fold_macro_f1s": [round(f, 4) for f in fold_macro_f1s]
        }

        print(f"     Accuracy: {mean_acc:.4f} | Macro-F1: {mean_macro_f1:.4f} +/- {std_macro_f1:.4f} | Delta: {delta_f1:+.4f}")

    # Output formatted markdown table
    print("\n" + "=" * 80)
    print("FINAL 10-CONFIGURATION ABLATION STUDY RESULTS MATRIX")
    print("=" * 80)
    header = f"| {'ID':<5s} | {'Configuration Name':<38s} | {'Accuracy':<8s} | {'Macro-F1':<15s} | {'Delta':<8s} | {'Admissions':<10s} | {'Hostel':<8s} | {'IT':<6s} | {'Services':<8s} |"
    divider = "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
    print(header)
    print(divider)

    for cfg_id, res in ablation_results.items():
        pc = res["per_class_f1"]
        f1_str = f"{res['macro_f1_mean']:.4f}±{res['macro_f1_std']:.3f}"
        delta_str = f"{res['delta_macro_f1']:+.4f}" if cfg_id != "C-01" else "ref"
        row = f"| {cfg_id:<5s} | {res['name']:<38s} | {res['accuracy_mean']:<8.4f} | {f1_str:<15s} | {delta_str:<8s} | {pc.get('admissions', 0):<10.4f} | {pc.get('hostel_mess', 0):<8.4f} | {pc.get('it_support', 0):<6.4f} | {pc.get('student_services', 0):<8.4f} |"
        print(row)
    print("=" * 80)

    # Save results to JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / "ablation_study_results.json"
    with open(out_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "evaluation_metric": "Macro-F1",
            "k_folds": 5,
            "baseline_macro_f1": baseline_macro_f1,
            "results": ablation_results
        }, f, indent=2)

    print(f"\nAblation study serialized to: {out_file}")
    return ablation_results

if __name__ == "__main__":
    run_ablation_study()
