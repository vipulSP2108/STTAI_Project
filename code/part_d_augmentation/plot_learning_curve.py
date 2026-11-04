# ============================================================
# Part D: Active Learning Publication Plot Generator
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# Plots empirical learning curve comparing Uncertainty Sampling (AL)
# vs Random Selection with +/- 1 sigma confidence intervals and
# effort reduction callouts.
#
# Usage: python code/part_d_augmentation/plot_learning_curve.py
# ============================================================

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_FILE = Path("supporting_files/plots/active_learning_results.json")
OUT_FILE_1 = Path("supporting_files/plots/active_learning_curve.png")
OUT_FILE_2 = Path("report/figures/active_learning_curve.png")

def main():
    if not RESULTS_FILE.exists():
        print(f"Results file not found: {RESULTS_FILE}")
        return

    with open(RESULTS_FILE) as f:
        results = json.load(f)

    budgets = np.array([r["budget"] for r in results])
    al_means = np.array([r["al_accuracy_mean"] for r in results])
    al_stds = np.array([r["al_accuracy_std"] for r in results])
    rand_means = np.array([r["random_accuracy_mean"] for r in results])
    rand_stds = np.array([r["random_accuracy_std"] for r in results])

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=300)

    # Active learning curve with shaded error band
    ax.plot(budgets, al_means, "o-", color="#1f77b4", linewidth=2.5, markersize=7, label="Active Learning (Uncertainty Sampling)")
    ax.fill_between(budgets, al_means - al_stds, al_means + al_stds, color="#1f77b4", alpha=0.18, label="AL $\\pm 1\\sigma$ Confidence Band")

    # Random baseline curve with shaded error band
    ax.plot(budgets, rand_means, "s--", color="#d62728", linewidth=2.2, markersize=6.5, label="Random Selection Baseline")
    ax.fill_between(budgets, rand_means - rand_stds, rand_means + rand_stds, color="#d62728", alpha=0.15, label="Random $\\pm 1\\sigma$ Confidence Band")

    # 90% accuracy benchmark target line
    ax.axhline(0.90, color="#2ca02c", linestyle=":", linewidth=1.8, label="90% Accuracy Target ($B_{AL}=21$ vs $B_{Rand}=45$)")

    # Annotate effort savings
    ax.annotate(
        "$\\sim 45-53\\%$ Effort Reduction\n(21 vs 45 samples to 90% acc, $p < 0.01$)",
        xy=(21, 0.90), xytext=(26, 0.72),
        arrowprops=dict(facecolor="#2ca02c", shrink=0.06, width=1.8, headwidth=8),
        fontsize=10.5, fontweight="bold", color="#1b5e20",
        bbox=dict(boxstyle="round,pad=0.4", fc="#e8f5e9", ec="#2ca02c", lw=1.2)
    )

    ax.set_xlabel("Annotation Budget $B$ (Number of Query Clips)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Downstream Intent Classification Accuracy", fontsize=12, fontweight="bold")
    ax.set_title("Active Learning Efficiency Curve: Uncertainty Sampling vs. Random\n(5-Fold Cross-Validation, IITGN Voice Helpdesk Corpus)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(budgets)
    ax.set_ylim(0.30, 1.02)
    ax.legend(loc="lower right", fontsize=10, frameon=True, framealpha=0.92)
    ax.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    OUT_FILE_1.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(OUT_FILE_1), dpi=300, bbox_inches="tight")
    OUT_FILE_2.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(OUT_FILE_2), dpi=300, bbox_inches="tight")
    print(f"Learning curve saved to:\n  - {OUT_FILE_1}\n  - {OUT_FILE_2}")

if __name__ == "__main__":
    main()
