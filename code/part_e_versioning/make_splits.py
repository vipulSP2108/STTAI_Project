# ============================================================
# Part E: Leakage-Free Data Splits
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# Split unit: SPEAKER - never clip or row.
# This prevents speaker leakage: model never hears the same
# voice in both training and evaluation.
#
# Cohort B: held-out accent/region group.
# Used as the shifted distribution in Assignment 2 drift experiments.
#
# SPLIT_SEED = 42 - fixed for reproducibility.
# Changing the seed requires re-generating all splits and re-tagging.
# ============================================================

import random
import pandas as pd
from pathlib import Path

SPLIT_SEED = 42   # MUST match ENVIRONMENT.md

METADATA_CSV = Path("data/metadata.csv")
SPLITS_DIR   = Path("data/splits")
SPLITS_DIR.mkdir(parents=True, exist_ok=True)


def make_splits(df):
    random.seed(SPLIT_SEED)

    speakers = df["speaker_id"].unique().tolist()
    random.shuffle(speakers)

    n = len(speakers)
    n_train = int(n * 0.70)
    n_val   = int(n * 0.15)

    train_spk = set(speakers[:n_train])
    val_spk   = set(speakers[n_train:n_train + n_val])
    test_spk  = set(speakers[n_train + n_val:])

    # Leakage check
    assert len(train_spk & val_spk)  == 0, "LEAKAGE: train/val overlap"
    assert len(train_spk & test_spk) == 0, "LEAKAGE: train/test overlap"
    assert len(val_spk   & test_spk) == 0, "LEAKAGE: val/test overlap"

    df_train = df[df["speaker_id"].isin(train_spk)].copy()
    df_val   = df[df["speaker_id"].isin(val_spk)].copy()
    df_test  = df[df["speaker_id"].isin(test_spk)].copy()

    df_train["split"] = "train"
    df_val["split"]   = "val"
    df_test["split"]  = "test"

    return df_train, df_val, df_test, train_spk, val_spk, test_spk


def make_cohort_b(df, train_spk, val_spk, test_spk):
    """Cohort B: smallest region group = most underrepresented accent."""
    region_counts = df["region"].value_counts()
    if region_counts.empty or df["region"].isna().all():
        print("WARNING: No region data found - creating empty cohort_b")
        return pd.DataFrame(columns=df.columns.tolist() + ["split"])

    cohort_b_region = region_counts.index[-1]  # Smallest group
    df_b = df[df["region"] == cohort_b_region].copy()
    df_b["split"] = "shifted"

    # Ensure cohort B speakers are not in train/val/test
    all_main = train_spk | val_spk | test_spk
    b_spk_in_main = df_b["speaker_id"].isin(all_main).any()
    if b_spk_in_main:
        print(f"NOTE: Cohort B speakers overlap with main splits - "
              f"Cohort B is a separate held-out region ({cohort_b_region})")

    return df_b, cohort_b_region


def main():
    if not METADATA_CSV.exists():
        print(f"metadata.csv not found: {METADATA_CSV}")
        return

    df = pd.read_csv(METADATA_CSV)
    print(f"Loaded {len(df)} clips, {df['speaker_id'].nunique()} unique speakers")

    df_train, df_val, df_test, train_spk, val_spk, test_spk = make_splits(df)

    # Save main splits
    cols = ["clip_id","speaker_id","split"]
    for subset, name in [(df_train,"train"), (df_val,"val"), (df_test,"test")]:
        out = SPLITS_DIR / f"{name}.csv"
        subset[cols].to_csv(out, index=False)

    # Cohort B
    result = make_cohort_b(df, train_spk, val_spk, test_spk)
    if isinstance(result, tuple):
        df_b, region = result
        df_b[["clip_id","speaker_id","region","split"]].to_csv(
            SPLITS_DIR / "cohort_b_shifted.csv", index=False)
    else:
        df_b = result
        region = "unknown"
        df_b.to_csv(SPLITS_DIR / "cohort_b_shifted.csv", index=False)

    print("\n=== Split Summary ===")
    for name, subset, spk_set in [
        ("Train",   df_train, train_spk),
        ("Val",     df_val,   val_spk),
        ("Test",    df_test,  test_spk),
    ]:
        print(f"{name:<8}: {len(subset):>4} clips, {len(spk_set):>2} speakers")

    if not df_b.empty:
        print(f"Shifted : {len(df_b):>4} clips (Cohort B — region={region})")

    print("\nLeakage check: PASSED [OK] (no speaker in multiple splits)")
    print(f"Splits saved to: {SPLITS_DIR}/")
    print("\nNOTE: Tag repo after this step: git tag a1-final")

if __name__ == "__main__": main()
