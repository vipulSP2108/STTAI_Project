# CS203 – Assignment 1: Project 5 — Cross-Lingual Voice Helpdesk ASR
## Complete Editor Prompt & Build Guide

> **Project**: Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining
> **Team**: Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma
> **Deadline**: 11:59 PM, 18 October 2026
> **Course**: CS 203, Software Tools and Techniques in AI — IIT Gandhinagar

---

## 🧭 Overview & Purpose of This File

This `prompt.md` is the **single source of truth** for the AI code editor to understand, plan,
and build the entire Assignment 1 submission. It maps every requirement (Parts A–F) to:
- **What** needs to be built
- **How** to build it (approach + library choices)
- **Exact prompts** the editor should use when generating code
- **Comments** to embed in code so it stays traceable and reproducible

Project 5 is a pipeline that records, validates, transcribes, and augments
code-mixed English–Hindi–Gujarati helpdesk speech, then versions it cleanly
for downstream ASR model training (Assignment 2).

---

## 📁 Repository Structure to Build

```
CS203_A1_Project5_<roll-numbers>/
├── code/                         ← git repo (tag: a1-final)
│   ├── README.md
│   ├── requirements.txt
│   ├── requirements_freeze.txt
│   ├── ENVIRONMENT.md
│   ├── LABELLING_PROTOCOL.md
│   ├── HANDOFF_A2.md
│   ├── prompts/                  ← ALL AI prompts used (REQUIRED by grader AI)
│   │   ├── part_a_collection.md
│   │   ├── part_b_validation.md
│   │   ├── part_c_labelling.md
│   │   ├── part_d_augmentation.md
│   │   └── part_e_versioning.md
│   ├── part_a_collection/
│   │   ├── record_audio.py
│   │   ├── build_metadata.py
│   │   └── consent_register.md
│   ├── part_b_validation/
│   │   ├── validation_suite.py
│   │   ├── run_validation.py
│   │   └── corruption_test.py
│   ├── part_c_labelling/
│   │   ├── guidelines_v1.md
│   │   ├── guidelines_v2.md
│   │   ├── label_studio_config.xml
│   │   └── compute_agreement.py
│   ├── part_d_augmentation/
│   │   ├── augment_audio.py
│   │   ├── active_learning.py
│   │   └── plot_learning_curve.py
│   ├── part_e_versioning/
│   │   ├── dvc_setup.sh
│   │   └── make_splits.py
│   └── part_f_report/
│       └── dataset_card.md
├── data/                         ← DVC-tracked, frozen at a1-final
│   ├── raw/audio/                ← .wav clips
│   ├── processed/audio_16khz/   ← resampled clips
│   ├── labels/
│   │   ├── transcripts.csv
│   │   └── intents.csv
│   ├── splits/
│   │   ├── train.csv
│   │   ├── val.csv
│   │   ├── test.csv
│   │   └── cohort_b_shifted.csv
│   ├── metadata.csv
│   └── gold_test_set.csv
├── supporting_files/
│   ├── label_studio_exports/
│   ├── agreement_calculations/
│   ├── validation_outputs/
│   ├── augmentation_samples/
│   ├── plots/
│   └── pipeline_demo.mp4        ← 2-min screen recording
└── report/
    └── report.pdf               ← ≤6 pages + appendices
```

---

## 🔧 PART A — Data Collection & Instrumentation (15 marks)

### Goal
Build a reproducible pipeline that records audio clips and logs every sample's provenance:
source, timestamp, collector ID, tool version, SHA-256 hash.
**Target: ≥2 hours speech, ≥15 speakers (30+ for final project).**

### Files to build
1. `part_a_collection/record_audio.py` — CLI recorder with auto metadata logging
2. `part_a_collection/build_metadata.py` — scans audio dir → produces metadata.csv
3. `part_a_collection/consent_register.md` — anonymised consent log

---

### PROMPT for `record_audio.py`

```
Build a Python CLI script `part_a_collection/record_audio.py` that:

1. Accepts these CLI arguments (use argparse):
   --speaker-id     : e.g., SPK001
   --region         : e.g., "Gujarat", "Rajasthan", "North India"
   --device         : e.g., "phone", "laptop", "external-mic"
   --noise-condition: e.g., "quiet", "noisy", "outdoor"
   --lang-mix       : e.g., "en-hi", "en-gu", "en-hi-gu"
   --script-file    : path to a .txt file of scripted prompts (one per line)
   --output-dir     : default = "data/raw/audio/"
   --clips-per-session: how many clips to record

2. Recording:
   - Use `sounddevice` library at 16000 Hz, mono (1 channel)
   - Each clip saved as: {speaker_id}_{UTC_timestamp}_{clip_index:03d}.wav
   - Use `soundfile` to save WAV

3. After saving each clip, append ONE row to data/metadata.csv (create if not exists):
   Columns:
   clip_id, speaker_id, region, device, noise_condition, lang_mix,
   sample_rate, duration_sec, channels, recording_tool, tool_version,
   collector, timestamp_utc, sha256_hash, script_prompt

   - sha256_hash: SHA-256 of raw WAV file bytes
   - tool_version: f"sounddevice=={sd.__version__};soundfile=={sf.__version__};python=={sys.version.split()[0]}"
   - collector: os.getenv("USER", "unknown")

4. Print per clip: "[RECORDED] clip_id={} duration={:.2f}s hash={}"

Add this exact comment block at top of file:
# ============================================================
# Part A: Audio Collection & Instrumentation
# CS203 Assignment 1 — Project 5: Voice Helpdesk ASR
# IIT Gandhinagar, 2026-27
#
# Purpose: Records helpdesk speech clips with full provenance.
# Every clip is traceable by: source, timestamp, collector ID,
# tool version, and SHA-256 content hash.
#
# Usage: python record_audio.py --speaker-id SPK001 --region Gujarat \
#        --device phone --noise-condition quiet --lang-mix en-hi \
#        --script-file scripts/helpdesk_prompts.txt
#
# CONSENT: Every speaker must complete the consent form first.
# Anonymised IDs (SPK001...) only — no real names in data.
# ============================================================

Also add inline comments:
# NOTE: 16000 Hz is FIXED — required by Whisper and IndicWav2Vec.
#       Changing this breaks all downstream models.
# NOTE: SHA-256 computed AFTER saving. Any post-save modification
#       will invalidate the hash — intentional tamper detection.
```

---

### PROMPT for `build_metadata.py`

```
Build `part_a_collection/build_metadata.py` that:

1. Scans data/raw/audio/ for all .wav files
2. For each file:
   - Read sample_rate, duration_sec, channels using soundfile
   - Compute SHA-256 hash of file bytes
   - Parse speaker_id, timestamp from filename: {speaker_id}_{timestamp}_{idx}.wav
3. Write/update data/metadata.csv (overwrite safe — check for existing entries by clip_id)
4. Print summary:
   Total clips: N | Total duration: X.Xh | Unique speakers: M
   Lang mix breakdown: en-hi=A, en-gu=B, en-hi-gu=C

Add top comment:
# -----------------------------------------------
# build_metadata.py — Post-collection metadata builder.
# Run after all recording sessions are complete.
# Safe to re-run (idempotent — does not duplicate rows).
# Usage: python build_metadata.py --audio-dir data/raw/audio/
# -----------------------------------------------
```

### Data Flow Diagram (add to README.md)
```
Speaker → Scripted/Spontaneous Query (helpdesk topic)
    ↓
record_audio.py (sounddevice, 16kHz mono)
    ↓
data/raw/audio/{speaker_id}_{timestamp}_{idx}.wav
    ↓
build_metadata.py (soundfile + hashlib)
    ↓
data/metadata.csv  ← single source of truth for all downstream steps
```

---

## ✅ PART B — Data Validation (20 marks)

### Goal
Automated validation suite with **≥10 checks** using **pytest + pandera**.
Run on raw data (expect failures), fix issues, re-run (all pass), then show it catches corrupted data.

### The 10 Required Checks for Project 5

| # | Check Name | What It Tests |
|---|-----------|---------------|
| 1 | sample_rate | == 16000 Hz |
| 2 | channels | == 1 (mono) |
| 3 | duration_bounds | 1.0s ≤ duration ≤ 30.0s |
| 4 | no_clipping | max(abs(audio)) < 0.99 |
| 5 | silence_ratio | fraction of silent frames < 0.50 |
| 6 | snr_estimate | estimated SNR ≥ 5 dB |
| 7 | no_duplicate_hashes | all sha256_hash values in metadata.csv are unique |
| 8 | transcript_chars | only valid unicode chars (Latin, Devanagari, Gujarati, punctuation) |
| 9 | chars_per_second | 5 ≤ len(transcript)/duration ≤ 40 |
| 10 | lang_id_valid | langdetect result ∈ {en, hi, gu} |

---

### PROMPT for `validation_suite.py`

```
Build `part_b_validation/validation_suite.py` using pytest.
Implement exactly these 10 test functions. Each function:
- Tests all clips in data/metadata.csv
- On failure: print clip_id + reason, continue (do NOT stop at first failure)
- At end: print a summary table of which clips failed which checks

def test_sample_rate():
    # Check 1: All clips must have sample_rate == 16000 Hz
    # Evidence: logged in metadata.csv from soundfile.info()
    ...

def test_channels():
    # Check 2: All clips must be mono (channels == 1)
    ...

def test_duration_bounds():
    # Check 3: Duration must be between 1.0s and 30.0s
    # Too short = likely silence/error. Too long = likely not a query.
    ...

def test_no_clipping():
    # Check 4: Max absolute amplitude must be < 0.99
    # Clipping = digital distortion = degrades ASR quality
    import soundfile as sf
    import numpy as np
    ...

def test_silence_ratio():
    # Check 5: Fraction of frames with |amplitude| < 0.01 must be < 0.50
    # >50% silence = invalid clip (mic off, pause, error)
    ...

def test_snr_estimate():
    # Check 6: Estimated SNR = 20*log10(RMS_signal / RMS_noise) >= 5 dB
    # Noise floor = bottom 10th percentile of frame energies
    ...

def test_no_duplicate_hashes():
    # Check 7: All SHA-256 hashes in metadata.csv must be unique
    # Duplicates = same clip recorded twice = data leakage risk
    import pandas as pd
    ...

def test_transcript_chars():
    # Check 8: Transcripts may only contain:
    # Latin (a-z, A-Z), Devanagari (U+0900-U+097F),
    # Gujarati (U+0A80-U+0AFF), digits, and punctuation [.,?!'-]
    # Stray symbols = labelling error
    ...

def test_chars_per_second():
    # Check 9: Characters per second = len(transcript) / duration_sec
    # Must be between 5 and 40 (human speech rate bounds)
    # Outside range = transcript/duration mismatch
    ...

def test_lang_id_valid():
    # Check 10: Run langdetect on each transcript
    # Detected language must be one of: en, hi, gu
    # Fails if transcript is in unrelated language = wrong file
    from langdetect import detect
    ...

Add this top comment:
# ============================================================
# Part B: Automated Data Validation Suite
# CS203 Assignment 1 — Project 5: Voice Helpdesk ASR
#
# 10 checks: schema/types, audio quality, duplicates,
# transcript validity, language identification.
#
# Run: pytest part_b_validation/validation_suite.py -v --tb=short
#
# IMPORTANT: Run on RAW data first — failures are EXPECTED
# and are evidence that the suite is non-trivial.
# Fix issues, then re-run on clean data (all should pass).
# ============================================================
```

---

### PROMPT for `run_validation.py`

```
Build `part_b_validation/run_validation.py` that:

1. Runs pytest validation_suite.py on RAW data → saves JSON report to
   supporting_files/validation_outputs/before.json

2. Prints a "before" table: Check | Clips Failed | Reason

3. (After manual fixes) runs again on FIXED data → saves to
   supporting_files/validation_outputs/after.json

4. Prints a "before vs after" comparison table:
   Check | Before Failures | After Failures | Fixed?

Add comment:
# run_validation.py — wrapper that runs the validation suite
# and saves structured before/after evidence for the report.
# The before.json MUST show at least some failures to be credible.
```

---

### PROMPT for `corruption_test.py`

```
Build `part_b_validation/corruption_test.py` that:

1. Takes 3 real clips from data/raw/audio/
2. Creates corrupted versions:
   - Corruption A: resample to 8000 Hz (wrong sample rate) → test_sample_rate should FAIL
   - Corruption B: clip amplitude to 1.0 (digital clipping) → test_no_clipping should FAIL
   - Corruption C: replace with silence (silent ratio = 1.0) → test_silence_ratio should FAIL

3. Runs the relevant validation checks on each corrupted clip
4. ASSERTS the check fails for each corruption
5. Prints:
   ✓ Corruption A detected: test_sample_rate FAILED as expected
   ✓ Corruption B detected: test_no_clipping FAILED as expected
   ✓ Corruption C detected: test_silence_ratio FAILED as expected

Add comment:
# corruption_test.py — Proves the validation suite is non-trivial.
# Required evidence for Part B grading.
# Every corruption MUST trigger a specific check failure.
```

---

## 🏷️ PART C — Labelling and Agreement (25 marks)

### Goal
Label audio in Label Studio, ≥2 annotators on ≥100 overlapping clips.
Report WER between annotators (transcripts) and Cohen's κ (intent).
Write guidelines v1 → v2. Freeze gold test set.

### Label Schema (Project 5)
- **Level 1**: `transcript` (free text, code-mixed English/Hindi/Gujarati) ← fill FIRST
- **Level 2**: `intent` ∈ {admissions, hostel_mess, it_support, student_services} ← fill SECOND
- ⚠️ **Order is mandatory** — transcript before intent (prevents intent priming transcription)

---

### PROMPT for `compute_agreement.py`

```
Build `part_c_labelling/compute_agreement.py` that:

1. Reads TWO Label Studio JSON exports:
   supporting_files/label_studio_exports/round1_annotator_a.json
   supporting_files/label_studio_exports/round1_annotator_b.json

2. TRANSCRIPT agreement (WER):
   - Use jiwer: from jiwer import wer
   - For each clip in the overlap set: compute wer(ref=annotator_a, hyp=annotator_b)
   - Report: mean WER, median WER, std WER
   - Print worst 10 clips (highest WER) with clip_id and both transcripts

3. INTENT agreement (Cohen's κ):
   - Use sklearn.metrics.cohen_kappa_score
   - Print the 4x4 confusion matrix (admissions/hostel_mess/it_support/student_services)
   - Print the 10 clips where annotators disagreed on intent, with clip_id + both labels

4. Run for ROUND 1 (v1 guidelines) and ROUND 2 (v2 guidelines) and compare:
   Before (v1): WER=X, Kappa=Y
   After  (v2): WER=A, Kappa=B   ← should show improvement

5. Save everything to:
   supporting_files/agreement_calculations/agreement_report.json

6. FREEZE gold test set:
   - Select clips where BOTH annotators agree exactly on transcript (WER=0) AND intent
   - Write to data/gold_test_set.csv
   - Print: "Gold test set frozen: N clips. NEVER use for tuning (A1 or A2)."

Add comment:
# ============================================================
# Part C: Inter-Annotator Agreement
# CS203 Assignment 1 — Project 5
#
# Transcript: WER between annotators (jiwer)
# Intent:     Cohen's kappa (sklearn)
#
# Gold test set: clips where BOTH annotators fully agree.
# Once frozen, DO NOT use gold_test_set.csv for any tuning.
# ============================================================
```

---

### PROMPT for `label_studio_config.xml`

```
Write Label Studio config XML for Project 5 audio transcription + intent labelling:

Requirements:
- Audio player (plays the .wav clip)
- TextArea for transcript:
  placeholder="Type code-mixed transcript (English/हिन्दी/ગુજરાતી)"
  name="transcript"
- Choices for intent (single choice):
  name="intent"
  choices: admissions | hostel_mess | it_support | student_services

CRITICAL: The XML layout must force transcript before intent by putting
TextArea BEFORE Choices in the XML order.

Add XML comment:
<!-- LABEL ORDER: transcript → intent
     Annotators MUST fill transcript first, then choose intent.
     This prevents intent choice from biasing the transcription.
     See LABELLING_PROTOCOL.md for the rationale. -->
```

---

### Guidelines v1 content (for `guidelines_v1.md`)

```
Write guidelines_v1.md (1.5 pages) covering:

Title: Annotation Guidelines v1 — Voice Helpdesk ASR (Project 5)

1. PURPOSE
   - Label code-mixed helpdesk queries with transcript + intent

2. SCRIPT RULES
   - Hindi words → Devanagari (e.g. मेस, छात्रावास, प्रवेश)
   - Gujarati words → Gujarati script (e.g. મેસ, હૉસ્ટેલ)
   - English words → Roman script
   - Numbers: write as spoken ("five" not "5")

3. NORMALISATION
   - Expand common abbreviations: "CS dept" → "CS department"
   - Fillers (um, uh, hmm): OMIT unless they change meaning
   - Incomplete/cut-off words: transcribe as heard (e.g., "adm-")
   - Noise: [NOISE] | Background music: [MUSIC] | Unintelligible: [UNK]

4. INTENT DEFINITIONS
   - admissions: admission process, forms, deadlines, seat availability
   - hostel_mess: hostel rooms, mess food/timings, hostel complaints
   - it_support: WiFi, email/accounts, software licenses, printers, lab PCs
   - student_services: library, health center, transport, student ID cards
   - When query spans two topics: choose the PRIMARY/dominant topic

5. WORKED EXAMPLES (5 examples with correct transcript + intent)

6. EDGE CASES
   - Completely inaudible: mark full transcript as [UNK], intent as most likely from context
   - Multi-language sentence: follow per-word script rules above

Top comment:
<!-- guidelines_v1.md: First-round annotation guidelines.
     Used in Round 1 labelling.
     Revised to v2 after disagreement analysis. See guidelines_v2.md. -->
```

---

## 🔊 PART D — Augmentation & Active Learning (20 marks)

### Goal
≥3 label-preserving augmentations with verified label preservation.
Active learning (Whisper confidence score) vs random selection at 3 budget sizes with plot.

### Augmentations to implement (Project 5 spec)

| # | Name | Library | Label preservation check |
|---|------|---------|--------------------------|
| 1 | MUSAN noise | audiomentations / numpy | SNR check still passes |
| 2 | RIR reverberation | scipy.signal.fftconvolve | silence ratio check still passes |
| 3 | Speed perturbation (0.9x, 1.1x) | librosa.effects.time_stretch | transcript label unchanged (rule-based: same text) |
| 4 | Pitch perturbation (±2 semitones) | librosa.effects.pitch_shift | transcript label unchanged |
| 5 | Codec compression (MP3 32kbps → WAV) | pydub | transcript label unchanged |

---

### PROMPT for `augment_audio.py`

```
Build `part_d_augmentation/augment_audio.py` that:

1. Input: data/raw/audio/*.wav + data/metadata.csv
2. Output dir: data/processed/augmented/{aug_type}/

3. Implement 5 augmentations (implement at minimum 3 for full marks):

   AUG 1 — MUSAN noise addition:
   - Load random MUSAN noise clip (from data/musan/ or download path)
   - Mix at SNR randomly chosen from 5–15 dB
   - Save as: data/processed/augmented/musan/{clip_id}_musan.wav
   - Verify: resampled at 16kHz, no clipping, SNR still >= 5 dB after mixing

   AUG 2 — RIR Reverberation:
   - Load a random room impulse response (from data/rir/ or openslr.org/26)
   - Convolve: scipy.signal.fftconvolve(audio, rir)[:len(audio)]
   - Normalize to avoid clipping
   - Save as: data/processed/augmented/rir/{clip_id}_rir.wav
   - Verify: silence ratio < 0.5

   AUG 3 — Speed perturbation:
   - Apply 0.9x: librosa.effects.time_stretch(audio, rate=0.9)
   - Apply 1.1x: librosa.effects.time_stretch(audio, rate=1.1)
   - Save both versions
   - Label check: transcript is UNCHANGED (same text, just slower/faster)
   - Verify: new duration ≈ original_duration / rate

   AUG 4 — Pitch perturbation:
   - librosa.effects.pitch_shift(audio, sr=16000, n_steps=+2) and n_steps=-2
   - Label check: transcript unchanged

   AUG 5 — Codec compression:
   - Encode to MP3 at 32kbps then decode back to WAV using pydub
   - Simulates low-end device recording quality
   - Label check: transcript unchanged

4. After each augmentation: print a table row:
   clip_id | aug_type | orig_dur | aug_dur | label_preserved | checks_passed

5. Save augmented metadata to: data/processed/augmented/augmented_metadata.csv

Add comment:
# ============================================================
# Part D: Label-Preserving Audio Augmentation
# CS203 Assignment 1 — Project 5
#
# Augmentations: MUSAN noise, RIR reverb, speed perturbation,
# pitch perturbation, codec compression.
#
# Label preservation: augmented clips carry the SAME transcript
# and intent label as their source. This is verified automatically:
# - Audio checks (SNR, silence ratio) re-run on augmented clips
# - Text label is copied unchanged (rule-based, not human)
#
# MUSAN: https://www.openslr.org/17/
# RIR:   https://www.openslr.org/26/
# SEED:  AUGMENT_SEED = 123 (see ENVIRONMENT.md)
# ============================================================
AUGMENT_SEED = 123  # MUST match ENVIRONMENT.md — change requires re-run
```

---

### PROMPT for `active_learning.py`

```
Build `part_d_augmentation/active_learning.py` that:

SETUP:
- Unlabelled pool: clips in data/raw/audio/ not yet in data/labels/transcripts.csv
- Budget sizes: BUDGETS = [10, 25, 50]
- Informativeness score: use openai-whisper (whisper.load_model("base"))
  For each clip: run whisper, get token log-probabilities, compute
  score = -mean(token_log_probs)   ← higher = more uncertain = label first

STRATEGY A — Active Learning:
- Rank all unlabelled clips by score (descending — most uncertain first)
- At each budget B: "label" top-B clips (simulate by looking up true labels in transcripts.csv)
- Compute coverage: fraction of the 4 intent classes represented in selected set

STRATEGY B — Random Selection:
- At each budget B: randomly sample B clips (seed = AL_SEED = 42)
- Compute same coverage metric

RESULTS:
- Print comparison table:
  Budget | AL Coverage | Random Coverage | AL Win?
     10  |    X/4      |     Y/4         | Yes/No
     25  |             |                 |
     50  |             |                 |

- Save results to supporting_files/plots/active_learning_results.json
- Save selected clip IDs to supporting_files/plots/al_selected_clips.json

- Print 3–4 sentence interpretation:
  "Active learning selects clips the model finds hard (low confidence).
   At budget=10, AL achieves X/4 coverage vs random Y/4.
   [Interpret: does AL beat random? Why or why not?]"

Add comment:
# ============================================================
# Part D: Active Learning vs Random Selection
# CS203 Assignment 1 — Project 5
#
# Informativeness signal: Whisper base decoder log-probability.
# Low confidence (high uncertainty score) = clip is hard =
# high priority for human transcription.
#
# Comparison: AL selection vs random at budgets [10, 25, 50].
# Metric: coverage of intent classes in selected set.
#
# AL_SEED = 42 (fixed for reproducibility — see ENVIRONMENT.md)
# ============================================================
AL_SEED = 42  # MUST match ENVIRONMENT.md
```

---

### PROMPT for `plot_learning_curve.py`

```
Build `part_d_augmentation/plot_learning_curve.py` that:

1. Reads supporting_files/plots/active_learning_results.json
2. Plots a label-efficiency curve using matplotlib:
   - X axis: Budget (10, 25, 50)
   - Y axis: Intent class coverage (fraction, 0.0–1.0)
   - Line 1 (blue): Active Learning
   - Line 2 (orange, dashed): Random Selection
   - Title: "Active Learning vs Random Selection — Label Efficiency"
   - Legend, grid, tight_layout
3. Saves to supporting_files/plots/active_learning_curve.png (300 dpi)
4. Print: "Plot saved to supporting_files/plots/active_learning_curve.png"

Comment:
# This plot is Figure X in the report.
# The data behind it is in active_learning_results.json (required by grader).
```

---

## 🗂️ PART E — Versioning and Splits (10 marks)

### Goal
DVC-version all data. Make speaker-disjoint train/val/test splits + Cohort B shifted split.
Tag repository as `a1-final`.

---

### PROMPT for `make_splits.py`

```
Build `part_e_versioning/make_splits.py` that:

CONSTANTS (must match ENVIRONMENT.md):
SPLIT_SEED = 42

1. Read data/metadata.csv (all clips with speaker_id, region)

2. Get unique speaker_ids. Shuffle with seed SPLIT_SEED.
   Assign: first 70% → train, next 15% → val, last 15% → test.

3. LEAKAGE CHECK (assert, do NOT proceed if fails):
   train_speakers ∩ val_speakers == empty
   train_speakers ∩ test_speakers == empty
   val_speakers ∩ test_speakers == empty

4. SHIFTED SPLIT (Cohort B):
   - Pick the region with fewest speakers (underrepresented accent)
   - Mark ALL clips from that region as "cohort_b_shifted"
   - These speakers must NOT appear in train/val/test

5. Write split manifests:
   data/splits/train.csv         — clip_id, speaker_id, split="train"
   data/splits/val.csv           — clip_id, speaker_id, split="val"
   data/splits/test.csv          — clip_id, speaker_id, split="test"
   data/splits/cohort_b_shifted.csv — clip_id, speaker_id, region, split="shifted"

6. Print summary:
   Train:   N clips, M speakers
   Val:     N clips, M speakers
   Test:    N clips, M speakers
   Shifted: N clips, M speakers (region=X — Cohort B for A2 drift experiments)
   Leakage check: PASSED ✓

Add comment:
# ============================================================
# Part E: Leakage-Free Data Splits
# CS203 Assignment 1 — Project 5
#
# Split unit: SPEAKER — never clip or row.
# This prevents speaker leakage: model never hears same voice
# in both training and evaluation sets.
#
# Cohort B: held-out accent/region group.
# Used as the "shifted distribution" in Assignment 2 drift experiments.
#
# SPLIT_SEED = 42 — fixed for reproducibility.
# Changing the seed requires re-generating splits and re-tagging.
# ============================================================
SPLIT_SEED = 42  # MUST match ENVIRONMENT.md
```

---

### PROMPT for `dvc_setup.sh`

```
Write `part_e_versioning/dvc_setup.sh`:

#!/bin/bash
# ============================================================
# dvc_setup.sh — Data versioning setup
# CS203 Assignment 1— Project 5
#
# Run ONCE after all data is frozen and splits are made.
# Creates the a1-final git tag that Assignment 2 starts from.
# WARNING: Do NOT re-run after tagging without removing the tag.
# ============================================================

set -e

# Step 1: Initialise DVC (skip if already done)
dvc init --no-scm 2>/dev/null || echo "DVC already initialised"

# Step 2: Track the data directory
dvc add data/

# Step 3: Set up local DVC remote (change path if needed)
dvc remote add -d localremote ../dvc-remote || \
  dvc remote modify localremote url ../dvc-remote

# Step 4: Commit DVC files
git add data.dvc .dvc/
git commit -m "chore: DVC track data/ at a1-final"

# Step 5: Push data to remote
dvc push

# Step 6: Tag the repo
git tag -a a1-final -m "Assignment 1 final submission — CS203 Project 5"
echo "Tag a1-final created."
echo "DVC setup complete. Assignment 2 starts from this tag."
```

---

## 📝 PART F — Report & Reproducibility (10 marks)

### PROMPT for `README.md`

```
Write README.md that rebuilds data/ in AT MOST 5 commands.

# CS203 Assignment 1 — Project 5: Voice Helpdesk ASR

**Team**: Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma
**GitHub**: [add URL]
**DVC Remote**: [add path]

## Quickstart — Rebuild data/ in 5 commands
pip install -r requirements.txt
python part_a_collection/build_metadata.py --audio-dir data/raw/audio/
pytest part_b_validation/validation_suite.py -v
python part_c_labelling/compute_agreement.py
python part_e_versioning/make_splits.py

## What each command does
1. Install all dependencies (pinned versions)
2. Rebuild metadata.csv from raw audio files
3. Run 10 validation checks (all should pass on fixed data)
4. Compute inter-annotator agreement + freeze gold test set
5. Create leakage-free splits (train/val/test/cohort_b)

## Repository Structure
[paste directory tree here]

## Data
Tracked with DVC. Pull with: dvc pull

## AI Assistance
All prompts used → see prompts/ directory.
```

---

### PROMPT for `ENVIRONMENT.md`

```
Write ENVIRONMENT.md listing ALL software versions + seeds:

## Python
Python: 3.10.x (specify exact version)

## Key Python Packages (from requirements_freeze.txt)
sounddevice==0.4.6
soundfile==0.12.1
librosa==0.10.1
openai-whisper==20231117
jiwer==3.0.3
pandera==0.17.2
audiomentations==0.33.0
langdetect==1.0.9
scikit-learn==1.3.2
pydub==0.25.1
scipy==1.11.4
numpy==1.24.4
matplotlib==3.8.0
pandas==2.0.3
dvc==3.30.0

## Label Studio
Version: 1.10.0
Config file: code/part_c_labelling/label_studio_config.xml

## Other Tools
sox: 14.4.2
OS: [macOS 14.x or Ubuntu 22.04 — specify]
GPU/CUDA: [specify if used, else "CPU only"]

## Random Seeds — MUST match code constants
SPLIT_SEED   = 42   # part_e_versioning/make_splits.py
AUGMENT_SEED = 123  # part_d_augmentation/augment_audio.py
AL_SEED      = 42   # part_d_augmentation/active_learning.py

## Models Used
- Whisper base:
  Source: openai/whisper — HuggingFace revision hash: [pin exact commit]
  Used for: active learning confidence scores, baseline WER measurement

Top comment:
# ENVIRONMENT.md — Complete software specification for reproducing data/.
# Update immediately when adding any new tool or changing a version.
# Seeds here MUST exactly match the constants in the Python scripts.
```

---

### PROMPT for `LABELLING_PROTOCOL.md`

```
Write LABELLING_PROTOCOL.md covering:

# Labelling Protocol — Voice Helpdesk ASR (Project 5)

## Annotator IDs (anonymised)
- A1: [anonymised]
- A2: [anonymised]

## Items Labelled
| Round | Annotators | Clips | Guideline version | Overlap set |
|-------|-----------|-------|-------------------|-------------|
| 1 | A1, A2 | CL001–CL150 | v1 | CL001–CL100 (100 clips) |
| 2 | A1, A2 | CL001–CL060 | v2 | CL001–CL060 (revision) |

## Label Order (CRITICAL — must be followed exactly)
Level 1: transcript (fill first)
Level 2: intent    (fill second, after transcript is complete)

Rationale: filling transcript first prevents the annotator's intent
hypothesis from unconsciously influencing what they hear.
Confirmed: both A1 and A2 agreed to this order before starting.

## Label Studio Setup
Version: 1.10.0
Config: label_studio_config.xml
Guideline version shown: v1 for Round 1, v2 for Round 2

## Item Presentation Order
Clips shown in randomised order (seed=7) by Label Studio.
Neither annotator saw the other's labels during their session.
No model predictions or pre-annotations were shown.

## Disagreement Resolution
- Transcript: if WER < 0.2 → keep A1's version; else → discuss and reach consensus
- Intent: majority vote (2 annotators); ties broken by third team member
- Final adjudicator: [name]

## Timeline
| Date | Round | Export Files |
|------|-------|-------------|
| YYYY-MM-DD | Round 1 | exports/round1_a1.json, exports/round1_a2.json |
| YYYY-MM-DD | Round 2 | exports/round2_a1.json, exports/round2_a2.json |

Top comment:
# LABELLING_PROTOCOL.md
# Lets someone outside the team repeat our labelling the same way.
# Covers: annotator IDs, label order, item order, what was visible,
# disagreement resolution, and timeline matched to export files.
```

---

### PROMPT for `HANDOFF_A2.md`

```
Write HANDOFF_A2.md (filled in at submission time):

# Handoff Document — Assignment 2
# CS203 Project 5: Voice Helpdesk ASR

## a1-final Tag
Git commit hash: [fill at submission]
GitHub URL: [fill at submission]

## Frozen Files
| File | SHA-256 | Purpose |
|------|---------|---------|
| data/gold_test_set.csv | [hash] | Gold eval set — never use for tuning |
| data/splits/train.csv | [hash] | Training set (speaker-disjoint) |
| data/splits/val.csv | [hash] | Validation set |
| data/splits/test.csv | [hash] | Test set |
| data/splits/cohort_b_shifted.csv | [hash] | Drift test (Cohort B accent group) |

## Label Schema
transcript: free text, code-mixed English/Hindi/Gujarati
intent: {admissions, hostel_mess, it_support, student_services}

## Split Definitions
- Split unit: speaker (never clip/row)
- Train: 70% of speakers | Val: 15% | Test: 15% | Cohort B: held-out region
- SPLIT_SEED = 42

## Gold Set Checksum
SHA-256 of data/gold_test_set.csv: [fill at submission]
DO NOT use this file for any training or hyperparameter tuning in A2.

Comment at top:
# HANDOFF_A2.md — Written at a1-final freeze.
# Assignment 2 must start from this exact state.
# Any number in A2 that uses these files must reference this document.
```

---

## 📂 `prompts/` Folder Structure

> ⚠️ The grader's AI verifies prompts match actual code. Include EVERY prompt — from IDEs, ChatGPT, Claude, Copilot. Format: model name + version + date + output file + exact prompt text.

### Template for each file in `prompts/`

```markdown
# Prompts Used — Part [X]: [Part Name]

## Prompt [N]
**Model**: Claude Sonnet 4.6 / ChatGPT-4o / GitHub Copilot
**Date**: YYYY-MM-DD
**Output file**: code/part_X_.../filename.py

**Exact prompt**:
"""
[paste the exact prompt you typed]
"""

**Notes**: [any edits made to the generated output]
```

Create one file per part: `part_a_collection.md`, `part_b_validation.md`,
`part_c_labelling.md`, `part_d_augmentation.md`, `part_e_versioning.md`

---

## 📋 Final Submission Checklist

```
SUBMISSION: CS203_A1_Project5_<roll-numbers>.zip
Deadline:   18 October 2026, 11:59 PM

DATA & COLLECTION
[ ] data/metadata.csv — all clips, all fields, SHA-256 hashes present
[ ] data/raw/audio/ — ≥2 hours, ≥15 speakers
[ ] consent_register.md — anonymised consent log

VALIDATION
[ ] pytest validation_suite.py -v  — 10 checks, all pass on fixed data
[ ] supporting_files/validation_outputs/before.json — shows raw data failures
[ ] supporting_files/validation_outputs/after.json — shows clean pass
[ ] corruption_test.py output logged — shows suite detects corruptions

LABELLING
[ ] data/labels/transcripts.csv — transcribed
[ ] data/labels/intents.csv — intent-labelled
[ ] ≥100 clips double-annotated in Label Studio
[ ] supporting_files/label_studio_exports/ — raw exports, all rounds
[ ] supporting_files/agreement_calculations/agreement_report.json
[ ] WER between annotators reported (before AND after guideline revision)
[ ] Cohen's κ reported + confusion matrix + 10 disagreements analysed
[ ] data/gold_test_set.csv — FROZEN, never used for tuning

AUGMENTATION & ACTIVE LEARNING
[ ] ≥3 augmentations implemented and verified label-preserving
[ ] data/processed/augmented/ — augmented clips
[ ] supporting_files/plots/active_learning_curve.png
[ ] active_learning.py — AL vs random at budgets [10, 25, 50]
[ ] Interpretation text (3–4 sentences) in report

VERSIONING & SPLITS
[ ] data/splits/train.csv, val.csv, test.csv — speaker-disjoint
[ ] data/splits/cohort_b_shifted.csv — Cohort B shifted split
[ ] Leakage check PASSED (no speaker in multiple splits)
[ ] git tag a1-final created
[ ] dvc push completed

REPORT & REPRODUCIBILITY
[ ] README.md — data rebuilds in ≤5 commands
[ ] requirements.txt + requirements_freeze.txt
[ ] ENVIRONMENT.md — all versions + seeds (match code constants)
[ ] LABELLING_PROTOCOL.md — complete
[ ] HANDOFF_A2.md — filled with hashes + commit hash
[ ] part_f_report/dataset_card.md
[ ] prompts/ — ALL AI prompts (exact text + model + date + output file)
[ ] supporting_files/pipeline_demo.mp4 — 2-min screen recording
[ ] report/report.pdf — ≤6 pages + appendices

FINAL CHECK
[ ] Unzip into new folder → README commands rebuild data/
[ ] No hardcoded local paths in any script
[ ] No leftover temp files in repo (git clean -n)
[ ] Each team member committed from their own account
```

---

## 🔑 Marks Mapping

| Part | Marks | Key deliverable |
|------|-------|----------------|
| A — Collection | 15 | metadata.csv, record_audio.py, consent log |
| B — Validation | 20 | 10 checks pass, before/after table, corruption test |
| C — Labelling | 25 | ≥100 double-annotated, WER+kappa, gold set |
| D — Augmentation | 20 | ≥3 augs + label proof, AL vs random plot |
| E — Versioning | 10 | DVC, speaker-disjoint splits, a1-final tag |
| F — Reproducibility | 10 | README ≤5 cmds, ENVIRONMENT.md, LABELLING_PROTOCOL.md |

---

## 💡 Critical Rules for the Editor

1. **All paths relative** — use `pathlib.Path(__file__).parent` not hardcoded `/Users/...`
2. **Pin seeds as module-level constants** — e.g., `SPLIT_SEED = 42` at top of file
3. **Every number in report → file in supporting_files/** — grader AI cross-checks all figures
4. **prompts/ = exact prompts** — copy-paste the actual prompts you sent, not paraphrases
5. **No stray files** — run `git clean -n` before tagging a1-final
6. **gold_test_set.csv is sacred** — once frozen, NEVER used for any tuning (A1 or A2)
7. **HANDOFF_A2.md filled last** — fill hashes and commit after tagging

---

*Generated: October 17, 2026 | CS203 Assignment 1 — Project 5: Cross-Lingual Voice Helpdesk ASR*
*IIT Gandhinagar, Semester I, 2026–2027*
