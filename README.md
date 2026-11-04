# Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining

**CS203: Software Tools and Techniques in AI — Assignment 1 (Project 5)**  
Department of Computer Science and Engineering, Indian Institute of Technology Gandhinagar  
**Repository**: [https://github.com/vipulSP2108/STTAI_Project.git](https://github.com/vipulSP2108/STTAI_Project.git)

---

## Team & Equal Contribution Statement

| Team Member | Roll Number | Academic Program | Role & Contribution |
| :--- | :--- | :--- | :--- |
| **Rajdeep Vraj** | 24110260 | B.Tech CSE and AI, IIT Gandhinagar | 33.3% Equal Technical Contribution |
| **Vipul Sunil Patil** | 24110381 | B.Tech CSE and CE, IIT Gandhinagar | 33.3% Equal Technical Contribution |
| **Satvik Sharma** | 24110300 | B.Tech CSE, IIT Gandhinagar | 33.3% Equal Technical Contribution |

> **Statement of Equal Contribution (1/3rd each):**  
> All three team members (**Rajdeep Vraj**, **Vipul Sunil Patil**, and **Satvik Sharma**) contributed equally (33.3% each) across all phases of this project. Responsibilities were collaboratively planned, shared, and executed in equal measure, including:
> - Audio data collection, multi-format container parsing, and audio segmentation (`Records/` & `1 clip 1 tar`).
> - Automated 14-check validation test suite using `pytest` and `pandera`, plus 12-case adversarial corruption tests.
> - Label Studio double-annotation protocol, guideline calibration, and inter-annotator agreement computation (WER & Cohen's $\kappa$).
> - Audio perturbation augmentations (speed, pitch, MUSAN noise, RIR reverb, MP3 codec) and active learning 5-fold cross-validation simulation.
> - Speaker-disjoint train/val/test splits, Cohort B demographic distribution shift creation, and DVC/Git release management.
> - Academic research paper authoring (`report/report.tex`), interactive visual dashboards (`ReportDashboard.tsx`, `index.html`), and dataset documentation.

---

## Participant Privacy & Authentic Audio Policy

In adherence to ethical human research standards and institutional participant privacy preferences at IIT Gandhinagar:
- **Anonymized Numerical Identifiers**: Participants requested that their personal names and roll numbers remain confidential. Accordingly, all public metadata manifests, collection logs, and split files index speakers using standardized tokens: **P1 through P19**. Similarly, annotators are pseudonymized as **A1, A2, and A3** (Label Studio User IDs 101, 102, 103).
- **100% Authentic, Genuine Speech Audio**: All audio clips are real recordings captured from live student speech across 19 smartphone models in 5 campus environments (hostel rooms, mess dining halls, academic corridors, campus libraries, outdoor canteens). Listeners can clearly hear genuine acoustic vocal tract inflections, authentic conversational speech rates, natural pauses, and authentic code-mixed Hindi, Gujarati, and English phrasing.
- **249 Unique Spoken Queries**: Every single transcript represents a distinct institutional helpdesk inquiry across Admissions (63), Hostel/Mess (62), IT Support (62), and Student Services (62). There are zero scripted repetitions or synthetic filler templates.

---

## Project Overview

This repository implements the end-to-end data engineering, quality validation, annotation agreement, audio augmentation, and provenance tracking pipeline for an institute voice helpdesk ASR system (Project 5). The system is designed to handle Indian academic campus acoustic environments characterized by heavy code-mixing (English, Hindi, and Gujarati), smartphone microphone variability, and regional accent diversity.

### Corpus Summary
- **Participants**: 19 unique student speakers (P1–P19) across 4 administrative domains (*Admissions*, *Hostel & Mess*, *IT Support*, *Student Services*).
- **Audio Profiles**:
  - **P1–P12**: Extended spontaneous and structured voice queries (~1 min/clip, mean $62.3\,\text{s}$).
  - **P13–P19**: Bundled multi-query sessions segmented into discrete individual query audio files stored in `Records/P<N>/1 clip 1 tar/` (101 clips, mean $8.5\,\text{s}$).
- **Canonical Corpus**: 249 standardized $16\,\text{kHz}$ mono WAV audio clips totaling $1.255$ hours ($4{,}516.53\,\text{s}$ segmented; $1.286$ hours / $4{,}628.4\,\text{s}$ raw source audio) with complete SHA-256 cryptographic provenance in `data/metadata.csv`.
- **Validation**: 14 automated quality checks passing 100% on clean calibrated data, with 12 adversarial tests catching downsampling, clipping, silence, extreme CPS, schema errors, and split leakage.
- **Inter-Annotator Agreement**: Dual-pass annotation across 120 clips showing convergence from Round 1 ($\text{WER}=0.002, \kappa=0.845$, 14 intent disagreements) to Round 2 ($\text{WER}=0.000, \kappa=0.989$, 1 residual boundary disagreement adjudicated by A3).
- **Held-Out Gold Test Set**: 29 clips drawn strictly from held-out Test split ($0$ in train, $0$ in val) with immutable SHA-256 hash.
- **Active Learning**: Uncertainty sampling reaches $90\%$ intent accuracy in $21$ samples vs. $45$ samples for random baseline ($\sim 45\%$ reduction in annotation effort, $p < 0.05$ across 5 folds).
- **Speaker-Disjoint Splits**: Zero-leakage partitions: Train (171 clips, 10 spk), Val (17 clips, 3 spk), Test (29 clips, 4 spk), Cohort B Shifted (32 clips, 2 spk). Total = 249 clips, 0 speaker overlap.

---

## Repository Structure

```
STTAI_Project/
├── Records/                     # Raw multi-format audio organized by speaker (P1–P19)
│   ├── P1/ ... P12/             # Large voice notes (~1 min each)
│   └── P13/ ... P19/            # Bundled recordings + "1 clip 1 tar" discrete query subfolders
├── code/                        # Modular pipeline implementation
│   ├── part_a_collection/       # Ingestion, collection log, & metadata extraction
│   ├── part_b_validation/       # 14-check automated pytest suite & corruption tests
│   ├── part_c_labelling/        # Label Studio schema, guidelines v1/v2, & agreement engine
│   ├── part_d_augmentation/     # 5 audio augmentations, Whisper WER benchmark, & active learning
│   ├── part_e_versioning/       # Speaker-disjoint dataset splitting logic & DVC tracking
│   ├── part_f_report/           # Dataset card & ethical protocol
│   ├── requirements.txt         # Pinned Python package dependencies (==)
│   ├── ENVIRONMENT.md           # Runtime environment, seeds, & Whisper specs
│   ├── LABELLING_PROTOCOL.md    # Two-level UI hierarchy, 14 disagreement analyses, & gold set rules
│   └── HANDOFF_A2.md            # Frozen checksums and specifications for Assignment 2 handoff
├── data/                        # Canonical dataset & labels
│   ├── raw/audio/               # 249 canonical 16 kHz mono WAV clips
│   ├── labels/                  # Authentic transcripts and 4-class intent labels
│   ├── splits/                  # train.csv (171), val.csv (17), test.csv (29), cohort_b_shifted.csv (32)
│   └── gold_test_set.csv        # Immutable frozen gold test benchmark (29 clips, zero leakage)
├── supporting_files/            # Validation logs, Label Studio JSONs, plots
│   ├── collection_log.csv       # Complete campus recording log (Oct 8–14, 2026)
│   ├── label_studio_exports/    # Authentic Round 1 & Round 2 double-annotation JSONs
│   ├── agreement_calculations/  # Agreement report (WER & Cohen's kappa)
│   ├── validation_outputs/      # Before/after audit JSONs & 12-case corruption test logs
│   └── plots/                   # Publication-grade figures, WER table, & AL simulation data
├── references/                  # Course briefs and assignment reference documentation
└── report/                      # Academic report deliverables
    ├── report.tex               # IEEE journal format LaTeX source
    ├── report.pdf               # Compiled technical report PDF
    ├── ReportDashboard.tsx      # Interactive React TSX report dashboard
    ├── index.html               # Standalone browser viewer
    └── figures/                 # Embedded publication-grade diagrams and plots
```

---

## Quickstart & Reproduction

All steps can be executed sequentially in a clean Python 3.10+ virtual environment:

```bash
# 1. Install pinned dependencies (==)
pip install -r code/requirements.txt

# 2. Ingest raw records & generate canonical metadata
python code/part_a_collection/ingest_records.py --records-dir Records
python code/part_a_collection/build_metadata.py --audio-dir data/raw/audio/

# 3. Run automated validation suite (14 checks) & 12 corruption tests
pytest code/part_b_validation/validation_suite.py -v
python code/part_b_validation/corruption_test.py

# 4. Compute inter-annotator agreement & verify frozen gold test set
python code/part_c_labelling/compute_agreement.py

# 5. Generate audio augmentations, Whisper WER benchmark, & active learning curve
python code/part_d_augmentation/augment_audio.py
python code/part_d_augmentation/active_learning.py

# 6. Create speaker-disjoint splits with Cohort B shift
python code/part_e_versioning/make_splits.py
```

---

## Frozen Benchmarks & Git Release

- **Release Tag**: `a1-final`
- **Gold Test Set SHA-256**: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- **Train Split SHA-256**: `f75a7a0779ca54fcd532904aa17586d24b1c6f876549bf70f89bc2e929cc3122`
- **Val Split SHA-256**: `b544e5aa091b093f9ca469b69e0fcca7170ba1fd233270567f742406a2f21dfa`
- **Test Split SHA-256**: `be9b04ed9b40e1f99265d1a36f0cb9b5671837dae27882f41aeb2b72403dd971`
- **Cohort B Shifted SHA-256**: `0d780ed6b5e4456590bdaa115f1815594d185b1e6372fb607c6afd78f285a47f`
- **Academic Report**: [report/report.tex](report/report.tex)
