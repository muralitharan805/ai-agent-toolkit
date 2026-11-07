from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_SCRIPT = REPO_ROOT / "bin" / "context.sh"


def write_skill(path: Path, body: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo skill used by safe sync tests.\n---\n\n" + body + "\n",
        encoding="utf-8",
    )


class SafeSyncIntegrationTests(unittest.TestCase):
    def run_sync(self, source: Path, target: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(CONTEXT_SCRIPT), "-w", str(source), "--target", str(target), *extra],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_unmanaged_existing_skill_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source" / "demo-skill"
            target = root / "project"
            installed = target / ".agents" / "skills" / "demo-skill"

            write_skill(source, "toolkit")
            write_skill(installed, "user-owned")

            result = self.run_sync(source, target)

            self.assertIn("Protected existing unmanaged demo-skill", result.stdout)
            self.assertIn("user-owned", (installed / "SKILL.md").read_text(encoding="utf-8"))

            manifest_path = target / ".agents" / ".toolkit-manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertNotIn("skills/demo-skill", manifest.get("managed", {}))

    def test_force_can_intentionally_take_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source" / "demo-skill"
            target = root / "project"
            installed = target / ".agents" / "skills" / "demo-skill"

            write_skill(source, "toolkit")
            write_skill(installed, "user-owned")

            self.run_sync(source, target, "--force")

            self.assertIn("toolkit", (installed / "SKILL.md").read_text(encoding="utf-8"))
            manifest = json.loads(
                (target / ".agents" / ".toolkit-manifest.json").read_text(encoding="utf-8")
            )
            self.assertIn("skills/demo-skill", manifest["managed"])

    def test_local_changes_to_managed_skill_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source" / "demo-skill"
            target = root / "project"
            installed = target / ".agents" / "skills" / "demo-skill"

            write_skill(source, "version-one")
            self.run_sync(source, target)

            write_skill(installed, "local-edit")
            write_skill(source, "version-two")

            result = self.run_sync(source, target)

            self.assertIn("Local modifications detected in demo-skill", result.stdout)
            self.assertIn("local-edit", (installed / "SKILL.md").read_text(encoding="utf-8"))

    def test_identical_legacy_copy_is_adopted_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source" / "demo-skill"
            target = root / "project"
            installed = target / ".agents" / "skills" / "demo-skill"

            write_skill(source, "same-content")
            write_skill(installed, "same-content")

            result = self.run_sync(source, target)

            self.assertIn("Adopted existing identical demo-skill", result.stdout)
            manifest = json.loads(
                (target / ".agents" / ".toolkit-manifest.json").read_text(encoding="utf-8")
            )
            self.assertIn("skills/demo-skill", manifest["managed"])


if __name__ == "__main__":
    unittest.main()
