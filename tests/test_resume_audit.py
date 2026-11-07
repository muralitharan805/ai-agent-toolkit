"""Regression tests for the resume text auditor (stdlib-only)."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT / "shared" / "resume-engineering-and-ats-optimization"
    / "skills" / "scripts" / "audit_resume_text.py"
)
SPEC = importlib.util.spec_from_file_location("resume_audit", SCRIPT)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


def sample_resume(bullet="- Built Angular v18 components"):
    return [
        "Candidate | candidate@example.com",
        "## Professional Summary",
        "Full Stack Developer",
        "## Technical Skills",
        "Angular, TypeScript",
        "## Professional Experience",
        bullet,
        "## Key Projects",
        "- Automated deployment checks, preventing regressions",
        "## Education",
        "B.Sc. Information Technology",
    ]


class ResumeAuditTests(unittest.TestCase):
    def test_no_default_stack_keyword_penalty(self):
        result = AUDITOR.analyze_resume_lines(sample_resume())
        self.assertEqual(result["keywords"]["source"], "not_provided")
        self.assertEqual(result["keywords"]["missing"], [])
        self.assertIsNone(result["scores"]["target_keyword_coverage"])
        self.assertEqual(result["score"], result["scores"]["ats_readability"])

    def test_explicit_target_keyword_coverage(self):
        result = AUDITOR.analyze_resume_lines(
            sample_resume(), target_keywords=["TypeScript", "PostgreSQL"]
        )
        self.assertEqual(result["keywords"]["found"], ["TypeScript"])
        self.assertEqual(result["keywords"]["missing"], ["PostgreSQL"])
        self.assertEqual(result["scores"]["target_keyword_coverage"], 50)
        self.assertEqual(result["keywords"]["source"], "user_supplied")

    def test_framework_version_is_not_impact_metric(self):
        result = AUDITOR.analyze_resume_lines(sample_resume())
        self.assertEqual(result["stats"]["quantified_bullets_count"], 0)
        self.assertEqual(result["stats"]["bullets_needing_outcome_count"], 1)

    def test_numeric_impact_and_qualitative_result(self):
        result = AUDITOR.analyze_resume_lines(
            sample_resume("- Reduced API latency by 30% using MySQL indexes")
        )
        self.assertEqual(result["stats"]["quantified_bullets_count"], 1)
        self.assertEqual(result["stats"]["bullets_needing_outcome_count"], 0)

        qualitative = AUDITOR.analyze_resume_lines(
            sample_resume("- Eliminated duplicate writes using database transactions")
        )
        self.assertEqual(qualitative["stats"]["quantified_bullets_count"], 0)
        self.assertEqual(qualitative["stats"]["bullets_needing_outcome_count"], 0)

    def test_ats_structure_score_is_not_content_score(self):
        good = AUDITOR.analyze_resume_lines(
            sample_resume("- Reduced API latency by 30% using MySQL indexes")
        )
        weak = AUDITOR.analyze_resume_lines(
            sample_resume("- Responsible for writing API code")
        )
        self.assertEqual(good["scores"]["ats_readability"], weak["scores"]["ats_readability"])
        self.assertGreater(good["scores"]["content_evidence"], weak["scores"]["content_evidence"])

    def test_section_match_requires_standalone_heading(self):
        self.assertEqual(AUDITOR.detect_heading("Experience building tools"), "")
        self.assertEqual(AUDITOR.detect_heading("## Professional Experience"), "Professional Experience")
        self.assertEqual(AUDITOR.detect_heading("Technical Skills:"), "Technical Skills")
        result = AUDITOR.analyze_resume_lines(["Experience building tools"])
        self.assertIn("Professional Experience", result["headings"]["missing"])

    def test_cli_returns_valid_json_and_optional_target_keywords(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.md"
            path.write_text("\n".join(sample_resume()), encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(SCRIPT), str(path),
                 "--target-keywords", "Angular,PostgreSQL"],
                text=True, capture_output=True, check=True,
            )
            report = json.loads(process.stdout)
            self.assertEqual(report["keywords"]["missing"], ["PostgreSQL"])
            self.assertIn("ATS Readability", process.stderr)

    def test_contact_pipe_separators_not_mistaken_for_tables(self):
        result = AUDITOR.analyze_resume_lines(
            ["Name | name@example.com | linkedin.com/in/name", *sample_resume()]
        )
        self.assertFalse(any("markdown table" in risk.lower()
                             for risk in result["formatting_risks"]))

    def test_missing_optional_projects_does_not_penalize_ats_readability(self):
        lines = [
            line for line in sample_resume()
            if line not in ("## Key Projects", "- Automated deployment checks, preventing regressions")
        ]
        result = AUDITOR.analyze_resume_lines(lines)
        self.assertIn("Key Projects", result["headings"]["missing"])
        self.assertEqual(result["scores"]["ats_readability"], 100)

    def test_docx_header_contact_risk(self):
        xml = (
            '<w:document xmlns:w="http://schemas.openxmlformats.org/'
            'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
            'Resume body</w:t></w:r></w:p></w:body></w:document>'
        )
        header = (
            '<w:hdr xmlns:w="http://schemas.openxmlformats.org/'
            'wordprocessingml/2006/main"><w:p><w:r><w:t>'
            'candidate@example.com</w:t></w:r></w:p></w:hdr>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
                archive.writestr("word/header1.xml", header)
            layout = AUDITOR.audit_docx_layout(str(path))
            self.assertTrue(layout["header_footer_trap"])
            self.assertTrue(any("Contact-info extraction risk" in x
                                for x in layout["layout_issues"]))


if __name__ == "__main__":
    unittest.main()
