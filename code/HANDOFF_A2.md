# HANDOFF_A2.md - Written at a1-final freeze.
# Assignment 2 must start from this exact state.
# Any number in A2 that uses these files must reference this document.

# Handoff Document — Assignment 2
# CS203 Project 5: Cross-Lingual Institute Voice Helpdesk ASR

## a1-final Tag
Git commit hash: a1-final (tagged at submission freeze)
GitHub URL: https://github.com/vipulSP2108/STTAI_Project.git

## Frozen Partition & Gold Artifacts
All manifests below are cryptographically frozen at commit `a1-final`. All checksums are SHA-256.

| File Path | SHA-256 Checksum | Clips | Speakers | Partition Role & Constraints |
|-----------|------------------|-------|----------|------------------------------|
| `data/gold_test_set.csv` | `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9` | 29 | 4 (P15, P17, P18, P19) | **Held-out Gold Test Set**. Sub-sampled strictly from Test split. **Never use for training or hyperparameter tuning.** |
| `data/splits/train.csv` | `f75a7a0779ca54fcd532904aa17586d24b1c6f876549bf70f89bc2e929cc3122` | 171 | 10 (P1, P2, P3, P5, P6, P7, P8, P9, P11, P14) | Model training partition (70% speaker-disjoint) |
| `data/splits/val.csv` | `b544e5aa091b093f9ca469b69e0fcca7170ba1fd233270567f742406a2f21dfa` | 17 | 3 (P10, P12, P16) | Validation and early stopping tuning set (15% speaker-disjoint) |
| `data/splits/test.csv` | `be9b04ed9b40e1f99265d1a36f0cb9b5671837dae27882f41aeb2b72403dd971` | 29 | 4 (P15, P17, P18, P19) | In-domain benchmark test set (15% speaker-disjoint) |
| `data/splits/cohort_b_shifted.csv` | `0d780ed6b5e4456590bdaa115f1815594d185b1e6372fb607c6afd78f285a47f` | 32 | 2 (P4, P13) | Out-of-domain acoustic & dialect drift benchmark (Maharashtra / fast speech cohort) |

**Total Canonical Dataset**: 249 clips, 19 speakers, 0 speaker overlap between partitions, 0 split leakage.

## Label Taxonomy & Schema
- **transcript**: Verbatim code-mixed Hindi/Gujarati/English speech transcription in Latin script (e.g., *"iit gandhinagar mtech admissions ke liye gate cut off score kya hai"*).
- **intent**: Exactly 4 mutually exclusive institutional categories:
  - `admissions`: Degree admissions, eligibility, cutoff ranks, entrance exams.
  - `hostel_mess`: Hostel room allotment, dining mess rebates, mess billing, warden requests.
  - `it_support`: Institute email/webmail, Wi-Fi configuration, VPN, ERP portal logins.
  - `student_services`: Scholarships, academic transcripts, bonafide certificates, semester registration.

## Split Generation Methodology
- **Unit of Partitioning**: Participant / speaker ID (strictly prevented clip-level or row-level leakage).
- **Random Seed**: `SPLIT_SEED = 42` (fixed across all split scripts).
- **Cohort B Isolation**: Held out prior to running random partition on remaining 17 speakers.
- **Gold Set Immutability**: `data/gold_test_set.csv` has 0 overlap with Train (`0 / 171`) and 0 overlap with Val (`0 / 17`). In Assignment 2, this file serves as the untuned final benchmark test bed.
