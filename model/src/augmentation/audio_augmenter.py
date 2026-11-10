#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""audio_augmenter.py - Acoustic Audio Perturbation Engine.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Speed perturbation (0.9x and 1.1x tempo).
2. Pitch shifting (+/- 2 semitones).
3. Additive noise injection (simulating campus / canteen ambient sound at 15 dB SNR).
"""

import math
import numpy as np
import scipy.io.wavfile as wavfile
from scipy import signal
from pathlib import Path
from typing import Tuple

def load_wav(path: str) -> Tuple[int, np.ndarray]:
    sr, data = wavfile.read(path)
    # Convert to float32 normalized between -1.0 and 1.0
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    if len(data.shape) > 1:
        data = data.mean(axis=1) # Mono
    return sr, data

def save_wav(path: str, sr: int, data: np.ndarray):
    # Clip and convert back to int16
    data = np.clip(data, -1.0, 1.0)
    int_data = (data * 32767.0).astype(np.int16)
    wavfile.write(path, sr, int_data)

def perturb_speed(data: np.ndarray, speed_factor: float = 1.1) -> np.ndarray:
    """Changes speed by resampling."""
    num_samples = int(len(data) / speed_factor)
    return signal.resample(data, num_samples)

def perturb_pitch(data: np.ndarray, semitones: float = 2.0) -> np.ndarray:
    """Approximate pitch shift via time-stretch followed by resampling."""
    factor = 2.0 ** (semitones / 12.0)
    resampled = signal.resample(data, int(len(data) / factor))
    # Interpolate back to original length
    x_old = np.linspace(0, 1, len(resampled))
    x_new = np.linspace(0, 1, len(data))
    return np.interp(x_new, x_old, resampled)

def add_ambient_noise(data: np.ndarray, snr_db: float = 15.0, seed: int = 42) -> np.ndarray:
    """Adds pink/Gaussian noise at specified SNR to simulate cafeteria noise."""
    rng = np.random.RandomState(seed)
    signal_power = np.mean(data ** 2)
    if signal_power == 0:
        return data
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise = rng.normal(0, np.sqrt(noise_power), len(data))
    return data + noise.astype(np.float32)

def augment_audio_file(input_path: str, output_path: str, aug_type: str = "speed_fast", seed: int = 42):
    """Augments single WAV file and saves output."""
    sr, data = load_wav(input_path)
    if aug_type == "speed_fast":
        aug_data = perturb_speed(data, 1.1)
    elif aug_type == "speed_slow":
        aug_data = perturb_speed(data, 0.9)
    elif aug_type == "pitch_up":
        aug_data = perturb_pitch(data, 2.0)
    elif aug_type == "pitch_down":
        aug_data = perturb_pitch(data, -2.0)
    elif aug_type == "noise_canteen":
        aug_data = add_ambient_noise(data, snr_db=15.0, seed=seed)
    else:
        aug_data = data
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    save_wav(output_path, sr, aug_data)

if __name__ == "__main__":
    import sys
    test_wav = "model/data/audio/016b6287.wav"
    if Path(test_wav).exists():
        augment_audio_file(test_wav, "model/data/augmented/audio_perturbed/test_speed.wav", "speed_fast")
        print("Acoustic perturbation successful.")
