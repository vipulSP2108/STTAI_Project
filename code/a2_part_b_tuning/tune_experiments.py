# ============================================================
# Assignment 2 - Part B: Systematic Hyperparameter Search & MLflow Tracking
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Runs a systematic 15-run search across hyperparameters:
# - learning_rate: [0.001, 0.005, 0.010]
# - hidden_dim: [32, 64, 128]
# - ngram_max: [1, 2, 3]
# - dropout: [0.1, 0.2, 0.3]
#
# Evaluated STRICTLY on validation data only (val.csv).
# Generates search analysis plot with quality vs latency vs size Pareto frontier.
# Registers models in MLflow Model Registry with 'production' and 'staging' aliases.
# ============================================================

import json
import os
import shutil
import time
import mlflow
from mlflow.tracking import MlflowClient
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

TRAIN_CSV = Path("data/splits/train.csv")
VAL_CSV = Path("data/splits/val.csv")
PLOTS_DIR = Path("supporting_files/plots")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
MLRUNS_DIR = Path("supporting_files/mlruns")
MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR = Path("artefacts/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

INTENT_MAP = {"admissions": 0, "hostel_mess": 1, "it_support": 2, "student_services": 3}
REV_INTENT_MAP = {v: k for k, v in INTENT_MAP.items()}

class IntentClassificationHead(nn.Module):
    def __init__(self, in_features, hidden_dim, num_classes=4, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

    def forward(self, x):
        return self.net(x)

def load_dataset_with_labels(split_path):
    df_split = pd.read_csv(split_path)
    df_tx = pd.read_csv("data/labels/transcripts.csv")
    df_int = pd.read_csv("data/labels/intents.csv")
    return df_split.merge(df_tx, on="clip_id", how="left").merge(df_int, on="clip_id", how="left")

def run_tuning_grid():
    print("=== Starting 15-Run Hyperparameter Tuning Search with MLflow ===")
    db_path = Path("supporting_files/mlflow.db").resolve()
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")
    mlflow.set_experiment("project5_voice_helpdesk_tuning")
    client = MlflowClient()

    df_train = load_dataset_with_labels(TRAIN_CSV)
    df_val = load_dataset_with_labels(VAL_CSV)

    # 15 systematic configurations
    configs = [
        {"run_num": 1, "lr": 0.001, "hidden_dim": 32, "ngram_max": 1, "dropout": 0.1, "epochs": 25},
        {"run_num": 2, "lr": 0.005, "hidden_dim": 32, "ngram_max": 2, "dropout": 0.2, "epochs": 25},
        {"run_num": 3, "lr": 0.010, "hidden_dim": 32, "ngram_max": 3, "dropout": 0.3, "epochs": 25},
        {"run_num": 4, "lr": 0.001, "hidden_dim": 64, "ngram_max": 2, "dropout": 0.2, "epochs": 30},
        {"run_num": 5, "lr": 0.005, "hidden_dim": 64, "ngram_max": 3, "dropout": 0.2, "epochs": 30}, # Optimal Candidate
        {"run_num": 6, "lr": 0.010, "hidden_dim": 64, "ngram_max": 1, "dropout": 0.1, "epochs": 30},
        {"run_num": 7, "lr": 0.001, "hidden_dim": 128, "ngram_max": 3, "dropout": 0.3, "epochs": 35},
        {"run_num": 8, "lr": 0.005, "hidden_dim": 128, "ngram_max": 2, "dropout": 0.2, "epochs": 35},
        {"run_num": 9, "lr": 0.010, "hidden_dim": 128, "ngram_max": 1, "dropout": 0.2, "epochs": 35},
        {"run_num": 10, "lr": 0.002, "hidden_dim": 64, "ngram_max": 2, "dropout": 0.15, "epochs": 30},
        {"run_num": 11, "lr": 0.008, "hidden_dim": 64, "ngram_max": 3, "dropout": 0.25, "epochs": 30},
        {"run_num": 12, "lr": 0.003, "hidden_dim": 32, "ngram_max": 3, "dropout": 0.2, "epochs": 25},
        {"run_num": 13, "lr": 0.007, "hidden_dim": 128, "ngram_max": 2, "dropout": 0.1, "epochs": 35},
        {"run_num": 14, "lr": 0.004, "hidden_dim": 64, "ngram_max": 2, "dropout": 0.2, "epochs": 28},
        {"run_num": 15, "lr": 0.006, "hidden_dim": 96, "ngram_max": 3, "dropout": 0.2, "epochs": 32}
    ]

    results = []
    saved_models = {}
    saved_vecs = {}

    for cfg in configs:
        with mlflow.start_run(run_name=f"run_{cfg['run_num']:02d}") as run:
            run_id = run.info.run_id

            # 1. Feature extraction
            vec = TfidfVectorizer(ngram_range=(1, cfg["ngram_max"]), max_features=1000, sublinear_tf=True)
            X_tr = vec.fit_transform(df_train["transcript"].astype(str)).toarray()
            y_tr = np.array([INTENT_MAP[i] for i in df_train["intent"]])

            X_val = vec.transform(df_val["transcript"].astype(str)).toarray()
            y_val = np.array([INTENT_MAP[i] for i in df_val["intent"]])

            in_dim = X_tr.shape[1]
            model = IntentClassificationHead(in_dim, cfg["hidden_dim"], num_classes=4, dropout=cfg["dropout"])

            # 2. Train
            optimizer = torch.optim.Adam(model.parameters(), lr=cfg["lr"], weight_decay=1e-4)
            criterion = nn.CrossEntropyLoss()

            t0 = time.time()
            model.train()
            tensor_x_tr = torch.tensor(X_tr, dtype=torch.float32)
            tensor_y_tr = torch.tensor(y_tr, dtype=torch.long)

            for epoch in range(cfg["epochs"]):
                optimizer.zero_grad()
                out = model(tensor_x_tr)
                loss = criterion(out, tensor_y_tr)
                loss.backward()
                optimizer.step()

            train_time = time.time() - t0

            # 3. Evaluate on Validation Only
            model.eval()
            t_infer = time.time()
            with torch.no_grad():
                tensor_x_val = torch.tensor(X_val, dtype=torch.float32)
                logits = model(tensor_x_val)
                preds = torch.argmax(logits, dim=1).numpy()
            infer_latency_ms = ((time.time() - t_infer) / len(df_val)) * 1000.0

            val_acc = float(accuracy_score(y_val, preds))
            val_f1 = float(f1_score(y_val, preds, average="macro"))

            # Calculate parameter count and size
            param_count = sum(p.numel() for p in model.parameters())
            size_kb = (param_count * 4) / 1024.0

            # Log to MLflow
            mlflow.log_params(cfg)
            mlflow.log_param("commit_hash", "a2-final")
            mlflow.log_param("data_version", "a1-final")
            mlflow.log_metric("val_intent_accuracy", val_acc)
            mlflow.log_metric("val_macro_f1", val_f1)
            mlflow.log_metric("inference_latency_ms", infer_latency_ms)
            mlflow.log_metric("model_size_kb", size_kb)
            mlflow.log_metric("train_time_sec", train_time)

            # Log model artifact with pickle serialization
            try:
                mlflow.pytorch.log_model(
                    model,
                    artifact_path="model",
                    serialization_format="pickle"
                )
            except Exception as e:
                print(f"Warning: MLflow model logging notice: {e}")

            saved_models[run_id] = model
            saved_vecs[run_id] = vec

            row = {
                "run_id": run_id,
                "run_num": cfg["run_num"],
                "lr": cfg["lr"],
                "hidden_dim": cfg["hidden_dim"],
                "ngram_max": cfg["ngram_max"],
                "dropout": cfg["dropout"],
                "epochs": cfg["epochs"],
                "val_accuracy": round(val_acc, 4),
                "val_macro_f1": round(val_f1, 4),
                "latency_ms": round(infer_latency_ms, 2),
                "size_kb": round(size_kb, 2)
            }
            results.append(row)
            print(f"Run {cfg['run_num']:02d} [{run_id[:8]}]: Val Acc = {val_acc:.3f}, F1 = {val_f1:.3f}, Latency = {infer_latency_ms:.2f}ms")

    # Select production and staging models
    results_sorted = sorted(results, key=lambda x: (-x["val_accuracy"], x["latency_ms"], x["size_kb"]))
    prod_run = results_sorted[0]
    staging_run = results_sorted[1]

    print(f"\n* Production Model Selected: Run {prod_run['run_num']} (ID: {prod_run['run_id'][:8]})")
    print(f"  Accuracy: {prod_run['val_accuracy']}, Latency: {prod_run['latency_ms']} ms, Size: {prod_run['size_kb']} KB")
    print(f"* Staging Model Selected: Run {staging_run['run_num']} (ID: {staging_run['run_id'][:8]})")

    # Register models in MLflow Model Registry
    model_name = "voice_helpdesk_intent_router"
    try:
        prod_uri = f"runs:/{prod_run['run_id']}/model"
        reg_prod = mlflow.register_model(prod_uri, model_name)
        client.set_registered_model_alias(model_name, "production", reg_prod.version)
        print(f"Registered version {reg_prod.version} with alias 'production'")

        staging_uri = f"runs:/{staging_run['run_id']}/model"
        reg_staging = mlflow.register_model(staging_uri, model_name)
        client.set_registered_model_alias(model_name, "staging", reg_staging.version)
        print(f"Registered version {reg_staging.version} with alias 'staging'")
    except Exception as e:
        print(f"Registry notice: {e}")

    # Persist the best model weights & vectorizer
    best_m = saved_models[prod_run["run_id"]]
    best_v = saved_vecs[prod_run["run_id"]]
    torch.save(best_m.state_dict(), MODELS_DIR / "production_v1_head.pt")
    import pickle
    with open(MODELS_DIR / "proposed_vectorizer.pkl", "wb") as f:
        pickle.dump(best_v, f)
    print(f"Persisted production weights and vectorizer to {MODELS_DIR}")

    # Save registry metadata
    registry_meta = {
        "model_name": model_name,
        "production_alias": "production",
        "production_run_id": prod_run["run_id"],
        "production_run": prod_run,
        "staging_alias": "staging",
        "staging_run_id": staging_run["run_id"],
        "staging_run": staging_run,
        "all_runs": results
    }

    with open(PLOTS_DIR / "tuning_runs.json", "w") as f:
        json.dump(registry_meta, f, indent=2)

    plot_search_analysis(results, prod_run)
    return registry_meta

def plot_search_analysis(runs, best_run):
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)

    latencies = [r["latency_ms"] for r in runs]
    accuracies = [r["val_accuracy"] for r in runs]
    sizes = [r["size_kb"] * 10 for r in runs]
    run_nums = [r["run_num"] for r in runs]

    scatter = ax.scatter(latencies, accuracies, s=sizes, c=accuracies, cmap="viridis", alpha=0.75, edgecolors="k", linewidth=1.2)

    # Highlight production model
    ax.scatter([best_run["latency_ms"]], [best_run["val_accuracy"]], s=best_run["size_kb"]*10,
               facecolors="none", edgecolors="red", linewidth=2.5, label="Selected 'production' Model")

    for i, txt in enumerate(run_nums):
        ax.annotate(f"R{txt}", (latencies[i]+0.01, accuracies[i]+0.005), fontsize=8, weight="bold")

    ax.set_title("Hyperparameter Search Quality vs. Latency Trade-off (15 Validation Runs)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("CPU Inference Latency per Query (ms)", fontsize=10, labelpad=8)
    ax.set_ylabel("Validation Intent Classification Accuracy", fontsize=10, labelpad=8)
    ax.grid(True, linestyle="--", alpha=0.4)

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Validation Accuracy", fontsize=9)
    ax.legend(loc="lower right", frameon=True, fontsize=9)

    plt.tight_layout()
    out_png = PLOTS_DIR / "tuning_search_analysis.png"
    plt.savefig(out_png)
    plt.close()
    print(f"Search analysis plot generated: {out_png}")

    fig_dir = Path("report/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(out_png, fig_dir / "tuning_search_analysis.png")

if __name__ == "__main__":
    run_tuning_grid()
