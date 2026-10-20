# ============================================================
# Part B: Automated Data Validation Suite
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# 10 automated checks: schema/types, audio quality, duplicates,
# transcript validity, language identification.
#
# Run: pytest part_b_validation/validation_suite.py -v --tb=short
#
# IMPORTANT: Run on RAW data first - failures are EXPECTED and are
# evidence that the suite is non-trivial. Fix, then re-run on clean data.
# ============================================================

import re, wave
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

METADATA_CSV = Path("data/metadata.csv")
AUDIO_DIR    = Path("data/raw/audio")

def load_metadata():
    assert METADATA_CSV.exists(), f"metadata.csv not found: {METADATA_CSV}"
    return pd.read_csv(METADATA_CSV)

def load_audio_numpy(clip_id):
    """Load WAV as float32 numpy array."""
    wav_path = AUDIO_DIR / f"{clip_id}.wav"
    try:
        import soundfile as sf
        audio, sr = sf.read(str(wav_path), dtype="float32")
        return audio, sr
    except ImportError:
        with wave.open(str(wav_path),"r") as w:
            sr = w.getframerate()
            raw = w.readframes(w.getnframes())
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        return audio, sr

# -------------------------------------------------------------------
# Check 1: Sample rate == 16000 Hz
# -------------------------------------------------------------------
def test_sample_rate():
    """All clips must be recorded at 16000 Hz (required by Whisper/IndicWav2Vec)."""
    df = load_metadata()
    failures = []
    for _, row in df.iterrows():
        if row["sample_rate"] != 16000:
            failures.append(f"clip_id={row['clip_id']} sample_rate={row['sample_rate']} (expected 16000)")
    if failures:
        pytest.fail("Sample rate check FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 2: Channels == 1 (mono)
# -------------------------------------------------------------------
def test_channels():
    """All clips must be mono (1 channel)."""
    df = load_metadata()
    failures = []
    for _, row in df.iterrows():
        if row["channels"] != 1:
            failures.append(f"clip_id={row['clip_id']} channels={row['channels']} (expected 1)")
    if failures:
        pytest.fail("Channels check FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 3: Duration bounds 1.0s <= duration <= 30.0s
# -------------------------------------------------------------------
def test_duration_bounds():
    """Duration must be between 1.0s and 30.0s. Too short = silence/error, too long = not a query."""
    df = load_metadata()
    failures = []
    for _, row in df.iterrows():
        if not (1.0 <= row["duration_sec"] <= 30.0):
            failures.append(f"clip_id={row['clip_id']} duration={row['duration_sec']:.2f}s (expected 1-30s)")
    if failures:
        pytest.fail("Duration bounds FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 4: No clipping (max |amplitude| < 0.99)
# -------------------------------------------------------------------
def test_no_clipping():
    """Max absolute amplitude must be < 0.99. Clipping = digital distortion."""
    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.glob("*.wav")):
        pytest.skip("Raw audio files in data/raw/audio/ not found (tracked via DVC, run 'dvc pull')")
    df = load_metadata()
    failures = []
    for _, row in df.iterrows():
        try:
            audio, _ = load_audio_numpy(row["clip_id"])
            max_amp = float(np.max(np.abs(audio)))
            if max_amp >= 0.99:
                failures.append(f"clip_id={row['clip_id']} max_amp={max_amp:.4f} >= 0.99 (CLIPPED)")
        except FileNotFoundError:
            failures.append(f"clip_id={row['clip_id']} WAV file not found")
    if failures:
        pytest.fail("Clipping check FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 5: Silence ratio < 0.50
# -------------------------------------------------------------------
def test_silence_ratio():
    """Fraction of frames with |amplitude| < 0.01 must be < 0.50. >50% = invalid clip."""
    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.glob("*.wav")):
        pytest.skip("Raw audio files in data/raw/audio/ not found (tracked via DVC, run 'dvc pull')")
    df = load_metadata()
    failures = []
    for _, row in df.iterrows():
        try:
            audio, _ = load_audio_numpy(row["clip_id"])
            silence_ratio = float(np.mean(np.abs(audio) < 0.01))
            if silence_ratio >= 0.5:
                failures.append(f"clip_id={row['clip_id']} silence_ratio={silence_ratio:.2f} >= 0.50")
        except FileNotFoundError:
            failures.append(f"clip_id={row['clip_id']} WAV file not found")
    if failures:
        pytest.fail("Silence ratio FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 6: Estimated SNR >= 5 dB
# -------------------------------------------------------------------
def test_snr_estimate():
    """SNR = 20*log10(RMS_signal / RMS_noise). Noise floor = bottom 10th percentile frames."""
    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.glob("*.wav")):
        pytest.skip("Raw audio files in data/raw/audio/ not found (tracked via DVC, run 'dvc pull')")
    df = load_metadata()
    failures = []
    frame_size = 512
    for _, row in df.iterrows():
        try:
            audio, _ = load_audio_numpy(row["clip_id"])
            # Frame-level RMS
            n_frames = len(audio) // frame_size
            if n_frames < 2:
                continue
            frames = audio[:n_frames*frame_size].reshape(n_frames, frame_size)
            frame_rms = np.sqrt(np.mean(frames**2, axis=1))
            noise_floor = np.percentile(frame_rms, 10)
            signal_rms = np.sqrt(np.mean(audio**2))
            if noise_floor < 1e-9: noise_floor = 1e-9
            snr_db = 20 * np.log10(signal_rms / noise_floor)
            if snr_db < 5.0:
                failures.append(f"clip_id={row['clip_id']} SNR={snr_db:.1f}dB < 5dB")
        except FileNotFoundError:
            failures.append(f"clip_id={row['clip_id']} WAV file not found")
    if failures:
        pytest.fail("SNR check FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 7: No duplicate SHA-256 hashes
# -------------------------------------------------------------------
def test_no_duplicate_hashes():
    """All SHA-256 hashes must be unique. Duplicates = same clip twice = data leakage risk."""
    df = load_metadata()
    dups = df[df.duplicated("sha256_hash", keep=False)]
    if not dups.empty:
        msg = dups[["clip_id","sha256_hash"]].to_string()
        pytest.fail(f"Duplicate hashes found:\n{msg}")

# -------------------------------------------------------------------
# Check 8: Transcript characters in valid unicode ranges
# -------------------------------------------------------------------
def test_transcript_chars():
    """Transcripts may only contain: Latin, Devanagari, Gujarati, digits, punctuation."""
    if not Path("data/labels/transcripts.csv").exists():
        pytest.skip("transcripts.csv not yet created - skip in Part A phase")
    df = pd.read_csv("data/labels/transcripts.csv")
    # Latin (basic + extended), Devanagari, Gujarati, digits, spaces, punctuation
    VALID = re.compile(r"^[a-zA-Z\u0900-\u097F\u0A80-\u0AFF0-9 .,?!\'\-\[\]]+$")
    failures = []
    for _, row in df.iterrows():
        text = str(row.get("transcript",""))
        if text and not VALID.match(text):
            bad_chars = [c for c in text if not VALID.match(c)]
            failures.append(f"clip_id={row['clip_id']} invalid chars: {set(bad_chars)}")
    if failures:
        pytest.fail("Transcript char check FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 9: Plausible characters-per-second (5 <= CPS <= 40)
# -------------------------------------------------------------------
def test_chars_per_second():
    """len(transcript)/duration must be 5-40 (human speech rate bounds)."""
    if not Path("data/labels/transcripts.csv").exists():
        pytest.skip("transcripts.csv not yet created")
    df_t = pd.read_csv("data/labels/transcripts.csv")
    df_m = load_metadata()
    df = df_t.merge(df_m[["clip_id","duration_sec"]], on="clip_id", how="left")
    failures = []
    for _, row in df.iterrows():
        text = str(row.get("transcript",""))
        dur = row.get("duration_sec", 0)
        if dur > 0:
            cps = len(text) / dur
            if not (5 <= cps <= 40):
                failures.append(f"clip_id={row['clip_id']} CPS={cps:.1f} (expected 5-40)")
    if failures:
        pytest.fail("CPS check FAILED:\n" + "\n".join(failures))

# -------------------------------------------------------------------
# Check 10: Language ID valid
# -------------------------------------------------------------------
def test_lang_id_valid():
    """Each transcript must be detected as one of: en, hi, gu."""
    if not Path("data/labels/transcripts.csv").exists():
        pytest.skip("transcripts.csv not yet created")
    try:
        from langdetect import detect, LangDetectException
    except ImportError:
        pytest.skip("langdetect not installed")
    df = pd.read_csv("data/labels/transcripts.csv")
    VALID_LANGS = {"en","hi","gu"}
    failures = []
    for _, row in df.iterrows():
        text = str(row.get("transcript",""))
        if len(text.split()) < 3:
            continue  # Too short to detect reliably
        try:
            lang = detect(text)
            if lang not in VALID_LANGS:
                failures.append(f"clip_id={row['clip_id']} detected lang={lang} (expected en/hi/gu)")
        except LangDetectException:
            failures.append(f"clip_id={row['clip_id']} lang detection failed")
    if failures:
        pytest.fail("Language ID check FAILED:\n" + "\n".join(failures))
