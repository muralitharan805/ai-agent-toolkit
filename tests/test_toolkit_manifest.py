from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "toolkit_manifest.py"
SPEC = importlib.util.spec_from_file_location("toolkit_manifest", MODULE_PATH)
assert SPEC and SPEC.loader
toolkit_manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(toolkit_manifest)


class ToolkitManifestTests(unittest.TestCase):
    def test_missing_target_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agents"
            target = root / "skills" / "demo"
            result = toolkit_manifest.status(root, "skills/demo", target, None)
            self.assertEqual(result["status"], "missing")

    def test_existing_unmanaged_target_is_protected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agents"
            target = root / "skills" / "demo"
            source = Path(tmp) / "source"
            target.mkdir(parents=True)
            source.mkdir()
            (target / "SKILL.md").write_text("user version\n", encoding="utf-8")
            (source / "SKILL.md").write_text("toolkit version\n", encoding="utf-8")

            result = toolkit_manifest.status(root, "skills/demo", target, source)
            self.assertEqual(result["status"], "unmanaged")

    def test_identical_pre_manifest_target_is_adoptable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agents"
            target = root / "skills" / "demo"
            source = Path(tmp) / "source"
            target.mkdir(parents=True)
            source.mkdir()
            (target / "SKILL.md").write_text("same\n", encoding="utf-8")
            (source / "SKILL.md").write_text("same\n", encoding="utf-8")

            result = toolkit_manifest.status(root, "skills/demo", target, source)
            self.assertEqual(result["status"], "adoptable")

    def test_recorded_target_becomes_clean_then_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / ".agents"
            target = root / "skills" / "demo"
            source = tmp_path / "toolkit" / "skills" / "demo"
            target.mkdir(parents=True)
            source.mkdir(parents=True)
            (target / "SKILL.md").write_text("managed\n", encoding="utf-8")
            (source / "SKILL.md").write_text("managed\n", encoding="utf-8")

            toolkit_manifest.record(
                root,
                "skills/demo",
                target,
                source,
                tmp_path / "toolkit",
            )

            clean = toolkit_manifest.status(root, "skills/demo", target, source)
            self.assertEqual(clean["status"], "clean")

            manifest = json.loads((root / ".toolkit-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["managed"]["skills/demo"]["source"], "skills/demo")

            (target / "SKILL.md").write_text("locally edited\n", encoding="utf-8")
            modified = toolkit_manifest.status(root, "skills/demo", target, source)
            self.assertEqual(modified["status"], "modified")


if __name__ == "__main__":
    unittest.main()
