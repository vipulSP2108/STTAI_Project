"""Restoring a private DVC payload must not corrupt or overwrite local annotations."""
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from private_data import restore, verify


class PrivateDataRestoreTest(unittest.TestCase):
    def bundle(self, root, relative="final_annotation/exports/A2.json"):
        body = '{"transcript": "નમસ્તે नमस्ते hello"}'.encode()
        payload = root / "bundle/payload" / relative
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_bytes(body)
        manifest = {"schema": 1, "files": [{"path": relative, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}]}
        (root / "bundle/manifest.json").write_text(json.dumps(manifest))
        return root / "bundle", body

    def test_restores_utf8_annotations_without_changes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, body = self.bundle(root)
            restore(bundle, root / "checkout")
            self.assertEqual((root / "checkout/final_annotation/exports/A2.json").read_bytes(), body)

    def test_preserves_newer_local_work_on_conflict(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, _ = self.bundle(root)
            current = root / "checkout/final_annotation/exports/A2.json"
            current.parent.mkdir(parents=True)
            current.write_text("newer user work")
            with self.assertRaises(FileExistsError):
                restore(bundle, root / "checkout")
            self.assertEqual(current.read_text(), "newer user work")

    def test_rejects_corruption_before_writing(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, _ = self.bundle(root)
            (bundle / "payload/final_annotation/exports/A2.json").write_text("corrupted")
            with self.assertRaises(ValueError):
                restore(bundle, root / "checkout")
            self.assertFalse((root / "checkout").exists())

    def test_rejects_paths_outside_the_payload(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, _ = self.bundle(root)
            manifest = json.loads((bundle / "manifest.json").read_text())
            manifest["files"][0]["path"] = "../../outside.json"
            (bundle / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                verify(bundle)


if __name__ == "__main__":
    unittest.main()
