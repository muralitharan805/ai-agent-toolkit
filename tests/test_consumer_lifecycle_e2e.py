"""End-to-end consumer journeys using the repository's real context catalog.

These tests run bin/context.sh against isolated app folders, not synthetic
toolkit modules, so a fresh checkout verifies the public README flow.
Actual Antigravity/Codex/Claude agent invocation still needs manual testing.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "bin" / "context.sh"
ANGULAR_MODULE = "frameworks/angular/angular-enterprise-forms"
ANGULAR_NAME = "angular-enterprise-forms"
ANOTHER_MODULE = "shared/ai-agent-toolkit"


def workspace_root(target: Path, tool: str) -> Path:
    return target / (".claude" if tool == "claude" else ".agents")


class ConsumerLifecycleEndToEndTests(unittest.TestCase):
    def run_sync(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"context.sh failed: {result.args}\n{result.stdout}\n{result.stderr}",
        )
        return result

    def test_real_angular_context_install_resync_protection_and_cleanup(self) -> None:
        for tool in ("antigravity", "codex", "claude"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "consumer-app"
                target.mkdir()
                app_file = target / "app-owned-file.txt"
                app_file.write_text("consumer content\n", encoding="utf-8")
                context_root = workspace_root(target, tool)

                self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool, "--target", str(target)
                )

                skill_dir = context_root / "skills" / ANGULAR_NAME
                installed_skill = skill_dir / "SKILL.md"
                self.assertTrue(installed_skill.is_file())
                self.assertEqual(
                    installed_skill.read_bytes(),
                    (REPO_ROOT / ANGULAR_MODULE / "skills" / "SKILL.md").read_bytes(),
                )
                self.assertTrue(
                    (skill_dir / "references" / "typed-forms-and-cva-patterns.md").is_file()
                )
                rule = context_root / "rules" / "angular-enterprise-forms-rules.md"
                self.assertEqual(rule.is_file(), tool == "antigravity")

                manifest_file = context_root / ".toolkit-manifest.json"
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                self.assertEqual(manifest["version"], 2)
                managed = manifest["managed"][f"skills/{ANGULAR_NAME}"]
                self.assertEqual(managed["source"], f"{ANGULAR_MODULE}/skills")
                self.assertEqual(managed["kind"], "skill")
                self.assertEqual(managed["tool"], tool)

                # Running the same command twice must preserve the installed content.
                baseline_bytes = installed_skill.read_bytes()
                self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool, "--target", str(target)
                )
                self.assertEqual(baseline_bytes, installed_skill.read_bytes())

                # User changes inside a managed skill must survive both re-sync
                # and ordinary cleanup, even when the source skill still exists.
                modified_bytes = baseline_bytes + b"\n# Consumer customisation\n"
                installed_skill.write_bytes(modified_bytes)
                result = self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool, "--target", str(target)
                )
                self.assertIn("Local modifications detected", result.stdout)
                self.assertEqual(modified_bytes, installed_skill.read_bytes())

                self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool,
                    "--target", str(target), "--clean",
                )
                self.assertEqual(modified_bytes, installed_skill.read_bytes())
                self.assertFalse(rule.exists())
                self.assertEqual(app_file.read_text(encoding="utf-8"), "consumer content\n")

                # Force cleanup is safe to verify only within this disposable
                # target; it intentionally discards the modified toolkit skill.
                self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool,
                    "--target", str(target), "--force-clean",
                )
                self.assertFalse(skill_dir.exists())
                self.assertTrue(app_file.is_file())

    def test_unmanaged_existing_skill_is_never_replaced_or_removed_by_default(self) -> None:
        for tool in ("antigravity", "codex", "claude"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "consumer-app"
                context_root = workspace_root(target, tool)
                skill = context_root / "skills" / ANGULAR_NAME
                skill.mkdir(parents=True)
                private_file = skill / "SKILL.md"
                private_file.write_text("user-owned local instructions\n", encoding="utf-8")

                result = self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool, "--target", str(target)
                )
                self.assertIn("Protected existing unmanaged", result.stdout)
                self.assertEqual(
                    private_file.read_text(encoding="utf-8"),
                    "user-owned local instructions\n",
                )

                manifest_file = context_root / ".toolkit-manifest.json"
                if manifest_file.exists():
                    managed = json.loads(
                        manifest_file.read_text(encoding="utf-8")
                    )["managed"]
                    self.assertNotIn(f"skills/{ANGULAR_NAME}", managed)

                self.run_sync(
                    "-w", ANGULAR_MODULE, "--tool", tool,
                    "--target", str(target), "--clean",
                )
                self.assertTrue(private_file.exists())

    def test_selective_cleanup_only_removes_selected_managed_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "consumer-app"
            self.run_sync(
                "-w", ANGULAR_MODULE, "--tool", "antigravity",
                "--target", str(target),
            )
            self.run_sync(
                "-w", ANOTHER_MODULE, "--tool", "antigravity",
                "--target", str(target),
            )

            skills = target / ".agents" / "skills"
            self.assertTrue((skills / ANGULAR_NAME / "SKILL.md").exists())
            self.assertTrue((skills / "ai-agent-toolkit" / "SKILL.md").exists())

            self.run_sync(
                "-w", ANGULAR_MODULE, "--tool", "antigravity",
                "--target", str(target), "--clean",
            )
            self.assertFalse((skills / ANGULAR_NAME).exists())
            self.assertTrue((skills / "ai-agent-toolkit" / "SKILL.md").exists())
            manifest = json.loads(
                (target / ".agents" / ".toolkit-manifest.json").read_text(encoding="utf-8")
            )
            self.assertIn("skills/ai-agent-toolkit", manifest["managed"])
            self.assertNotIn(f"skills/{ANGULAR_NAME}", manifest["managed"])


if __name__ == "__main__":
    unittest.main()
