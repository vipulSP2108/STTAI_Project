#!/usr/bin/env python3
"""
Acoustic Model Adaptation Script
CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

Fine-tunes Whisper base decoder cross-attention layers on training audio clips
while freezing the audio encoder (honoring freeze_encoder: true in configs/final.yaml).
Saves adapted weights to artefacts/models/whisper_base_adapted.pt.
"""

import os
import sys
import time
import yaml
import json
import torch
import whisper
from pathlib import Path
import pandas as pd
import mlflow
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# Add code dir to sys.path
sys.path.append(str(Path(__file__).parent))
from normalisation import normalise_text

os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
CONFIG_PATH = Path("configs/final.yaml")
AUDIO_DIR = Path("data/raw/audio")
OUTPUT_MODEL_PATH = Path("artefacts/models/whisper_base_adapted.pt")
OUTPUT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

def train_whisper_adaptation(max_steps=15, batch_size=4, lr=1e-5):
    print("="*65)
    print("🚀 Commencing Real Whisper Base Acoustic Adaptation Pipeline")
    print("="*65)

    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    freeze_encoder = cfg["model"].get("freeze_encoder", True)
    print(f"Configuration: {CONFIG_PATH}")
    print(f"Freeze Encoder Setting: {freeze_encoder}")

    # Load training splits
    df_train = pd.read_csv("data/splits/train.csv")
    df_tx = pd.read_csv("data/labels/transcripts.csv")
    df_train = df_train.merge(df_tx, on="clip_id", how="left")
    print(f"Loaded {len(df_train)} training clips across 10 speakers.")

    # Load processor and model
    print("Loading OpenAI Whisper base backbone...")
    processor = WhisperProcessor.from_pretrained("openai/whisper-base")
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

    # Freeze encoder if specified
    if freeze_encoder:
        print("Freezing Whisper audio encoder (30.8M parameters)...")
        model.model.encoder.requires_grad_(False)
        for name, p in model.model.decoder.named_parameters():
            if "encoder_attn" in name:
                p.requires_grad = True
            else:
                p.requires_grad = False
    else:
        for p in model.parameters():
            p.requires_grad = True

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Trainable Parameters: {trainable_params:,} / {total_params:,} ({trainable_params/total_params*100:.2f}%)")

    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    model.train()

    # Setup MLflow
    mlflow.set_tracking_uri("sqlite:///supporting_files/mlflow.db")
    mlflow.set_experiment("cs203_voice_helpdesk_production")

    losses = []
    t_start = time.time()

    print(f"\nExecuting {max_steps} optimization steps on local CPU (batch size = {batch_size})...")
    step = 0
    while step < max_steps:
        batch_samples = df_train.sample(n=batch_size, random_state=42 + step)
        input_features_list = []
        labels_list = []

        for _, row in batch_samples.iterrows():
            cid = row["clip_id"]
            wav_path = AUDIO_DIR / f"{cid}.wav"
            if not wav_path.exists():
                continue
            audio_data = whisper.load_audio(str(wav_path))
            
            # Extract mel using Whisper processor
            inputs = processor(audio_data, sampling_rate=16000, return_tensors="pt")
            input_features_list.append(inputs.input_features)

            target_text = normalise_text(str(row["transcript"]))
            label_ids = processor.tokenizer(target_text, return_tensors="pt").input_ids
            labels_list.append(label_ids)

        if not input_features_list:
            continue

        feat_tensor = torch.cat(input_features_list, dim=0)
        # Pad labels
        max_len = max(l.shape[1] for l in labels_list)
        padded_labels = torch.full((len(labels_list), max_len), -100, dtype=torch.long)
        for i, l in enumerate(labels_list):
            padded_labels[i, :l.shape[1]] = l[0]

        optimizer.zero_grad()
        outputs = model(input_features=feat_tensor, labels=padded_labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()

        loss_val = float(loss.item())
        losses.append(loss_val)
        step += 1
        print(f"  Step {step}/{max_steps} - Loss: {loss_val:.4f} (Elapsed: {time.time()-t_start:.1f}s)")

    duration = time.time() - t_start
    avg_loss = sum(losses) / len(losses)
    print(f"\nAdaptation completed in {duration:.1f}s. Average Loss: {avg_loss:.4f}")

    # Save adapted weights (trainable state dict)
    adapted_state = {k: v for k, v in model.state_dict().items() if "encoder_attn" in k}
    torch.save(adapted_state, OUTPUT_MODEL_PATH)
    print(f"✓ Saved adapted cross-attention checkpoint to: {OUTPUT_MODEL_PATH} ({os.path.getsize(OUTPUT_MODEL_PATH)/1024:.1f} KB)")

    # Log to MLflow
    with mlflow.start_run(run_name="whisper_base_cross_attn_adaptation") as run:
        mlflow.log_params({
            "model_architecture": "openai/whisper-base",
            "freeze_encoder": freeze_encoder,
            "trainable_params": trainable_params,
            "max_steps": max_steps,
            "batch_size": batch_size,
            "lr": lr,
            "train_clips": len(df_train)
        })
        mlflow.log_metrics({
            "train_loss_final": losses[-1],
            "train_loss_avg": avg_loss,
            "train_duration_sec": duration
        })
        mlflow.set_tag("adaptation_type", "decoder_cross_attention")
        run_id = run.info.run_id
        print(f"Logged adaptation run to MLflow: {run_id}")

    return {
        "status": "SUCCESS",
        "adapted_checkpoint": str(OUTPUT_MODEL_PATH),
        "avg_loss": avg_loss,
        "run_id": run_id
    }

if __name__ == "__main__":
    train_whisper_adaptation(max_steps=5, batch_size=2)
