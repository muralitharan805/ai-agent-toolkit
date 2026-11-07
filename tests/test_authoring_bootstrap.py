"""Fresh-workspace bootstrap checks for the canonical authoring toolchain.

Uses the shipped context.sh without setup scripts or a new installer.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_SCRIPT = ROOT / "bin" / "context.sh"
AUTHORING_SELECTORS = (
    "tools/generators/generate-agent-suite",
    "tools/generators/generate-skill",
    "tools/generators/generate-rule",
    "shared/ai-agent-toolkit",
)
SKILL_NAMES = (
    "generate-agent-suite",
    "generate-skill",
    "generate-rule",
    "ai-agent-toolkit",
)


class AuthoringBootstrapTests(unittest.TestCase):
    def run_sync(self, tool: str, target: Path) -> None:
        result = subprocess.run(
            [
                "bash", str(CONTEXT_SCRIPT), "-w",
                *AUTHORING_SELECTORS, "--tool", tool, "--target", str(target),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)

    def test_installed_authoring_skill_links_and_companions(self) -> None:
        for tool in ("antigravity", "codex", "claude"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)
                skill_root = target / (".claude" if tool == "claude" else ".agents") / "skills"

                self.run_sync(tool, target)
                for name in SKILL_NAMES:
                    with self.subTest(tool=tool, skill=name):
                        skill_dir = skill_root / name
                        skill_file = skill_dir / "SKILL.md"
                        self.assertTrue(skill_file.is_file(), f"Missing {skill_file}")
                        content = skill_file.read_text(encoding="utf-8")
                        # Check actual Markdown links, not fictional paths inside
                        # fenced scaffold examples (including quadruple-backtick blocks).
                        in_fence = False
                        fence_width = 0
                        for line in content.splitlines():
                            trimmed = line.lstrip()
                            ticks = len(trimmed) - len(trimmed.lstrip("`"))
                            if ticks >= 3:
                                if not in_fence:
                                    in_fence, fence_width = True, ticks
                                elif ticks >= fence_width:
                                    in_fence, fence_width = False, 0
                                continue
                            if in_fence:
                                continue
                            for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", line):
                                if "://" in link or link.startswith(("#", "mailto:")):
                                    continue
                                destination = link.split("#", 1)[0]
                                self.assertTrue(
                                    (skill_dir / destination).exists(),
                                    f"{name} has broken installed link {link!r} for {tool}",
                                )

                main = (skill_root / "generate-agent-suite" / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("../generate-skill/SKILL.md", main)
                self.assertIn("../generate-rule/SKILL.md", main)
                self.assertIn("directly CREATE or UPDATE", main)

                if tool == "antigravity":
                    self.assertTrue(
                        (target / ".agents" / "rules" / "ai-toolkit-authoring-rules.md").is_file()
                    )
                    # Running the same sync twice must be safe and preserve installed content.
                    before = (skill_root / "generate-agent-suite" / "SKILL.md").read_bytes()
                    self.run_sync(tool, target)
                    self.assertEqual(
                        before, (skill_root / "generate-agent-suite" / "SKILL.md").read_bytes()
                    )
                else:
                    self.assertFalse(
                        (target / (".claude" if tool == "claude" else ".agents") / "rules").exists()
                    )


if __name__ == "__main__":
    unittest.main()
