# Team contributions — CS203 Project 5 (Voice Helpdesk ASR)

**Team:** Rajdeep Vraj (22110215, GitHub `rajdeepvraj`), Vipul Sunil Patil (22110189, `vipulSP2108`),
Satvik Sharma (26120008, `satvikboi`). Contribution: **equal, 33.3 % each**.

## Why the commit history does not show three equal authors

Most of the work was done together, in person, on one shared laptop (Vipul's macOS machine, which
also held the recordings, the Label Studio instances and Docker). Whoever was at the keyboard, the
commits were made from that laptop under Vipul's git identity, so the history shows most commits as
`VipulSP2108`. Satvik's commits from his own machine (Docker build and offline validation on
Windows, DVC pointer, CI workflow) appear under `satvikboi`. Rajdeep worked on the shared laptop and
has no commits under his own account.

The history has not been rewritten to change authors. This file and the contribution tables in both
reports are the record of who led what; each member can explain any part of the code and results.

## Who led what

| Area | Rajdeep Vraj | Vipul Sunil Patil | Satvik Sharma |
|---|---|---|---|
| **A1 – data** | audio collection protocol, ingestion scripts, 14-check Pandera validation suite, corruption tests | dual Label Studio deployment, consent register, expert adjudication pass, active learning | speaker-grouped splitting, augmentation quality gates, leakage audit, DVC versioning |
| **A2 – models** | Whisper decoding integration, intent router, MLflow and W&B tracking, bootstrap evaluation | FastAPI service, Streamlit UI, Docker packaging, offline verification harness | drift detection and replay, retraining pipeline, promotion/rollback gate, error taxonomy |

The annotator roles (A1, A2, expert A3) are pseudonymous in the data and the labelling protocol; the
Label Studio exports for each annotator are the evidence of that work.

## From the final submission onward

Members commit their own changes from their own accounts, and pair-programmed commits carry a
`Co-authored-by:` line for everyone who worked on them.

## Use of AI assistants

AI assistants (Claude by Anthropic, ChatGPT) were used as assistants for drafting and formatting the
reports and documentation, for boilerplate code (metric computation, plotting, report numbers) and
for debugging. The team designed the pipeline, recorded and annotated all data, ran the experiments,
and checked every reported number against the result files. Prompts are kept in `code/prompts/`.
