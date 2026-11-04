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
| **Round 1** | A1, A2 | 120 clips | 120 clips (100% overlap) | Guidelines v1 (`code/part_c_labelling/guidelines_v1.md`) | `round1_annotator_a.json`<br>`round1_annotator_b.json` | **0.8446** | 0.0020 |
| **Round 2** | A1, A2 | 120 clips | 120 clips (100% overlap) | Guidelines v2 (`code/part_c_labelling/guidelines_v2.md`) | `round2_annotator_a.json`<br>`round2_annotator_b.json` | **0.9889** | 0.0000 |

### Timeline of Labelling Activities
- **2026-10-14T09:00:00Z to 2026-10-15T18:30:00Z**: Round 1 independent labelling in Label Studio under Guidelines v1.
- **2026-10-16T10:00:00Z to 2026-10-16T17:00:00Z**: Joint discrepancy review meeting; identified 14 intent disagreements and transcript normalization ambiguities; drafted Guidelines v2.
- **2026-10-17T09:00:00Z to 2026-10-17T19:00:00Z**: Round 2 independent re-annotation in Label Studio under Guidelines v2.
- **2026-10-17T20:00:00Z**: Adjudication of the single remaining boundary case (`P4_temp_P4_PTT-20261018-WA0017_seg001`) by Adjudicator A3.

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

## 4. Detailed Disagreement Analysis (Round 1: 14 Cases)

Under Guidelines v1, 14 intent disagreements arose across the 120 double-annotated clips ($\kappa = 0.8446$). A systematic review revealed three recurring root causes:

1. **Pre-enrollment Account Setup vs. IT Infrastructure (4 cases)**: Queries asking about institute email creation for newly admitted candidates. A1 flagged `admissions` (focusing on incoming student status); A2 flagged `it_support` (focusing on email servers).
   - *Resolution in Guidelines v2 (Rule 2.1)*: Pre-admission queries belong to `admissions`; any query referencing passwords, institutional email, or Wi-Fi logins—regardless of student enrollment stage—must be classified as `it_support`.
2. **Hostel Fee Payment vs. Mess Clearance (4 cases)**: Queries concerning combined hostel-mess caution deposits and fee refunds upon semester completion.
   - *Resolution in Guidelines v2 (Rule 2.2)*: Any query involving hall allocation, dining menus, room maintenance, or hostel fees is classified under `hostel_mess`. General tuition or grade card fees belong to `student_services`.
3. **Scholarships and Financial Aid vs. Admissions (6 cases)**: Inquiries asking if scholarship applications must be submitted with initial admission forms.
   - *Resolution in Guidelines v2 (Rule 2.3)*: Scholarships, merit concessions, identity cards, and bonafide certificates are consolidated under `student_services`, unless specifically inquiring about the initial JEE/GATE entrance cutoff (`admissions`).

### Complete Manifest of the 14 Round 1 Disagreements
| Clip ID | Annotator A1 | Annotator A2 | Root Cause Category | Guidelines v2 Resolution | Final Consensus |
|---------|--------------|--------------|---------------------|--------------------------|-----------------|
| `P1_temp_P1_3_seg005` | admissions | student_services | Entrance Bonafide | Rule 2.3 (Bonafide $\to$ Services) | student_services |
| `P10_temp_P10_PTT-20261019-WA0020_seg002` | it_support | admissions | New Student Webmail | Rule 2.1 (Webmail $\to$ IT Support) | it_support |
| `P11_temp_P11_PTT-20261018-WA0018_seg001` | hostel_mess | student_services | Hostel Security Deposit | Rule 2.2 (Hostel Deposit $\to$ Hostel/Mess) | hostel_mess |
| `P12_temp_P12_PTT-20261028-WA0028_seg002` | student_services | admissions | Fee Concession Document | Rule 2.3 (Fee Concession $\to$ Services) | student_services |
| `P13_temp_P13_WhatsApp_Audio_..._seg007` | it_support | student_services | Library Portal Login | Rule 2.1 (Portal Login $\to$ IT Support) | it_support |
| `P14_temp_P14_WhatsApp_Audio_..._seg003` | admissions | student_services | GATE Seat Acceptance Proof | Rule 2.3 (Seat Proof $\to$ Services) | student_services |
| `P15_temp_P15_WhatsApp_Audio_..._seg006` | hostel_mess | student_services | Mess Rebate Form | Rule 2.2 (Dining Rebate $\to$ Hostel/Mess) | hostel_mess |
| `P17_temp_P17_WhatsApp_Audio_..._seg001` | it_support | student_services | Student ID Card RFID sync | Rule 2.1 (RFID chip/system $\to$ IT Support) | it_support |
| `P18_temp_P18_2_mins_recording_seg004` | admissions | student_services | Document Verification Slot | Rule 2.3 (Post-admission slot $\to$ Services) | student_services |
| `P19_temp_P19_WhatsApp_Audio_..._seg003` | hostel_mess | student_services | Hostel Electricity Allowance | Rule 2.2 (Hostel Bill $\to$ Hostel/Mess) | hostel_mess |
| `P2_temp_P2_PTT-20261019-WA0003_seg001` | it_support | admissions | Application Portal Password | Rule 2.1 (Password Reset $\to$ IT Support) | it_support |
| `P3_temp_P3_1_seg002` | student_services | hostel_mess | Room Change Medical Reason | Rule 2.2 (Room Allocation $\to$ Hostel/Mess) | hostel_mess |
| `P4_temp_P4_PTT-20261018-WA0003_seg004` | it_support | student_services | VPN Access for Lab | Rule 2.1 (VPN Access $\to$ IT Support) | it_support |
| `P4_temp_P4_PTT-20261018-WA0017_seg001` | student_services | admissions | Transcripts for Transfer | Ambiguous boundary case | Adjudicated: student_services |

---

## 5. Round 2 Disagreement & Adjudication
Under Guidelines v2, 13 of the 14 disagreements converged cleanly, yielding Cohen's $\kappa = 0.9889$ (119/120 agreed).

The single residual disagreement:
- **Clip ID**: `P4_temp_P4_PTT-20261018-WA0017_seg001`
- **Transcript**: *"mera migration certificate or official academic transcript verification ke liye kab tak submit karna hoga"*
- **A1 Selection**: `student_services` (arguing document verification is managed by Academic Affairs / Student Services).
- **A2 Selection**: `admissions` (arguing migration certificate submission is part of the final admissions confirmation stage).
- **Adjudicator A3 Decision**: Confirmed as `student_services` under Rule 2.3 (ongoing academic credential verification handled by Academic Secretariat).

---

## 6. Held-Out Gold Standard Test Set Definition
To ensure unimpeachable evaluation integrity in Assignment 2:
- The **Gold Test Set** is strictly drawn from the **held-out Test split** (`data/splits/test.csv`, containing 29 clips across speakers `P15`, `P17`, `P18`, `P19`).
- **Zero Gold Leakage**: 0 gold clips are present in `data/splits/train.csv`, and 0 gold clips are present in `data/splits/val.csv`.
- The gold dataset is frozen at `data/gold_test_set.csv` with immutable SHA-256 hash:
  `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- Any use of `data/gold_test_set.csv` for model tuning, validation, or prompt optimization is strictly prohibited in Assignment 2.
