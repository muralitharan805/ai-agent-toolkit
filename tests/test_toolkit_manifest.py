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


    def test_shared_skill_records_multiple_tools_and_releases_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / ".agents"
            target = root / "skills" / "demo"
            source = tmp_path / "toolkit" / "demo" / "skills"
            target.mkdir(parents=True)
            source.mkdir(parents=True)
            (target / "SKILL.md").write_text("shared\n", encoding="utf-8")
            (source / "SKILL.md").write_text("shared\n", encoding="utf-8")
            for tool in ("antigravity", "codex", "codex"):
                toolkit_manifest.record(
                    root, "skills/demo", target, source, tmp_path / "toolkit",
                    kind="skill", scope="workspace", tool=tool,
                )

            manifest = toolkit_manifest.load_manifest(root)
            self.assertEqual(
                manifest["managed"]["skills/demo"]["tools"],
                ["antigravity", "codex"],
            )

            released = toolkit_manifest.clean(root, tool="codex")
            self.assertEqual(released["released"], ["skills/demo"])
            self.assertTrue(target.exists())
            after_release = toolkit_manifest.load_manifest(root)["managed"]["skills/demo"]
            self.assertEqual(after_release["tools"], ["antigravity"])
            self.assertEqual(after_release["tool"], "antigravity")

            last = toolkit_manifest.clean(root, tool="antigravity")
            self.assertEqual(last["removed"], ["skills/demo"])
            self.assertFalse(target.exists())

    def test_legacy_manifest_migrates_without_dropping_previous_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / ".agents"
            source = tmp_path / "toolkit" / "demo" / "skills"
            target = root / "skills" / "demo"
            source.mkdir(parents=True)
            target.mkdir(parents=True)
            (source / "SKILL.md").write_text("same\n", encoding="utf-8")
            (target / "SKILL.md").write_text("same\n", encoding="utf-8")

            # An existing v2 manifest has only a single tool property.
            toolkit_manifest.record(
                root, "skills/demo", target, source, tmp_path / "toolkit",
                kind="skill", scope="workspace", tool="codex",
            )
            legacy = toolkit_manifest.load_manifest(root)
            legacy["managed"]["skills/demo"].pop("tools")
            toolkit_manifest.save_manifest(root, legacy)

            toolkit_manifest.record(
                root, "skills/demo", target, source, tmp_path / "toolkit",
                kind="skill", scope="workspace", tool="antigravity",
            )
            upgraded = toolkit_manifest.load_manifest(root)["managed"]["skills/demo"]
            self.assertEqual(upgraded["tools"], ["codex", "antigravity"])

            # No other tool may remove the shared path.
            skipped = toolkit_manifest.clean(root, tool="claude")
            self.assertIn("skills/demo", skipped["skipped"])
            self.assertTrue(target.exists())

    def test_recording_a_different_source_does_not_inherit_tool_owners(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / ".agents"
            target = root / "skills" / "demo"
            source_a = tmp_path / "toolkit" / "source-a"
            source_b = tmp_path / "toolkit" / "source-b"
            target.mkdir(parents=True)
            source_a.mkdir(parents=True)
            source_b.mkdir(parents=True)
            (target / "SKILL.md").write_text("new content\n", encoding="utf-8")
            for tool, source in (("antigravity", source_a), ("codex", source_b)):
                toolkit_manifest.record(
                    root, "skills/demo", target, source, tmp_path / "toolkit",
                    kind="skill", scope="workspace", tool=tool,
                )
            manifest = toolkit_manifest.load_manifest(root)
            self.assertEqual(manifest["managed"]["skills/demo"]["tools"], ["codex"])


    def test_aggregate_sources_can_be_added_and_removed_by_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / ".gemini"
            toolkit = tmp_path / "toolkit"
            first = toolkit / "frameworks" / "angular" / "rules" / "one.md"
            second = toolkit / "shared" / "security" / "rules" / "two.md"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("one\n", encoding="utf-8")
            second.write_text("two\n", encoding="utf-8")

            added = toolkit_manifest.aggregate_add(
                root,
                "gemini_rules",
                [first, second],
                toolkit,
            )
            self.assertEqual(
                added["sources"],
                [
                    "frameworks/angular/rules/one.md",
                    "shared/security/rules/two.md",
                ],
            )

            removed = toolkit_manifest.aggregate_remove(
                root,
                "gemini_rules",
                source_prefixes=["frameworks/angular"],
            )
            self.assertEqual(removed["removed"], ["frameworks/angular/rules/one.md"])
            self.assertEqual(removed["sources"], ["shared/security/rules/two.md"])

if __name__ == "__main__":
    unittest.main()
