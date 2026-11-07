"""Ensure copied vendor docs are not silently redistributed or referenced.

These checks cover the current checkout only; historical Git commits require
separate privacy and licensing review before making the repo public.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "reference-specs"

REMOVED_ANTIGRAVITY_FILES = (
    "antigravity-ide-hooks.md",
    "antigravity-ide-mcp.md",
    "antigravity-ide-migrating-from-Workflows-to-skills.md",
    "antigravity-ide-plugin.ini",
    "antigravity-ide-rules.md",
    "antigravity-ide-skills.md",
    "antigravity-ide-workflows.md",
)


class ReferenceDocumentationTests(unittest.TestCase):
    def test_licensed_agent_skills_snapshots_have_attribution(self):
        index = (REFERENCE_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("CC BY 4.0", index)
        self.assertIn("https://creativecommons.org/licenses/by/4.0/", index)
        self.assertIn("https://github.com/agentskills/agentskills", index)

    def test_no_copied_antigravity_docs_in_current_tree(self):
        for name in REMOVED_ANTIGRAVITY_FILES:
            with self.subTest(name=name):
                self.assertFalse((REFERENCE_DIR / name).exists())

    def test_no_stale_local_links_to_removed_antigravity_docs(self):
        excluded_parts = {".git", ".agents", ".claude", "__pycache__", ".pytest_cache", ".venv", "node_modules"}
        suffixes = {".md", ".mdx", ".txt", ".py", ".json", ".yaml", ".yml", ".ini", ".sh", ".ts"}
        stale = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            if set(path.relative_to(ROOT).parts) & excluded_parts:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "docs/reference-specs/antigravity-ide-" in content:
                stale.append(str(path.relative_to(ROOT)))
            elif any(name in content for name in REMOVED_ANTIGRAVITY_FILES):
                stale.append(str(path.relative_to(ROOT)))
        self.assertEqual([], stale, f"Stale local references: {stale}")


if __name__ == "__main__":
    unittest.main()
