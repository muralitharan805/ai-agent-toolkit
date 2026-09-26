"""Deterministic tests for discovery-state custom tools and guardrails."""

from __future__ import annotations

import pickle
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from agents.problem_discovery.config import get_discovery_db_class
from agents.problem_discovery.tools.discovery_state_tools import DiscoveryStateTools


def make_plan() -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "research_id": "RUN-2026-001",
        "status": "READY",
        "original_request": "Investigate inventory sync",
        "objective": "Determine recurring sync failures",
        "scope": {"domain": "ecommerce", "scope_type": "BROAD", "geography": None},
        "research_streams": [
            {
                "stream_id": "RS-001",
                "focus": "operator friction",
                "search_queries": ["sync failure"],
            }
        ],
        "unknowns": [],
    }


class ProblemDiscoveryAgentToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_discovery.sqlite")
        db_cls = get_discovery_db_class()
        self.db = db_cls(db_path=self.db_path)
        self.tools = DiscoveryStateTools(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_tool_registration_signatures(self) -> None:
        """Verify that all 15 discovery tools are properly registered with docstrings."""
        all_tools = self.tools.get_all_tools()
        self.assertEqual(len(all_tools), 15)

        read_tools = self.tools.get_read_tools()
        self.assertEqual(len(read_tools), 9)

        write_tools = self.tools.get_write_tools()
        self.assertEqual(len(write_tools), 6)

        for tool_fn in all_tools:
            self.assertTrue(callable(tool_fn))
            self.assertTrue(bool(tool_fn.__doc__), f"Tool {tool_fn.__name__} must have a docstring")

    def test_registered_antigravity_tools_are_pickle_safe(self) -> None:
        """Antigravity may serialize bound Python tools before runtime execution."""
        for tool_fn in self.tools.get_all_tools():
            payload = pickle.dumps(tool_fn)
            restored = pickle.loads(payload)
            self.assertTrue(callable(restored))
            self.assertEqual(restored.__name__, tool_fn.__name__)

        restored_get_run = pickle.loads(pickle.dumps(self.tools.get_discovery_run))
        result = restored_get_run("RUN-DOES-NOT-EXIST")
        self.assertFalse(result["found"])

    def test_scenario_o_compound_experiment_primary_metric_is_rejected(self) -> None:
        """Scenario O: Preregistration rejects compound disjunctive/conjunctive metrics."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            plan_dict=make_plan(),
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            title="Inventory sync discrepancies",
            evaluation_dict={
                "problem_statement": "Sync issues",
                "research_score": {
                    "status": "SCORED",
                    "total": 21,
                    "scores": {"frequency": 3, "severity": 3, "workaround": 3, "wtp": 3, "decision_maker": 3, "feasibility": 3, "discrepancy": 3},
                },
            },
        )

        compound_metrics = [
            "manual_sync_or_stockout_events_per_week",
            "stockout_and_inventory_discrepancies",
            "sync_failures / week",
            "errors or retries",
        ]

        for compound in compound_metrics:
            with self.assertRaises(ValueError, msg=f"Expected rejection for compound metric: {compound}"):
                self.tools.preregister_experiment(
                    experiment_id="EXP-BAD-01",
                    candidate_id="CAND-001",
                    contract_dict={
                        "hypothesis": "Test compound metric rejection",
                        "metric_name": compound,
                        "target_threshold": 2.0,
                        "direction": ">=",
                        "sample_target": 5,
                        "aggregation_rule": "MEAN_PER_PARTICIPANT",
                    },
                )

    def test_scenario_n_solution_finalization_is_blocked_when_unfinished_experiments_exist(self) -> None:
        """Scenario N: Solution finalization is strictly blocked if PREREGISTERED/INCOMPLETE experiments exist."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            plan_dict=make_plan(),
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            title="Inventory sync discrepancies",
            evaluation_dict={
                "problem_statement": "Sync issues",
                "research_score": {
                    "status": "SCORED",
                    "total": 21,
                    "scores": {"frequency": 3, "severity": 3, "workaround": 3, "wtp": 3, "decision_maker": 3, "feasibility": 3, "discrepancy": 3},
                },
            },
        )
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict={
                "hypothesis": "Test",
                "metric_name": "manual_sync_events_per_week",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
            },
        )

        # Finalizing solution while EXP-001 is PREREGISTERED must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            self.tools.finalize_solution(
                candidate_id="CAND-001",
                solution_class="PROCESS_SOP",
                solution_dict={"sop": "Daily checklist"},
            )
        self.assertIn("Unfinished experiments exist", str(ctx.exception))

    def test_scenario_l_raw_unassessed_signal_cannot_become_candidate_l3_from_proposal(self) -> None:
        """Scenario L: Raw uninspected signal stays UNASSESSED; candidate evidence level cannot be promoted by model proposal."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            plan_dict=make_plan(),
        )

        # Save snippet-only signal (inspection_status: SNIPPET_ONLY)
        raw_signal = {
            "signal_id": "SIG-RAW-01",
            "stream_id": "RS-001",
            "source": {
                "platform": "REDDIT",
                "url": "https://reddit.com/r/ecommerce/123",
                "inspection_status": "SNIPPET_ONLY",
            },
            "actor": {"role": "seller", "role_provenance": "UNVERIFIED"},
            "observation": {"reported_issue": "Sync failed"},
            "evidence": {"classification": "L3"},  # Model claims L3!
        }
        self.tools.save_evidence_signals("RUN-2026-001", [raw_signal])

        # Model proposes candidate with L3 level and 28 score
        proposed_evaluation = {
            "problem_statement": "Sync issues",
            "evidence_level": "L3",  # Model claims L3
            "research_score": {
                "status": "SCORED",
                "total": 28,
                "scores": {"frequency": 4, "severity": 4, "workaround": 4, "wtp": 4, "decision_maker": 4, "feasibility": 4, "discrepancy": 4},
            },
        }

        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            title="Sync issues",
            evaluation_dict=proposed_evaluation,
            signal_ids=["SIG-RAW-01"],
        )

        cand = self.tools.get_candidate("CAND-001")
        # Evidence gate must enforce UNASSESSED because source was SNIPPET_ONLY!
        self.assertEqual(cand["evidence_level"], "UNASSESSED")
        # Gated score must be capped at 0 for UNASSESSED
        self.assertEqual(cand["research_score"], 0)

    def test_scenario_m_existing_stable_candidate_is_reused_across_research_runs(self) -> None:
        """Scenario M: Existing stable candidate is linked across subsequent research runs instead of duplicated."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            plan_dict=make_plan(),
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            title="Multi-channel inventory sync failure",
            evaluation_dict={
                "problem_statement": "Inventory synchronization",
                "research_score": {"scores": {"frequency": 3, "severity": 3, "workaround": 3, "wtp": 3, "decision_maker": 3, "feasibility": 3, "discrepancy": 3}},
            },
        )

        # Later research run in same domain
        self.tools.create_research_run(
            research_id="RUN-2026-002",
            plan_dict=make_plan(),
        )

        # Search discovery for candidate
        matches = self.tools.search_discovery("inventory sync", entity_type="CANDIDATE")
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0]["entity_id"], "CAND-001")


    def test_missing_assessment_evidence_never_defaults_to_pass(self) -> None:
        """Missing audit material must leave the experiment PREREGISTERED."""
        self.tools.create_research_run(
            research_id="RUN-2026-010",
            plan_dict={
                "schema_version": "1.0",
                "research_id": "RUN-2026-010",
                "original_request": "Test experiment safety",
                "scope": {"domain": "ops", "scope_type": "NARROW"},
                "research_streams": [],
                "unknowns": [],
            },
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-010",
            origin_research_id="RUN-2026-010",
            title="Manual operational intervention",
            evaluation_dict={"research_score": {"scores": {}}},
        )
        self.tools.preregister_experiment(
            experiment_id="EXP-010",
            candidate_id="CAND-010",
            contract_dict={
                "hypothesis": "Operators intervene manually.",
                "metric_name": "manual_interventions",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "minimum_usable": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
                "artifact_requirements": {"required": True},
                "review_requirements": {"human_review_required": True},
            },
        )

        with self.assertRaises(ValueError):
            self.tools.record_experiment_assessment(
                experiment_id="EXP-010",
                result_dict={
                    "sample_achieved": 5,
                    "observed_value": 4.0,
                },
            )

        conn = self.tools._get_connection()
        try:
            row = conn.execute(
                "SELECT outcome_verdict, assessment_json FROM experiments WHERE experiment_id='EXP-010'"
            ).fetchone()
            self.assertEqual(row["outcome_verdict"], "PREREGISTERED")
            self.assertIsNone(row["assessment_json"])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
