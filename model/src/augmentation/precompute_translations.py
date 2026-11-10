#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""precompute_translations.py - High-Throughput Multithreaded Translation Engine.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)
"""

import sys
import json
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from model.src.augmentation.tri_directional_translator import translate_cross_lingual, save_cache, _CACHE

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEXT_DIR = BASE_DIR / "model" / "data" / "text"

text_files = sorted(list(TEXT_DIR.glob("*.txt")))
print(f"Precomputing cross-lingual translations for {len(text_files)} original text files with 8 threads...")

lock = threading.Lock()
start_t = time.time()
processed_cnt = 0

def process_file(p: Path):
    lines = p.read_text().splitlines()
    transcript = ""
    for line in lines:
        if line.startswith("Transcript:"):
            transcript = line.split(":", 1)[1].strip()
            break
    
    if not transcript or len(transcript.split()) < 3:
        return (p.name, 0)

    try:
        results = translate_cross_lingual(transcript)
        return (p.name, len(results))
    except Exception as e:
        return (p.name, -1)

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(process_file, p): p for p in text_files}
    for fut in as_completed(futures):
        p_name, n_res = fut.result()
        with lock:
            processed_cnt += 1
            if processed_cnt % 10 == 0 or processed_cnt == len(text_files):
                save_cache()
                elapsed = time.time() - start_t
                print(f"[{processed_cnt}/{len(text_files)}] Done: {p_name} | Cached pairs: {len(_CACHE)} | Elapsed: {elapsed:.1f}s")

save_cache()
print(f"ALL COMPLETE in {time.time() - start_t:.1f}s! Total cached translations: {len(_CACHE)}")
