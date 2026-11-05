# ============================================================
# Assignment 2 - Part D: Hardware Performance & Latency Benchmark
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Measures real empirical latency, throughput, RTF, and memory consumption
# on local CPU hardware according to Guide Section 3.4.5 and 5.7.
# Outputs to supporting_files/loadtest/latency_profile.json
# ============================================================

import json
import os
import platform
import resource
import time
import wave
import numpy as np
import pandas as pd
import torch
import pickle
from pathlib import Path

AUDIO_DIR = Path("data/raw/audio")
GOLD_CSV = Path("data/gold_test_set.csv")
MODELS_DIR = Path("artefacts/models")
OUT_DIR = Path("supporting_files/loadtest")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "latency_profile.json"


def get_system_hardware_info():
    """Gathers detailed hardware specifications."""
    info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "torch_threads": torch.get_num_threads(),
    }
    return info


def benchmark_pipeline(n_iterations=29):
    print("=== Commencing Pipeline Latency & Memory Benchmark ===")
    hw_info = get_system_hardware_info()
    print(f"Hardware: {hw_info['os']} {hw_info['machine']} ({hw_info['cpu_count']} cores)")

    import whisper
    print("Loading Whisper base model on CPU...")
    t0_load = time.time()
    whisper_model = whisper.load_model("base", device="cpu")
    whisper_load_sec = round(time.time() - t0_load, 3)

    # Load vectorizer and intent head
    vec_path = MODELS_DIR / "proposed_vectorizer.pkl"
    with open(vec_path, "rb") as f:
        vec = pickle.load(f)

    head_path = MODELS_DIR / "production_v1_head.pt"
    in_dim = len(vec.get_feature_names_out())
    import torch.nn as nn
    head = nn.Sequential(
        nn.Linear(in_dim, 64),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(64, 4)
    )
    if head_path.exists():
        sd = torch.load(head_path, weights_only=True)
        head.load_state_dict({k.replace("net.", ""): v for k, v in sd.items()})
    head.eval()

    # Gather audio clips for test
    df_gold = pd.read_csv(GOLD_CSV)
    clips = [AUDIO_DIR / f"{cid}.wav" for cid in df_gold["clip_id"] if (AUDIO_DIR / f"{cid}.wav").exists()]
    if len(clips) < n_iterations:
        all_wavs = list(AUDIO_DIR.glob("*.wav"))
        clips = (clips + all_wavs)[:n_iterations]

    print(f"Benchmarking {len(clips)} audio queries sequentially...")

    latencies_asr_ms = []
    latencies_router_ms = []
    latencies_total_ms = []
    audio_durations_sec = []

    for idx, wav_path in enumerate(clips):
        # Audio duration
        with wave.open(str(wav_path), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        audio_durations_sec.append(dur)

        # 1. ASR stage
        t0 = time.perf_counter()
        res = whisper_model.transcribe(
            str(wav_path),
            fp16=False,
            condition_on_previous_text=False,
            temperature=0.0,
            compression_ratio_threshold=2.0,
            no_speech_threshold=0.6,
            beam_size=1
        )
        t1 = time.perf_counter()
        asr_ms = (t1 - t0) * 1000.0

        # 2. Router stage
        tx = res.get("text", "").strip()
        X = vec.transform([tx]).toarray()
        t2 = time.perf_counter()
        with torch.no_grad():
            logits = head(torch.tensor(X, dtype=torch.float32))
            _ = torch.softmax(logits, dim=1).numpy()
        t3 = time.perf_counter()
        router_ms = (t3 - t2) * 1000.0

        total_ms = (t3 - t0) * 1000.0

        latencies_asr_ms.append(asr_ms)
        latencies_router_ms.append(router_ms)
        latencies_total_ms.append(total_ms)

        if (idx + 1) % 5 == 0 or idx == len(clips) - 1:
            print(f"  [{idx+1}/{len(clips)}] Latency: {total_ms:.1f}ms (ASR: {asr_ms:.1f}ms, Router: {router_ms:.2f}ms) | Audio: {dur:.1f}s")

    # Peak memory
    # Note: On macOS, ru_maxrss is in bytes; on Linux, in KB.
    usage = resource.getrusage(resource.RUSAGE_SELF)
    maxrss = usage.ru_maxrss
    if platform.system() == "Darwin":
        max_rss_mb = round(maxrss / (1024.0 * 1024.0), 2)
    else:
        max_rss_mb = round(maxrss / 1024.0, 2)

    total_proc_sec = sum(latencies_total_ms) / 1000.0
    total_audio_sec = sum(audio_durations_sec)
    rtf = round(total_proc_sec / total_audio_sec, 3) if total_audio_sec > 0 else 0.0
    throughput_qps = round(len(clips) / total_proc_sec, 2) if total_proc_sec > 0 else 0.0

    profile = {
        "hardware": hw_info,
        "model_loading_sec": whisper_load_sec,
        "sample_count": len(clips),
        "total_audio_duration_sec": round(total_audio_sec, 1),
        "total_processing_time_sec": round(total_proc_sec, 2),
        "real_time_factor_rtf": rtf,
        "throughput_queries_per_sec": throughput_qps,
        "peak_memory_mb": max_rss_mb,
        "latency_stats_ms": {
            "p50_total_ms": round(float(np.percentile(latencies_total_ms, 50)), 2),
            "p90_total_ms": round(float(np.percentile(latencies_total_ms, 90)), 2),
            "p95_total_ms": round(float(np.percentile(latencies_total_ms, 95)), 2),
            "mean_total_ms": round(float(np.mean(latencies_total_ms)), 2),
            "p50_asr_ms": round(float(np.percentile(latencies_asr_ms, 50)), 2),
            "p95_asr_ms": round(float(np.percentile(latencies_asr_ms, 95)), 2),
            "p50_router_ms": round(float(np.percentile(latencies_router_ms, 50)), 4),
            "p95_router_ms": round(float(np.percentile(latencies_router_ms, 95)), 4),
        }
    }

    with open(OUT_JSON, "w") as f:
        json.dump(profile, f, indent=2)

    print("\n=== Benchmark Summary ===")
    print(f"Total Clips Benchmarked: {len(clips)}")
    print(f"Peak Memory:            {max_rss_mb} MB")
    print(f"Real-Time Factor (RTF): {rtf} (< 1.0 = Faster than Real-Time)")
    print(f"Throughput:             {throughput_qps} requests/sec")
    print(f"p50 Latency:            {profile['latency_stats_ms']['p50_total_ms']} ms")
    print(f"p95 Latency:            {profile['latency_stats_ms']['p95_total_ms']} ms")
    print(f"Router p50 Latency:     {profile['latency_stats_ms']['p50_router_ms']} ms")
    print(f"Saved profile to:       {OUT_JSON}")
    return profile


if __name__ == "__main__":
    benchmark_pipeline(n_iterations=29)
