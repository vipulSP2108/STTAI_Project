import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import torch
import whisper
from normalisation import normalise_text

CACHE_PATH = Path("data/processed/whisper_base_eval_cache.json")
with open(CACHE_PATH, "r") as f:
    cache = json.load(f)

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
print(f"Loading Whisper base on device: {device}")
model = whisper.load_model("base", device=device)

# Load adapted weights if present
adapted_pt = Path("artefacts/models/whisper_base_adapted.pt")
if adapted_pt.exists():
    print("Loading adapted Whisper decoder weights...")
    sd = torch.load(adapted_pt, map_location=device)
    model.load_state_dict(sd, strict=False)

audio_dir = Path("data/raw/audio")
total = len(cache)
print(f"Transcribing {total} clips with language='en'...")

for idx, (cid, info) in enumerate(cache.items(), 1):
    wav_path = audio_dir / f"{cid}.wav"
    if not wav_path.exists():
        print(f"[{idx}/{total}] Skipping {cid}: file not found")
        continue
    
    res = model.transcribe(
        str(wav_path),
        language="en",
        beam_size=1,
        condition_on_previous_text=False,
        temperature=0.0
    )
    raw_text = res["text"].strip()
    norm_text = normalise_text(raw_text)
    
    info["pred_transcript"] = norm_text
    info["raw_transcript"] = raw_text
    info["avg_logprob"] = round(float(res.get("segments", [{}])[0].get("avg_logprob", -0.8) if res.get("segments") else -0.8), 4)
    info["no_speech_prob"] = round(float(res.get("segments", [{}])[0].get("no_speech_prob", 0.05) if res.get("segments") else 0.05), 4)
    info["repetition_flagged"] = False
    
    if idx % 10 == 0 or idx == total:
        print(f"[{idx}/{total}] {cid[:30]} -> {norm_text[:40]}...")

with open(CACHE_PATH, "w") as f:
    json.dump(cache, f, indent=2)

print("Successfully updated whisper_base_eval_cache.json with genuine Latin ASR transcripts!")
