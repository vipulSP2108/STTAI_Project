# Prompts Used — Part B: Data Validation
<!-- Required by CS203 Assignment 1 Grader AI -->

## Prompt 1: 10-Check Automated Validation Test Suite
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-17  
**Output file**: `code/part_b_validation/validation_suite.py`  

**Exact prompt**:
"""
Build `part_b_validation/validation_suite.py` using pytest.
Implement exactly these 10 test functions. Each function:
- Tests all clips in data/metadata.csv
- On failure: print clip_id + reason, continue (do NOT stop at first failure)
- At end: print a summary table of which clips failed which checks

The 10 Required Checks:
1. test_sample_rate: == 16000 Hz
2. test_channels: == 1 (mono)
3. test_duration_bounds: 1.0s <= duration <= 30.0s
4. test_no_clipping: max(abs(audio)) < 0.99
5. test_silence_ratio: fraction of silent frames < 0.50
6. test_snr_estimate: estimated SNR = 20*log10(RMS_signal / RMS_noise) >= 5 dB
7. test_no_duplicate_hashes: all sha256_hash values in metadata.csv are unique
8. test_transcript_chars: only valid unicode chars (Latin, Devanagari, Gujarati, punctuation)
9. test_chars_per_second: 5 <= len(transcript)/duration <= 40
10. test_lang_id_valid: langdetect result in {en, hi, gu}

Add this top comment:
# ============================================================
# Part B: Automated Data Validation Suite
# CS203 Assignment 1 — Project 5: Voice Helpdesk ASR
#
# 10 checks: schema/types, audio quality, duplicates,
# transcript validity, language identification.
#
# Run: pytest part_b_validation/validation_suite.py -v --tb=short
# ============================================================
"""

**Notes**: Configured graceful fallback if langdetect is not installed, marking Check 10 as skipped rather than failing unexpectedly.

---

## Prompt 2: Before vs After Validation Auditor
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-17  
**Output file**: `code/part_b_validation/run_validation.py`  

**Exact prompt**:
"""
Build `part_b_validation/run_validation.py` that:

1. Runs pytest validation_suite.py on RAW data -> saves JSON report to
   supporting_files/validation_outputs/before.json
2. Prints a "before" table: Check | Clips Failed | Reason
3. (After fixes) runs again on FIXED data -> saves to
   supporting_files/validation_outputs/after.json
4. Prints a "before vs after" comparison table:
   Check | Before Failures | After Failures | Fixed?

Add comment:
# run_validation.py — wrapper that runs the validation suite
# and saves structured before/after evidence for the report.
"""

**Notes**: Integrated with pytest-json-report.

---

## Prompt 3: Adversarial Corruption Verification
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-17  
**Output file**: `code/part_b_validation/corruption_test.py`  

**Exact prompt**:
"""
Build `part_b_validation/corruption_test.py` that:

1. Takes 3 real clips from data/raw/audio/
2. Creates corrupted versions:
   - Corruption A: resample to 8000 Hz (wrong sample rate) -> test_sample_rate should FAIL
   - Corruption B: clip amplitude to 1.0 (digital clipping) -> test_no_clipping should FAIL
   - Corruption C: replace with silence (silent ratio = 1.0) -> test_silence_ratio should FAIL
3. Runs the relevant validation checks on each corrupted clip
4. ASSERTS the check fails for each corruption
5. Prints:
   [PASS] Corruption A detected: test_sample_rate FAILED as expected
   [PASS] Corruption B detected: test_no_clipping FAILED as expected
   [PASS] Corruption C detected: test_silence_ratio FAILED as expected

Add comment:
# corruption_test.py — Proves the validation suite is non-trivial.
# Required evidence for Part B grading.
"""

**Notes**: Uses standard wave and numpy modules to avoid external library reliance during corruption synthesis.
