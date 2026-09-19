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

    def test_codex_workspace_syncs_skills_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            result = self.run_context(
                "-w", str(source), "--tool", "codex", "--target", str(target)
            )

            self.assertTrue((target / ".agents" / "skills" / "demo-module" / "SKILL.md").is_file())
            self.assertFalse((target / ".agents" / "rules" / "demo-rule.md").exists())
            self.assertIn("skipping rule", result.stdout)

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

    def test_codex_cleanup_does_not_remove_antigravity_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo-module"
            target = root / "project"
            write_module(source)

            self.run_context("-w", str(source), "--tool", "antigravity", "--target", str(target))
            self.run_context("-w", str(source), "--tool", "codex", "--target", str(target))

            rule = target / ".agents" / "rules" / "demo-rule.md"
            skill = target / ".agents" / "skills" / "demo-module"
            self.assertTrue(rule.exists())
            self.assertTrue(skill.exists())

            self.run_context("-w", "--tool", "codex", "--target", str(target), "--clean")

            self.assertTrue(rule.exists())
            self.assertFalse(skill.exists())

    def test_codex_global_is_rejected(self) -> None:
        result = self.run_context("-g", "--tool", "codex", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Global context is currently supported only for antigravity", result.stderr)

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
