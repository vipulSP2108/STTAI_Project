# LABELLING_PROTOCOL.md
# Lets someone outside the team repeat our labelling the same way.
# Covers: annotator IDs, label order, item order, what was visible,
# disagreement resolution, and timeline matched to export files.

# Labelling Protocol — Voice Helpdesk ASR (Project 5)
## CS203 Assignment 1, IIT Gandhinagar 2026-27

---

## Annotator IDs (anonymised)
| ID | Role |
|----|------|
| A1 | [anonymised team member] |
| A2 | [anonymised team member] |

---

## Items Labelled

| Round | Annotators | Clip range | Total clips | Overlap | Guideline |
|-------|-----------|-----------|-------------|---------|-----------|
| 1 | A1, A2 | CL001–CL150 | 150 | CL001–CL100 (100 clips) | v1 |
| 2 | A1, A2 | CL001–CL060 | 60 | All 60 | v2 (revised) |

---

## Label Order (CRITICAL — followed by all annotators)

**Level 1**: transcript (fill first — type exactly what was said)
**Level 2**: intent (fill second — choose from 4 categories)

**Rationale**: Filling transcript first prevents the annotator's intent hypothesis
from unconsciously influencing what they hear and write.

**Confirmation**: Both A1 and A2 confirmed they followed this order before starting.
This is enforced in the Label Studio UI (TextArea appears above Choices).

---

## Label Studio Setup
- Version: 1.10.0
- Project config: `code/part_c_labelling/label_studio_config.xml`
- Guidelines shown: v1 for Round 1, v2 for Round 2

## Item Presentation Order
- Clips shown in randomised order (seed=7) in Label Studio
- Both annotators see the same ordering (same Label Studio project)
- Annotators did NOT see each other's labels during their session
- NO model predictions or pre-annotations were shown

---

## What Annotators Could See
- Audio clip (playback controls)
- Empty transcript text area (no pre-fill)
- Empty intent choice set (no pre-selection)
- The guidelines document (v1 or v2, pinned to top of Label Studio)

---

## Disagreement Resolution
| Label type | Resolution rule |
|-----------|----------------|
| Transcript | If WER < 0.2: keep A1's version; else: discuss and reach consensus |
| Intent | Majority vote; ties broken by third team member |

Final adjudicator for ties: Satvik Sharma (Third Team Member)

---

## Timeline
| Date | Round | Annotators | Clips | Guidelines | Label Studio Export Files |
|------|-------|-----------|-------|-----------|--------------------------|
| 2026-10-14 | Round 1 | A1, A2 | 120 clips | v1 | `supporting_files/label_studio_exports/round1_annotator_a.json`, `round1_annotator_b.json` |
| 2026-10-17 | Round 2 | A1, A2 | 120 clips | v2 | `supporting_files/label_studio_exports/round2_annotator_a.json`, `round2_annotator_b.json` |
