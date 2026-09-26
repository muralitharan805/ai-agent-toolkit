"""Unit tests for the SeyaliCraft Build Verdict Engine."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from agents.problem_discovery.config import ProblemDiscoveryConfig
from agents.problem_discovery.tools.discovery_state_tools import DiscoveryStateTools
from agents.problem_discovery.verdict import (
    BuildDecision,
    RecommendedShape,
    evaluate_candidate,
    evaluate_all_candidates,
)


class TestVerdictEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_discovery.sqlite")
        self.tools = DiscoveryStateTools(db_path=self.db_path)
        self.db = self.tools.db

        # Create a sample research run
        self.db.create_research_run(
            research_id="RUN-TEST-001",
            request="Research coordinate conversion friction",
            domain="geospatial",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_low_score_yields_no_go(self):
        # Insert weak candidate with no signals
        self.db.upsert_candidate(
            candidate_id="CAND-WEAK",
            research_id="RUN-TEST-001",
            title="Trivial coordinate issue",
            domain="geospatial",
            target_operator="GIS analysts",
            track="COMMERCIAL",
            evaluation_dict={"scores": {"pain_severity": 1, "frequency": 1}},
            supporting_signal_ids=[],
        )

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            verdict = evaluate_candidate(conn, "CAND-WEAK")
            self.assertIsNotNone(verdict)
            self.assertEqual(verdict.decision, BuildDecision.NO_GO)
            self.assertIn("below the viability threshold", verdict.justification)
        finally:
            conn.close()

    def test_utility_tool_high_score_yields_go(self):
        # Add supporting signals with full source review
        self.db.save_evidence_signals(
            research_id="RUN-TEST-001",
            signals=[
                {
                    "platform": "reddit",
                    "actor": {"role_is_self_reported": True},
                    "source": {"inspection_status": "FULL_SOURCE_REVIEWED"},
                    "source_url": "https://reddit.com/r/gis/1",
                    "reported_issue": "Datum shift errors in lat long conversion",
                    "evidence_level": "L2",
                },
                {
                    "platform": "gis_stackexchange",
                    "actor": {"role_is_self_reported": True},
                    "source": {"inspection_status": "FULL_SOURCE_REVIEWED"},
                    "source_url": "https://gis.stackexchange.com/q/123",
                    "reported_issue": "UTM to WGS84 batch conversion failures",
                    "evidence": {"independently_corroborated": True},
                    "evidence_level": "L3",
                },
            ],
        )

        self.db.upsert_candidate(
            candidate_id="CAND-GEO",
            research_id="RUN-TEST-001",
            title="Geospatial Coordinate Datum & CRS Conversion Friction",
            domain="geospatial",
            target_operator="Surveyors and GIS Analysts",
            track="COMMERCIAL",
            evaluation_dict={
                "research_score": {
                    "scores": {
                        "frequency": 4,
                        "severity": 4,
                        "workaround": 4,
                        "wtp": 3,
                        "decision_maker": 3,
                        "feasibility": 4,
                        "discrepancy": 3,
                    }
                }
            },
            supporting_signal_ids=["SIG-RUN-TEST-001-001", "SIG-RUN-TEST-001-002"],
        )

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            verdict = evaluate_candidate(conn, "CAND-GEO")
            self.assertIsNotNone(verdict)
            self.assertEqual(verdict.decision, BuildDecision.GO)
            self.assertEqual(verdict.recommended_shape, RecommendedShape.CLIENT_SIDE_UTILITY)
            self.assertIn("Type 2", verdict.reversibility)
            self.assertIn("seyalicraft.com/tools/", verdict.seyalicraft_fit["Target Placement"])
            self.assertIn("$0 / month", verdict.seyalicraft_fit["Monthly Infra Cost"])

            # Verify terminal card formatting
            card = verdict.format_terminal_card()
            self.assertIn("SEYALICRAFT BUILD VERDICT: CAND-GEO", card)
            self.assertIn("RECOMMENDED TO BUILD", card)
        finally:
            conn.close()

    def test_saas_candidate_without_passed_experiment_yields_hold(self):
        self.db.save_evidence_signals(
            research_id="RUN-TEST-001",
            signals=[
                {
                    "platform": "reddit",
                    "actor": {"role_is_self_reported": True},
                    "source": {"inspection_status": "FULL_SOURCE_REVIEWED"},
                    "source_url": "https://reddit.com/r/dentistry/1",
                    "reported_issue": "Distributor backorders cause inventory stockouts",
                    "evidence_level": "L2",
                }
            ],
        )

        self.db.upsert_candidate(
            candidate_id="CAND-SAAS",
            research_id="RUN-TEST-001",
            title="Dental Practice Consumables Inventory Backorder Sync",
            domain="dental_inventory",
            target_operator="Clinic office managers",
            track="COMMERCIAL",
            evaluation_dict={
                "research_score": {
                    "scores": {
                        "frequency": 4,
                        "severity": 4,
                        "workaround": 4,
                        "wtp": 3,
                        "decision_maker": 3,
                        "feasibility": 4,
                        "discrepancy": 3,
                    }
                }
            },
            supporting_signal_ids=["SIG-RUN-TEST-001-001"],
        )

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            verdict = evaluate_candidate(conn, "CAND-SAAS")
            self.assertIsNotNone(verdict)
            self.assertEqual(verdict.decision, BuildDecision.HOLD)
            self.assertEqual(verdict.recommended_shape, RecommendedShape.STANDALONE_SAAS)
            self.assertIn("Type 1", verdict.reversibility)
            self.assertIn("Do NOT write backend SaaS code", verdict.next_steps[0])
        finally:
            conn.close()

    def test_evaluate_all_candidates(self):
        verdicts = evaluate_all_candidates(self.db_path)
        self.assertIsInstance(verdicts, list)


if __name__ == "__main__":
    unittest.main()
