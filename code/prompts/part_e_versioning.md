# Prompts Used — Part E: Versioning and Splits
<!-- Required by CS203 Assignment 1 Grader AI -->

## Prompt 1: Speaker-Disjoint Split Generator with Regional Drift Cohort
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_e_versioning/make_splits.py`  

**Exact prompt**:
"""
Build `part_e_versioning/make_splits.py` that:

CONSTANTS:
SPLIT_SEED = 42

1. Read data/metadata.csv (all clips with speaker_id, region)
2. Get unique speaker_ids. Shuffle with seed SPLIT_SEED.
   Assign: first 70% -> train, next 15% -> val, last 15% -> test.
3. LEAKAGE CHECK (assert, do NOT proceed if fails):
   train_speakers & val_speakers == empty
   train_speakers & test_speakers == empty
   val_speakers & test_speakers == empty
4. SHIFTED SPLIT (Cohort B):
   - Pick the underrepresented regional accent group (Maharashtra)
   - Mark clips as "cohort_b_shifted" for A2 drift evaluation
5. Write split manifests:
   data/splits/train.csv
   data/splits/val.csv
   data/splits/test.csv
   data/splits/cohort_b_shifted.csv
6. Print summary & verify leakage check.

Add comment:
# ============================================================
# Part E: Leakage-Free Data Splits
# CS203 Assignment 1 — Project 5
# Split unit: SPEAKER — never clip or row.
# SPLIT_SEED = 42
# ============================================================
"""

**Notes**: Enforces strict set assertions ensuring zero speaker ID overlap between train, val, and test splits.

---

## Prompt 2: DVC Versioning Automation Script
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_e_versioning/dvc_setup.sh`  

**Exact prompt**:
"""
Write `part_e_versioning/dvc_setup.sh`:
1. Initializes DVC without SCM conflicts.
2. Tracks the entire data/ directory via `dvc add data/`.
3. Configures local remote ../dvc-remote.
4. Commits data.dvc, .dvc/, and .dvcignore to Git.
5. Pushes data to the DVC remote.
6. Tags the repository with frozen release tag `a1-final`.
"""

**Notes**: Includes guard clauses to prevent accidental re-tagging or double-initialization.
