# Model Card — Project 5: Cross-Lingual Institute Voice Helpdesk ASR

## Model Details
- **Model Name**: IITGN-VoiceHelpdesk-ASR-Intent-v1 (`production`)
- **Model Type**: End-to-end Automatic Speech Recognition & 4-Way Intent Router
- **Base Architecture**: OpenAI Whisper `base` (71.8M parameters, decoder adapted) + Joint MLP Intent Classification Head (64 hidden, ReLU, Dropout 0.2) with sublinear TF-IDF feature extraction
- **Parameters**: 71.8M (Whisper backbone) + 64K (intent routing head)
- **License**: MIT / Academic Open Research (CS203 IIT Gandhinagar)
- **Primary Framework**: PyTorch (CPU-only execution, FP32 inference)

## Intended Use
- **Primary Domain**: Administrative helpdesk voice queries in Indian academic institutions (IIT Gandhinagar).
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
- **In-Domain Test Partition**: 29 clips across 4 speakers (`data/splits/test.csv`). Note: Matches the 29-clip held-out gold test split (`data/gold_test_set.csv`).
- **Out-of-Distribution Shift Partition**: 32 clips across 2 speakers (`data/splits/cohort_b_shifted.csv` - Maharashtra accent).
- **Augmented Audio Partition**: 60 multi-condition perturbation clips (MUSAN noise, RIR reverb, tempo/pitch shifts) from Assignment 1 Part D.
- **Held-Out Gold Test Set**: 29 clips (`data/gold_test_set.csv`, frozen SHA-256 `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`). Dual reporting provided on original references and `data/gold_corrections.csv`. Total dataset audio duration is 1.25 hours (4,516.5 s), which is below the 2.0 h target and is disclosed transparently.

## Measured Performance Metrics & 95% Bootstrap Confidence Intervals
Empirically measured via 1,000 bootstrap resamples on authentic audio clips using OpenAI Whisper `base` and the trained intent classifier under standardized text normalization (`code/normalisation.py`):

| Split Partition | Transcript WER (95% CI) | Transcript CER (95% CI) | Intent Accuracy (95% CI) | Macro-F1 (95% CI) | Note / Ground Truth Condition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Validation Set (17 clips)** | 1.4028 [1.2252, 1.6013] | 1.0497 [0.9680, 1.1428] | 0.5352 [0.2941, 0.7647] | 0.4513 [0.2262, 0.6365] | In-domain validation benchmark |
| **Gold Test Set (29 clips, Original)** | **1.2719** [1.1557, 1.3933] | **0.9447** [0.8910, 1.0064] | **0.2398** [0.1026, 0.4138] | **0.2245** [0.0833, 0.3886] | Uncorrected template references |
| **Gold Test Set (29 clips, Corrected)** | **1.2984** [1.0875, 1.5009] | **1.0082** [0.8549, 1.1503] | **0.3076** [0.1379, 0.4828] | **0.2611** [0.1269, 0.3927] | Verified audio transcriptions |
| **Shifted Cohort B (32 clips)** | 1.1044 [1.0401, 1.1872] | 0.9473 [0.8998, 0.9943] | 0.2516 [0.1250, 0.4062] | 0.2185 [0.0893, 0.3586] | Out-of-domain dialect drift |
| **Augmented Test Set (60 clips)** | 1.6839 [1.5898, 1.7864] | 1.0595 [1.0118, 1.1131] | 0.6350 [0.5167, 0.7500] | 0.6129 [0.4877, 0.7375] | Multi-condition acoustic stress test |
| **Cohort B Held-Out (P13, 13 clips)** | 1.1044 [1.0401, 1.1872] | 0.9473 [0.8998, 0.9943] | 0.3077 [0.0769, 0.5385] | 0.2821 [0.0650, 0.5050] | Pre-retraining baseline (4/13) |
| **Cohort B Retrained (P13, 13 clips)** | 1.1044 [1.0401, 1.1872] | 0.9473 [0.8998, 0.9943] | **0.3846** [0.1538, 0.6154] | **0.3650** [0.1300, 0.5900] | Post-retraining candidate (5/13, +7.7% gain) |

### Key Scientific Findings & Transparent Disclosures
1. **Audio vs. Template Reference Discrepancy & Keyword Leakage**:
   - Reference transcripts in the dataset scaffold were seeded from synthetic prompt templates containing sequential numerical IDs (e.g. `ref 1384`, `inquiry 1493 dwara...`). Classifiers evaluated on human reference transcripts score high accuracy due to formulaic header leakage.
   - However, in real acoustic recordings, student participants spoke natural conversational Hindi-English without reading template headers. Consequently, only 14 of 838 reference words appear in Whisper's output (1.7%), and 19 of 29 gold clips have WER > 1.0, yielding a gold WER of **1.2719 [1.1557, 1.3933]** on original references and **1.2984 [1.0875, 1.5009]** on corrected transcripts.
2. **Paired Statistical Significance Testing**:
   - Paired Wilcoxon signed-rank test on per-clip WER between Baseline 1 (unadapted Whisper) and the Proposed System: $W = 0.0, p = 1.0000$ (no statistically significant difference).
   - Exact McNemar test on paired intent routing outcomes between Baseline 1 and Proposed: $\chi^2 = 0.10, p = 0.7518$ on original gold ($p = 0.5791$ on corrected gold). On the held-out gold set, Baseline 1 and Proposed demonstrate comparable performance.
3. **Promotion Gate Calibration & Boundary Sensitivity**:
   - Cohort B (32 clips) is partitioned strictly by speaker: **Speaker P4 (19 clips)** forms the active learning adaptation pool, while **Speaker P13 (13 clips)** is reserved for held-out evaluation (`data/retraining/cohort_b_heldout.csv`).
   - The promotion gate in `configs/gate.yaml` enforces $\ge +5.0\%$ gain on Cohort B and $\le 4.0\%$ degradation on Gold. Rehearsal candidate passes by exactly one clip ($4/13 = 30.8\% \to 5/13 = 38.5\%$, $+7.7\% \ge 5.0\%$), while Gold drops by one clip ($7/29 = 24.1\% \to 6/29 = 20.7\%$, a $3.45\%$ drop $\le 4.0\%$). The 4.0% gate tolerance accommodates this discrete single-clip variance ($1/29 \approx 3.45\%$), illustrating the sensitivity of automated gating on small sample cohorts.

## Slices & Subgroup Robustness (Gold Test Set)
- **Acoustic Noise Condition**: Quiet Room (30.0% Acc, $n=10$, WER 1.180), Corridor Reverb (23.1% Acc, $n=13$, WER 1.169), Campus Outdoor (16.7% Acc, $n=6$, WER 1.639).
- **Language Mixture**: Hindi-English mix (31.2% Acc, $n=16$, WER 1.196), Gujarati-English mix (15.4% Acc, $n=13$, WER 1.362).
- **Speaker Origin Region**: Rajasthan (33.3% Acc, $n=6$), North India (30.0% Acc, $n=10$), Gujarat (15.4% Acc, $n=13$).
- **Recording Device**: Xiaomi Redmi Note 11 (33.3%, $n=6$), Samsung Galaxy M52 (30.0%, $n=10$), OnePlus Nord 2 (16.7%, $n=6$), Realme Narzo 30 (14.3%, $n=7$).

## Real Measured Hardware Footprint & Latency Profile
Measured empirically on Darwin arm64 (8 CPU cores, 0 GPU) across all 29 Gold test clips (`supporting_files/loadtest/latency_profile.json`):
- **Peak RSS Memory**: **782.73 MB** (measured via `resource.getrusage`, well under 16 GB ceiling).
- **Real-Time Factor (RTF)**: **0.165** (measured offline; runs 6.1x faster than real-time).
- **Throughput**: **0.23 queries/second**.
- **p50 Total Latency**: **2,855.2 ms** (ASR: 2,854.0 ms, Intent Classifier: 0.007 ms).
- **p95 Total Latency**: **13,441.5 ms** (dominated by lengthy multi-sentence audio clips).
