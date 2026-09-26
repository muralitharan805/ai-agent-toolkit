"""Regression tests proving the orchestrator stops at real-world experiment gates."""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from agents.problem_discovery.agent import ProblemDiscoveryAgent
from agents.problem_discovery.config import ProblemDiscoveryConfig


class ProblemDiscoveryRealExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "real_execution.sqlite")
        self.agent = ProblemDiscoveryAgent(
            config=ProblemDiscoveryConfig(db_path=self.db_path)
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    async def _fake_stage_agent(self, prompt: str, *args: Any, **kwargs: Any) -> str:
        """Simulate Antigravity tool usage without inventing experiment execution."""
        if "Use the research-planning skill." in prompt:
            run_id = re.search(r"Reserved research_id: (RUN-[0-9-]+)", prompt).group(1)
            request = prompt.split("Original user request:\n", 1)[1].split(
                "\n\nCreate a valid ResearchPlan", 1
            )[0].strip()
            plan = {
                "schema_version": "1.0",
                "research_id": run_id,
                "original_request": request,
                "scope": {
                    "domain": "ecommerce",
                    "scope_type": "NARROW",
                    "geography": None,
                },
                "research_streams": [
                    {
                        "stream_id": "RS-001",
                        "name": "Inventory operations",
                        "research_questions": ["Where is inventory synchronized manually?"],
                    }
                ],
                "unknowns": ["frequency"],
            }
            self.agent.tools_provider.create_research_run(
                research_id=run_id,
                request=request,
                domain="ecommerce",
                scope_type="NARROW",
                plan_dict=plan,
            )
            return "ResearchPlan persisted."

        if "Use the evidence-research skill" in prompt:
            run_id = re.search(r"research_id=(RUN-[0-9-]+)", prompt).group(1)
            self.agent.tools_provider.save_evidence_signals(
                run_id,
                [
                    {
                        "signal_id": f"SIG-{run_id}-001",
                        "stream_id": "RS-001",
                        "source": {
                            "platform": "FORUM",
                            "url": "https://example.test/real-reviewed-source",
                            "inspection_status": "FULL_SOURCE_REVIEWED",
                        },
                        "actor": {
                            "role": "multi-channel seller",
                            "role_is_self_reported": True,
                            "role_provenance": "SELF_REPORTED",
                        },
                        "observation": {
                            "reported_issue": "Inventory is manually reconciled between sales channels.",
                            "reported_workaround": "Spreadsheet reconciliation.",
                        },
                        "evidence": {
                            "classification": "L3",
                            "evidence_kind": "INDEPENDENT_CORROBORATION",
                            "independently_corroborated": True,
                            "human_audited_primary_evidence": False,
                            "verification_status": "CORROBORATED",
                        },
                    }
                ],
            )
            return "Reviewed signal persisted."

        if "Use the problem-evaluation skill." in prompt:
            run_id = re.search(r"research_id=(RUN-[0-9-]+)", prompt).group(1)
            candidate_id = re.search(
                r"reserved_new_candidate_id=(CAND-[0-9]+)", prompt
            ).group(1)
            signal_id = f"SIG-{run_id}-001"
            evaluation = {
                "problem_statement": "Sellers manually reconcile inventory across channels.",
                "research_score": {
                    "status": "SCORED",
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
            self.agent.tools_provider.upsert_candidate(
                candidate_id=candidate_id,
                research_id=run_id,
                title="Manual multi-channel inventory synchronization",
                domain="ecommerce",
                target_operator="multi-channel seller",
                evaluation_dict=evaluation,
                supporting_signal_ids=[signal_id],
            )
            return "Candidate persisted."

        if "experiment-validation in DESIGN mode" in prompt:
            candidate_id = re.search(r"candidate_id=(CAND-[0-9]+)", prompt).group(1)
            experiment_id = re.search(
                r"reserved_new_experiment_id=(EXP-[0-9]+)", prompt
            ).group(1)
            contract = {
                "schema_version": "1.0",
                "mode": "DESIGN",
                "status": "PREREGISTERED",
                "experiment_id": experiment_id,
                "candidate_id": candidate_id,
                "validation_target": "BEHAVIOR_FREQUENCY",
                "hypothesis": "Sellers perform repeated manual inventory synchronization.",
                "sample": {"target": 5, "minimum_usable": 5},
                "primary_metric": {"name": "manual_sync_events", "unit": "events"},
                "aggregation_rule": "MEAN_PER_PARTICIPANT",
                "success_threshold": {
                    "metric": "manual_sync_events",
                    "operator": ">=",
                    "value": 3,
                },
                "artifact_requirements": {"required": True, "expected_type": "CSV"},
                "review_requirements": {"human_review_required": True},
                "preregistration_locked": True,
            }
            self.agent.tools_provider.preregister_experiment(
                experiment_id=experiment_id,
                candidate_id=candidate_id,
                contract_dict=contract,
            )
            return "Experiment preregistered; waiting for real-world data."

        self.fail(f"Unexpected stage prompt: {prompt[:120]}")

    def test_new_research_runs_to_preregistered_experiment_then_pauses(self) -> None:
        self.agent._chat_sdk = self._fake_stage_agent
        visited = []

        result = asyncio.run(
            self.agent.run_until_blocked(
                "Research whether multi-channel ecommerce inventory sync is a recurring problem.",
                callback=lambda stage, data: visited.append(stage),
            )
        )

        self.assertEqual(result.workflow_status.value, "PAUSED")
        self.assertEqual(result.pause_reason, "WAITING_FOR_REAL_WORLD_EXPERIMENT")
        self.assertEqual(
            visited,
            [
                "RESEARCH_PLANNING",
                "EVIDENCE_RESEARCH",
                "PROBLEM_EVALUATION",
                "EXPERIMENT_VALIDATION",
            ],
        )

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM research_runs").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM evidence_signals").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0], 1)

            exp = conn.execute(
                "SELECT outcome_verdict, assessment_json, artifact_hash, audited_by, audit_date "
                "FROM experiments"
            ).fetchone()
            self.assertEqual(exp["outcome_verdict"], "PREREGISTERED")
            self.assertIsNone(exp["assessment_json"])
            self.assertIsNone(exp["artifact_hash"])
            self.assertIsNone(exp["audited_by"])
            self.assertIsNone(exp["audit_date"])

            candidate = conn.execute(
                "SELECT lifecycle_status, validation_status, solution_json FROM candidates"
            ).fetchone()
            self.assertEqual(candidate["lifecycle_status"], "VALIDATING")
            self.assertEqual(candidate["validation_status"], "IN_PROGRESS")
            self.assertIsNone(candidate["solution_json"])
        finally:
            conn.close()

    def test_exact_legacy_synthetic_fingerprint_blocks_further_reasoning(self) -> None:
        run_id = "RUN-2026-099"
        candidate_id = "CAND-099"
        experiment_id = "EXP-099"

        self.agent.tools_provider.create_research_run(
            research_id=run_id,
            request="Legacy synthetic demo state",
            domain="ops",
            plan_dict={
                "schema_version": "1.0",
                "research_id": run_id,
                "original_request": "Legacy synthetic demo state",
                "scope": {"domain": "ops", "scope_type": "NARROW", "geography": None},
                "research_streams": [],
                "unknowns": [],
            },
        )
        self.agent.tools_provider.upsert_candidate(
            candidate_id=candidate_id,
            research_id=run_id,
            title="Recurring Operational Friction & Manual Workarounds in Ops",
            domain="ops",
            evaluation_dict={"research_score": {"scores": {}}},
            supporting_signal_ids=[],
        )

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO experiments (
                    experiment_id, candidate_id, hypothesis, metric_name,
                    target_threshold, direction, sample_target, sample_achieved,
                    observed_value, outcome_verdict, contract_json,
                    assessment_json, artifact_hash, audited_by, audit_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    candidate_id,
                    "Synthetic legacy hypothesis",
                    "weekly_operational_interventions",
                    3.0,
                    ">=",
                    6,
                    6,
                    4.6,
                    "PASSED",
                    json.dumps({"aggregation_rule": "MEAN_PER_PARTICIPANT"}),
                    json.dumps({"status": "EXPERIMENT_PASSED"}),
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "Murali (Principal Architect & SeyaliCraft Lead)",
                    "2026-09-26",
                ),
            )
            conn.execute(
                """
                UPDATE candidates
                SET validation_status='PARTIALLY_VALIDATED',
                    lifecycle_status='READY_FOR_SOLUTION'
                WHERE candidate_id=?
                """,
                (candidate_id,),
            )
            conn.commit()
        finally:
            conn.close()

        self.agent._chat_sdk = AsyncMock(return_value="should not run")
        initial = self.agent.state_machine.evaluate_next_action(candidate_id)
        self.assertEqual(initial.current_stage.value, "SOLUTION_STRATEGY")

        result = asyncio.run(self.agent._run_existing_state_until_blocked(initial))

        self.assertEqual(result.workflow_status.value, "ERROR")
        self.assertEqual(result.next_action, "AUDIT_OR_RESET_LEGACY_SYNTHETIC_STATE")
        self.assertIn("removed synthetic end-to-end demo", result.message)
        self.agent._chat_sdk.assert_not_awaited()

    def test_backward_compatible_full_lifecycle_alias_also_pauses(self) -> None:
        self.agent._chat_sdk = self._fake_stage_agent
        summary = asyncio.run(
            self.agent.run_full_lifecycle(
                "Research whether multi-channel ecommerce inventory sync is a recurring problem."
            )
        )
        self.assertEqual(summary["workflow_status"], "PAUSED")
        self.assertEqual(summary["pause_reason"], "WAITING_FOR_REAL_WORLD_EXPERIMENT")

    def test_new_research_does_not_hijack_unrelated_candidate(self) -> None:
        """New research requests must create their own run and not hijack existing candidates via FTS."""
        # Seed an existing ecommerce candidate with common words 'manual' and 'spreadsheet'
        self.agent.tools_provider.create_research_run(
            research_id="RUN-2026-001",
            request="Ecommerce inventory research",
            domain="ecommerce",
            plan_dict={"schema_version": "1.0"},
        )
        self.agent.tools_provider.upsert_candidate(
            candidate_id="CAND-001",
            research_id="RUN-2026-001",
            title="Manual inventory sync causes stockouts",
            domain="ecommerce",
            evaluation_dict={"problem_statement": "Manual spreadsheet sync"},
        )

        self.agent._chat_sdk = self._fake_stage_agent
        result = asyncio.run(
            self.agent.run(
                "Research whether accountants frequently make manual spreadsheet errors when reconciling invoices"
            )
        )
        # Must create RUN-2026-002, not resume CAND-001
        self.assertEqual(result.research_id, "RUN-2026-002")
        self.assertNotIn("Reusing existing stable candidate", result.message)

    def test_incomplete_experiment_can_be_assessed_when_full_data_submitted(self) -> None:
        """An experiment previously marked INCOMPLETE must be assessable when full results are submitted."""
        self.agent.tools_provider.create_research_run(
            research_id="RUN-2026-001",
            request="Inventory sync research",
            domain="ecommerce",
            plan_dict={"schema_version": "1.0"},
        )
        self.agent.tools_provider.upsert_candidate(
            candidate_id="CAND-001",
            research_id="RUN-2026-001",
            title="Inventory sync issues",
            domain="ecommerce",
            evaluation_dict={"problem_statement": "Inventory sync issues"},
        )
        self.agent.tools_provider.preregister_experiment(
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
        # Mark as INCOMPLETE first
        self.agent.tools_provider.record_experiment_assessment(
            experiment_id="EXP-001",
            result_dict={
                "status": "INCOMPLETE",
                "sample_achieved": 2,
                "observed_value": 4.0,
                "audited_by": "Murali",
                "audit_date": "2026-09-26",
            },
        )

        conn = sqlite3.connect(self.db_path)
        try:
            verdict = conn.execute(
                "SELECT outcome_verdict FROM experiments WHERE experiment_id='EXP-001'"
            ).fetchone()[0]
            self.assertEqual(verdict, "INCOMPLETE")
        finally:
            conn.close()

        # Mock stage agent for the assessment turn
        async def fake_assessment(prompt: str, *args: Any, **kwargs: Any) -> str:
            self.agent.tools_provider.record_experiment_assessment(
                experiment_id="EXP-001",
                result_dict={
                    "status": "EXPERIMENT_PASSED",
                    "sample_achieved": 5,
                    "observed_value": 4.5,
                    "audited_by": "Murali",
                    "audit_date": "2026-09-26",
                    "artifact_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
                },
            )
            return "Assessment recorded."

        self.agent._chat_sdk = fake_assessment
        result = asyncio.run(
            self.agent.run(
                "EXP-001 trial result recorded. sample_achieved=5, observed mean=4.5, "
                "artifact hash a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0, "
                "audited_by Murali, audit_date 2026-09-26."
            )
        )
        self.assertEqual(result.intent.value, "EXPERIMENT_RESULT")
        # Experiment should now be PASSED
        conn = sqlite3.connect(self.db_path)
        try:
            new_verdict = conn.execute(
                "SELECT outcome_verdict FROM experiments WHERE experiment_id='EXP-001'"
            ).fetchone()[0]
            self.assertEqual(new_verdict, "PASSED")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
