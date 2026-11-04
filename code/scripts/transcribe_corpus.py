import os
import glob
import json
import time
import re
import pandas as pd
import whisper

AUDIO_DIR = "data/raw/audio"
OUTPUT_JSON = "supporting_files/whisper_raw_transcripts.json"

def clean_transcript(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def infer_intent(text):
    t = text.lower()
    # Keyword-based domain assignment with clear semantic rules
    it_keywords = ["wifi", "eduroam", "ldap", "password", "vpn", "hpc", "cluster", "login", "server", "ip address", "lan", "portal", "internet", "network", "system", "account access", "storage", "quota", "google workspace"]
    mess_keywords = ["mess", "hostel", "room", "allotment", "rebate", "warden", "geyser", "food", "dining", "canteen", "menu", "cleaning", "washroom", "maintenance", "ac room", "block"]
    adm_keywords = ["admission", "mtech", "btech", "phd", "counselling", "cutoff", "application", "form", "entrance", "written test", "interview", "gate", "jam", "documents", "eligibility", "foreign national", "fellowship"]
    serv_keywords = ["fee", "tuition", "bonafide", "certificate", "id card", "library", "sports", "gym", "medical", "insurance", "health centre", "ambulance", "attestation", "scholarship", "dean academic", "transcript", "convocation", "grade sheet", "rebate refund"]

    scores = {
        "it_support": sum(1 for k in it_keywords if k in t),
        "hostel_mess": sum(1 for k in mess_keywords if k in t),
        "admissions": sum(1 for k in adm_keywords if k in t),
        "student_services": sum(1 for k in serv_keywords if k in t)
    }
    
    # Intent tie-breaking
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    
    # Context-based default fallback
    if any(w in t for w in ["course", "branch", "syllabus", "degree"]):
        return "admissions"
    if any(w in t for w in ["book", "doctor", "medicine", "money", "receipt"]):
        return "student_services"
    return "student_services"

def main():
    print("Loading whisper tiny model...")
    model = whisper.load_model("tiny")
    wavs = sorted(glob.glob(os.path.join(AUDIO_DIR, "*.wav")))
    print(f"Transcribing {len(wavs)} audio clips...")

    results = {}
    t0 = time.time()
    for i, w in enumerate(wavs):
        cid = os.path.splitext(os.path.basename(w))[0]
        try:
            res = model.transcribe(w)
            raw_text = clean_transcript(res.get("text", ""))
            intent = infer_intent(raw_text)
            results[cid] = {
                "clip_id": cid,
                "raw_whisper": raw_text,
                "inferred_intent": intent
            }
        except Exception as e:
            print(f"Error on {cid}: {e}")
            results[cid] = {"clip_id": cid, "raw_whisper": "", "inferred_intent": "student_services"}

        if (i + 1) % 25 == 0 or (i + 1) == len(wavs):
            elapsed = time.time() - t0
            print(f"[{i+1}/{len(wavs)}] Processed in {elapsed:.1f}s ({elapsed/(i+1):.2f}s/clip)")

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Transcriptions saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
