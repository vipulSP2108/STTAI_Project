# Prompts Used — Part D: Augmentation & Active Learning
<!-- Required by CS203 Assignment 1 Grader AI -->

## Prompt 1: Label-Preserving Audio Augmentation Engine
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_d_augmentation/augment_audio.py`  

**Exact prompt**:
"""
Build `part_d_augmentation/augment_audio.py` that:

1. Input: data/raw/audio/*.wav + data/metadata.csv
2. Output dir: data/processed/augmented/{aug_type}/

3. Implement 5 augmentations (implement at minimum 3 for full marks):
   - AUG 1 — MUSAN noise addition: Mix noise at SNR randomly chosen from 5–15 dB; verify SNR >= 5 dB after mixing.
   - AUG 2 — RIR Reverberation: Convolve with simulated room impulse response, normalize, verify silence ratio < 0.5.
   - AUG 3 — Speed perturbation: Apply 0.9x and 1.1x speed modifications; verify duration scaling and copy text label unchanged.
   - AUG 4 — Pitch perturbation: Pitch shift (+2 semitones); verify text label unchanged.
   - AUG 5 — Codec compression: Simulate low-bitrate acoustic compression (32kbps); verify text label unchanged.

4. After each augmentation: print a table row:
   clip_id | aug_type | orig_dur | aug_dur | label_preserved | checks_passed

5. Save augmented metadata to: data/processed/augmented/augmented_metadata.csv

Constants:
AUGMENT_SEED = 123
"""

**Notes**: Integrated automatic quality verification gates (clipping and silence ratio checks) run on every augmented audio waveform before writing to disk.

---

## Prompt 2: Uncertainty-Driven Active Learning Simulation
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_d_augmentation/active_learning.py`  

**Exact prompt**:
"""
Build `part_d_augmentation/active_learning.py` that:

SETUP:
- Unlabelled pool: clips in data/raw/audio/
- Budget sizes: BUDGETS = [10, 25, 50]
- Informativeness score: use openai-whisper (whisper.load_model("base"))
  For each clip: run whisper, compute score = -mean(token_log_probs) (higher = more uncertain = label first)

STRATEGY A — Active Learning:
- Rank clips by score (descending)
- At each budget B: "label" top-B clips (simulate by looking up true labels in intents.csv)
- Compute coverage: fraction of the 4 intent classes represented in selected set

STRATEGY B — Random Selection:
- At each budget B: randomly sample B clips (seed = AL_SEED = 42)
- Compute same coverage metric

RESULTS:
- Print comparison table: Budget | AL Coverage | Random Coverage | AL Win?
- Save results to supporting_files/plots/active_learning_results.json
- Save selected clip IDs to supporting_files/plots/al_selected_clips.json
- Print 3–4 sentence interpretation.

Constants:
AL_SEED = 42
"""

**Notes**: Added simulated fallback scoring logic when GPU or Whisper runtime is unavailable in headless environments.

---

## Prompt 3: Label-Efficiency Curve Visualization
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_d_augmentation/plot_learning_curve.py`  

**Exact prompt**:
"""
Build `part_d_augmentation/plot_learning_curve.py` that:
1. Reads supporting_files/plots/active_learning_results.json
2. Plots a label-efficiency curve using matplotlib:
   - X axis: Budget (10, 25, 50)
   - Y axis: Intent class coverage (fraction, 0.0–1.0)
   - Line 1 (blue): Active Learning
   - Line 2 (orange/red, dashed): Random Selection
   - Title: "Active Learning vs Random Selection — Label Efficiency"
3. Saves to supporting_files/plots/active_learning_curve.png (300 dpi)
"""

**Notes**: Configured publication-quality fonts, DPI, and formatting matching IEEE style.
