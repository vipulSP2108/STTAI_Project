# Prompts Used — Part A: Data Collection & Instrumentation
<!-- Required by CS203 Assignment 1 Grader AI -->

## Prompt 1: Audio Recording CLI with Automated Provenance
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-17  
**Output file**: `code/part_a_collection/record_audio.py`  

**Exact prompt**:
"""
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
# ============================================================
"""

**Notes**: Configured default fallback for sounddevice/soundfile when running headlessly.

---

## Prompt 2: Metadata Extraction & Checksum Catalog
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-17  
**Output file**: `code/part_a_collection/build_metadata.py`  

**Exact prompt**:
"""
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
"""

**Notes**: Added wave module fallback when soundfile is unavailable.

---

## Prompt 3: Dynamic Ingestion Pipeline for Field WhatsApp Recordings
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_a_collection/ingest_records.py`  

**Exact prompt**:
"""
Build `part_a_collection/ingest_records.py` that:
1. Dynamically discovers speaker folders (P1–P19) containing heterogeneous audio containers (.m4a, .opus, .ogg, .mp4, .mpeg, .aac, .wav).
2. Converts/resamples each clip to standard 16 kHz mono WAV via ffmpeg.
3. Automatically identifies multi-query sessions and performs energy-based silence segmentation into query clips (1.0s - 30.0s).
4. Computes SHA-256 cryptographic signatures on all output WAVs and updates data/metadata.csv with full provenance.
5. Preserves raw Records/ intact (read-only ingestion).
"""

**Notes**: Handles 1-clip-1-tar subdirectories for P13–P19 and maps regions accurately.
