"""Deterministic state machine and lifecycle tests for ProblemDiscoveryAgent."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from agents.problem_discovery.config import get_discovery_db_class
from agents.problem_discovery.orchestration.models import (
    IntentType,
    PauseReason,
    WorkflowStage,
    WorkflowStatus,
)
from agents.problem_discovery.orchestration.state_machine import DiscoveryStateMachine
from agents.problem_discovery.tools.discovery_state_tools import DiscoveryStateTools


def make_test_plan(domain: str = "ecommerce") -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "research_id": "RUN-2026-001",
        "status": "READY",
        "original_request": "Investigate inventory sync problems",
        "objective": "Determine recurring operational sync failures",
        "scope": {
            "domain": domain,
            "scope_type": "BROAD",
            "geography": None,
            "in_scope": ["inventory sync", "stockout"],
            "out_of_scope": ["pricing algorithms"],
        },
        "research_streams": [
            {
                "stream_id": "RS-001",
                "focus": "operator friction",
                "search_queries": ["inventory sync failure amazon shopify"],
            }
        ],
        "unknowns": ["exact error frequency"],
    }


def make_test_signal(signal_id: str, issue: str = "Repeated manual inventory sync.") -> Dict[str, Any]:
    return {
        "signal_id": signal_id,
        "stream_id": "RS-001",
        "source": {
            "platform": "REDDIT",
            "url": f"https://example.test/{signal_id}",
            "inspection_status": "FULL_SOURCE_REVIEWED",
        },
        "actor": {
            "role": "ecommerce seller",
            "role_is_self_reported": True,
            "role_provenance": "SELF_REPORTED",
        },
        "observation": {
            "reported_issue": issue,
            "reported_workaround": "Manual spreadsheet reconciliation.",
        },
        "evidence": {
            "classification": "L3",
            "evidence_kind": "INDEPENDENT_CORROBORATION",
            "independently_corroborated": True,
            "human_audited_primary_evidence": False,
            "verification_status": "CORROBORATED",
        },
    }


def make_test_evaluation() -> Dict[str, Any]:
    return {
        "problem_statement": "Manual multi-channel inventory synchronization causes recurring stockouts.",
        "research_score": {
            "status": "SCORED",
            "total": 28,
            "maximum": 35,
            "scores": {
                "frequency": 4,
                "severity": 4,
                "workaround": 4,
                "wtp": 4,
                "decision_maker": 4,
                "feasibility": 4,
                "discrepancy": 4,
            },
        },
        "stop_checks": {"triggered": False, "reasons": []},
    }


class ProblemDiscoveryAgentStateMachineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_discovery.sqlite")
        db_cls = get_discovery_db_class()
        self.db = db_cls(db_path=self.db_path)
        self.sm = DiscoveryStateMachine(db_path=self.db_path)
        self.tools = DiscoveryStateTools(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scenario_a_new_research_routes_to_planning(self) -> None:
        """Scenario A: Non-existent research run routes to RESEARCH_PLANNING."""
        result = self.sm.evaluate_next_action("RUN-2026-999")
        self.assertEqual(result.current_stage, WorkflowStage.RESEARCH_PLANNING)
        self.assertEqual(result.next_action, "RUN_RESEARCH_PLANNING")
        self.assertEqual(result.workflow_status, WorkflowStatus.CONTINUED)

    def test_scenario_b_persisted_run_at_evidence_research_routes_correctly(self) -> None:
        """Scenario B: Persisted run with zero signals routes to EVIDENCE_RESEARCH."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        result = self.sm.evaluate_next_action("RUN-2026-001")
        self.assertEqual(result.current_stage, WorkflowStage.EVIDENCE_RESEARCH)
        self.assertEqual(result.next_action, "RUN_EVIDENCE_RESEARCH")
        self.assertEqual(result.workflow_status, WorkflowStatus.CONTINUED)

    def test_scenario_c_run_at_problem_evaluation_routes_correctly(self) -> None:
        """Scenario C: Run with persisted unassigned signals routes to PROBLEM_EVALUATION."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001"), make_test_signal("SIG-002")],
        )
        result = self.sm.evaluate_next_action("RUN-2026-001")
        self.assertEqual(result.current_stage, WorkflowStage.PROBLEM_EVALUATION)
        self.assertEqual(result.next_action, "RUN_PROBLEM_EVALUATION")

    def test_scenario_d_candidate_with_no_experiment_routes_to_experiment_design(self) -> None:
        """Scenario D: Candidate with no experiments routes to EXPERIMENT_VALIDATION in DESIGN mode."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001"), make_test_signal("SIG-002")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001", "SIG-002"],
        )

        result = self.sm.evaluate_next_action("CAND-001")
        self.assertEqual(result.current_stage, WorkflowStage.EXPERIMENT_VALIDATION)
        self.assertEqual(result.next_action, "DESIGN_EXPERIMENT_CONTRACT")
        self.assertEqual(result.workflow_status, WorkflowStatus.CONTINUED)

    def test_scenario_e_preregistered_experiment_pauses_workflow(self) -> None:
        """Scenario E: PREREGISTERED experiment pauses workflow awaiting real-world trial execution."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001"), make_test_signal("SIG-002")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001", "SIG-002"],
        )

        contract = {
            "hypothesis": "Sellers experience at least 3 sync discrepancies weekly.",
            "metric_name": "manual_sync_events_per_seller_per_week",
            "target_threshold": 3.0,
            "direction": ">=",
            "sample_target": 5,
            "aggregation_rule": "MEAN_PER_PARTICIPANT",
        }
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict=contract,
        )

        result = self.sm.evaluate_next_action("CAND-001")
        self.assertEqual(result.current_stage, WorkflowStage.EXPERIMENT_VALIDATION)
        self.assertEqual(result.workflow_status, WorkflowStatus.PAUSED)
        self.assertEqual(result.pause_reason, PauseReason.WAITING_FOR_REAL_WORLD_EXPERIMENT.value)
        self.assertIn("Workflow paused", result.message)
        self.assertIn("EXP-001", result.message)

    def test_scenario_f_incomplete_experiment_pauses_workflow(self) -> None:
        """Scenario F: INCOMPLETE experiment pauses workflow and remains in EXPERIMENT_VALIDATION."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001"],
        )
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict={
                "metric_name": "manual_sync_events",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
            },
        )

        # Record incomplete trial (only 2 participants achieved out of 5 required)
        self.tools.record_experiment_assessment(
            experiment_id="EXP-001",
            result_dict={
                "status": "INCOMPLETE",
                "sample_achieved": 2,
                "observed_value": 4.0,
                "audited_by": "Murali",
                "audit_date": "2026-09-26",
            },
        )

        result = self.sm.evaluate_next_action("CAND-001")
        self.assertEqual(result.current_stage, WorkflowStage.EXPERIMENT_VALIDATION)
        self.assertEqual(result.workflow_status, WorkflowStatus.PAUSED)
        self.assertEqual(result.pause_reason, PauseReason.INCOMPLETE_EXPERIMENT.value)

    def test_scenario_g_invalid_experiment_does_not_route_to_solution_strategy(self) -> None:
        """Scenario G: INVALID experiment does NOT route to solution strategy."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001"],
        )
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict={
                "metric_name": "manual_sync_events",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
            },
        )

        # Record INVALID assessment (integrity failure: missing named human reviewer)
        self.tools.record_experiment_assessment(
            experiment_id="EXP-001",
            result_dict={
                "status": "INVALID_EXPERIMENT",
                "sample_achieved": 5,
                "observed_value": 4.5,
                "audited_by": None,  # Missing auditor triggers INVALID
                "audit_date": "2026-09-26",
            },
        )

        result = self.sm.evaluate_next_action("CAND-001")
        self.assertNotEqual(result.current_stage, WorkflowStage.SOLUTION_STRATEGY)
        self.assertEqual(result.workflow_status, WorkflowStatus.PAUSED)
        self.assertEqual(result.pause_reason, PauseReason.INVALID_EXPERIMENT_AUDIT.value)

    def test_scenario_h_passed_audited_experiment_routes_to_solution_strategy(self) -> None:
        """Scenario H: PASSED audited experiment routes to SOLUTION_STRATEGY."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001"), make_test_signal("SIG-002")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001", "SIG-002"],
        )
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict={
                "metric_name": "manual_sync_events",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
            },
        )

        # Record valid PASSED assessment
        self.tools.record_experiment_assessment(
            experiment_id="EXP-001",
            result_dict={
                "sample_achieved": 5,
                "observed_value": 4.2,
                "audited_by": "Murali Principal Reviewer",
                "audit_date": "2026-09-26",
                "artifact_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            },
        )

        result = self.sm.evaluate_next_action("CAND-001")
        self.assertEqual(result.current_stage, WorkflowStage.SOLUTION_STRATEGY)
        self.assertEqual(result.next_action, "RUN_SOLUTION_STRATEGY")
        self.assertEqual(result.workflow_status, WorkflowStatus.CONTINUED)

    def test_scenario_i_discovery_query_is_read_only(self) -> None:
        """Scenario I: DISCOVERY_QUERY is strictly read-only and causes zero lifecycle mutations."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001"],
        )

        cand_before = self.tools.get_candidate("CAND-001")
        query_result = self.sm.handle_query("CAND-001 status enna?")
        cand_after = self.tools.get_candidate("CAND-001")

        self.assertEqual(query_result.workflow_status, WorkflowStatus.READ_ONLY)
        self.assertEqual(cand_before["lifecycle_status"], cand_after["lifecycle_status"])
        self.assertEqual(cand_before["validation_status"], cand_after["validation_status"])

    def test_scenario_j_fresh_process_can_resume_from_sqlite(self) -> None:
        """Scenario J: New state machine / process instance resumes directly from SQLite without chat memory."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001"],
        )

        # Create completely fresh state machine instance with only the db_path
        fresh_sm = DiscoveryStateMachine(db_path=self.db_path)
        result = fresh_sm.evaluate_next_action("CAND-001")

        self.assertEqual(result.candidate_id, "CAND-001")
        self.assertEqual(result.current_stage, WorkflowStage.EXPERIMENT_VALIDATION)
        self.assertEqual(result.next_action, "DESIGN_EXPERIMENT_CONTRACT")

    def test_scenario_k_multiple_candidates_prevent_premature_run_completion(self) -> None:
        """Scenario K: If one candidate is PILOT_READY but another is unfinished, run remains ACTIVE."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Multi-candidate ecommerce research",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001"), make_test_signal("SIG-002")],
        )
        # CAND-001 reaches PILOT_READY
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Problem 1: inventory sync",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001"],
        )
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict={
                "metric_name": "manual_sync_events",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
            },
        )
        self.tools.record_experiment_assessment(
            experiment_id="EXP-001",
            result_dict={
                "sample_achieved": 5,
                "observed_value": 4.5,
                "audited_by": "Murali Reviewer",
                "audit_date": "2026-09-26",
                "artifact_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            },
        )
        self.tools.finalize_solution(
            candidate_id="CAND-001",
            solution_class="PROCESS_SOP",
            solution_dict={"sop": "Daily reconciliation checklist"},
        )

        # CAND-002 is still unfinished (no experiments)
        self.tools.upsert_candidate(
            candidate_id="CAND-002",
            origin_research_id="RUN-2026-001",
            problem_statement="Problem 2: tax calculation rounding",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-002"],
        )

        # Run state must remain ACTIVE, not COMPLETED
        result = self.sm.evaluate_next_action("RUN-2026-001")
        self.assertNotEqual(result.workflow_status, WorkflowStatus.COMPLETED)
        self.assertEqual(result.current_stage, WorkflowStage.EXPERIMENT_VALIDATION)
        self.assertEqual(result.candidate_id, "CAND-002")

    def test_unassigned_signals_with_existing_paused_candidate_routes_to_problem_evaluation(self) -> None:
        """Unassigned signals must not be starved when an existing candidate is paused on an experiment."""
        self.tools.create_research_run(
            research_id="RUN-2026-001",
            prompt="Investigate inventory sync",
            plan_dict=make_test_plan(),
        )
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-001")],
        )
        self.tools.upsert_candidate(
            candidate_id="CAND-001",
            origin_research_id="RUN-2026-001",
            problem_statement="Inventory sync failures cause stockouts.",
            evaluation_dict=make_test_evaluation(),
            signal_ids=["SIG-001"],
        )
        # Preregister experiment so CAND-001 is paused
        self.tools.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict={
                "metric_name": "manual_sync_events",
                "target_threshold": 3.0,
                "direction": ">=",
                "sample_target": 5,
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
            },
        )
        # Verify CAND-001 is paused
        cand_res = self.sm.evaluate_next_action("CAND-001")
        self.assertEqual(cand_res.workflow_status, WorkflowStatus.PAUSED)

        # Now add a new unassigned signal to the research run
        self.db.save_evidence_signals(
            research_id="RUN-2026-001",
            signals=[make_test_signal("SIG-002", issue="New unassigned friction pattern")],
        )

        # Evaluating RUN-2026-001 must route to PROBLEM_EVALUATION to cluster the new signal
        run_res = self.sm.evaluate_next_action("RUN-2026-001")
        self.assertEqual(run_res.current_stage, WorkflowStage.PROBLEM_EVALUATION)
        self.assertEqual(run_res.next_action, "RUN_PROBLEM_EVALUATION")
        self.assertEqual(run_res.workflow_status, WorkflowStatus.CONTINUED)


if __name__ == "__main__":
    unittest.main()
