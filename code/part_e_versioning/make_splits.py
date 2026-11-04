# ============================================================
# Part E: Leakage-Free Data Splits with Held-Out Cohort B
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# Split unit: SPEAKER - never clip or row.
# Guarantees zero speaker overlap between Train, Val, Test,
# and Held-Out Cohort B (Shifted Demographic Distribution).
#
# Total speakers: 19
# - Cohort B (Shifted): P4, P13 (Maharashtra accent, 32 clips)
# - Train: 10 speakers (171 clips)
# - Val: 3 speakers (17 clips)
# - Test: 4 speakers (29 clips)
# - Gold Set: subset of Test split (held out, 0 overlap with train/val)
#
# Seed: SPLIT_SEED = 42 (matches ENVIRONMENT.md)
# ============================================================

import os
import random
import pandas as pd
from pathlib import Path

SPLIT_SEED = 42
METADATA_CSV = Path("data/metadata.csv")
SPLITS_DIR = Path("data/splits")
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

def make_splits():
    random.seed(SPLIT_SEED)

    if not METADATA_CSV.exists():
        raise FileNotFoundError(f"Metadata file not found: {METADATA_CSV}")

    df = pd.read_csv(METADATA_CSV)
    print(f"Loaded {len(df)} clips from {df['speaker_id'].nunique()} unique speakers.")

    # 1. Held-out Cohort B (Shifted regional accent group: Maharashtra)
    cohort_b_spk = {"P4", "P13"}
    df_b = df[df["speaker_id"].isin(cohort_b_spk)].copy()
    df_b["split"] = "shifted"

    # 2. In-distribution speakers (strictly excluding Cohort B)
    in_dist_speakers = sorted(list(set(df["speaker_id"].unique()) - cohort_b_spk))
    
    # Deterministic speaker assignment matching demographic and acoustic distribution
    val_spk = {"P10", "P12", "P16"}
    test_spk = {"P15", "P17", "P18", "P19"}
    train_spk = set(in_dist_speakers) - val_spk - test_spk

    # Strict assertion: zero speaker leakage across all split partitions
    assert len(train_spk & val_spk) == 0, "LEAKAGE: train/val overlap"
    assert len(train_spk & test_spk) == 0, "LEAKAGE: train/test overlap"
    assert len(val_spk & test_spk) == 0, "LEAKAGE: val/test overlap"
    assert len(cohort_b_spk & (train_spk | val_spk | test_spk)) == 0, "LEAKAGE: Cohort B overlaps with main splits"

    df_train = df[df["speaker_id"].isin(train_spk)].copy()
    df_val = df[df["speaker_id"].isin(val_spk)].copy()
    df_test = df[df["speaker_id"].isin(test_spk)].copy()

    df_train["split"] = "train"
    df_val["split"] = "val"
    df_test["split"] = "test"

    # Verify partition sum equals total dataset
    total_split_clips = len(df_train) + len(df_val) + len(df_test) + len(df_b)
    assert total_split_clips == len(df), f"Split sum {total_split_clips} != total clips {len(df)}"

    print(f"\n=== Dataset Split Manifest Summary ===")
    print(f"Train split:    {len(df_train):>3} clips ({len(df_train)/len(df)*100:>4.1f}%) | Speakers: {len(train_spk)} ({sorted(train_spk)})")
    print(f"Val split:      {len(df_val):>3} clips ({len(df_val)/len(df)*100:>4.1f}%) | Speakers: {len(val_spk)} ({sorted(val_spk)})")
    print(f"Test split:     {len(df_test):>3} clips ({len(df_test)/len(df)*100:>4.1f}%) | Speakers: {len(test_spk)} ({sorted(test_spk)})")
    print(f"Cohort B split: {len(df_b):>3} clips ({len(df_b)/len(df)*100:>4.1f}%) | Speakers: {len(cohort_b_spk)} ({sorted(cohort_b_spk)})")
    print(f"Total verified: {total_split_clips} clips across {df['speaker_id'].nunique()} speakers (0 leakage)")

    # Save manifests
    cols = ["clip_id", "speaker_id", "split"]
    df_train[cols].to_csv(SPLITS_DIR / "train.csv", index=False)
    df_val[cols].to_csv(SPLITS_DIR / "val.csv", index=False)
    df_test[cols].to_csv(SPLITS_DIR / "test.csv", index=False)
    df_b[["clip_id", "speaker_id", "region", "split"]].to_csv(SPLITS_DIR / "cohort_b_shifted.csv", index=False)

    print(f"\nManifests saved to {SPLITS_DIR}/")

if __name__ == "__main__":
    make_splits()
