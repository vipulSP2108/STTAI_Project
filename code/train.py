# ============================================================
# Assignment 2 - Part A: Config-Driven Training Pipeline
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Usage:
#   python code/train.py --config configs/final.yaml
#   python code/train.py --config configs/final.yaml --compare-augmentations
# ============================================================

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
import yaml
import mlflow
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from jiwer import wer, cer

# Import deterministic normaliser
import sys
sys.path.append(str(Path(__file__).parent))
from normalisation import normalise_text

INTENT_MAP = {"admissions": 0, "hostel_mess": 1, "it_support": 2, "student_services": 3}
REV_INTENT_MAP = {v: k for k, v in INTENT_MAP.items()}


def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return os.environ.get("GIT_COMMIT", "a2-final")


def compute_file_hash(path):
    if not Path(path).exists():
        return "none"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class IntentRouterHead(nn.Module):
    def __init__(self, in_features, hidden_dim=64, num_classes=4, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

    def forward(self, x):
        return self.net(x)


def load_dataset(split_csv, data_dir=Path("data")):
    df = pd.read_csv(split_csv)
    if "transcript" not in df.columns:
        df_tx = pd.read_csv(data_dir / "labels/transcripts.csv")
        df = df.merge(df_tx, on="clip_id", how="left")
    if "intent" not in df.columns:
        df_int = pd.read_csv(data_dir / "labels/intents.csv")
        df = df.merge(df_int, on="clip_id", how="left")
    return df


def train_pipeline(config_path="configs/final.yaml", compare_augmentations=False):
    print(f"=== Commencing Production Training Pipeline ===")
    print(f"Configuration: {config_path}")

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    seed = cfg.get("seed", 42)
    torch.manual_seed(seed)
    np.random.seed(seed)

    git_commit = get_git_commit()
    config_hash = compute_file_hash(config_path)
    data_dir = Path("data")

    # Load datasets
    df_train = load_dataset(cfg["data"]["train_manifest"], data_dir)
    df_val = load_dataset(cfg["data"]["val_manifest"], data_dir)
    print(f"Loaded Train: {len(df_train)} clips | Val: {len(df_val)} clips")

    # 1. Fit Vectorizer on Training Transcripts (normalised)
    norm_train_tx = [normalise_text(t) for t in df_train["transcript"].astype(str)]
    feat_cfg = cfg.get("features", {})
    vectorizer = TfidfVectorizer(
        ngram_range=tuple(feat_cfg.get("ngram_range", [1, 2])),
        max_features=feat_cfg.get("max_features", 1000),
        sublinear_tf=feat_cfg.get("sublinear_tf", True)
    )
    X_train = vectorizer.fit_transform(norm_train_tx).toarray()
    y_train = np.array([INTENT_MAP[i] for i in df_train["intent"]])

    # 2. Build Intent Router Head
    m_cfg = cfg.get("model", {})
    in_dim = X_train.shape[1]
    head = IntentRouterHead(
        in_features=in_dim,
        hidden_dim=m_cfg.get("hidden_dim", 64),
        num_classes=m_cfg.get("num_classes", 4),
        dropout=m_cfg.get("dropout", 0.2)
    )

    t_cfg = cfg.get("training", {})
    optimizer = torch.optim.Adam(
        head.parameters(),
        lr=t_cfg.get("lr", 0.005),
        weight_decay=t_cfg.get("weight_decay", 0.0001)
    )
    criterion = nn.CrossEntropyLoss()

    tensor_x = torch.tensor(X_train, dtype=torch.float32)
    tensor_y = torch.tensor(y_train, dtype=torch.long)

    # Train loop
    t0_train = time.time()
    head.train()
    epochs = t_cfg.get("epochs", 10)
    for epoch in range(epochs):
        optimizer.zero_grad()
        out = head(tensor_x)
        loss = criterion(out, tensor_y)
        loss.backward()
        optimizer.step()
    train_time_sec = round(time.time() - t0_train, 3)
    head.eval()

    # 3. Validation Evaluation
    # Load ASR predictions from safe whisper cache
    cache = {}
    cache_path = data_dir / "processed/whisper_base_eval_cache.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            cache = json.load(f)

    val_preds_tx = []
    val_refs_tx = []
    for _, r in df_val.iterrows():
        cid = r["clip_id"]
        tx = cache.get(cid, {}).get("pred_transcript", "helpdesk query")
        val_preds_tx.append(normalise_text(tx))
        val_refs_tx.append(normalise_text(r["transcript"]))

    X_val = vectorizer.transform(val_preds_tx).toarray()
    with torch.no_grad():
        logits = head(torch.tensor(X_val, dtype=torch.float32))
        probs = torch.softmax(logits, dim=1).numpy()
    pred_intents = [REV_INTENT_MAP[i] for i in np.argmax(probs, axis=1)]
    true_intents = df_val["intent"].tolist()

    val_wer = float(np.mean([wer(r, p) for r, p in zip(val_refs_tx, val_preds_tx)]))
    val_cer = float(np.mean([cer(r, p) for r, p in zip(val_refs_tx, val_preds_tx)]))
    val_acc = float(accuracy_score(true_intents, pred_intents))
    val_f1 = float(f1_score(true_intents, pred_intents, average="macro", zero_division=0))

    print(f"\n--- Validation Performance (17 clips, 3 speakers) ---")
    print(f"Val WER:        {val_wer:.4f}")
    print(f"Val CER:        {val_cer:.4f}")
    print(f"Val Intent Acc: {val_acc:.4f} ({val_acc*100:.1f}%)")
    print(f"Val Macro-F1:   {val_f1:.4f}")
    print(f"Training Time:  {train_time_sec}s")

    # 4. Save Model Artifacts
    models_dir = Path("artefacts/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    torch.save(head.state_dict(), models_dir / "production_v1_head.pt")
    with open(models_dir / "proposed_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    # 5. MLflow Tracking
    mlflow.set_tracking_uri("sqlite:///supporting_files/mlflow.db")
    mlflow.set_experiment(cfg.get("experiment_name", "cs203_voice_helpdesk_production"))

    with mlflow.start_run(run_name=cfg.get("run_name", "production_v1")) as run:
        mlflow.log_params({
            "seed": seed,
            "git_commit": git_commit,
            "config_hash": config_hash,
            "epochs": epochs,
            "lr": t_cfg.get("lr", 0.005),
            "batch_size": t_cfg.get("batch_size", 8),
            "hidden_dim": m_cfg.get("hidden_dim", 64),
            "ngram_range": str(feat_cfg.get("ngram_range", [1, 2])),
            "max_features": feat_cfg.get("max_features", 1000),
            "hardware": platform.processor() or platform.machine(),
            "os": platform.system()
        })
        mlflow.log_metrics({
            "val_wer": val_wer,
            "val_cer": val_cer,
            "val_intent_accuracy": val_acc,
            "val_intent_macro_f1": val_f1,
            "train_time_sec": train_time_sec
        })
        run_id = run.info.run_id
        print(f"Logged run to MLflow: Run ID = {run_id}")

    # 6. Comparison Table on Validation (Guide 3.1.4)
    comp_results = []
    if compare_augmentations:
        print("\n=== Running Empirical Comparison Across Training Configurations (Guide Section 3.1.4) ===")
        # Load augmented metadata if exists
        aug_p = data_dir / "processed/augmented/augmented_metadata.csv"
        df_aug = pd.read_csv(aug_p) if aug_p.exists() else pd.DataFrame()

        # Build genuine datasets
        datasets = {
            "Train Only (171 clips)": df_train[["transcript", "intent"]].copy(),
        }
        if not df_aug.empty:
            datasets["Train + Augmented (231 clips)"] = pd.concat(
                [df_train[["transcript", "intent"]], df_aug[["transcript", "intent"]]],
                ignore_index=True
            )

        y_val_indices = np.array([INTENT_MAP[i] for i in df_val["intent"]])
        for name, d_df in datasets.items():
            t_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=1000, sublinear_tf=True)
            X_t = t_vec.fit_transform([normalise_text(t) for t in d_df["transcript"].astype(str)]).toarray()
            y_t = np.array([INTENT_MAP[i] for i in d_df["intent"]])

            torch.manual_seed(seed)
            t_model = nn.Sequential(
                nn.Linear(X_t.shape[1], m_cfg.get("hidden_dim", 64)),
                nn.ReLU(),
                nn.Dropout(m_cfg.get("dropout", 0.2)),
                nn.Linear(m_cfg.get("hidden_dim", 64), 4)
            )
            t_opt = torch.optim.Adam(t_model.parameters(), lr=t_cfg.get("lr", 0.005))
            t_crit = nn.CrossEntropyLoss()

            t_model.train()
            tx_tensor = torch.tensor(X_t, dtype=torch.float32)
            ty_tensor = torch.tensor(y_t, dtype=torch.long)
            for _ in range(epochs):
                t_opt.zero_grad()
                l = t_crit(t_model(tx_tensor), ty_tensor)
                l.backward()
                t_opt.step()

            t_model.eval()
            with torch.no_grad():
                val_feats = torch.tensor(t_vec.transform(val_preds_tx).toarray(), dtype=torch.float32)
                p_out = t_model(val_feats).argmax(dim=1).numpy()
            c_acc = float(accuracy_score(y_val_indices, p_out))
            c_wer = float(val_wer)  # Whisper base validation WER remains governed by acoustic backbone

            with mlflow.start_run(run_name=f"emp_eval_{name.split()[0].lower()}") as ab_run:
                mlflow.log_param("training_data", name)
                mlflow.log_param("num_samples", len(d_df))
                mlflow.log_metrics({"val_wer": c_wer, "val_intent_acc": c_acc})
                ab_id = ab_run.info.run_id

            comp_results.append({
                "Training Data": name,
                "Sample Count": len(d_df),
                "Val WER (Whisper Base)": f"{c_wer:.3f}",
                "Val Intent Acc": f"{c_acc*100:.1f}%",
                "MLflow Run ID": ab_id[:8]
            })

        df_comp = pd.DataFrame(comp_results)
        print("\n" + df_comp.to_markdown(index=False))
        df_comp.to_csv("supporting_files/part_a_baselines_benchmark.csv", index=False)

    return {
        "val_wer": val_wer,
        "val_cer": val_cer,
        "val_intent_acc": val_acc,
        "val_intent_f1": val_f1,
        "train_time_sec": train_time_sec,
        "run_id": run_id,
        "git_commit": git_commit
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    parser.add_argument("--compare-augmentations", action="store_true")
    parser.add_argument("--train-asr", action="store_true", help="Fine-tune Whisper base decoder cross-attention")
    args = parser.parse_args()
    if args.train_asr:
        from train_asr import train_whisper_adaptation
        train_whisper_adaptation()
    train_pipeline(args.config, args.compare_augmentations)

