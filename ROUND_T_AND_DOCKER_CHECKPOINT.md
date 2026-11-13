# Round T and Docker archive checkpoint — 12 November 2026


## Completed annotation export and private handoff — 13 November 2026

- User completed all 141 A2 tasks. Exported through the original `export_round_t.sh A2`; confirmed 141 submitted tasks and 141 unique clip IDs.
- Consistent SQLite backup: external live A2 state `backups/completed_A2_20261113.sqlite3`, copied into the checkout's ignored `final_annotation/transcription_round/ls_data_A2/label_studio.sqlite3` for the DVC payload.
- Completed raw export remains `final_annotation/transcription_round/exports/A2.json`, private/DVC-only.
- Git previously tracked private annotations, transcripts, model/run artifacts and `.env`. Removed 1,228 private paths from the Git index, retaining local copies; the clean tree will track code/docs/DVC pointers only. Old shared history is not force-rewritten and formerly committed real keys require owner rotation.
- Private payload: `private_project_data.dvc`; generic tools `code/private_data.py`, `code/dvc.ps1`, `code/Dockerfile.dvc-tools`; restore and public/private CI instructions in `PRIVATE_DATA_HANDOFF.md`.
- DVC uses pinned 3.67.1; remote/cache are outside the repo. Docker wrapper maps the existing Downloads store/cache. Portable snapshot supplies sibling `dvc_remote` and `local_assets`, plus the previously validated Docker archive.
- Clean DVC recovery test passed: 1,563 private payload files, 141 submitted A2 tasks, valid SQLite, all 182 active WAV SHA-256 hashes, 201 original recording files and 249 legacy WAVs. Verification summary: `Downloads/STTAI_DVC_Restore_Verification_20261113/verification_summary.json`.
- Snapshot builder: `scratch/build_friend_snapshot.py`; target folder/ZIP: `Downloads/STTAI_Project_Snapshot_20261113` and `.zip`. Its private `HANDOFF.md`, `SNAPSHOT_MANIFEST.json`, `.zip.sha256`, and `Downloads/STTAI_Project_Snapshot_20261113_summary.json` record the exact source commit, annotation count, archive hash and completed verification. Check these records for final packaging status. The source commit is pushed normally to main; no force-push/history rewrite is part of this work.

## Latest transcript-draft correction status

**Latest requested corrections applied:** recognizable IIT GN/helpdesk variants normalized across English/Hindi/Gujarati drafts; 64 literal U+FFFD damaged fragments across 34 clips repaired using overlapping hypotheses and 51 targeted audio re-decodes plus 8 focused checks. Updated the existing second-pass TXT and authoritative JSON transcript fields. No U+FFFD or IIT Jain remains in the edited transcript text. Raw words/chunks and `drafts/raw_backup/` intentionally preserve original model output. Detailed edits: `drafts/requested_corrections_log.json`; audio evidence: `character_repair_candidates.json` and `character_repair_focused.json`. Methodology and Label Studio submissions unchanged. Drafts are still not human-verified. The decoder now flags replacement characters and no longer uses the old 160-token cap; for another raw ASR pass use a NEW output stem, since decoder options changed and this output now contains edits. Exact original runner is backed up with a matching SHA-256.

**Full second Whisper pass COMPLETED:** all 141 assigned recordings were freshly decoded from 82.76 minutes of source audio with local Whisper large-v3 on the RTX 4060, offline. Exit code 0; total model decode time 60.67 minutes. Outputs: `final_annotation/transcription_round/drafts/A2_141_WHISPER_PASS_2.txt` and `.json`. Verification passed for 141 unique clip IDs, task mapping, all source WAV SHA-256 hashes, and 141 nonempty transcripts. These remain machine drafts, not human-verified transcripts. The audit lists 92 clips with automatic review flags (including imperfect metadata-language hints, possible boundary duplication, low confidence/repetition and script checks); see `A2_141_WHISPER_PASS_2_REVIEW.md` and `.json`. Flags are not a measured error count, and unflagged clips can still be wrong. In particular, do not claim every spoken word now matches its required script without checking audio.

Exact runner command: `python /work/transcribe_codeswitch.py --model large-v3 --window 6 --overlap 2 --output-stem A2_141_WHISPER_PASS_2`. Full run provenance, script/task hashes, mounts and exit status: `drafts/whisper_pass_2_run.json`. Logs: `drafts/whisper_pass_2.log`; exit status: `drafts/whisper_pass_2_exit.txt`. Resume with the same arguments/output stem only if further work is needed; completed clips are skipped after audio hash checks. Old draft/pilot outputs remain preserved. No Label Studio submissions or methodology documents were changed by this pass. The completed temporary Whisper container was removed; Label Studio remains running.

The user requested all 141 A2 transcripts. Existing ASR text was compiled into `final_annotation/transcription_round/drafts/A2_141_ASR_TRANSCRIPTS.txt` and its JSON counterpart; those are old machine outputs, not corrected human references. The user identified missing Hindi in the first clip, `P9_41` (`076e2bba`), whose metadata incorrectly routes it as English-only. The earlier fresh multilingual files contain pilot results only; the active full pass is tracked above. A 12-second-window large-v3-turbo pass produced 1/141 drafts and still missed the Hindi; a Hindi-hinted comparison recovered Hindi passages but also transliterated English and repeated words. The active full pass uses the tested shorter-window decoder. Do not call the mixed-script correction finished or treat the old compiled file as corrected.

Pilot runner: `final_annotation/transcription_round/drafts/retranscribe_multilingual.py`. Model cache (outside Git): `C:\Users\Satvik Sharma\Downloads\STTAI_Transcription_ModelCache`. Pinned model: `dropbox-dash/faster-whisper-large-v3-turbo@0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf`. Pilot/comparison JSON files are saved in the drafts directory. User requested methodology remain unchanged; no methodology documents or Label Studio annotations have been changed by these draft experiments. Machine drafts remain identified as such.

Further pilot work: the laptop has an NVIDIA RTX 4060 8 GiB GPU. A separate helper image `voice-helpdesk-asr:transcription-gpu` adds CUDA 12/cuDNN 9 libraries; the archived release image is unchanged. `drafts/transcribe_codeswitch.py` implements resumable, overlapping-window decoding and filters language detection to en/hi/gu (the unrestricted detector mistakenly selected Urdu script for Hindi). GPU turbo pilot output `A2_141_CODESWITCH_TURBO.json` contains only 1 clip and still omits some Hindi; do not regard it as corrected. The full model `Systran/faster-whisper-large-v3@edaa852ec7e145841d8ffdb056a99866b5f0a478`, window 6 seconds, overlap 2 seconds, recovered both candidate Hindi passages in `A2_141_CODESWITCH_LARGE-V3.json`, but also wrote some English boundary words phonetically in Devanagari. A longer-context Hindi-hinted comparison (`P9_41_LARGE_V3_LONG_CONTEXT.json`) was worse, transliterating most English; do not use it as a corrected transcript. These outputs contain ONLY ONE test clip each. The full rerun was started subsequently and is tracked at the top of this checkpoint; these pilot files are not its output. Script-character presence checks do not prove transcript accuracy. Pilot containers do not change Label Studio state.

## Current source

- Original checkout: `C:\programmes\STTAI_Project`.
- Pulled `main` successfully; HEAD `0ec5ed1` (`wandb`). No push performed.
- Local Round T fixes: `.sh` line endings normalized to LF; `.gitattributes` now enforces LF for the two Round T shell scripts.
- The pre-existing `data/gold_test_set.csv` status entry had no content diff before the pull. Do not discard it blindly.

## Transcription — ready for A2

- Open <http://localhost:8092>; use the A2 credentials supplied separately. Credentials are deliberately omitted here.
- Docker container: `sttai-round-t-a2`; pinned official Label Studio 1.23.0 image.
- 141 tasks: 100 shared clips with no draft, plus 41 A2-only clips with ASR drafts to correct.
- Existing saved work preserved: 1 completed task at setup verification. All 141 audio files exist; authenticated WAV playback verified after fixing the imported Mac storage path.
- Follow `code/LABELLING_PROTOCOL.md` sections 1–3 and `final_annotation/GUIDELINES.md`. This round supplies transcripts; intent/language decisions are already established. Shared clips require independent listening/transcription; single clips allow correction of the supplied ASR draft.
- Runtime scripts/config/task lists come from the original checkout. Audio and the live database remain outside it:
  - Audio: `C:\Users\Satvik Sharma\Downloads\STTAI_Project\STTAI_Project\final_annotation\annotator_1\records` (read-only mount).
  - Database/login: `C:\Users\Satvik Sharma\Downloads\STTAI_Project\STTAI_Project\final_annotation\transcription_round\ls_data_A2` (persistent read/write mount).
  - Pre-start SQLite backup: `ls_data_A2\backups\before_docker_start.sqlite3` under that directory.
- Important Docker setting: `LABEL_STUDIO_BASE_DATA_DIR=/project/final_annotation/transcription_round/ls_data_A2`. Without this, the image uses a fresh database under `/label-studio/data`, ignoring the intended saved state.
- Local storage ID 1 in the live database now points to `/project/final_annotation/annotator_1/records`, replacing the teammate's Mac path. No task or annotation was rewritten.
- Export destination is the original checkout's `final_annotation\transcription_round\exports\A2.json`. Initial export completed with 1 annotated clip. Export again after working; saved annotations live in the database even before export.

PowerShell commands (from any directory):

```powershell
# Restart the existing container if needed:
docker start sttai-round-t-a2

# Export your current work; leaves the app running:
docker exec sttai-round-t-a2 bash final_annotation/transcription_round/export_round_t.sh A2

# Only AFTER finishing a session: export, then stop:
docker exec sttai-round-t-a2 bash final_annotation/transcription_round/export_round_t.sh A2
docker exec sttai-round-t-a2 bash final_annotation/transcription_round/start_round_t.sh stop
docker stop sttai-round-t-a2
```

Do not run the stop script on the Windows host using a PID generated inside Docker.

## Offline model image/archive — completed locally

Instructions inspected: `C:\Users\Satvik Sharma\Downloads\DOCKER_ARCHIVE_FOR_FRIEND.md`.

This can proceed before Round T is complete. It packages the existing committed model. A later release will be needed if model code/data changes. Current code deliberately omits WER/CER when no human transcript references are bundled; do not manufacture references to populate those metrics.

- Output directory: `C:\Users\Satvik Sharma\Downloads\STTAI_Project_Docker_Archive_20261112`.
- Source: clean `git archive HEAD` snapshot of only Docker build inputs, in that output directory's `source` folder. Local annotation changes and live SQLite/login files are excluded.
- External audio context: `C:\Users\Satvik Sharma\Downloads\release_audio_for_friend\release_audio`.
- Preflight passed: 44 WAV SHA-256/format/duration checks; 104 train / 38 validation / 40 test clips.
- Build tag: `voice-helpdesk-asr:indic-v2`; platform `linux/amd64`, target `release`.
- Build log: `build.log`; status will be recorded in `build_exit.txt`.
- OS/CPU/RAM/Docker details saved in `environment.json`.

Remaining checkpoints:

- [x] Build succeeded unchanged (exit 0); router training and 44 bundled audio checks passed.
- [x] Ran `validate` with `--network none` and no host mounts; exit 0 on all 40 test clips. Saved full JSON and terminal log. Intent accuracy 60%; intent macro F1 0.594805; language-route accuracy 72.5%.
- [x] Saved Docker image as gzip archive outside the Git checkout (1,466,489,118 bytes).
- [x] Recorded archive SHA-256 and image ID; verified full gzip CRC and Docker manifest/tag. Docker loaded the archive successfully with the same image ID (`archive_load_verification.log`).
- [x] Prepared `SEND_TO_TEAMMATE.md` in the output directory, with measured results, artifact paths, archive checksum/image ID and machine details. `docker_version.txt` contains the plain Docker version output.
- [ ] User uploads archive to Drive and shares it with teammate. No upload or external message is authorized or performed merely by reading the instruction file.
- [ ] A2 completes transcript work, exports it, then stops Label Studio.
- [ ] Team combines A1/A2 exports and adjudicates transcript disagreements before computing transcript agreement/WER or using human references downstream.

Build completion details: image ID `sha256:362a326553d6d84c5592b435874f652aec0a70bbb17866a12ede61e0bebae972`. Offline evaluation container `sttai-indic-v2-offline-validation` runs `validate --output /tmp/offline_validation.json`, with network mode `none` and no bind mounts. Evidence is saved in `offline_container_proof.json`. Live progress is in `offline_validation.log`; final status in `validation_exit.txt`. Archive generation/integrity checks use `package_image.py`; see `packaging.log` and, when complete, `archive_metadata.json`.

Archive: `C:\Users\Satvik Sharma\Downloads\STTAI_Project_Docker_Archive_20261112\docker_image.tar.gz`.
SHA-256: `4d174accc18db803e982ae05919d215792cb34d8905ef971ae08136ee1067ad4`.

Final results: `offline_validation.json` (including per-clip predictions), `offline_validation.log`, `validation_exit.txt`, `environment.json`, `docker_version.txt`, `archive_metadata.json`, and `archive_load_verification.log`, all in the output directory. WER/CER are null with reference count 0, as expected until real Round T references are bundled. The friend's note allows JSON text OR a screenshot; real JSON/log evidence is saved, with no screenshot claimed. The completed temporary evaluation container was removed after exporting its results. The A2 Label Studio container remains running for the user. No commit, push, public upload or external message was performed.

Do not delete Docker build caches or unrelated images as part of the instruction file's optional cleanup.
