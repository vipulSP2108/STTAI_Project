"""Pack private project artifacts for DVC, restore their paths, and guard Git.

The payload/manifest are private and ignored by Git. Only the .dvc pointer and
this implementation belong in Git. Audio has its own existing DVC pointers.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".json", ".jsonl", ".csv", ".tsv", ".sqlite3", ".db", ".pt", ".pth", ".pkl", ".joblib", ".wandb", ".syncstate"}
AUDIO = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma"}
PRIVATE_PREFIXES = ("mlruns/", "wandb/", "model/models/", "model/results/", "final_annotation/transcription_round/drafts/", "private_project_data/", "dvc_cache/", "dvc_remote/")
PRIVATE_SINGLE_FILES = {"model/src/asr/curate_gold_transcripts.py"}  # withdrawn data-bearing reference dictionary


def secret_path(relative):
    name = PurePosixPath(relative).name.lower()
    return (name == ".env" or name.startswith(".env.") and name != ".env.example"
            or name in {"login.txt", ".netrc", "credentials.json"})


def private_path(relative):
    path = PurePosixPath(relative)
    if path.suffix == ".dvc" or path.name in {".gitignore", ".dvcignore", ".env.example"}:
        return False
    if secret_path(relative) or relative.startswith(PRIVATE_PREFIXES) or relative in PRIVATE_SINGLE_FILES:
        return True
    if path.suffix.lower() in EXTENSIONS | AUDIO:
        return True
    return path.suffix.lower() == ".txt" and not (path.name.lower().startswith("requirements") or path.name.lower().startswith("license"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else digest_stream(stream)


def digest_stream(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def contained(root, relative):
    portable = PurePosixPath(relative)
    if portable.is_absolute() or ".." in portable.parts or not portable.parts or ":" in relative or "\\" in relative:
        raise ValueError("Unsafe payload path")
    target = root.joinpath(*portable.parts).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("Payload path escapes root")
    return target


def pack(bundle, models=None):
    if bundle.exists():
        raise FileExistsError("Bundle already exists; preserve it before packing a new version")
    files = {}
    excluded_dirs = {".git", ".dvc", "__pycache__", ".pytest_cache", ".venv", "venv", "private_project_data", "dvc_cache", "dvc_remote"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in excluded_dirs for part in path.relative_to(ROOT).parts):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if private_path(relative) and not secret_path(relative) and path.suffix.lower() not in AUDIO:
            files[relative] = path
    if models:
        for path in models.rglob("*"):
            if path.is_file() and not secret_path(path.name) and "__pycache__" not in path.parts:
                files["model/models/" + path.relative_to(models).as_posix()] = path
    entries = []
    for relative, source in sorted(files.items()):
        destination = contained(bundle / "payload", relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        entries.append({"path": relative, "sha256": sha256(destination), "bytes": destination.stat().st_size})
    manifest = {"schema": 1, "description": "Private data/annotations/model assets; credentials and raw audio are excluded.", "files": entries}
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Packed {len(entries)} private files ({sum(e['bytes'] for e in entries):,} bytes)")


def verify(bundle):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise ValueError("Unsupported private data schema")
    seen = set()
    for entry in manifest["files"]:
        relative = entry["path"]
        if relative in seen or secret_path(relative):
            raise ValueError("Duplicate or credential file in payload")
        seen.add(relative)
        source = contained(bundle / "payload", relative)
        if source.stat().st_size != entry["bytes"] or sha256(source) != entry["sha256"]:
            raise ValueError("Private payload integrity check failed: " + relative)
    return manifest


def restore(bundle, root, overwrite=False):
    manifest = verify(bundle)
    # Preflight conflicts before writing anything, protecting newer local labels.
    for entry in manifest["files"]:
        target = contained(root, entry["path"])
        if target.exists() and sha256(target) != entry["sha256"] and not overwrite:
            raise FileExistsError("Newer/different local file; back it up or explicitly use --overwrite: " + entry["path"])
    for entry in manifest["files"]:
        target = contained(root, entry["path"])
        if not target.exists() or sha256(target) != entry["sha256"]:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(contained(bundle / "payload", entry["path"]), target)
    print(f"Restored/verified {len(manifest['files'])} private files")


def check_git():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    bad = [p for p in tracked if p and private_path(p)]
    if bad:
        raise SystemExit("Private files are still Git-tracked:\n" + "\n".join(bad))
    print("Git privacy check passed: data, annotations, model binaries and credentials are not tracked.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["pack", "verify", "restore", "check-git"])
    parser.add_argument("--bundle", type=Path, default=ROOT / "private_project_data")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--include-models", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.command == "pack":
        pack(args.bundle, args.include_models)
    elif args.command == "verify":
        print(f"Verified {len(verify(args.bundle)['files'])} private files")
    elif args.command == "restore":
        restore(args.bundle, args.root, args.overwrite)
    else:
        check_git()


if __name__ == "__main__":
    main()
