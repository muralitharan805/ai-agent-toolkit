"""Unit tests for Stage Precondition Gates and Quality Verification in Problem Discovery."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from agents.problem_discovery.orchestration.models import WorkflowStage
from agents.problem_discovery.orchestration.preconditions import (
    validate_stage_preconditions,
    verify_stage_postconditions,
)
from agents.problem_discovery.config import get_discovery_db_class


class StagePreconditionGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_preconditions.sqlite")
        db_cls = get_discovery_db_class()
        self.db = db_cls(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_research_planning_preconditions(self) -> None:
        """Test RESEARCH_PLANNING precondition gating on prompt length."""
        # Short / empty prompt
        res_empty = validate_stage_preconditions(
            WorkflowStage.RESEARCH_PLANNING,
            prompt="short",
            db_path=self.db_path,
        )
        self.assertFalse(res_empty.allowed)
        self.assertIn("too short", res_empty.reason.lower())

        # Valid prompt
        res_valid = validate_stage_preconditions(
            WorkflowStage.RESEARCH_PLANNING,
            prompt="Developers waste hours debugging API schema drift in staging environments.",
            db_path=self.db_path,
        )
        self.assertTrue(res_valid.allowed)

    def test_evidence_research_preconditions(self) -> None:
        """Test EVIDENCE_RESEARCH precondition checks."""
        # Non-existent run
        res_missing = validate_stage_preconditions(
            WorkflowStage.EVIDENCE_RESEARCH,
            identifier="RUN-2026-999",
            db_path=self.db_path,
        )
        self.assertFalse(res_missing.allowed)
        self.assertIn("does not exist", res_missing.reason)

        # Create run with valid plan
        plan = {
            "schema_version": "1.0",
            "research_id": "RUN-2026-001",
            "original_request": "Investigate schema drift",
            "scope": {"domain": "api_tooling", "scope_type": "NARROW"},
            "research_streams": [
                {
                    "stream_id": "RS-001",
                    "stream_name": "Schema Drift",
                    "search_queries": ["openapi schema drift staging"],
                }
            ],
        }
        self.db.create_research_run(
            research_id="RUN-2026-001",
            request="Investigate schema drift",
            domain="api_tooling",
            scope_type="NARROW",
            plan_dict=plan,
        )

        res_ok = validate_stage_preconditions(
            WorkflowStage.EVIDENCE_RESEARCH,
            identifier="RUN-2026-001",
            db_path=self.db_path,
        )
        self.assertTrue(res_ok.allowed)
        self.assertEqual(res_ok.diagnostics.get("streams_count"), 1)

    def test_problem_evaluation_preconditions_rejects_unassessed_or_empty(self) -> None:
        """Test PROBLEM_EVALUATION blocks if signals are 0 or all UNASSESSED."""
        # 1. 0 signals
        plan = {
            "schema_version": "1.0",
            "research_id": "RUN-2026-002",
            "original_request": "Investigate prompt tokens",
            "scope": {"domain": "ai", "scope_type": "NARROW"},
            "research_streams": [{"stream_id": "RS-001", "stream_name": "Tokens"}],
        }
        self.db.create_research_run(
            research_id="RUN-2026-002",
            request="Investigate prompt tokens",
            domain="ai",
            scope_type="NARROW",
            plan_dict=plan,
        )
        res_no_sig = validate_stage_preconditions(
            WorkflowStage.PROBLEM_EVALUATION,
            identifier="RUN-2026-002",
            db_path=self.db_path,
        )
        self.assertFalse(res_no_sig.allowed)
        self.assertIn("0 evidence signals", res_no_sig.reason)

        # 2. Signals exist but all are UNASSESSED
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO evidence_signals (signal_id, research_id, platform, source_url, reported_issue, evidence_level, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "SIG-001",
                "RUN-2026-002",
                "WEB",
                "https://example.com/raw",
                "Tokens mismatch",
                "UNASSESSED",
                json.dumps({"evidence": {"classification": "UNASSESSED"}}),
            ),
        )
        conn.commit()
        conn.close()

        res_unassessed = validate_stage_preconditions(
            WorkflowStage.PROBLEM_EVALUATION,
            identifier="RUN-2026-002",
            db_path=self.db_path,
        )
        self.assertFalse(res_unassessed.allowed)
        self.assertIn("UNASSESSED", res_unassessed.reason)

        # 3. Elevate signal to L3
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE evidence_signals SET evidence_level='L3' WHERE signal_id='SIG-001'")
        conn.commit()
        conn.close()

        res_assessed = validate_stage_preconditions(
            WorkflowStage.PROBLEM_EVALUATION,
            identifier="RUN-2026-002",
            db_path=self.db_path,
        )
        self.assertTrue(res_assessed.allowed)
        self.assertEqual(res_assessed.diagnostics.get("qualified_signals"), 1)

    def test_experiment_validation_preconditions(self) -> None:
        """Test EXPERIMENT_VALIDATION gating against duplicate design and unassessed candidate."""
        # Non-existent candidate
        res_missing = validate_stage_preconditions(
            WorkflowStage.EXPERIMENT_VALIDATION,
            identifier="CAND-999",
            db_path=self.db_path,
        )
        self.assertFalse(res_missing.allowed)

        # Create prerequisite research run
        plan = {
            "schema_version": "1.0",
            "research_id": "RUN-2026-001",
            "original_request": "Investigate schema drift",
            "scope": {"domain": "ai", "scope_type": "NARROW"},
            "research_streams": [{"stream_id": "RS-001", "stream_name": "Tokens"}],
        }
        self.db.create_research_run(
            research_id="RUN-2026-001",
            request="Investigate schema drift",
            domain="ai",
            scope_type="NARROW",
            plan_dict=plan,
        )

        # Create candidate with valid score
        evaluation = {
            "problem_statement": "Token mismatch",
            "research_score": {"scores": {"frequency": 4}, "total": 24},
        }
        self.db.upsert_candidate(
            candidate_id="CAND-001",
            research_id="RUN-2026-001",
            title="Token mismatch across tokenizers",
            domain="ai",
            target_operator="Developer",
            track="COMMERCIAL",
            research_score=24,
            evidence_level="L3",
            evaluation_dict=evaluation,
            supporting_signal_ids=[],
        )

        # Ready for experiment design
        res_ready = validate_stage_preconditions(
            WorkflowStage.EXPERIMENT_VALIDATION,
            identifier="CAND-001",
            db_path=self.db_path,
        )
        self.assertTrue(res_ready.allowed)

        # Preregister experiment
        contract = {
            "hypothesis": "Unified tokenizer wrapper reduces token count errors by >= 80%",
            "metric_name": "error_rate",
            "target_threshold": 0.8,
            "direction": ">=",
            "sample_target": 25,
            "aggregation_rule": "MEAN",
        }
        self.db.preregister_experiment(
            experiment_id="EXP-001",
            candidate_id="CAND-001",
            contract_dict=contract,
        )

        # Attempt duplicate design -> BLOCKED
        res_duplicate = validate_stage_preconditions(
            WorkflowStage.EXPERIMENT_VALIDATION,
            identifier="CAND-001",
            prompt="",
            db_path=self.db_path,
        )
        self.assertFalse(res_duplicate.allowed)
        self.assertIn("already PREREGISTERED", res_duplicate.reason)

        # Submitting trial result material -> ALLOWED (ASSESS mode)
        res_assess = validate_stage_preconditions(
            WorkflowStage.EXPERIMENT_VALIDATION,
            identifier="CAND-001",
            prompt="EXP-001: observed_value=0.88, sample=30 participants, reviewer=Alice, hash=abc",
            db_path=self.db_path,
        )
        self.assertTrue(res_assess.allowed)

    def test_solution_strategy_preconditions(self) -> None:
        """Test SOLUTION_STRATEGY requires completed, evaluated experiments."""
        plan = {
            "schema_version": "1.0",
            "research_id": "RUN-2026-001",
            "original_request": "Investigate token mismatch",
            "scope": {"domain": "ai", "scope_type": "NARROW"},
            "research_streams": [{"stream_id": "RS-001", "stream_name": "Tokens"}],
        }
        self.db.create_research_run(
            research_id="RUN-2026-001",
            request="Investigate token mismatch",
            domain="ai",
            scope_type="NARROW",
            plan_dict=plan,
        )

        evaluation = {
            "problem_statement": "Token mismatch",
            "research_score": {"scores": {"frequency": 4}, "total": 24},
        }
        self.db.upsert_candidate(
            candidate_id="CAND-002",
            research_id="RUN-2026-001",
            title="Token mismatch",
            domain="ai",
            target_operator="Developer",
            track="COMMERCIAL",
            research_score=24,
            evidence_level="L3",
            evaluation_dict=evaluation,
            supporting_signal_ids=[],
        )

        # 0 experiments -> BLOCKED
        res_no_exp = validate_stage_preconditions(
            WorkflowStage.SOLUTION_STRATEGY,
            identifier="CAND-002",
            db_path=self.db_path,
        )
        self.assertFalse(res_no_exp.allowed)
        self.assertIn("0 experiments", res_no_exp.reason)

        # Preregister experiment -> still BLOCKED (pending trial)
        contract = {
            "hypothesis": "Wrapper reduces errors",
            "metric_name": "reduction",
            "target_threshold": 0.5,
            "direction": ">=",
            "sample_target": 10,
            "aggregation_rule": "MEAN",
        }
        self.db.preregister_experiment(
            experiment_id="EXP-002",
            candidate_id="CAND-002",
            contract_dict=contract,
        )
        res_pending = validate_stage_preconditions(
            WorkflowStage.SOLUTION_STRATEGY,
            identifier="CAND-002",
            db_path=self.db_path,
        )
        self.assertFalse(res_pending.allowed)
        self.assertIn("pending experiment", res_pending.reason)

        # Complete experiment assessment as VALIDATED
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            UPDATE experiments
            SET outcome_verdict='PASSED', observed_value=0.75, sample_achieved=15, audited_by='Dr. Smith', audit_date='2026-09-27'
            WHERE experiment_id='EXP-002'
            """
        )
        conn.commit()
        conn.close()

        # Now ALLOWED for solution strategy
        res_ok = validate_stage_preconditions(
            WorkflowStage.SOLUTION_STRATEGY,
            identifier="CAND-002",
            db_path=self.db_path,
        )
        self.assertTrue(res_ok.allowed)

    def test_postcondition_verification(self) -> None:
        """Test verify_stage_postconditions behavior."""
        # Non-existent run
        ver_bad = verify_stage_postconditions(
            WorkflowStage.RESEARCH_PLANNING,
            identifier="RUN-NONEXISTENT",
            db_path=self.db_path,
        )
        self.assertFalse(ver_bad.verified)


if __name__ == "__main__":
    unittest.main()
