# corruption_test.py - Proves validation suite catches corrupted data.
# CS203 Assignment 1 - Part B
#
# Creates 3 corrupted audio variants and verifies the suite detects each.
# Required evidence for Part B grading.
#
# Usage: python corruption_test.py

import wave, struct, tempfile, shutil, numpy as np
from pathlib import Path

AUDIO_DIR = Path("data/raw/audio")
LOG_FILE = Path("supporting_files/validation_outputs/corruption_test.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def get_first_wav():
    wavs = list(AUDIO_DIR.glob("*.wav"))
    if wavs:
        return wavs[0]
    aug_wavs = list(Path("data/processed/augmented").glob("**/*.wav"))
    if aug_wavs:
        return aug_wavs[0]
    tmp_path = Path("temp_clean_ref.wav")
    sr = 16000
    t = np.linspace(0, 2.0, 2 * sr, endpoint=False)
    sig = (np.sin(2 * np.pi * 440 * t) * 0.5 * 32767).astype(np.int16)
    write_wav(tmp_path, sr, 1, 2, sig.tobytes())
    return tmp_path

def read_wav(path):
    with wave.open(str(path),"r") as w:
        sr=w.getframerate(); ch=w.getnchannels(); sw=w.getsampwidth()
        raw=w.readframes(w.getnframes())
    return sr, ch, sw, raw

def write_wav(path, sr, ch, sw, raw):
    with wave.open(str(path),"w") as w:
        w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(sr)
        w.writeframes(raw)

def check_sample_rate(path):
    with wave.open(str(path),"r") as w: return w.getframerate() == 16000

def check_no_clipping(path):
    _, _, sw, raw = read_wav(path)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)/32768.0
    return float(np.max(np.abs(audio))) < 0.99

def check_silence_ratio(path):
    _, _, sw, raw = read_wav(path)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)/32768.0
    return float(np.mean(np.abs(audio) < 0.01)) < 0.5

def main():
    src = get_first_wav()
    sr, ch, sw, raw = read_wav(src)
    lines = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Corruption A: wrong sample rate (8000 Hz)
        path_a = Path(tmpdir)/"corrupt_a.wav"
        write_wav(path_a, 8000, ch, sw, raw)  # Change only header SR
        passed = check_sample_rate(path_a)
        result_a = "FAILED as expected (PASS)" if not passed else "PASSED - BUG: corruption NOT detected"
        line_a = f"Corruption A (wrong sample rate 8kHz): {result_a}"
        print(f"[PASS] {line_a}"); lines.append(line_a)
        assert not passed, "Bug: corruption A was not caught by check_sample_rate"

        # Corruption B: clipping (amplitude = 1.0)
        path_b = Path(tmpdir)/"corrupt_b.wav"
        clipped = np.ones(len(raw)//2, dtype=np.int16) * 32767  # Max value = clipping
        write_wav(path_b, sr, ch, sw, clipped.tobytes())
        passed = check_no_clipping(path_b)
        result_b = "FAILED as expected (PASS)" if not passed else "PASSED - BUG: corruption NOT detected"
        line_b = f"Corruption B (clipped audio): {result_b}"
        print(f"[PASS] {line_b}"); lines.append(line_b)
        assert not passed, "Bug: corruption B was not caught by check_no_clipping"

        # Corruption C: full silence
        path_c = Path(tmpdir)/"corrupt_c.wav"
        n = len(raw)//sw
        silence = np.zeros(n, dtype=np.int16)
        write_wav(path_c, sr, ch, sw, silence.tobytes())
        passed = check_silence_ratio(path_c)
        result_c = "FAILED as expected (PASS)" if not passed else "PASSED - BUG: corruption NOT detected"
        line_c = f"Corruption C (full silence): {result_c}"
        print(f"[PASS] {line_c}"); lines.append(line_c)
        assert not passed, "Bug: corruption C was not caught by check_silence_ratio"

    LOG_FILE.write_text("\n".join(lines))
    print(f"\nAll 3 corruptions detected correctly. Log: {LOG_FILE}")

if __name__ == "__main__": main()
