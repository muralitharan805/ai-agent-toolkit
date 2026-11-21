from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_SCRIPT = REPO_ROOT / "bin" / "context.sh"


def write_module(module: Path, *, body: str = "skill body", rule: str = "rule body") -> None:
    skill_dir = module / "skills"
    rule_dir = module / "rules"
    skill_dir.mkdir(parents=True, exist_ok=True)
    rule_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-module\ndescription: Demo context skill.\n---\n\n" + body + "\n",
        encoding="utf-8",
    )
    (rule_dir / "demo-rule.md").write_text(
        "---\ndescription: Demo rule.\ntrigger: always_on\n---\n\n" + rule + "\n",
        encoding="utf-8",
    )


class ContextV2IntegrationTests(unittest.TestCase):
    def run_context(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["bash", str(CONTEXT_SCRIPT), *args],
            cwd=REPO_ROOT,
            check=check,
            text=True,
            capture_output=True,
            env=merged_env,
        )

    def test_antigravity_workspace_syncs_skill_and_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            self.run_context("-w", str(source), "--target", str(target))

            self.assertTrue((target / ".agents" / "skills" / "demo-module" / "SKILL.md").is_file())
            self.assertTrue((target / ".agents" / "rules" / "demo-rule.md").is_file())
            manifest = json.loads(
                (target / ".agents" / ".toolkit-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], 2)
            self.assertEqual(manifest["managed"]["skills/demo-module"]["tool"], "antigravity")
            self.assertEqual(manifest["managed"]["skills/demo-module"]["scope"], "workspace")

    def test_codex_workspace_syncs_skills_and_project_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)
            target.mkdir()
            instructions = target / "AGENTS.md"
            user_text = b"# Project instructions\r\nKeep this text.\r\n"
            instructions.write_bytes(user_text)
            args = ("-w", "--tool", "codex", "--target", str(target))

            self.run_context(*args, str(source))

            self.assertTrue((target / ".agents" / "skills" / "demo-module" / "SKILL.md").is_file())
            self.assertFalse((target / ".agents" / "rules" / "demo-rule.md").exists())
            combined = instructions.read_bytes()
            self.assertTrue(combined.startswith(user_text))
            self.assertIn(b"rule body", combined)
            self.assertNotIn(b"trigger:", combined)
            self.run_context(*args, str(source))
            self.assertEqual(instructions.read_bytes(), combined)

            self.run_context(*args, str(source), "--clean")
            self.assertEqual(instructions.read_bytes(), user_text)
            self.assertFalse((target / ".agents" / "skills" / "demo-module").exists())

    def test_codex_rejects_invalid_markers_before_changing_managed_context(self) -> None:
        for scope in ("workspace", "global"):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "demo-module"
                target = root / "project"
                codex_home = root / "codex"
                home = root / "home"
                env = {"HOME": str(home), "CODEX_HOME": str(codex_home)}
                write_module(source)
                if scope == "workspace":
                    args = ("-w", "--tool", "codex", "--target", str(target))
                    instructions = target / "AGENTS.md"
                    skill_root = target / ".agents"
                else:
                    args = ("-g", "--tool", "codex")
                    instructions = codex_home / "AGENTS.md"
                    skill_root = home / ".agents"
                instructions.parent.mkdir(parents=True)
                invalid = b"<!-- AGENT_TOOLKIT_START -->\n"
                instructions.write_bytes(invalid)

                result = self.run_context(*args, str(source), env=env, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Invalid toolkit block markers", result.stderr)
                self.assertEqual(instructions.read_bytes(), invalid)
                manifest = skill_root / ".toolkit-manifest.json"
                skill = skill_root / "skills" / "demo-module" / "SKILL.md"
                self.assertFalse(manifest.exists())
                self.assertFalse(skill.exists())

                instructions.write_text("# User instructions\n", encoding="utf-8")
                self.run_context(*args, str(source), env=env)
                installed = skill.read_bytes()
                recorded = manifest.read_bytes()
                instructions.write_bytes(invalid)
                result = self.run_context(*args, "--clean", env=env, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Invalid toolkit block markers", result.stderr)
                self.assertEqual(skill.read_bytes(), installed)
                self.assertEqual(manifest.read_bytes(), recorded)
                self.assertEqual(instructions.read_bytes(), invalid)

    def test_claude_workspace_uses_claude_skill_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            self.run_context(
                "-w", str(source), "--tool", "claude", "--target", str(target)
            )

            self.assertTrue((target / ".claude" / "skills" / "demo-module" / "SKILL.md").is_file())
            self.assertFalse((target / ".agents").exists())

    def test_cleanup_removes_only_managed_content_and_preserves_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            self.run_context("-w", str(source), "--target", str(target))
            managed_skill = target / ".agents" / "skills" / "demo-module" / "SKILL.md"
            managed_skill.write_text(managed_skill.read_text(encoding="utf-8") + "local edit\n", encoding="utf-8")
            unmanaged = target / ".agents" / "skills" / "company-skill"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("user owned\n", encoding="utf-8")

            result = self.run_context("-w", "--target", str(target), "--clean")

            self.assertTrue(managed_skill.exists())
            self.assertTrue((unmanaged / "SKILL.md").exists())
            self.assertFalse((target / ".agents" / "rules" / "demo-rule.md").exists())
            self.assertIn("preserved locally modified skills/demo-module", result.stdout)

            self.run_context("-w", "--target", str(target), "--force-clean")
            self.assertFalse((target / ".agents" / "skills" / "demo-module").exists())
            self.assertTrue((unmanaged / "SKILL.md").exists())

    def test_codex_cleanup_preserves_skill_still_used_by_antigravity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            self.run_context("-w", str(source), "--tool", "antigravity", "--target", str(target))
            self.run_context("-w", str(source), "--tool", "codex", "--target", str(target))

            rule = target / ".agents" / "rules" / "demo-rule.md"
            skill = target / ".agents" / "skills" / "demo-module"
            manifest_path = target / ".agents" / ".toolkit-manifest.json"
            self.assertTrue(rule.exists())
            self.assertTrue(skill.exists())
            managed = json.loads(manifest_path.read_text(encoding="utf-8"))["managed"]
            self.assertEqual(managed["skills/demo-module"]["tools"], ["antigravity", "codex"])

            codex_clean = self.run_context("-w", "--tool", "codex", "--target", str(target), "--clean")
            self.assertIn("released skills/demo-module", codex_clean.stdout)
            self.assertTrue(rule.exists())
            self.assertTrue(skill.exists())
            managed = json.loads(manifest_path.read_text(encoding="utf-8"))["managed"]
            self.assertEqual(managed["skills/demo-module"]["tools"], ["antigravity"])
            self.assertEqual(managed["rules/demo-rule.md"]["tools"], ["antigravity"])

            # The last owner's cleanup may now remove the shared skill.
            self.run_context("-w", "--tool", "antigravity", "--target", str(target), "--clean")
            self.assertFalse(rule.exists())
            self.assertFalse(skill.exists())

    def test_shared_skill_survives_until_all_three_tools_release_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            self.run_context("-w", str(source), "--tool", "antigravity", "--target", str(target))
            self.run_context("-w", str(source), "--tool", "codex", "--target", str(target))

            self.run_context("-w", str(source), "--tool", "cursor", "--target", str(target))

            rule = target / ".agents" / "rules" / "demo-rule.md"
            skill = target / ".agents" / "skills" / "demo-module"
            manifest_path = target / ".agents" / ".toolkit-manifest.json"

            antigravity_clean = self.run_context(
                "-w", "--tool", "antigravity", "--target", str(target), "--clean"
            )
            self.assertIn("released skills/demo-module", antigravity_clean.stdout)
            self.assertTrue(skill.exists())
            self.assertFalse(rule.exists())
            managed = json.loads(manifest_path.read_text(encoding="utf-8"))["managed"]
            self.assertEqual(managed["skills/demo-module"]["tools"], ["codex", "cursor"])
            self.assertEqual(managed["skills/demo-module"]["tool"], "cursor")

            self.run_context("-w", "--tool", "codex", "--target", str(target), "--clean")
            self.assertTrue(skill.exists())

            self.run_context("-w", "--tool", "cursor", "--target", str(target), "--clean")
            self.assertFalse(skill.exists())

    def test_cleaning_one_tool_does_not_affect_other_tool_modified_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)
            self.run_context("-w", str(source), "--tool", "antigravity", "--target", str(target))
            self.run_context("-w", str(source), "--tool", "codex", "--target", str(target))

            skill_file = target / ".agents" / "skills" / "demo-module" / "SKILL.md"
            skill_file.write_text(skill_file.read_text(encoding="utf-8") + "user edit\n", encoding="utf-8")
            self.run_context("-w", "--tool", "codex", "--target", str(target), "--force-clean")
            self.assertTrue(skill_file.exists())
            self.assertIn("user edit", skill_file.read_text(encoding="utf-8"))

            # With only Antigravity remaining, normal cleanup protects modifications.
            normal = self.run_context("-w", "--tool", "antigravity", "--target", str(target), "--clean")
            self.assertIn("preserved locally modified", normal.stdout)
            self.assertTrue(skill_file.exists())

    def test_cursor_global_is_rejected(self) -> None:
        result = self.run_context("-g", "--tool", "cursor", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Global context is supported for antigravity and codex", result.stderr)

    def test_codex_global_sync_and_selective_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            codex_home = root / "custom-codex"
            codex_home.mkdir()
            env = {"HOME": str(home), "CODEX_HOME": str(codex_home)}
            instructions = codex_home / "AGENTS.md"
            user_prefix = b"# My instructions\r\n\r\nUse tabs.  \r\n"
            user_suffix = b"\nRun tests before reporting results.  \n"
            instructions.write_bytes(user_prefix)
            first, second = root / "first", root / "second"
            write_module(first, rule="FIRST RULE")
            write_module(second, rule="SECOND RULE")
            args = ("-g", "--tool", "codex")

            self.run_context(*args, str(first), str(second), env=env)
            combined = instructions.read_bytes()
            self.assertTrue(combined.startswith(user_prefix))
            self.assertIn(b"FIRST RULE", combined)
            self.assertIn(b"SECOND RULE", combined)
            self.assertNotIn(b"trigger:", combined)
            self.assertEqual(combined.count(b"<!-- AGENT_TOOLKIT_START -->"), 1)
            self.assertFalse((home / ".gemini").exists())
            self.assertFalse((home / ".codex").exists())
            skills = home / ".agents" / "skills"
            self.assertTrue((skills / "first" / "SKILL.md").is_file())
            self.assertTrue((skills / "second" / "SKILL.md").is_file())

            instructions.write_bytes(combined + user_suffix)
            self.run_context(*args, str(first), str(second), env=env)
            self.assertEqual(instructions.read_bytes(), combined + user_suffix)

            invalid = self.run_context(*args, "--clean", "nonexistent-module", env=env, check=False)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(instructions.read_bytes(), combined + user_suffix)

            self.run_context(*args, "--clean", str(first), env=env)
            self.assertNotIn(b"FIRST RULE", instructions.read_bytes())
            self.assertIn(b"SECOND RULE", instructions.read_bytes())
            self.assertFalse((skills / "first").exists())
            self.assertTrue((skills / "second").exists())

            self.run_context(*args, "--clean", env=env)
            self.assertEqual(instructions.read_bytes(), user_prefix + user_suffix)
            self.assertFalse((skills / "second").exists())

    def test_antigravity_global_rules_are_tagged_and_cleanup_preserves_user_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            home = root / "home"
            gemini_dir = home / ".gemini"
            gemini_dir.mkdir(parents=True)
            gemini_md = gemini_dir / "GEMINI.md"
            gemini_md.write_text("USER CONTENT\n", encoding="utf-8")
            write_module(source)

            self.run_context(
                "-g",
                str(source),
                "--tool",
                "antigravity",
                env={"HOME": str(home)},
            )

            content = gemini_md.read_text(encoding="utf-8")
            self.assertIn("USER CONTENT", content)
            self.assertIn("<!-- AGENT_TOOLKIT_START -->", content)
            self.assertIn("rule body", content)
            self.assertTrue(
                (home / ".gemini" / "config" / "skills" / "demo-module" / "SKILL.md").is_file()
            )

            self.run_context(
                "-g",
                "--tool",
                "antigravity",
                "--clean",
                env={"HOME": str(home)},
            )

            cleaned = gemini_md.read_text(encoding="utf-8")
            self.assertEqual(cleaned.strip(), "USER CONTENT")
            self.assertFalse(
                (home / ".gemini" / "config" / "skills" / "demo-module").exists()
            )

    def test_antigravity_selective_global_cleanup_keeps_other_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            home.mkdir(parents=True)

            first = root / "first"
            second = root / "second"
            write_module(first, rule="FIRST RULE")
            write_module(second, rule="SECOND RULE")

            self.run_context("-g", str(first), env={"HOME": str(home)})
            self.run_context("-g", str(second), env={"HOME": str(home)})

            gemini_md = home / ".gemini" / "GEMINI.md"
            combined = gemini_md.read_text(encoding="utf-8")
            self.assertIn("FIRST RULE", combined)
            self.assertIn("SECOND RULE", combined)

            self.run_context(
                "-g",
                str(first),
                "--clean",
                env={"HOME": str(home)},
            )

            remaining = gemini_md.read_text(encoding="utf-8")
            self.assertNotIn("FIRST RULE", remaining)
            self.assertIn("SECOND RULE", remaining)

    def test_dynamic_tools_family_selector_is_explicitly_resolvable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "toolkit-dev"
            self.run_context(
                "-w",
                "generators/generate-skill",
                "--target",
                str(target),
            )
            self.assertTrue(
                (target / ".agents" / "skills" / "generate-skill" / "SKILL.md").is_file()
            )

    def test_shorthand_selector_resolves_under_frameworks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "project"
            self.run_context(
                "-w",
                "angular/angular-enterprise-forms",
                "--target",
                str(target),
            )
            self.assertTrue(
                (target / ".agents" / "skills" / "angular-enterprise-forms" / "SKILL.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
