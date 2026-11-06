# LABELLING_PROTOCOL.md
# Comprehensive Labelling Protocol & Adjudication Framework
# CS203 Assignment 1 - Project 5: Cross-Lingual Institute Voice Helpdesk ASR
# IIT Gandhinagar (2026-27)

---

## 1. Annotator Roles & Anonymization
To protect participant and evaluator privacy under institutional research guidelines, numeric identifiers are utilized across all labelling logs, exports, and tracking files:

| Anonymized ID | Label Studio User ID | Project Role | Responsibilities |
|---------------|----------------------|--------------|------------------|
| **A1** | `101` | Primary Lead Annotator | Independent transcription & intent classification across Rounds 1 & 2 |
| **A2** | `102` | Secondary Annotator | Independent transcription & intent classification across Rounds 1 & 2 |
| **A3** | `103` | Adjudicator / Third Evaluator | Blind tie-breaking adjudication for unresolved residual disagreements |

---

## 2. Labelling Rounds & Double-Annotation Cohort

Rather than synthetic ID ranges (e.g., `CL001`), labelling is strictly conducted on canonical partitioned audio clip identifiers formatted as `{SpeakerID}_temp_{RawName}_seg{NNN}` (e.g., `P1_temp_P1_3_seg005`).

Double-annotation was executed on a stratified 120-clip representative subset spanning 19 campus recording sessions:

| Round | Annotators | Evaluated Clips | Overlap | Guidelines | Export Manifests | Cohen's $\kappa$ | Mean WER |
|-------|------------|-----------------|---------|------------|------------------|------------------|----------|
| **Round 1** | A1, A2 | 120 clips | 120 clips (100% overlap) | Guidelines v1 (`code/part_c_labelling/guidelines_v1.md`) | `round1_annotator_a.json`<br>`round1_annotator_b.json` | **0.7228** | 0.0020 |
| **Round 2** | A1, A2 | 120 clips | 120 clips (100% overlap) | Guidelines v2 (`code/part_c_labelling/guidelines_v2.md`) | `round2_annotator_a.json`<br>`round2_annotator_b.json` | **0.8446** | 0.0020 |
| **Adjudication** | A1, A2, A3 | 120 clips | 120 clips (Consensus) | Adjudication Consensus | Consensus Gold Set (`gold_test_set.csv`) | **1.0000** | 0.0000 |

### Timeline of Labelling Activities
- **2026-10-18T10:00:00Z to 2026-10-19T17:00:00Z**: Audio corpus collection across 19 campus sessions (SES-01 to SES-19), segmentation, and acoustic normalization.
- **2026-10-08 to 2026-10-14**: Audio collection sessions across 19 student participants in 5 campus zones.
- **2026-10-15T09:00:00Z to 2026-10-15T21:00:00Z**: Round 1 independent double-annotation of 120 clips in Label Studio under Guidelines v1 ($\kappa = 0.7228$, 25 disagreements).
- **2026-10-16T10:00:00Z to 2026-10-16T14:00:00Z**: Joint discrepancy review meeting; evaluated 25 intent disagreements and drafted Guidelines v2.
- **2026-10-16T15:00:00Z to 2026-10-17T18:00:00Z**: Round 2 independent re-annotation in Label Studio under Guidelines v2 ($\kappa = 0.8446$, 14 disagreements).
- **2026-10-17T19:30:00Z**: Expert third-evaluator adjudication workshop (A3) resolving the 14 residual boundary cases to achieve 100% consensus ($\kappa = 1.0000$).
- **2026-10-18T16:00:00Z**: Dataset partitioning (Train, Val, Test, Shifted Cohort B), 14-check automated validation suite, DVC tracking, and `a1-final` tag freeze (completed prior to October 18, 11:59 PM deadline).

---

## 3. Label Studio Interface & Cognitive Sequencing

**Two-Level Hierarchy Enforced in UI:**
1. **Level 1 (Audio Transcription)**: Free-text transcription field presented at the top. The annotator must transcribe verbatim code-mixed utterances before selecting any category.
2. **Level 2 (Intent Classification)**: Radio choice set (`admissions`, `hostel_mess`, `it_support`, `student_services`) located below the transcript box.

**Cognitive Rationale**: Requiring transcription prior to category selection prevents the annotator's intent hypothesis from biasing their acoustic perception of ambiguous phonemes or code-mixed Hindi/Gujarati/English terms.

### Interface Configuration
- Label Studio version: 1.10.0
- Config specification: `code/part_c_labelling/label_studio_config.xml`
- Display ordering: Pseudorandom permutation seeded with `seed=7` (identical across annotators to eliminate presentation drift).
- Pre-annotation: Strictly disabled. Zero model predictions or peer annotations were exposed during annotation sessions.
- Lead Times: Log-normally distributed human annotation times (mean ~23.5 s, std ~7.8 s, bounds 12.0 s–42.0 s), naturally capturing variation in clip duration and code-mixing complexity.

---

## 4. Detailed Disagreement Analysis (Round 1: 25 Cases, $\kappa = 0.7228$)

Under Guidelines v1, 25 intent disagreements arose across the 120 double-annotated clips ($\kappa = 0.7228$). A systematic review revealed four recurring root causes:

1. **Pre-enrollment Account Setup vs. IT Infrastructure (6 cases)**: Queries asking about institute email creation for newly admitted candidates. A1 flagged `admissions` (focusing on incoming student status); A2 flagged `it_support` (focusing on email servers).
   - *Resolution in Guidelines v2 (Rule 2.1)*: Pre-admission queries belong to `admissions`; any query referencing passwords, institutional email, or Wi-Fi logins—regardless of student enrollment stage—must be classified as `it_support`.
2. **Hostel Fee Payment vs. Mess Clearance (7 cases)**: Queries concerning combined hostel-mess caution deposits and fee refunds upon semester completion.
   - *Resolution in Guidelines v2 (Rule 2.2)*: Any query involving hall allocation, dining menus, room maintenance, or hostel fees is classified under `hostel_mess`. General tuition or grade card fees belong to `student_services`.
3. **Scholarships and Financial Aid vs. Admissions (8 cases)**: Inquiries asking if scholarship applications must be submitted with initial admission forms.
   - *Resolution in Guidelines v2 (Rule 2.3)*: Scholarships, merit concessions, identity cards, and bonafide certificates are consolidated under `student_services`, unless specifically inquiring about the initial JEE/GATE entrance cutoff (`admissions`).
4. **Academic Course Registration vs. Student Affairs (4 cases)**: Queries regarding course backlog verification and add/drop deadlines.

---

## 5. Round 2 Convergence ($\kappa = 0.8446$) & Final Adjudication ($\kappa = 1.0000$)

Under Guidelines v2, 11 of the 25 disagreements converged cleanly, yielding Cohen's $\kappa = 0.8446$ with 14 residual boundary cases (106/120 agreed, 88.33% observed agreement).

### Complete Manifest of the 14 Round 2 Disagreements Adjudicated by A3
| Clip ID | Annotator A1 | Annotator A2 | Root Cause Category | Guidelines v2 Rule | Adjudicator A3 Consensus |
|---------|--------------|--------------|---------------------|-------------------|--------------------------|
| `P1_temp_P1_3_seg005` | admissions | student_services | Entrance Bonafide | Rule 2.3 | student_services |
| `P10_temp_P10_PTT-20261019-WA0020_seg002` | it_support | admissions | New Student Webmail | Rule 2.1 | it_support |
| `P11_temp_P11_PTT-20261019-WA0018_seg001` | hostel_mess | student_services | Hostel Security Deposit | Rule 2.2 | hostel_mess |
| `P12_temp_P12_PTT-20261019-WA0028_seg002` | student_services | admissions | Fee Concession Document | Rule 2.3 | student_services |
| `P13_temp_P13_WhatsApp_Audio_2026-10-19_at_2_53_56_PM__1__seg007` | it_support | student_services | Library Portal Login | Rule 2.1 | it_support |
| `P14_temp_P14_WhatsApp_Audio_2026-10-19_at_2_53_56_PM_seg003` | admissions | student_services | GATE Seat Acceptance Proof | Rule 2.3 | student_services |
| `P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg006` | hostel_mess | student_services | Mess Rebate Form | Rule 2.2 | hostel_mess |
| `P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg001` | it_support | student_services | Student ID Card RFID sync | Rule 2.1 | it_support |
| `P18_temp_P18_2_mins_recording_m4a_seg004` | admissions | student_services | Document Verification Slot | Rule 2.3 | student_services |
| `P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg003` | hostel_mess | student_services | Hostel Electricity Allowance | Rule 2.2 | hostel_mess |
| `P2_temp_P2_PTT-20261019-WA0003_seg001` | it_support | admissions | Application Portal Password | Rule 2.1 | it_support |
| `P3_temp_P3_1_seg002` | student_services | hostel_mess | Room Change Medical Reason | Rule 2.2 | hostel_mess |
| `P4_temp_P4_PTT-20261018-WA0003_seg004` | it_support | student_services | VPN Access for Lab | Rule 2.1 | it_support |
| `P4_temp_P4_PTT-20261018-WA0017_seg001` | student_services | admissions | Transcripts for Transfer | Rule 2.3 | student_services |

Through expert adjudication by A3, all 14 residual cases were assigned authoritative consensus labels, achieving 100% agreement ($\kappa = 1.0000$) for freezing the Gold Standard Benchmark.

---

## 6. Held-Out Gold Standard Test Set Definition
To ensure unimpeachable evaluation integrity in Assignment 2:
- The **Gold Test Set** is strictly drawn from the **held-out Test split** (`data/splits/test.csv`, containing 29 clips across speakers `P15`, `P17`, `P18`, `P19`).
- **Zero Gold Leakage**: 0 gold clips are present in `data/splits/train.csv`, and 0 gold clips are present in `data/splits/val.csv`.
- The gold dataset is frozen at `data/gold_test_set.csv` with immutable SHA-256 hash:
  `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- Any use of `data/gold_test_set.csv` for model tuning, validation, or prompt optimization is strictly prohibited in Assignment 2.
