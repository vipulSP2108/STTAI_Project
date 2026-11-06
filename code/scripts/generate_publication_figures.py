#!/usr/bin/env python3
"""
Generate high-resolution publication-quality figures for Assignment 1 & 2 reports:
1. system_architecture_diagram.png (Complete SLU architecture: ingestion, ASR adaptation, MLP, serving, drift)
2. reproducibility_flowchart.png (Step-by-step reproduction pipeline via Git, DVC, pytest, and training)
3. methodology_retraining_flow.png (Closed-loop drift detection and retraining promotion gating tree)
4. baselines_comparison_chart.png (Comparative multi-metric evaluation across baselines and proposed model)
5. annotation_iaa_progression.png (Two-stage Label Studio IAA progression across rounds)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

os.makedirs("supporting_files/plots", exist_ok=True)

# Set high-resolution styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#94a3b8'
plt.rcParams['axes.linewidth'] = 0.8

# ==============================================================================
# 1. SYSTEM ARCHITECTURE DIAGRAM
# ==============================================================================
def create_system_architecture():
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')

    # Color palette
    c_blue = '#1e40af'     # Ingestion
    c_indigo = '#4338ca'   # ASR
    c_purple = '#6b21a8'   # Intent MLP
    c_emerald = '#047857'  # Serving
    c_amber = '#b45309'    # Monitoring & Retraining

    def draw_box(x, y, w, h, title, subtitle, color, bg_color='#f8fafc', badge=None):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                      facecolor=bg_color, edgecolor=color, linewidth=1.5, zorder=2)
        ax.add_patch(rect)
        # Header banner
        banner = patches.FancyBboxPatch((x, y + h - 4.5), w, 4.5, boxstyle="round,pad=0.2,rounding_size=0.6",
                                        facecolor=color, edgecolor='none', zorder=3)
        ax.add_patch(banner)
        ax.text(x + w/2, y + h - 2.5, title, ha='center', va='center', color='white',
                fontsize=8.5, fontweight='bold', zorder=4)
        ax.text(x + w/2, y + (h - 4.5)/2, subtitle, ha='center', va='center', color='#1e293b',
                fontsize=7.2, linespacing=1.3, zorder=4)
        if badge:
            badge_patch = patches.FancyBboxPatch((x + w - 16, y + h - 3.8), 15, 3.2,
                                                 boxstyle="round,pad=0.1", facecolor='#fef08a', edgecolor='#ca8a04', lw=0.6, zorder=5)
            ax.add_patch(badge_patch)
            ax.text(x + w - 8.5, y + h - 2.2, badge, ha='center', va='center', fontsize=6, fontweight='bold', color='#854d0e', zorder=6)

    def draw_arrow(x1, y1, x2, y2, label=None, color='#64748b', style='->', lw=1.5):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=3, shrinkB=3), zorder=5)
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 1.2, label, ha='center', va='bottom', fontsize=6.5, color='#475569',
                    fontweight='bold', bbox=dict(boxstyle='square,pad=0.1', facecolor='white', edgecolor='none'), zorder=6)

    # Stages
    # Stage 1: Audio Ingestion
    draw_box(2, 28, 16, 20, "1. INGESTION", "• Multi-Format Audio\n• 16 kHz Resampling\n• WebRTC VAD Trim\n• Peak Norm (-1 dBFS)\n• SHA-256 Hashing", c_blue)

    # Stage 2: Whisper Base Adaptation
    draw_box(22, 28, 22, 20, "2. ASR ADAPTATION", "OpenAI Whisper Base\n• Frozen Encoder (21.5M)\n• Trainable Cross-Attn (6.3M)\n• Checkpoint: base_adapted.pt\n• Decoded Hypothesis W", c_indigo, badge="freeze_enc: true")

    # Stage 3: TF-IDF & Intent MLP
    draw_box(48, 28, 22, 20, "3. INTENT ROUTING", "Semantic Intent Head\n• Sub-linear TF-IDF (1-2 gram)\n• 2-Layer MLP (Hidden: 64)\n• Dropout (0.20) + AdamW\n• 6 Campus Classes", c_purple, badge="@Champion (F1: 0.94)")

    # Stage 4: Production Serving
    draw_box(74, 28, 24, 20, "4. SERVING & API", "Production Deployment\n• FastAPI REST (/predict)\n• Streamlit UI (Port 8501)\n• Latency p50: 2,855 ms\n• Real-Time Factor: 0.165", c_emerald, badge="Local Mac M-Series")

    # Lower Stage 5: Continuous Monitoring & Retraining
    draw_box(22, 4, 34, 18, "5. PRODUCTION DRIFT TELEMETRY", "Continuous Telemetry Monitor\n• Streaming Traffic Batches (N=20)\n• Confidence & Length Tracking\n• Two-Sample KS-Test (p < 0.05)\n• Population Stability Index (PSI > 0.25)", c_amber)

    draw_box(60, 4, 38, 18, "6. CLOSED-LOOP RETRAINING GATE", "Active Retraining & Promotion\n• Cohort B (32 shifted clips)\n• In-Domain Rehearsal vs No-Rehearsal\n• Gate: Gain >= +5% & Regress <= 4%\n• LOG-005 PROMOTED | LOG-006 REJECTED", '#0369a1')

    # Arrows between components
    draw_arrow(18, 38, 22, 38, "16kHz WAV")
    draw_arrow(44, 38, 48, 38, "ASR Text Ŵ")
    draw_arrow(70, 38, 74, 38, "Intent Class ŷ")
    draw_arrow(86, 28, 86, 23, "Live Inferences")
    draw_arrow(86, 23, 39, 23, "")
    draw_arrow(39, 23, 39, 22, "")
    draw_arrow(56, 13, 60, 13, "Drift Trigger (p=0.04)")
    draw_arrow(79, 22, 79, 28, "Promote Model", color='#059669', style='->', lw=1.8)

    plt.tight_layout()
    plt.savefig("supporting_files/plots/system_architecture_diagram.png", bbox_inches='tight', dpi=300)
    plt.close()
    print("Generated system_architecture_diagram.png")


# ==============================================================================
# 2. REPRODUCIBILITY FLOWCHART
# ==============================================================================
def create_reproducibility_flowchart():
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 42)
    ax.axis('off')

    steps = [
        ("Step 1: Environment", "Clone Git repository\nCheckout tag: a2-final\nPython 3.13 / pinned deps", '#1e293b'),
        ("Step 2: DVC Pull", "dvc pull\nFetch Records/ & audio/\nVerify SHA-256 hashes", '#0284c7'),
        ("Step 3: Verification", "pytest tests/ -v\n8/8 passing tests\nVerify gold test set hash", '#059669'),
        ("Step 4: Adaptation", "python code/train_asr.py\nFine-tune Whisper cross-attn\nSave whisper_adapted.pt", '#7c3aed'),
        ("Step 5: Offline Valid.", "python validate_offline.py\nLive 29-clip Gold evaluation\nRTF: 0.165, Latency: 2,986ms", '#d97706'),
        ("Step 6: Live API UI", "uvicorn app:app / streamlit\nPOST /predict audio.wav\nInteractive helpdesk UI", '#b91c1c')
    ]

    for i, (title, desc, col) in enumerate(steps):
        x = 2 + i * 16.3
        y = 12
        w = 14.8
        h = 24
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.0",
                                      facecolor='#f8fafc', edgecolor=col, linewidth=1.5, zorder=2)
        ax.add_patch(rect)
        hdr = patches.FancyBboxPatch((x, y + h - 5), w, 5, boxstyle="round,pad=0.2,rounding_size=0.6",
                                     facecolor=col, edgecolor='none', zorder=3)
        ax.add_patch(hdr)
        ax.text(x + w/2, y + h - 2.5, title, ha='center', va='center', color='white',
                fontsize=7.5, fontweight='bold', zorder=4)
        ax.text(x + w/2, y + (h - 5)/2, desc, ha='center', va='center', color='#1e293b',
                fontsize=6.8, linespacing=1.3, zorder=4)

        if i < len(steps) - 1:
            ax.annotate('', xy=(x + w + 1.5, y + h/2), xytext=(x + w, y + h/2),
                        arrowprops=dict(arrowstyle='->', color='#64748b', lw=1.6, shrinkA=1, shrinkB=1), zorder=5)

    # Bottom status banner
    status_box = patches.FancyBboxPatch((2, 2), 96, 6.5, boxstyle="round,pad=0.4",
                                       facecolor='#ecfdf5', edgecolor='#10b981', linewidth=1.2, zorder=2)
    ax.add_patch(status_box)
    ax.text(50, 5.2, "Bit-for-Bit Deterministic Reproducibility Manifest · SHA-256 Pinned Weights · 100% Offline Capable",
            ha='center', va='center', color='#065f46', fontsize=8, fontweight='bold', zorder=4)

    plt.tight_layout()
    plt.savefig("supporting_files/plots/reproducibility_flowchart.png", bbox_inches='tight', dpi=300)
    plt.close()
    print("Generated reproducibility_flowchart.png")


# ==============================================================================
# 3. METHODOLOGY RETRAINING FLOW
# ==============================================================================
def create_retraining_flow():
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis('off')

    def draw_card(x, y, w, h, title, text, col, bg='#f8fafc'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.0",
                                      facecolor=bg, edgecolor=col, linewidth=1.4, zorder=2)
        ax.add_patch(rect)
        hdr = patches.FancyBboxPatch((x, y + h - 4.2), w, 4.2, boxstyle="round,pad=0.2",
                                     facecolor=col, edgecolor='none', zorder=3)
        ax.add_patch(hdr)
        ax.text(x + w/2, y + h - 2.1, title, ha='center', va='center', color='white',
                fontsize=7.8, fontweight='bold', zorder=4)
        ax.text(x + w/2, y + (h - 4.2)/2, text, ha='center', va='center', color='#1e293b',
                fontsize=6.8, linespacing=1.25, zorder=4)

    def draw_diamond(x, y, w, h, text, col):
        diamond = patches.Polygon([[x + w/2, y], [x + w, y + h/2], [x + w/2, y + h], [x, y + h/2]],
                                  closed=True, facecolor='#fef3c7', edgecolor=col, linewidth=1.5, zorder=3)
        ax.add_patch(diamond)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', color='#78350f',
                fontsize=6.8, fontweight='bold', linespacing=1.2, zorder=4)

    draw_card(2, 26, 20, 16, "Production Stream", "Logs audio duration,\nconfidence & intent\nBatches of N=20", '#3b82f6')
    draw_diamond(26, 25, 18, 18, "Drift Test\nKS-test < 0.05?\nPSI > 0.25?", '#d97706')
    draw_card(48, 26, 22, 16, "Active Querying", "Query 12 clips from\nheld-out Cohort B\nUncertainty sampling", '#8b5cf6')
    draw_card(74, 26, 24, 16, "Candidate Retrain", "Retrain candidate v2\nCondition A: Rehearsal\nCondition B: No-Rehearsal", '#0284c7')

    draw_diamond(74, 5, 24, 16, "Gate Evaluation\nCohort B gain >= +5%?\nGold regress <= 4%?", '#b45309')

    draw_card(38, 5, 28, 15, "PROMOTED (LOG-005)", "Rehearsal Mode\n• Cohort B: +7.7% gain\n• Gold: +3.4% gain\nPromoted to Production!", '#059669', bg='#ecfdf5')
    draw_card(4, 5, 28, 15, "REJECTED (LOG-006)", "No-Rehearsal Mode\n• Cohort B: 0.0% gain\n• Fails Criterion 1\nProduction Unchanged", '#dc2626', bg='#fef2f2')

    # Arrows
    ax.annotate('', xy=(26, 34), xytext=(22, 34), arrowprops=dict(arrowstyle='->', color='#64748b', lw=1.5))
    ax.annotate('', xy=(48, 34), xytext=(44, 34), arrowprops=dict(arrowstyle='->', color='#d97706', lw=1.5))
    ax.text(46, 35.5, "Yes", fontsize=7, fontweight='bold', color='#b45309')
    ax.annotate('', xy=(74, 34), xytext=(70, 34), arrowprops=dict(arrowstyle='->', color='#64748b', lw=1.5))
    ax.annotate('', xy=(86, 21), xytext=(86, 26), arrowprops=dict(arrowstyle='->', color='#64748b', lw=1.5))
    ax.annotate('', xy=(66, 13), xytext=(74, 13), arrowprops=dict(arrowstyle='->', color='#059669', lw=1.8))
    ax.text(70, 14.5, "Pass", fontsize=7, fontweight='bold', color='#059669')
    ax.annotate('', xy=(32, 13), xytext=(38, 13), arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.8))
    ax.text(35, 14.5, "Fail", fontsize=7, fontweight='bold', color='#dc2626')

    plt.tight_layout()
    plt.savefig("supporting_files/plots/methodology_retraining_flow.png", bbox_inches='tight', dpi=300)
    plt.close()
    print("Generated methodology_retraining_flow.png")


# ==============================================================================
# 4. BASELINES MULTI-METRIC COMPARISON CHART
# ==============================================================================
def create_baselines_comparison():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8), dpi=300)

    models = ['Majority Class', 'Length Heuristic', 'Zero-Shot Whisper\n+ TF-IDF MLP', 'Adapted Whisper\n+ Tuned MLP']
    val_acc = [0.176, 0.235, 0.882, 0.941]
    gold_acc = [0.172, 0.241, 0.345, 0.345]
    f1_scores = [0.050, 0.128, 0.882, 0.941]

    x = np.arange(len(models))
    w = 0.35

    rects1 = ax1.bar(x - w/2, val_acc, w, label='Validation Acc (N=17)', color='#3b82f6', edgecolor='#1d4ed8')
    rects2 = ax1.bar(x + w/2, gold_acc, w, label='Gold Test Acc (N=29)', color='#f59e0b', edgecolor='#b45309')

    ax1.set_ylabel('Classification Accuracy', fontsize=8.5, fontweight='bold')
    ax1.set_title('Accuracy: Validation vs. Frozen Gold Test', fontsize=9.5, fontweight='bold', color='#0f172a')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, fontsize=7.2)
    ax1.set_ylim(0, 1.15)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    ax1.legend(fontsize=7.5, loc='upper left')

    # Add data values
    for rect in rects1:
        h = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2., h + 0.02, f'{h:.3f}', ha='center', va='bottom', fontsize=6.8)
    for rect in rects2:
        h = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2., h + 0.02, f'{h:.3f}', ha='center', va='bottom', fontsize=6.8)

    # Panel B: F1 and WER comparison
    colors_f1 = ['#94a3b8', '#94a3b8', '#0284c7', '#059669']
    bars = ax2.bar(models, f1_scores, color=colors_f1, width=0.5, edgecolor='#0f172a', lw=0.8)
    ax2.set_ylabel('Validation Macro F1', fontsize=8.5, fontweight='bold')
    ax2.set_title('Validation Macro F1 Across Models', fontsize=9.5, fontweight='bold', color='#0f172a')
    ax2.set_xticklabels(models, fontsize=7.2)
    ax2.set_ylim(0, 1.15)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.02, f'{h:.3f}', ha='center', va='bottom', fontsize=7.2, fontweight='bold')

    plt.tight_layout()
    plt.savefig("supporting_files/plots/baselines_comparison_chart.png", bbox_inches='tight', dpi=300)
    plt.close()
    print("Generated baselines_comparison_chart.png")


# ==============================================================================
# 5. ANNOTATION IAA PROGRESSION
# ==============================================================================
def create_iaa_progression():
    fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=300)

    stages = ['Round 1\n(Initial Guidelines)', 'Round 2\n(Refined Guidelines)', 'Post-Adjudication\n(Consensus)']
    cohen_k = [0.7228, 0.8446, 1.0000]
    kripp_a = [0.7231, 0.8448, 1.0000]
    disagreements = [25, 14, 0]

    x = np.arange(len(stages))
    w = 0.28

    r1 = ax.bar(x - w/2, cohen_k, w, label="Cohen's Kappa (κ)", color='#4f46e5', edgecolor='#3730a3')
    r2 = ax.bar(x + w/2, kripp_a, w, label="Krippendorff's Alpha (α)", color='#06b6d4', edgecolor='#0891b2')

    ax.set_ylabel('Agreement Coefficient', fontsize=8.5, fontweight='bold')
    ax.set_title('Inter-Annotator Agreement Progression Across Annotation Stages', fontsize=9.5, fontweight='bold', color='#0f172a')
    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=7.5)
    ax.set_ylim(0, 1.18)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(fontsize=7.5, loc='upper left')

    for r in r1:
        h = r.get_height()
        ax.text(r.get_x() + r.get_width()/2., h + 0.02, f'{h:.4f}', ha='center', va='bottom', fontsize=7.0, fontweight='bold')
    for r in r2:
        h = r.get_height()
        ax.text(r.get_x() + r.get_width()/2., h + 0.02, f'{h:.4f}', ha='center', va='bottom', fontsize=7.0)

    # Annotate disagreement drops
    ax.annotate('25 Disagreements\n(Initial Ambiguities)', xy=(0, 0.72), xytext=(0.2, 0.55),
                arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.2), fontsize=7, color='#dc2626')
    ax.annotate('14 Residual Cases\n(Refined v2)', xy=(1, 0.84), xytext=(1.1, 0.68),
                arrowprops=dict(arrowstyle='->', color='#d97706', lw=1.2), fontsize=7, color='#d97706')

    plt.tight_layout()
    plt.savefig("supporting_files/plots/annotation_iaa_progression.png", bbox_inches='tight', dpi=300)
    plt.close()
    print("Generated annotation_iaa_progression.png")


if __name__ == "__main__":
    create_system_architecture()
    create_reproducibility_flowchart()
    create_retraining_flow()
    create_baselines_comparison()
    create_iaa_progression()
    print("All publication figures successfully created!")

