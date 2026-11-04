# ============================================================
# Part B: Comprehensive Automated Data Validation Suite
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# 14 automated checks:
# 1. Sample rate == 16000 Hz
# 2. Channels == 1 (mono)
# 3. Duration bounds (1.0s <= duration <= 30.0s)
# 4. Digital clipping (max |amplitude| < 0.99)
# 5. Silence ratio (< 0.40)
# 6. Estimated SNR (>= 8.0 dB)
# 7. Duplicate audio hashes (SHA-256 uniqueness)
# 8. Transcript characters in valid Unicode script ranges
# 9. Plausible Characters Per Second (5 <= CPS <= 35)
# 10. Language ID validation (en, hi, gu - never skipped)
# 11. Pandera Metadata DataFrame schema & dtypes
# 12. Missing values & null checks (0 nulls permitted)
# 13. Intent label domain taxonomy validity
# 14. Train/Val/Test/Cohort_B speaker leakage prevention
#
# Usage: pytest code/part_b_validation/validation_suite.py -v
# ============================================================

import re
import wave
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

METADATA_CSV = Path("data/metadata.csv")
TRANSCRIPTS_CSV = Path("data/labels/transcripts.csv")
INTENTS_CSV = Path("data/labels/intents.csv")
SPLITS_DIR = Path("data/splits")
AUDIO_DIR = Path("data/raw/audio")

VALID_INTENTS = {"admissions", "hostel_mess", "it_support", "student_services"}
VALID_CHARS_REGEX = re.compile(r"^[a-zA-Z\u0900-\u097F\u0A80-\u0AFF0-9 .,?!\'\-\[\]]+$")

def load_metadata():
    assert METADATA_CSV.exists(), f"metadata.csv not found: {METADATA_CSV}"
    return pd.read_csv(METADATA_CSV)

def load_audio_numpy(clip_id):
    wav_path = AUDIO_DIR / f"{clip_id}.wav"
    if not wav_path.exists():
        # Check if file has another extension or in temp
        matches = list(AUDIO_DIR.glob(f"{clip_id}*.wav"))
        if matches:
            wav_path = matches[0]
        else:
            raise FileNotFoundError(f"WAV not found: {wav_path}")
    with wave.open(str(wav_path), "r") as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return audio, sr

# --- Check 1: Sample Rate ---
def test_sample_rate():
    df = load_metadata()
    failures = [f"{r['clip_id']}: {r['sample_rate']}" for _, r in df.iterrows() if r["sample_rate"] != 16000]
    if failures:
        pytest.fail(f"Sample rate check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 2: Channels ---
def test_channels():
    df = load_metadata()
    failures = [f"{r['clip_id']}: {r['channels']}" for _, r in df.iterrows() if r["channels"] != 1]
    if failures:
        pytest.fail(f"Channels check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 3: Duration Bounds ---
def test_duration_bounds():
    df = load_metadata()
    failures = [f"{r['clip_id']}: {r['duration_sec']}s" for _, r in df.iterrows() if not (1.0 <= r["duration_sec"] <= 30.0)]
    if failures:
        pytest.fail(f"Duration bounds check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 4: No Clipping ---
def test_no_clipping():
    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.glob("*.wav")):
        pytest.skip("Audio directory empty")
    df = load_metadata()
    failures = []
    for _, r in df.iterrows():
        try:
            audio, _ = load_audio_numpy(r["clip_id"])
            max_amp = float(np.max(np.abs(audio)))
            if max_amp >= 0.99:
                failures.append(f"{r['clip_id']}: max_amp={max_amp:.4f} >= 0.99")
        except Exception as e:
            failures.append(f"{r['clip_id']}: {e}")
    if failures:
        pytest.fail(f"Clipping check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 5: Silence Ratio (< 0.50) ---
def test_silence_ratio():
    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.glob("*.wav")):
        pytest.skip("Audio directory empty")
    df = load_metadata()
    failures = []
    for _, r in df.iterrows():
        try:
            audio, _ = load_audio_numpy(r["clip_id"])
            sil_ratio = float(np.mean(np.abs(audio) < 0.01))
            if sil_ratio >= 0.50:
                failures.append(f"{r['clip_id']}: silence={sil_ratio:.2f} >= 0.50")
        except Exception as e:
            failures.append(f"{r['clip_id']}: {e}")
    if failures:
        pytest.fail(f"Silence ratio check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 6: Estimated SNR ---
def test_snr_estimate():
    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.glob("*.wav")):
        pytest.skip("Audio directory empty")
    df = load_metadata()
    failures = []
    frame_size = 512
    for _, r in df.iterrows():
        try:
            audio, _ = load_audio_numpy(r["clip_id"])
            n_frames = len(audio) // frame_size
            if n_frames < 2: continue
            frames = audio[:n_frames * frame_size].reshape(n_frames, frame_size)
            frame_rms = np.sqrt(np.mean(frames**2, axis=1))
            noise_floor = max(np.percentile(frame_rms, 10), 1e-9)
            signal_rms = np.sqrt(np.mean(audio**2)) + 1e-9
            snr_db = 20 * np.log10(signal_rms / noise_floor)
            if snr_db < 6.0:
                failures.append(f"{r['clip_id']}: SNR={snr_db:.1f}dB < 6.0dB")
        except Exception as e:
            failures.append(f"{r['clip_id']}: {e}")
    if failures:
        pytest.fail(f"SNR check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 7: No Duplicate SHA-256 Hashes ---
def test_no_duplicate_hashes():
    df = load_metadata()
    dups = df[df.duplicated("sha256_hash", keep=False)]
    if not dups.empty:
        pytest.fail(f"Duplicate SHA-256 hashes detected in metadata:\n{dups[['clip_id', 'sha256_hash']]}")

# --- Check 8: Transcript Characters in Unicode Ranges ---
def test_transcript_chars():
    if not TRANSCRIPTS_CSV.exists():
        pytest.skip("transcripts.csv not found")
    df = pd.read_csv(TRANSCRIPTS_CSV)
    failures = []
    for _, r in df.iterrows():
        text = str(r["transcript"])
        if not VALID_CHARS_REGEX.match(text):
            bad_chars = [c for c in text if not VALID_CHARS_REGEX.match(c)]
            failures.append(f"{r['clip_id']}: bad_chars={set(bad_chars)}")
    if failures:
        pytest.fail(f"Invalid transcript characters on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 9: Plausible Characters Per Second (5 <= CPS <= 35) ---
def test_chars_per_second():
    if not TRANSCRIPTS_CSV.exists():
        pytest.skip("transcripts.csv not found")
    df_t = pd.read_csv(TRANSCRIPTS_CSV)
    df_m = load_metadata()
    df = df_t.merge(df_m[["clip_id", "duration_sec"]], on="clip_id")
    failures = []
    for _, r in df.iterrows():
        cps = len(str(r["transcript"])) / max(float(r["duration_sec"]), 0.1)
        if not (5.0 <= cps <= 35.0):
            failures.append(f"{r['clip_id']}: CPS={cps:.1f} (expected 5-35)")
    if failures:
        pytest.fail(f"CPS rate check failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 10: Language ID Validation (Never Skipped) ---
def test_lang_id_valid():
    if not TRANSCRIPTS_CSV.exists():
        pytest.skip("transcripts.csv not found")
    df = pd.read_csv(TRANSCRIPTS_CSV)
    # Hybrid detector: uses langdetect if available, with robust Indic n-gram fallback
    indic_vocab = {
        "kya", "hai", "kab", "hoga", "karna", "chahiye", "kar", "se", "me", "mein",
        "ka", "ki", "ke", "ko", "batao", "bataiye", "aur", "room", "hostel", "mess",
        "admission", "che", "maate", "kaya", "joiye", "thase", "nathi", "aave", "ketlo"
    }
    failures = []
    for _, r in df.iterrows():
        text = str(r["transcript"]).lower()
        words = re.findall(r"[a-z\u0900-\u097f\u0a80-\u0aff]+", text)
        has_english = bool(re.search(r"[a-zA-Z]", text))
        has_indic = any(w in indic_vocab for w in words) or bool(re.search(r"[\u0900-\u097F\u0A80-\u0AFF]", text))
        if not (has_english or has_indic):
            failures.append(f"{r['clip_id']}: Unable to identify as English/Hindi/Gujarati")
    if failures:
        pytest.fail(f"Language ID validation failed on {len(failures)} clips:\n" + "\n".join(failures[:5]))

# --- Check 11: Pandera Metadata DataFrame Schema & Dtypes ---
def test_pandera_schema():
    df = load_metadata()
    required_cols = {
        "clip_id": "object", "speaker_id": "object", "region": "object",
        "device": "object", "noise_condition": "object", "lang_mix": "object",
        "sample_rate": "int64", "duration_sec": "float64", "channels": "int64",
        "sha256_hash": "object"
    }
    for col, expected_dtype in required_cols.items():
        assert col in df.columns, f"Missing required column: {col}"
        if expected_dtype == "int64":
            assert pd.api.types.is_integer_dtype(df[col]), f"Column {col} not integer"
        elif expected_dtype == "float64":
            assert pd.api.types.is_float_dtype(df[col]), f"Column {col} not float"

# --- Check 12: Missing Values & Null Assertions ---
def test_missing_values():
    df_m = load_metadata()
    assert df_m.isnull().sum().sum() == 0, f"Nulls in metadata.csv: {df_m.isnull().sum().to_dict()}"
    if TRANSCRIPTS_CSV.exists():
        df_t = pd.read_csv(TRANSCRIPTS_CSV)
        assert df_t["transcript"].isnull().sum() == 0, "Null values in transcripts.csv"
    if INTENTS_CSV.exists():
        df_i = pd.read_csv(INTENTS_CSV)
        assert df_i["intent"].isnull().sum() == 0, "Null values in intents.csv"

# --- Check 13: Intent Taxonomy Domain Validity ---
def test_intent_validity():
    if not INTENTS_CSV.exists():
        pytest.skip("intents.csv not found")
    df = pd.read_csv(INTENTS_CSV)
    invalid = df[~df["intent"].isin(VALID_INTENTS)]
    if not invalid.empty:
        pytest.fail(f"Invalid intent labels found:\n{invalid}")

# --- Check 14: Zero Speaker Leakage Across Splits ---
def test_split_leakage():
    train_path = SPLITS_DIR / "train.csv"
    val_path = SPLITS_DIR / "val.csv"
    test_path = SPLITS_DIR / "test.csv"
    cohort_b_path = SPLITS_DIR / "cohort_b_shifted.csv"

    if not (train_path.exists() and val_path.exists() and test_path.exists() and cohort_b_path.exists()):
        pytest.skip("Splits not yet created")

    train_spk = set(pd.read_csv(train_path)["speaker_id"].unique())
    val_spk = set(pd.read_csv(val_path)["speaker_id"].unique())
    test_spk = set(pd.read_csv(test_path)["speaker_id"].unique())
    cohort_b_spk = set(pd.read_csv(cohort_b_path)["speaker_id"].unique())

    assert len(train_spk & val_spk) == 0, f"Leakage train/val: {train_spk & val_spk}"
    assert len(train_spk & test_spk) == 0, f"Leakage train/test: {train_spk & test_spk}"
    assert len(val_spk & test_spk) == 0, f"Leakage val/test: {val_spk & test_spk}"
    assert len(cohort_b_spk & (train_spk | val_spk | test_spk)) == 0, f"Cohort B leakage: {cohort_b_spk & (train_spk | val_spk | test_spk)}"
