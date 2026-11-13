#!/usr/bin/env python3
"""
package_submission.py
=====================
Packages the repository strictly according to the CS203 Assignment 2 submission specification:
- Name format: CS203_A2_Project5_24110260_24110381_24110300.zip
- Top-level folders: code/, data/, artefacts/, supporting_files/, report/, presentation/
- Explicitly includes intact .git/ directory to guarantee tag & commit history verification.
- Excludes OS cache, virtualenvs, local wandb traces, and pytest caches.
"""

import os
import zipfile
import subprocess
from pathlib import Path

ZIP_NAME = "CS203_A2_Project5_24110260_24110381_24110300.zip"
EXCLUDE_DIRS = {
    ".venv", "venv", "env", "__pycache__", ".pytest_cache", "wandb",
    "Records", ".DS_Store"
}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd"}

def should_exclude(rel_path_str: str) -> bool:
    parts = rel_path_str.split(os.sep)
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
    _, ext = os.path.splitext(rel_path_str)
    if ext in EXCLUDE_EXTS:
        return True
    # Allow artefacts/docker_image.tar.gz to be bundled directly in submission zip as per requirement
    return False

def package():
    root = Path(".")
    zip_path = root / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    print(f"Creating submission package: {ZIP_NAME}...")
    file_count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for folder_name in [".git", "code", "data", "artefacts", "supporting_files", "report", "presentation", "STTAI_reports"]:
            folder = root / folder_name
            if not folder.exists():
                continue
            for item in folder.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(root)
                    rel_path_str = str(rel_path)
                    if should_exclude(rel_path_str):
                        continue
                    zipf.write(item, arcname=rel_path_str)
                    file_count += 1

        # Also write root markdown files
        for root_file in ["README.md", "DOCKER.md", "ENVIRONMENT.md", "MODELS.md", "TEST_SET_LOG.md", "DATA_CHANGES.md", "MODEL_CARD.md"]:
            rf = root / root_file
            if rf.exists():
                zipf.write(rf, arcname=root_file)
                file_count += 1

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"✓ Packaged {file_count} files into {ZIP_NAME} ({size_mb:.2f} MB)")
    print(f"✓ .git directory is fully preserved and bundled.")

if __name__ == "__main__":
    package()
