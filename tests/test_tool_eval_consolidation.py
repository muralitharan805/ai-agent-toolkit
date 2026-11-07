"""Safety regressions for existing evaluation and consolidation tools."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EVAL_SCRIPT = ROOT / "tools/generators/eval-skill/skills/scripts/run_evals.py"
SCAN_SCRIPT = (
    ROOT / "tools/generators/consolidate-agent-toolkit/skills/scripts/scan_duplicates.py"
)
SCHEMA = ROOT / "tools/generators/eval-skill/skills/assets/grading-schema.json"


def import_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


eval_runner = import_script("eval_runner_under_test", EVAL_SCRIPT)
duplicate_scanner = import_script("duplicate_scanner_under_test", SCAN_SCRIPT)


class ToolEvaluationTests(unittest.TestCase):
    def test_natural_language_file_keyword_does_not_auto_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "src" / "example.ts"
            file.parent.mkdir()
            file.write_text("export const example = 1;\n", encoding="utf-8")
            cases = [
                {
                    "id": 1,
                    "name": "Explicit evidence only",
                    "assertions": [
                        "The output follows every file-security convention",
                        "files_exist",
                    ],
                    "files": ["src/example.ts"],
                }
            ]
            with patch("os.getcwd", return_value=str(root)):
                report = eval_runner.run_evaluation(str(root / "skill"), cases)
            self.assertEqual(report["verdict"], "not_evaluated")
            self.assertEqual(report["benchmark"], None)
            self.assertEqual(report["deterministic_coverage_percent"], 50)
            self.assertEqual(
                [detail["status"] for detail in report["test_cases"][0]["details"]],
                ["not_evaluated", "verified"],
            )

    def test_missing_file_and_escape_path_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            outside = Path(tmp) / "not-in-workspace.md"
            outside.write_text("outside\n", encoding="utf-8")
            for files in (["src/absent.ts"], ["../not-in-workspace.md"]):
                ok, missing = eval_runner.evaluate_files_presence(str(root), files)
                self.assertFalse(ok)
                self.assertEqual(missing, files)
                with patch("os.getcwd", return_value=str(root)):
                    result = eval_runner.run_evaluation(
                        str(root / "skill"),
                        [{"id": "case", "assertions": ["files_exist"], "files": files}],
                    )
                self.assertEqual(result["verdict"], "failed")

    def test_cli_marks_unverified_real_evaluation_nonzero_but_dry_run_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "demo-skill"
            (skill / "evals").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: Demonstrates an evaluation\n---\n",
                encoding="utf-8",
            )
            (skill / "evals" / "evals.json").write_text(
                json.dumps({
                    "skill_name": "demo-skill",
                    "evals": [
                        {
                            "id": 1,
                            "prompt": "Generate a working form",
                            "expected_output": "Working form",
                            "assertions": ["Form uses strictly typed controls"],
                            "files": [],
                        },
                        {
                            "id": 2,
                            "prompt": "Add validation",
                            "expected_output": "Validated form",
                            "assertions": ["Validation errors are accessible"],
                            "files": [],
                        },
                    ],
                }),
                encoding="utf-8",
            )
            cmd = [sys.executable, str(EVAL_SCRIPT), str(skill), "--json"]
            run = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertEqual(json.loads(run.stdout)["verdict"], "not_evaluated")
            self.assertIsNone(json.loads(run.stdout)["benchmark"])

            dry = subprocess.run(cmd + ["--dry-run"], capture_output=True, text=True, cwd=root)
            self.assertEqual(dry.returncode, 0, dry.stderr)

    def test_grading_schema_matches_runner_output_keys(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertIn("deterministic_coverage_percent", required)
        self.assertIn("benchmark", required)
        self.assertEqual(schema["properties"]["benchmark"]["type"], "null")
        self.assertEqual(
            set(schema["properties"]["verdict"]["enum"]),
            {"verified", "failed", "not_evaluated"},
        )
        for k in ("verified_assertions", "failed_assertions", "not_evaluated_assertions"):
            self.assertIn(k, schema["properties"]["summary"]["required"])


class ToolConsolidationTests(unittest.TestCase):
    def test_parent_folder_named_tools_does_not_hide_consumer_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tools" / "workspace"
            skill = target / "frameworks" / "angular" / "demo" / "skills"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
            report = duplicate_scanner.scan_skills_and_rules(str(target))
            self.assertEqual(report["total_skills_scanned"], 1)

    def test_source_tools_directory_is_excluded_from_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "toolkit"
            actual = target / "shared" / "sample" / "skills"
            ignored = target / "tools" / "generators" / "internal" / "skills"
            actual.mkdir(parents=True)
            ignored.mkdir(parents=True)
            (actual / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            (ignored / "SKILL.md").write_text("# Ignore\n", encoding="utf-8")
            report = duplicate_scanner.scan_skills_and_rules(str(target))
            self.assertEqual(report["total_skills_scanned"], 1)

    def test_repeated_names_collect_skills_and_rules_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "toolkit"
            skill = target / "shared" / "demo" / "skills"
            rule_dir = target / "shared" / "demo" / "rules"
            skill.mkdir(parents=True)
            rule_dir.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
            (rule_dir / "demo.md").write_text("# Rule\n", encoding="utf-8")
            report = duplicate_scanner.scan_skills_and_rules(str(target))
            self.assertEqual(report["total_skills_scanned"], 1)
            self.assertEqual(report["total_rules_scanned"], 1)
            self.assertEqual(len(report["exact_duplicates"]["demo"]), 2)


if __name__ == "__main__":
    unittest.main()
