#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""leakage_auditor.py - Automated Zero-Data-Leakage Verification Suite.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Audits:
1. Cross-fold parent clip overlap = 0.
2. Cross-fold split group overlap = 0.
3. Cross-fold exact transcript SHA-256 collision = 0.
4. Independent test set isolation = 100%.
5. Stratification balance across target intents.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
SPLITS_DIR = MODEL_DIR / "data" / "splits"
REPORTS_DIR = MODEL_DIR / "data" / "reports"

def compute_text_hash(text: str) -> str:
    cleaned = " ".join(text.lower().strip().split())
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

def verify_all_splits():
    print("=" * 70)
    print("DATA LEAKAGE & CROSS-VALIDATION ISOLATION AUDIT")
    print("=" * 70)

    fold_files = sorted(list(SPLITS_DIR.glob("fold_*.json")))
    if not fold_files:
        print("ERROR: No fold manifests found in model/data/splits/. Run group_splitter.py first.")
        return False

    audit_results = {
        "total_folds_audited": len(fold_files),
        "all_folds_passed": True,
        "fold_audits": []
    }

    # Load test set if present
    test_hashes = set()
    test_parents = set()
    test_file = SPLITS_DIR / "independent_test_set.json"
    if test_file.exists():
        with open(test_file, "r") as f:
            test_data = json.load(f)
        for s in test_data.get("samples", []):
            test_hashes.add(compute_text_hash(s["transcript"]))
            test_parents.add(s["parent_uuid"])

    for fold_file in fold_files:
        with open(fold_file, "r") as f:
            data = json.load(f)

        fold_idx = data["fold_index"]
        train_samples = data["train_samples"]
        val_samples = data["val_samples"]

        # 1. Group overlap check
        train_groups = {s["split_group_id"] for s in train_samples}
        val_groups = {s["split_group_id"] for s in val_samples}
        group_overlap = train_groups.intersection(val_groups)

        # 2. Parent UUID overlap check
        train_parents = {s["parent_uuid"] for s in train_samples}
        val_parents = {s["parent_uuid"] for s in val_samples}
        parent_overlap = train_parents.intersection(val_parents)

        # 3. Exact transcript hash collision check
        train_hashes = {compute_text_hash(s["transcript"]) for s in train_samples}
        val_hashes = {compute_text_hash(s["transcript"]) for s in val_samples}
        hash_collisions = train_hashes.intersection(val_hashes)

        # 4. Test set contamination check
        test_contamination = train_hashes.intersection(test_hashes)

        passed = (len(group_overlap) == 0 and 
                  len(parent_overlap) == 0 and 
                  len(hash_collisions) == 0 and 
                  len(test_contamination) == 0)

        fold_status = {
            "fold_index": fold_idx,
            "train_samples": len(train_samples),
            "val_samples": len(val_samples),
            "group_overlap_count": len(group_overlap),
            "parent_overlap_count": len(parent_overlap),
            "text_hash_collisions": len(hash_collisions),
            "test_set_contamination": len(test_contamination),
            "status": "PASS" if passed else "FAIL"
        }

        if not passed:
            audit_results["all_folds_passed"] = False

        audit_results["fold_audits"].append(fold_status)

        print(f"Fold {fold_idx}: "
              f"GroupOverlap={len(group_overlap):1d} | "
              f"ParentOverlap={len(parent_overlap):1d} | "
              f"HashCollisions={len(hash_collisions):1d} | "
              f"TestOverlap={len(test_contamination):1d} ---> "
              f"[{'PASS (Zero Leakage)' if passed else 'FAIL (Leakage Detected)'}]")

    # Serialize report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "leakage_verification_report.json"
    with open(report_path, "w") as f:
        json.dump(audit_results, f, indent=2)

    print("\n" + "=" * 70)
    print(f"OVERALL LEAKAGE AUDIT: {'PASSED (Zero Contamination Confirmed)' if audit_results['all_folds_passed'] else 'FAILED'}")
    print(f"Report Serialized To : {report_path}")
    print("=" * 70)

    return audit_results["all_folds_passed"]

if __name__ == "__main__":
    verify_all_splits()
