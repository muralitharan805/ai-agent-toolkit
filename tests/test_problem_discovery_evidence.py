"""Regression tests for problem discovery evidence and export safety gates."""
from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import date, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "shared/problem-discovery/skills/scripts"
LEGACY_AVAILABLE = SCRIPTS.exists()

if LEGACY_AVAILABLE:
    sys.path.insert(0, str(SCRIPTS))
    from score_problem_candidate import (ScoreDimensions, StopCheckStatus, audit_evidence,
                                         derive_smallest_solution, evaluate_candidate,
                                         export_to_obsidian, refresh_discovery_csv)
    from export_discovery_matrix import generate_matrix


@unittest.skipUnless(LEGACY_AVAILABLE, "legacy monolithic problem-discovery evidence suite was removed")
class EvidenceGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.artifact = self.folder / "actual-observation.csv"
        self.artifact.write_text("date,uses\n2026-09-01,1\n", encoding="utf-8")
        self.digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.today = date.today().isoformat()
        self.yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.evidence = [{"level": 1, "claim": "Operator repeated the task",
                          "observed_on": self.yesterday, "artifact_path": str(self.artifact),
                          "sha256": self.digest, "reviewed_by": "field researcher", "reviewed_on": self.today}]
        self.scores = ScoreDimensions(4, 4, 4, 4, 4, 4, 4)

    def candidate(self, **overrides):
        kw = dict(candidate_id="PROB-SMOKE", title="Production mismatch", domain="Manufacturing",
                  track="commercial", raw_scores=self.scores, evidence_level=1,
                  stops=StopCheckStatus(), evidence_records=self.evidence)
        kw.update(overrides)
        return evaluate_candidate(**kw)

    def experiment(self, **overrides):
        exp = {"hypothesis": "At least 3 repeat uses", "metric": "repeat_uses",
               "failure_rule": "Park if repeat_uses < 3", "success_threshold": 3,
               "observed_value": 4, "direction": "at_least", "sample_size": 3,
               "preregistered_on": self.yesterday, "started_on": self.yesterday,
               "ended_on": self.today, "artifact_path": str(self.artifact), "sha256": self.digest,
               "reviewed_by": "field researcher", "reviewed_on": self.today}
        exp.update(overrides)
        return exp

    def test_score_and_prose_do_not_validate(self):
        result = self.candidate(evidence_records=[], evidence_sources=["https://example.org/post"],
                                evidence_artifacts=["/missing/file.csv"],
                                experiment_outcome="Customers loved the demo")
        self.assertEqual(result.status, "UNVERIFIED")
        self.assertFalse(result.evidence_verified)

    def test_nonexistent_or_tampered_or_unreviewed_artifact_rejected(self):
        for override in ({"artifact_path": "/not/a/file"}, {"sha256": "0" * 64},
                         {"reviewed_by": ""}, {"reviewed_on": ""}):
            with self.subTest(override=override):
                bad = [{**self.evidence[0], **override}]
                self.assertEqual(self.candidate(evidence_records=bad).status, "UNVERIFIED")

    def test_verified_evidence_only_is_research_priority(self):
        result = self.candidate()
        self.assertTrue(result.evidence_verified)
        self.assertEqual(result.status, "RESEARCH_PRIORITY")
        self.assertFalse(result.experiment_completed)

    def test_structured_experiment_success_and_failure(self):
        success = self.candidate(experiment=self.experiment())
        self.assertEqual(success.status, "VALIDATED")
        self.assertTrue(success.experiment_completed and success.experiment_passed)
        failure = self.candidate(experiment=self.experiment(observed_value=1))
        self.assertEqual(failure.status, "EXPERIMENT_FAILED")
        self.assertFalse(failure.experiment_passed)

    def test_experiment_cannot_be_backdated_or_self_certified(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        for override in ({"started_on": future}, {"sample_size": 0},
                         {"artifact_path": "https://example.org/fake"},
                         {"sha256": "0" * 64}, {"observed_value": "great"}):
            with self.subTest(override=override):
                self.assertNotEqual(self.candidate(experiment=self.experiment(**override)).status, "VALIDATED")

    def test_secondary_evidence_capped_and_score_does_not_override_stop(self):
        self.assertEqual(self.candidate(evidence_level=4).total_score, 7)
        stopped = self.candidate(stops=StopCheckStatus(single_source_bias=True), experiment=self.experiment())
        self.assertEqual(stopped.status, "PARKED")

    def test_explicit_solution_constraints_not_title_keywords(self):
        self.assertIsNone(derive_smallest_solution(None))
        self.assertEqual(derive_smallest_solution({"non_software_sufficient": True})["format"], "template_sop")
        self.assertEqual(derive_smallest_solution({"needs_interactive_ui": True})["format"], "static_web_utility")
        self.assertEqual(derive_smallest_solution({"needs_batch_automation": True})["format"], "cli_tool")
        self.assertEqual(derive_smallest_solution({"needs_browser_integration": True})["format"], "browser_extension")
        self.assertEqual(derive_smallest_solution({"needs_multi_user_sync": True})["format"], "micro_saas")

    def test_dossier_csv_keeps_score_separate_from_validation(self):
        result = self.candidate(evidence_records=[])
        output = export_to_obsidian(result, self.folder)
        rows = generate_matrix(self.folder, self.folder / "discovery_matrix.csv")
        self.assertEqual(output.suffix, ".md")
        self.assertEqual(rows[0]["score"], 28)
        self.assertEqual(rows[0]["status"], "UNVERIFIED")
        self.assertNotEqual(rows[0]["classification"], "TIER-1 GOLD")
        self.assertEqual(len(refresh_discovery_csv(self.folder).read_text(encoding="utf-8").splitlines()), 2)

    def test_legacy_claim_cannot_gain_validated_status_on_export(self):
        legacy = self.folder / "legacy.md"
        legacy.write_text("---\npriority_score: 35\nvalidation_status: VALIDATED\n---\n# Old\n", encoding="utf-8")
        rows = generate_matrix(self.folder, self.folder / "discovery_matrix.csv")
        self.assertEqual(rows[0]["status"], "UNVERIFIED_LEGACY_CLAIM")

    def test_cli_round_trip_and_strict_gate(self):
        candidate = {"id": "PROB-CLI", "title": "Observed mismatch", "domain": "Textiles",
                     "track": "commercial", "evidence_level": 1,
                     "scores": asdict(self.scores), "evidence_records": self.evidence,
                     "experiment": self.experiment(), "solution_constraints": {"needs_interactive_ui": True}}
        input_path = self.folder / "candidate.json"
        input_path.write_text(json.dumps(candidate), encoding="utf-8")
        command = [sys.executable, str(SCRIPTS / "score_problem_candidate.py"), "--input-json", str(input_path),
                   "--json", "--strict", "--export-obsidian", str(self.folder / "logs")]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "VALIDATED")
        self.assertTrue((self.folder / "logs" / "discovery_matrix.csv").exists())


if __name__ == "__main__":
    unittest.main()
