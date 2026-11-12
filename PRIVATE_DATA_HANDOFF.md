# Private data, annotations and the shareable snapshot

Git stores code, schemas, documentation and DVC pointers. Annotation exports,
SQLite databases, transcripts, experiment artifacts, datasets and model binaries
are local/DVC content. `code/private_data.py check-git` enforces that boundary.
Credentials are local only and are excluded from the DVC payload.

## Restore the private project paths

The `private_project_data.dvc` pointer versions a payload plus SHA-256 manifest.
The payload preserves the original relative paths, including the completed
`final_annotation/transcription_round/exports/A2.json` and the A2 SQLite snapshot.

With DVC 3.67.1 installed and the shared snapshot's `dvc_remote` beside the repo:

```bash
dvc pull private_project_data.dvc
python code/private_data.py restore
python code/private_data.py verify
```

Restoration refuses to overwrite different/newer local files. Back up local work
before deliberately using `--overwrite`. Do not use an older private snapshot to
replace a teammate's newer annotations.

On this Windows machine, without native DVC, Docker provides the pinned helper:

```powershell
.\code\dvc.ps1 pull private_project_data.dvc
python code/private_data.py restore
```

The wrapper uses `Downloads\STTAI_Project_DVC` and
`Downloads\STTAI_Project_DVC_Cache`, mounted outside the Git checkout. Override
them through `STTAI_DVC_REMOTE` and `STTAI_DVC_CACHE` if necessary. In the portable
snapshot, point those variables to its sibling `dvc_remote` and `dvc_cache` when
using the wrapper. Native DVC uses the relative paths in `.dvc/config` directly.

Processed model audio remains under its separate `model/data/audio.dvc` pointer.
Original recordings in the private handoff stay outside the Git folder.

## Save later private changes

After exporting annotations, build a NEW private bundle instead of overwriting
an old one blindly. `code/private_data.py pack --bundle <new-folder>` writes a
manifest with every file's SHA-256. Preserve previous exports/snapshots, then
replace the current local bundle deliberately, run `dvc add` and `dvc push`, and
commit only its `.dvc` metadata and code. Never `git add -f` the payload.

## Docker

Restore the private data before building `code/Dockerfile`; its training inputs
are intentionally absent from a plain Git clone. The shared ZIP also includes the
previously validated `voice-helpdesk-asr:indic-v2` archive and its checksums and
offline evaluation JSON. That image records its original source commit; exporting
new annotations does not silently retrain or modify it.

## GitHub Actions

Public CI checks the Git privacy boundary, restoration safety, model-gate logic,
WAV validation and shell syntax. Its real-data split test explicitly skips when
the private dataset is absent. It does not claim to validate a private model image.

The `private-release` job runs only when the repository variable
`RUN_PRIVATE_DATA_CI=true` is deliberately configured with a reachable HTTP/S3 DVC
remote in the `DVC_CONFIG` secret (and storage credentials as needed). The local
remote delivered inside the ZIP is not reachable by GitHub-hosted runners.

## Existing Git history

Older commits already contained data, annotation files and a root `.env`.
Removing them from the current tree does not erase those historical objects.
No shared history is force-rewritten here. Any real key formerly committed in
`.env` should be rotated by its owner. The private ZIP uses a fresh shallow
checkout of the cleaned commit, rather than copying that older object history.
