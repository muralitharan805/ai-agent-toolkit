"""Regression checks for existing toolkit authoring and audit tools.

Antigravity rules: https://antigravity.google/docs/rules
Antigravity workflows: https://antigravity.google/docs/migration/workflows-to-skills
"""

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
RULE_VALIDATOR = (
    ROOT / "tools/generators/generate-rule/skills/scripts/validate_rule.py"
)
AUDIT_TOOL = (
    ROOT / "tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py"
)


def import_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rule_validator = import_script("rule_validator_under_test", RULE_VALIDATOR)
audit_toolkit = import_script("toolkit_audit_under_test", AUDIT_TOOL)


def rule_content(
    trigger: str = "glob",
    glob_field: str = 'globs: "**/*.ts, **/*.tsx"',
    description: bool = True,
    extra: str = "",
) -> str:
    fm = [
        "---",
        f"trigger: {trigger}",
    ]
    if description:
        fm.append("description: TypeScript rule activation examples for workspace changes")
    if trigger == "glob":
        fm.append(glob_field)
    fm.extend(["framework_version: Angular 20", "last_verified_date: 2026-11-07", "---"])
    return "\n".join(fm) + "\n# Example\n\n## Description\nCheck source.\n\n## Constraints\n- Prefer tests.\n\n## Examples\n- Good.\n" + extra


class ToolSpecAlignmentTests(unittest.TestCase):
    def test_glob_string_and_singular_alias_are_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "example.md"
            for glob_field in ('globs: "**/*.ts, **/*.tsx"', 'glob: "*.py, *_test.py"'):
                target.write_text(rule_content(glob_field=glob_field), encoding="utf-8")
                result = rule_validator.validate_rule_file(str(target))
                self.assertTrue(result["valid"], result["errors"])
                self.assertTrue(result["stats"]["has_globs"])

    def test_yaml_array_glob_is_not_documented_antigravity_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "invalid.md"
            target.write_text(
                rule_content(glob_field='globs: ["**/*.ts", "**/*.tsx"]'), encoding="utf-8"
            )
            result = rule_validator.validate_rule_file(str(target))
            self.assertFalse(result["valid"])
            self.assertTrue(any("comma-separated string" in e for e in result["errors"]))

    def test_description_required_for_model_decision_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "description.md"
            target.write_text(
                rule_content(trigger="model_decision", description=False), encoding="utf-8"
            )
            model_result = rule_validator.validate_rule_file(str(target))
            self.assertFalse(model_result["valid"])
            self.assertTrue(any("description" in e for e in model_result["errors"]))
            target.write_text(
                rule_content(trigger="always_on", description=False), encoding="utf-8"
            )
            always_result = rule_validator.validate_rule_file(str(target))
            self.assertTrue(always_result["valid"], always_result["errors"])
            self.assertTrue(any("description" in w for w in always_result["warnings"]))

    def test_utf8_byte_limit_is_distinct_from_toolkit_char_recommendation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "byte-rule.md"
            # Over old 12k-char ceiling, under current Antigravity 24k-byte limit.
            target.write_text(
                rule_content(trigger="always_on", extra="x" * 12_300), encoding="utf-8"
            )
            under_limit = rule_validator.validate_rule_file(str(target))
            self.assertTrue(under_limit["valid"], under_limit["errors"])
            self.assertGreater(under_limit["stats"]["char_count"], 12_000)
            self.assertTrue(under_limit["warnings"])

            # Multibyte UTF-8 characters must be counted as bytes.
            target.write_text(
                rule_content(trigger="always_on", extra="é" * 12_100), encoding="utf-8"
            )
            over_limit = rule_validator.validate_rule_file(str(target))
            self.assertFalse(over_limit["valid"])
            self.assertGreater(over_limit["stats"]["byte_count"], 24_000)

    def test_audit_strict_fails_warnings_that_normal_audit_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            rules = target / "rules"
            rules.mkdir()
            (rules / "verbose.md").write_text(
                rule_content(trigger="always_on", extra="x" * 8_500), encoding="utf-8"
            )
            base_cmd = [sys.executable, str(AUDIT_TOOL), str(target), "--json"]
            normal = subprocess.run(base_cmd, capture_output=True, text=True)
            self.assertEqual(normal.returncode, 0, normal.stderr)
            result = json.loads(normal.stdout)
            self.assertTrue(result["overall_pass"])
            self.assertGreater(result["strict_warning_count"], 0)

            strict = subprocess.run(base_cmd + ["--strict"], capture_output=True, text=True)
            self.assertEqual(strict.returncode, 1, strict.stderr)
            strict_result = json.loads(strict.stdout)
            self.assertFalse(strict_result["overall_pass"])
            self.assertFalse(strict_result["global_parity_verified"])

    def test_global_size_only_audit_can_fail_on_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            gemini = home / ".gemini"
            gemini.mkdir(parents=True)
            rule = gemini / "GEMINI.md"
            rule.write_text("x" * 13_000, encoding="utf-8")
            with patch.dict(os.environ, {"HOME": str(home)}):
                report = audit_toolkit.audit_global_parity(tmp)
            self.assertTrue(report["gemini_md_valid"])
            self.assertEqual(report["gemini_md_byte_count"], 13_000)

            rule.write_text("é" * 12_100, encoding="utf-8")
            with patch.dict(os.environ, {"HOME": str(home)}):
                report = audit_toolkit.audit_global_parity(tmp)
            self.assertFalse(report["gemini_md_valid"])
            self.assertGreater(report["gemini_md_byte_count"], 24_000)

    def test_current_tools_keep_the_existing_seven_skill_names(self):
        generators = ROOT / "tools" / "generators"
        expected = {
            "audit-agent-toolkit",
            "consolidate-agent-toolkit",
            "eval-skill",
            "generate-agent-suite",
            "generate-prompt",
            "generate-rule",
            "generate-skill",
        }
        actual = {directory.name for directory in generators.iterdir() if directory.is_dir()}
        self.assertEqual(actual, expected)
        for name in expected:
            self.assertTrue((generators / name / "skills" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
