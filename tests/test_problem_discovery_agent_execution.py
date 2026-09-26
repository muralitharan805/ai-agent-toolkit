"""Regression tests proving the orchestrator stops at real-world experiment gates."""

from __future__ import annotations

import asyncio
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

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

    async def _fake_stage_agent(self, prompt: str) -> str:
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

    def test_backward_compatible_full_lifecycle_alias_also_pauses(self) -> None:
        self.agent._chat_sdk = self._fake_stage_agent
        summary = asyncio.run(
            self.agent.run_full_lifecycle(
                "Research whether multi-channel ecommerce inventory sync is a recurring problem."
            )
        )
        self.assertEqual(summary["workflow_status"], "PAUSED")
        self.assertEqual(summary["pause_reason"], "WAITING_FOR_REAL_WORLD_EXPERIMENT")


if __name__ == "__main__":
    unittest.main()
