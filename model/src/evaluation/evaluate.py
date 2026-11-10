#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""evaluate.py - Classification Evaluation & Metrics Suite.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Computes Macro-F1, Weighted-F1, Precision, Recall, and Accuracy.
2. Computes per-class F1 breakdown for the 4 canonical intent targets.
3. Formats clean 4x4 confusion matrices.
4. Strictly omits per-speaker breakdowns to protect participant privacy.
"""

from typing import List, Dict, Any
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from model.src.training.dataset import INTENT_CLASSES, INTENT2ID, ID2INTENT

def compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    # Per-class breakdown
    p_per_class, r_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=list(range(len(INTENT_CLASSES))), zero_division=0
    )

    per_class_metrics = {}
    for idx, cls_name in enumerate(INTENT_CLASSES):
        per_class_metrics[cls_name] = {
            "precision": round(float(p_per_class[idx]), 4),
            "recall": round(float(r_per_class[idx]), 4),
            "f1_score": round(float(f1_per_class[idx]), 4),
            "support": int(support_per_class[idx])
        }

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(INTENT_CLASSES)))).tolist()

    return {
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(macro_p), 4),
        "macro_recall": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "per_class": per_class_metrics,
        "confusion_matrix": cm,
        "labels": INTENT_CLASSES
    }

def print_metrics_summary(metrics: Dict[str, Any], title: str = "EVALUATION METRICS"):
    print("=" * 70)
    print(f"{title}")
    print("=" * 70)
    print(f"Accuracy        : {metrics['accuracy']:.4f}")
    print(f"Macro-F1        : {metrics['macro_f1']:.4f}")
    print(f"Weighted-F1     : {metrics['weighted_f1']:.4f}")
    print(f"Macro-Precision : {metrics['macro_precision']:.4f}")
    print(f"Macro-Recall    : {metrics['macro_recall']:.4f}\n")
    print("Per-Class Metrics:")
    print(f"  {'Class':<18s} | {'Precision':<9s} | {'Recall':<7s} | {'F1-Score':<8s} | {'Support':<7s}")
    print("  " + "-" * 58)
    for cls_name, vals in metrics["per_class"].items():
        print(f"  {cls_name:<18s} | {vals['precision']:<9.4f} | {vals['recall']:<7.4f} | {vals['f1_score']:<8.4f} | {vals['support']:<7d}")
    print("=" * 70)

if __name__ == "__main__":
    y_t = [0, 1, 2, 3, 0, 1, 2, 3]
    y_p = [0, 1, 2, 3, 0, 1, 1, 3]
    res = compute_metrics(y_t, y_p)
    print_metrics_summary(res)
