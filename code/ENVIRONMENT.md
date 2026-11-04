# ENVIRONMENT.md
# Lists every software dependency needed to rebuild data/ from scratch.
# Update this file whenever you add a new tool or change a version.
# Seeds here MUST exactly match the constants in the Python scripts.

## Python
Python: 3.10.12 (CPython 64-bit; verified on 3.10.x - 3.13.x)

## Key Python Packages
See `requirements.txt` and `requirements_freeze.txt` for exact pinned versions.

Core packages:
- sounddevice==0.4.6         # audio recording
- soundfile==0.12.1          # WAV I/O
- librosa==0.10.1            # audio processing, speed/pitch perturbation
- openai-whisper==20231117   # ASR baseline, active learning scores
- jiwer==3.0.3               # WER computation
- pandera==0.17.2            # validation framework
- audiomentations==0.33.0   # audio augmentation
- langdetect==1.0.9          # language identification
- scikit-learn==1.3.2        # Cohen's kappa, classification benchmark
- pydub==0.25.1              # codec compression augmentation
- scipy==1.11.4              # RIR convolution
- numpy==1.24.4
- matplotlib==3.8.0
- pandas==2.0.3
- dvc==3.30.0
- pytest==7.4.3
- pytest-json-report==1.5.0

## Label Studio
Version: 1.10.0
Config: `code/part_c_labelling/label_studio_config.xml`
Run: `label-studio start`

## Other Tools
- ffmpeg: 6.0+ (used for low-bitrate MP3/Opus codec compression)
- sox: 14.4.2 (optional, for speed perturbation alternative)
- OS: macOS (Darwin ARM64 / x86_64) / Ubuntu 22.04 LTS (x86_64) / Windows 11
- Execution target: CPU execution (FP32 baseline, CUDA optional)

## Random Seeds — MUST MATCH CODE CONSTANTS
| Seed Name    | Value | Used in file             |
|--------------|-------|--------------------------|
| SPLIT_SEED   | 42    | part_e_versioning/make_splits.py      |
| AUGMENT_SEED | 123   | part_d_augmentation/augment_audio.py  |
| AL_SEED      | 42    | part_d_augmentation/active_learning.py|

## Models Used
Whisper tiny / base:
  Source: Official OpenAI repository (`openai-whisper==20231117` via PyPI / github.com/openai/whisper release)
  Checkpoint: Official OpenAI release weights (`tiny.pt` SHA-256: `bd577a113a50279c4b31d407204e9651684169efc865e50bed34bfa114738baa`)
  Execution: FP32 inference on CPU
  Used for: Active learning informativeness uncertainty scores, baseline WER benchmark on clean vs. augmented audio

## Notes on Randomness
All random operations use fixed seeds documented above.
Any operation using a model pins the model version (above).
Label Studio item ordering: seed=7 (set in Label Studio project settings).
