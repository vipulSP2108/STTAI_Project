# plot_learning_curve.py - Generates active learning efficiency plot.
# CS203 Assignment 1 - Part D
# This plot is Figure X in the report. Data behind it: active_learning_results.json

import json
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_FILE = Path("supporting_files/plots/active_learning_results.json")
OUT_FILE     = Path("supporting_files/plots/active_learning_curve.png")

def main():
    if not RESULTS_FILE.exists():
        print(f"Results file not found: {RESULTS_FILE}")
        print("Run active_learning.py first.")
        return

    with open(RESULTS_FILE) as f:
        results = json.load(f)

    budgets    = [r["budget"] for r in results]
    al_covs    = [r.get("al_accuracy_mean", r.get("al_coverage", 0)) for r in results]
    rand_covs  = [r.get("random_accuracy_mean", r.get("random_coverage", 0)) for r in results]
    y_label    = "Intent Accuracy / Coverage" if "al_accuracy_mean" in results[0] else "Intent Class Coverage (fraction of 4 classes)"

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(budgets, al_covs,   "b-o", linewidth=2, markersize=8, label="Active Learning (Whisper confidence)")
    ax.plot(budgets, rand_covs, "r--s",linewidth=2, markersize=8, label="Random Selection")
    ax.set_xlabel("Labelling Budget (# clips)", fontsize=13)
    ax.set_ylabel(y_label, fontsize=13)
    ax.set_title("Active Learning vs Random Selection\nLabel Efficiency Curve — CS203 Project 5", fontsize=14)
    ax.set_xticks(budgets)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(OUT_FILE), dpi=300, bbox_inches="tight")
    print(f"Plot saved: {OUT_FILE}")

if __name__ == "__main__": main()
