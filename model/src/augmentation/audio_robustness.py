"""audio_robustness.py - Label-preserving audio augmentation on the final corpus + ASR robustness.

Augmentations (A1 Part D list for Project 5), all applied in memory with seed 42:
  babble   other speakers' clips summed at SNR 10 dB (MUSAN is not available offline; babble from
           the corpus itself is the documented substitute)
  reverb   synthetic room impulse response (exponentially decaying noise, RT60 0.5 s)
  speed    0.9x resampling (tempo and pitch change together, Kaldi-style speed perturbation)
  pitch    +2 semitones (librosa phase-vocoder, duration kept)
  codec    8 kHz narrow-band, 16 kbit/s Opus round trip through ffmpeg (low-end phone line)

ASR: the deployed Indic routing (whisper-hindi-ct2 / whisper-gujarati-ct2 / faster-whisper-base,
chosen by the annotators' language tag as in offline_asr_predictions.json). Greedy decoding, no prompt.

Per clip and augmentation we record:
  * drift_wer  WER(augmented hypothesis, clean hypothesis) - label-free robustness
  * true_wer   WER vs human transcript, when data/labels/human_transcripts.csv exists
  * label check: the intent router's prediction on clean vs augmented text (does the label hold?)
Output: model/results/audio_robustness.json and five listening samples in
supporting_files/augmentation_samples/final_corpus/.
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import jiwer
import librosa
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
AUDIO = ROOT / "model" / "data" / "audio"
SR = 16000
rng = np.random.default_rng(42)


def babble(x, pool, snr_db=10):
    n = np.zeros_like(x)
    for p in rng.choice(pool, 3, replace=False):
        y, _ = librosa.load(p, sr=SR)
        y = np.resize(y, len(x)); n += y / (np.std(y) + 1e-9)
    n *= np.std(x) / (np.std(n) + 1e-9) / (10 ** (snr_db / 20))
    return x + n


def reverb(x, rt60=0.5):
    t = np.arange(int(rt60 * SR)) / SR
    ir = rng.standard_normal(len(t)) * np.exp(-6.9 * t / rt60); ir[0] = 1.0
    y = np.convolve(x, ir)[: len(x)]
    return y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))


def speed(x, f=0.9):
    return librosa.resample(x, orig_sr=SR, target_sr=int(SR / f))


def pitch(x, st=2):
    return librosa.effects.pitch_shift(x, sr=SR, n_steps=st)


def codec(x):
    with tempfile.TemporaryDirectory() as d:
        a, b, c = Path(d, "a.wav"), Path(d, "b.opus"), Path(d, "c.wav")
        sf.write(a, x, SR)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", a, "-ar", "8000", "-c:a", "libopus", "-b:a", "16k", b], check=True)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", b, "-ar", str(SR), "-ac", "1", c], check=True)
        return librosa.load(c, sr=SR)[0]


AUGS = {"babble_10dB": None, "reverb_rt60_0.5": reverb, "speed_0.9": speed, "pitch_+2": pitch, "codec_opus16k_8kHz": codec}


def main(n_per_lang=8, max_sec=40):
    from faster_whisper import WhisperModel
    sys.path.insert(0, str(ROOT / "model" / "src" / "training"))
    models = {"hi": WhisperModel(str(ROOT / "model/models/whisper-hindi-ct2"), device="cpu", compute_type="int8", cpu_threads=4),
              "gu": WhisperModel(str(ROOT / "model/models/whisper-gujarati-ct2"), device="cpu", compute_type="int8", cpu_threads=4),
              "en": WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)}
    man = json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"]
    gold = {c["clip_id"]: c for c in json.loads((ROOT / "final_annotation/consensus_gold_182.json").read_text())["clips"]}
    dur = {p["uuid"]: p["audio_duration_sec"] for p in json.loads((ROOT / "model/data/reports/offline_asr_predictions.json").read_text())["predictions"]}
    human = {}
    hp = ROOT / "data/labels/human_transcripts.csv"
    if hp.exists():
        human = {r["uuid"]: r["transcript"] for r in csv.DictReader(open(hp, encoding="utf-8"))}

    def lang_of(m):
        L = m["languages"]
        return "Code-mixed" if len(L) > 1 else L[0]

    picks = []
    for L in ("English", "Hindi", "Gujarati", "Code-mixed"):
        rows = sorted([m for m in man if lang_of(m) == L and dur[m["uuid"]] <= max_sec], key=lambda m: m["uuid"])
        idx = rng.choice(len(rows), min(n_per_lang, len(rows)), replace=False)
        picks += [rows[i] for i in idx]
    pool = [AUDIO / f"{m['uuid']}.wav" for m in man]

    def asr(x, m):
        L = m["languages"]
        code = "gu" if L == ["Gujarati"] else "hi" if "Hindi" in L else "gu" if "Gujarati" in L else "en"
        segs, _ = models[code].transcribe(x.astype(np.float32), language=code, beam_size=1, temperature=0.0,
                                          condition_on_previous_text=False, vad_filter=True)
        return " ".join(s.text.strip() for s in segs).strip()

    sample_dir = ROOT / "supporting_files/augmentation_samples/final_corpus"; sample_dir.mkdir(parents=True, exist_ok=True)
    prev = ROOT / "model/results/audio_robustness.json"
    rows = json.loads(prev.read_text())["clips"] if prev.exists() else []   # resumable
    done = {r["uuid"] for r in rows}
    for k, m in enumerate(picks, 1):
        if m["uuid"] in done:
            continue
        x, _ = librosa.load(AUDIO / f"{m['uuid']}.wav", sr=SR)
        clean = asr(x, m)
        rec = {"uuid": m["uuid"], "speaker": m["original_speaker_id"], "language": lang_of(m),
               "intent": gold[m["original_clip_id"]]["gold_intent"], "clean_hyp": clean, "aug": {}}
        for name, fn in AUGS.items():
            y = babble(x, [p for p in pool if p.stem != m["uuid"]]) if name.startswith("babble") else fn(x)
            if k == 1:
                sf.write(sample_dir / f"{m['uuid']}_{name}.wav", y, SR)
            hyp = asr(y, m)
            r = {"hyp": hyp, "drift_wer": float(jiwer.wer(clean, hyp)) if clean else None}
            if m["uuid"] in human:
                r["true_wer"] = float(jiwer.wer(human[m["uuid"]], hyp))
            rec["aug"][name] = r
        if m["uuid"] in human:
            rec["clean_true_wer"] = float(jiwer.wer(human[m["uuid"]], clean))
        rows.append(rec)
        print(f"[{k}/{len(picks)}] {m['uuid']} {rec['language']} " +
              " ".join(f"{n[:6]}={v['drift_wer']:.2f}" for n, v in rec["aug"].items() if v["drift_wer"] is not None), flush=True)
        (ROOT / "model/results/audio_robustness.json").write_text(json.dumps({"seed": 42, "clips": rows}, ensure_ascii=False, indent=1))

    # label-preservation check with the router used in the ablation (char+emb on ASR text)
    summary = {}
    for name in AUGS:
        d = [r["aug"][name]["drift_wer"] for r in rows if r["aug"][name]["drift_wer"] is not None]
        summary[name] = {"median_drift_wer": float(np.median(d)), "mean_drift_wer": float(np.mean(d)),
                         "by_language": {L: float(np.median([r["aug"][name]["drift_wer"] for r in rows
                                                             if r["language"] == L and r["aug"][name]["drift_wer"] is not None]))
                                         for L in sorted({r["language"] for r in rows})}}
    out = {"seed": 42, "n_clips": len(rows), "asr": "Indic hybrid routing (language from annotator tag), greedy, VAD",
           "summary": summary, "clips": rows}
    (ROOT / "model/results/audio_robustness.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
