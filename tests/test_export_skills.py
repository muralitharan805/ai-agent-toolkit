#!/usr/bin/env python3
"""
Unit and integration tests for export_skills.py and Dual-Mode export functionality.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "tools" / "packagers" / "export-skills" / "skills" / "scripts" / "export_skills.py"
CONTEXT_SH = REPO_ROOT / "bin" / "context.sh"


class TestExportSkills(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "skills"
        self.prompt_dir = Path(self.temp_dir.name) / "prompts"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_zip_chatgpt_and_gemini_layout(self):
        """Verifies zip archives adhere to ChatGPT and Gemini structural specifications."""
        cmd = [
            "python3",
            str(SCRIPT_PATH),
            "shared/thanglish-mentor-persona",
            "--tool",
            "both",
            "--mode",
            "zip",
            "--out",
            str(self.out_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"export_skills failed: {res.stderr}")

        chatgpt_zip = self.out_dir / "chatgpt-thanglish-mentor-persona.zip"
        gemini_zip = self.out_dir / "gemini-thanglish-mentor-persona.zip"

        self.assertTrue(chatgpt_zip.is_file(), "ChatGPT zip archive was not created")
        self.assertTrue(gemini_zip.is_file(), "Gemini zip archive was not created")

        # Verify ChatGPT layout: <skill-name>/SKILL.md, agents/openai.yaml, assets/icon.svg
        with zipfile.ZipFile(chatgpt_zip, "r") as zf:
            names = set(zf.namelist())
            self.assertIn("thanglish-mentor-persona/SKILL.md", names)
            self.assertIn("thanglish-mentor-persona/agents/openai.yaml", names)
            self.assertIn("thanglish-mentor-persona/assets/icon.svg", names)

        # Verify Gemini layout: SKILL.md directly at root
        with zipfile.ZipFile(gemini_zip, "r") as zf:
            names = set(zf.namelist())
            self.assertIn("SKILL.md", names)
            self.assertNotIn("thanglish-mentor-persona/SKILL.md", names)

    def test_export_prompt_structure_and_tags(self):
        """Verifies prompt generation produces valid XML tags and knowledge references."""
        cmd = [
            "python3",
            str(SCRIPT_PATH),
            "shared/thanglish-mentor-persona",
            "--tool",
            "both",
            "--mode",
            "prompt",
            "--prompt-out",
            str(self.prompt_dir),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"export_skills failed: {res.stderr}")

        chatgpt_md = self.prompt_dir / "chatgpt-thanglish-mentor-persona.md"
        gemini_md = self.prompt_dir / "gemini-thanglish-mentor-persona.md"

        self.assertTrue(chatgpt_md.is_file(), "ChatGPT prompt markdown file was not created")
        self.assertTrue(gemini_md.is_file(), "Gemini prompt markdown file was not created")

        content = chatgpt_md.read_text(encoding="utf-8")
        self.assertIn("<role>", content)
        self.assertIn("</role>", content)
        self.assertIn("<instructions>", content)
        self.assertIn("</instructions>", content)
        self.assertIn("<knowledge_references>", content)

    def test_dual_mode_both_generates_all_artifacts(self):
        """Verifies --mode both produces both zip archives and markdown prompt files."""
        cmd = [
            "python3",
            str(SCRIPT_PATH),
            "shared/thanglish-mentor-persona",
            "--tool",
            "both",
            "--mode",
            "both",
            "--out",
            str(self.out_dir),
            "--prompt-out",
            str(self.prompt_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"export_skills failed: {res.stderr}")

        self.assertTrue((self.out_dir / "chatgpt-thanglish-mentor-persona.zip").is_file())
        self.assertTrue((self.out_dir / "gemini-thanglish-mentor-persona.zip").is_file())
        self.assertTrue((self.prompt_dir / "chatgpt-thanglish-mentor-persona.md").is_file())
        self.assertTrue((self.prompt_dir / "gemini-thanglish-mentor-persona.md").is_file())

    def test_strict_budget_failure(self):
        """Verifies --strict-budget flags oversized prompts with exit code 2."""
        cmd = [
            "python3",
            str(SCRIPT_PATH),
            "shared/thanglish-mentor-persona",
            "--tool",
            "chatgpt",
            "--mode",
            "prompt",
            "--strict-budget",
            "--prompt-out",
            str(self.prompt_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 2, "Expected exit code 2 on strict budget failure")
        self.assertIn("exceeds ChatGPT 8,000 character limit", res.stderr)

    def test_clipboard_fallback_handling(self):
        """Verifies clipboard flag handles absence of clipboard tools gracefully."""
        cmd = [
            "python3",
            str(SCRIPT_PATH),
            "shared/thanglish-mentor-persona",
            "--tool",
            "chatgpt",
            "--mode",
            "prompt",
            "--copy",
            "--prompt-out",
            str(self.prompt_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"export_skills with --copy failed: {res.stderr}")
        self.assertIn("[Clipboard]", res.stderr)

    def test_context_sh_prompt_shortcut(self):
        """Verifies bin/context.sh -P shortcut executes correctly."""
        cmd = [
            str(CONTEXT_SH),
            "-P",
            "shared/thanglish-mentor-persona",
            "--prompt-out",
            str(self.prompt_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"bin/context.sh -P failed: {res.stderr}")
        self.assertTrue((self.prompt_dir / "chatgpt-thanglish-mentor-persona.md").is_file())


if __name__ == "__main__":
    unittest.main()
