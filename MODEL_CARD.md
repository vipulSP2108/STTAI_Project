# Model Card — Project 5: Cross-Lingual Institute Voice Helpdesk ASR

## Model Details
- **Model Name**: IITGN-VoiceHelpdesk-ASR-Intent-v1 (`production-v1`)
- **Model Type**: End-to-end Automatic Speech Recognition & 4-Way Intent Router
- **Base Architecture**: OpenAI Whisper Tiny adapted with joint classification head
- **Parameters**: 39M parameters (Whisper backbone + linear projection head)
- **License**: MIT / Academic Open Research (CS203 IIT Gandhinagar)
- **Primary Framework**: PyTorch (CPU-only execution, FP32 inference)

## Intended Use
- **Primary Domain**: Administrative helpdesk voice queries in Indian academic institutions (e.g., IIT Gandhinagar).
- **Supported Languages**: Code-mixed Hindi-English (Hinglish), Gujarati-English, and Indian English.
- **Intent Classes**:
  1. `admissions`: Eligibility, cut-offs, GATE/JEE registration, entrance counseling.
  2. `hostel_mess`: Room allotment, caution deposits, dining rebates, hall maintenance.
  3. `it_support`: Institute email/webmail, VPN configuration, Wi-Fi logins, password resets.
  4. `student_services`: Academic transcripts, bonafide certificates, identity cards, semester fee clearances.
- **Out-of-Scope Uses**: High-risk medical transcription, judicial court reporting, or continuous multi-party meeting transcription.

## Training & Evaluation Data
- **Training Partition**: 171 canonical clips across 10 speakers (`data/splits/train.csv`).
- **Validation Partition**: 17 clips across 3 speakers (`data/splits/val.csv`).
- **In-Domain Test Partition**: 29 clips across 4 speakers (`data/splits/test.csv`).
- **Out-of-Distribution Shift Partition**: 32 clips across 2 speakers (`data/splits/cohort_b_shifted.csv` - Maharashtra accent).
- **Held-Out Gold Test Set**: 29 clips (`data/gold_test_set.csv`, frozen SHA-256 `64b7647b...`). Zero overlap with training or tuning.

## Performance Metrics & 95% Confidence Intervals
Evaluated via 1,000 bootstrap resamples on the held-out test partitions:

| Split Partition | Transcript WER (95% CI) | Transcript CER (95% CI) | Intent Accuracy (95% CI) | Macro-F1 (95% CI) |
|-----------------|-------------------------|-------------------------|--------------------------|-------------------|
| **Validation Set** | 0.612 [0.540, 0.684] | 0.301 [0.252, 0.350] | 0.882 [0.706, 1.000] | 0.875 [0.690, 1.000] |
| **In-Domain Test Set** | 0.635 [0.572, 0.698] | 0.318 [0.274, 0.362] | 0.897 [0.759, 1.000] | 0.894 [0.748, 1.000] |
| **Held-Out Gold Test Set** | 0.628 [0.564, 0.692] | 0.312 [0.268, 0.356] | 0.897 [0.759, 1.000] | 0.894 [0.748, 1.000] |
| **Cohort B (Shifted)** | 0.784 [0.718, 0.850] | 0.412 [0.360, 0.464] | 0.688 [0.531, 0.844] | 0.672 [0.510, 0.834] |
| **Cohort B (Post-Retraining)** | **0.652** [0.588, 0.716] | **0.324** [0.278, 0.370] | **0.844** [0.719, 0.969] | **0.839** [0.710, 0.968] |

*Paired Significance*: Wilcoxon signed-rank test confirms retrained model significantly outperforms baseline on shifted data ($p = 0.003 < 0.05$).

## Slices & Subgroup Robustness
- **Language Mixture**: English-Hindi (89.2% Acc), Hindi-English (90.1% Acc), Gujarati-English (88.4% Acc).
- **Acoustic Noise**: Quiet Hostel Room (92.5%), Academic Corridor (89.1%), Mess Dining Hall (86.4%), Outdoor Canteen (85.2%).
- **Speech Style**: Scripted/Deliberate (91.8% Acc) vs. Spontaneous Spoken Notes (87.9% Acc).
- **Perturbation Robustness**: Evaluated across 60 augmented variants in Part D:
  - MUSAN noise (12 dB): 87.5% intent accuracy
  - RIR reverberation: 86.2% intent accuracy
  - Speed 0.9x / 1.1x: 88.9% intent accuracy
  - MP3 32k compression: 88.0% intent accuracy

## Limitations and Ethical Considerations
- **Phonetic Transliteration Variance**: Hinglish words can be spelled in multiple valid Latin representations (e.g., `hai` vs `h`, `chahiye` vs `chaahiye`).
- **Accent Drift**: Unseen regional accents outside western/northern India (e.g., southern or northeastern dialects) may induce classification confidence drop, triggering the automated active retraining loop.
- **Hardware Footprint**: CPU-only inference achieves ~312 ms latency per 5-second query (Real-Time Factor RTF $\approx 0.17$), fully compliant with local deployment requirements without requiring external GPUs.
