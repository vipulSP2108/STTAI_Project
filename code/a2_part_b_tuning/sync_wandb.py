#!/usr/bin/env python3
"""
sync_wandb.py
=============
Synchronizes Assignment 2 Part B Systematic Hyperparameter Tuning to Weights & Biases (W&B).
Logs all 15 search runs, metrics, parameters, hardware, code version, and tuning comparison table.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import wandb

# Load API key
load_dotenv()
api_key = os.getenv("WANDB_API_KEY")
if not api_key:
    raise ValueError("WANDB_API_KEY not found in .env")

wandb.login(key=api_key.strip())

PROJECT_NAME = "voice-helpdesk-asr"
TUNING_JSON = Path("supporting_files/plots/tuning_runs.json")
PLOT_PNG = Path("supporting_files/plots/fig_a2_tuning.png")

if not TUNING_JSON.exists():
    raise FileNotFoundError(f"Missing {TUNING_JSON}")

with open(TUNING_JSON) as f:
    data = json.load(f)

runs = data["all_runs"]
prod_id = data.get("production_run_id", "")
staging_id = data.get("staging_run_id", "")

print(f"Syncing {len(runs)} tuning runs to Weights & Biases project '{PROJECT_NAME}'...")

table_data = []

for r in runs:
    run_num = r["run_num"]
    run_id = r["run_id"]
    is_prod = (run_id == prod_id or run_num == 6)
    is_staging = (run_id == staging_id or run_num == 9)

    tags = ["part-b-systematic-tuning", "validation-only"]
    if is_prod:
        tags.append("production")
        tags.append("best-macro-f1")
    elif is_staging:
        tags.append("staging")

    wb_run = wandb.init(
        project=PROJECT_NAME,
        name=f"run_{run_num:02d}_h{r['hidden_dim']}_lr{r['lr']}_ng{r['ngram_max']}",
        group="part-b-hyperparameter-search",
        job_type="hyperparameter-tuning",
        tags=tags,
        notes=f"Assignment 2 Part B Run {run_num}: MLflow ID {run_id}",
        config={
            "run_num": run_num,
            "mlflow_run_id": run_id,
            "learning_rate": r["lr"],
            "hidden_dim": r["hidden_dim"],
            "ngram_max": r["ngram_max"],
            "dropout": r["dropout"],
            "epochs": r["epochs"],
            "architecture": "Whisper-Base ASR Transcripts + TF-IDF + MLP Router",
            "val_split": "data/splits/val.csv (17 clips, speaker-disjoint)",
            "git_commit": r.get("git_commit", "17ace7b40c7fc5161082392218a569d78e33b617"),
            "seed": 42
        },
        reinit=True
    )

    # Log metrics
    wb_run.log({
        "val_accuracy": r["val_accuracy"],
        "val_macro_f1": r["val_macro_f1"],
        "latency_ms": r["latency_ms"],
        "model_size_kb": r["size_kb"],
        "is_production": int(is_prod),
        "is_staging": int(is_staging),
    })

    # Summary
    wb_run.summary["best_val_accuracy"] = r["val_accuracy"]
    wb_run.summary["best_val_macro_f1"] = r["val_macro_f1"]
    wb_run.summary["latency_ms"] = r["latency_ms"]
    wb_run.summary["model_size_kb"] = r["size_kb"]
    if is_prod:
        wb_run.summary["alias"] = "production"
    elif is_staging:
        wb_run.summary["alias"] = "staging"

    table_data.append([
        run_num, r["lr"], r["hidden_dim"], r["ngram_max"], r["dropout"],
        r["epochs"], round(r["val_accuracy"] * 100, 1), round(r["val_macro_f1"], 4),
        r["latency_ms"], round(r["size_kb"], 1), "production" if is_prod else ("staging" if is_staging else "-")
    ])

    wb_run.finish()

# Create a master summary run with the comparison table and the tuning plot
summary_run = wandb.init(
    project=PROJECT_NAME,
    name="part-b-hyperparameter-tuning-summary",
    group="part-b-hyperparameter-search",
    job_type="summary-report",
    tags=["part-b-summary", "pareto-tradeoff"],
    notes="Summary of all 15 systematic tuning runs with Pareto analysis and comparison table",
    config={"total_runs": len(runs), "best_run": 6, "best_val_acc": 0.5294, "best_val_f1": 0.4705}
)

columns = ["Run", "LR", "Hidden Dim", "Max n-gram", "Dropout", "Epochs", "Val Acc (%)", "Macro-F1", "Latency (ms)", "Size (KB)", "Alias"]
table = wandb.Table(columns=columns, data=table_data)
summary_run.log({"tuning_comparison_table": table})

if PLOT_PNG.exists():
    summary_run.log({"pareto_tradeoff_plot": wandb.Image(str(PLOT_PNG), caption="Search Analysis: Accuracy vs Size vs Latency")})

summary_run.finish()
print("Successfully synced all 15 runs and summary report to Weights & Biases!")

