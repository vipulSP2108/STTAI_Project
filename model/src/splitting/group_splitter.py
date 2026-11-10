#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""group_splitter.py - Leakage-Free StratifiedGroupKFold Splitter.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Implements StratifiedGroupKFold (K=5) grouped by parent clip & speaker.
2. Ensures all augmented variants and acoustic derivatives remain in the exact same fold as their parent.
3. Carves out an independent unseen-speaker evaluation benchmark (held-out test set).
4. Emits clean fold manifests to model/data/splits/fold_1.json .. fold_5.json.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from collections import Counter
from sklearn.model_selection import StratifiedGroupKFold

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
TEXT_DIR = MODEL_DIR / "data" / "text"
AUG_DIR = MODEL_DIR / "data" / "augmented"
METADATA_DIR = MODEL_DIR / "data" / "metadata"
SPLITS_DIR = MODEL_DIR / "data" / "splits"

def create_splits(n_splits=5, test_held_out_speakers=None, seed=42):
    print("=" * 70)
    print(f"LEAKAGE-FREE STRATIFIED GROUP K-FOLD PARTITIONING (K={n_splits})")
    print("=" * 70)

    # 1. Load internal manifest (originals)
    manifest_path = METADATA_DIR / "internal_manifest.json"
    with open(manifest_path, "r") as f:
        internal_data = json.load(f)
    all_records = list(internal_data["manifest"])

    # 2. Load augmented manifest if present
    aug_manifest_path = METADATA_DIR / "augmented_manifest.json"
    if aug_manifest_path.exists():
        with open(aug_manifest_path, "r") as f:
            aug_data = json.load(f)
        aug_records = aug_data.get("manifest", [])
        all_records.extend(aug_records)
        print(f"Loaded {len(aug_records)} augmented records into split pool.")

    # 3. Read transcripts for all records
    valid_samples = []
    for rec in all_records:
        rec_uuid = rec["uuid"]
        transcript = ""
        # Search in text or augmented directories
        txt_path = TEXT_DIR / f"{rec_uuid}.txt"
        if not txt_path.exists():
            # Check augmented dirs
            matches = list(AUG_DIR.glob(f"*/{rec_uuid}.txt"))
            if matches:
                txt_path = matches[0]

        if txt_path.exists():
            for line in txt_path.read_text().splitlines():
                if line.startswith("Transcript:"):
                    transcript = line.replace("Transcript:", "").strip()
                    break

        if transcript:
            valid_samples.append({
                "uuid": rec_uuid,
                "transcript": transcript,
                "gold_intent": rec["gold_intent"],
                "split_group_id": rec["split_group_id"],
                "original_speaker_id": rec.get("original_speaker_id", "unknown"),
                "is_augmented": rec.get("is_augmented", False),
                "parent_uuid": rec.get("parent_uuid", rec_uuid),
                "augmentation_type": rec.get("augmentation_type", "original")
            })

    print(f"Total valid samples with transcripts: {len(valid_samples)}")

    # 4. Optional Held-Out Independent Test Benchmark (Unseen Speakers)
    held_out_test_set = []
    cross_val_pool = []
    if test_held_out_speakers:
        for s in valid_samples:
            if s["original_speaker_id"] in test_held_out_speakers:
                held_out_test_set.append(s)
            else:
                cross_val_pool.append(s)
        print(f"Held-out Unseen Speaker Test Set: {len(held_out_test_set)} samples (Speakers: {test_held_out_speakers})")
    else:
        cross_val_pool = valid_samples

    # 5. Execute StratifiedGroupKFold on cross_val_pool
    X = np.array([s["transcript"] for s in cross_val_pool])
    y = np.array([s["gold_intent"] for s in cross_val_pool])
    groups = np.array([s["split_group_id"] for s in cross_val_pool])

    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    fold_manifests = []
    for fold_idx, (train_indices, val_indices) in enumerate(sgkf.split(X, y, groups), start=1):
        train_samples = [cross_val_pool[i] for i in train_indices]
        val_samples = [cross_val_pool[i] for i in val_indices]

        train_dist = dict(Counter([s["gold_intent"] for s in train_samples]))
        val_dist = dict(Counter([s["gold_intent"] for s in val_samples]))

        fold_data = {
            "fold_index": fold_idx,
            "train_count": len(train_samples),
            "val_count": len(val_samples),
            "train_class_distribution": train_dist,
            "val_class_distribution": val_dist,
            "train_samples": train_samples,
            "val_samples": val_samples
        }

        fold_file = SPLITS_DIR / f"fold_{fold_idx}.json"
        with open(fold_file, "w") as f:
            json.dump(fold_data, f, indent=2)

        fold_manifests.append(fold_data)
        print(f"Fold {fold_idx}: Train={len(train_samples):4d} {train_dist} | Val={len(val_samples):3d} {val_dist}")

    # Save held-out test benchmark
    test_file = SPLITS_DIR / "independent_test_set.json"
    with open(test_file, "w") as f:
        json.dump({
            "test_count": len(held_out_test_set),
            "speakers": test_held_out_speakers or [],
            "class_distribution": dict(Counter([s["gold_intent"] for s in held_out_test_set])),
            "samples": held_out_test_set
        }, f, indent=2)

    print(f"\nAll 5 fold manifests saved to {SPLITS_DIR}/fold_*.json")
    print(f"Independent test benchmark saved to {test_file}")
    print("=" * 70)

    return fold_manifests

if __name__ == "__main__":
    create_splits()
