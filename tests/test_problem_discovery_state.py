from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "shared" / "problem-discovery-suites"
STATE_SCRIPTS = SUITES / "discovery-state" / "skills" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


discovery_db = load_module("discovery_db_under_test", STATE_SCRIPTS / "discovery_db.py")
context_builder = load_module("context_builder_under_test", STATE_SCRIPTS / "build_agent_context.py")


class DiscoveryStateLifecycleTest(unittest.TestCase):
    def test_full_lifecycle_and_fresh_context_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "discovery.sqlite")
            db = discovery_db.DiscoveryDB(db_path)

            run_id = "RUN-2026-900"
            signal_id = "SIG-RUN-2026-900-001"
            candidate_id = "CAND-STATE-001"
            experiment_id = "EXP-STATE-001"

            plan = {
                "schema_version": "1.0",
                "research_id": run_id,
                "original_request": "Find ecommerce inventory workflow problems",
                "scope": {"domain": "ecommerce", "scope_type": "BROAD"},
                "research_streams": [
                    {
                        "stream_id": "RS-001",
                        "name": "Inventory operations",
                        "research_questions": ["Where is inventory updated manually?"],
                    }
                ],
                "unknowns": ["frequency"],
            }
            db.create_research_run(run_id, plan["original_request"], "ecommerce", plan_dict=plan)

            db.save_evidence_signals(
                run_id,
                [
                    {
                        "signal_id": signal_id,
                        "stream_id": "RS-001",
                        "source": {
                            "platform": "REDDIT",
                            "url": "https://example.test/signal",
                            "inspection_status": "SNIPPET_ONLY",
                        },
                        "actor": {"role": "ecommerce seller"},
                        "observation": {
                            "reported_issue": "Inventory is manually updated across marketplaces.",
                            "reported_workaround": "Open each marketplace dashboard.",
                        },
                        "evidence": {
                            "classification": "UNASSESSED",
                            "verification_status": "UNVERIFIED",
                        },
                    }
                ],
            )

            db.upsert_candidate(
                candidate_id=candidate_id,
                research_id=run_id,
                title="Manual multi-channel inventory synchronization",
                domain="ecommerce",
                target_operator="ecommerce seller",
                research_score=28,
                evidence_level="L3",
                lifecycle_status="RESEARCH_PRIORITY",
                evaluation_dict={
                    "problem_statement": "Some sellers manually synchronize inventory across channels.",
                    "supporting_signal_ids": [signal_id],
                },
                supporting_signal_ids=[signal_id],
            )

            contract = {
                "schema_version": "1.0",
                "mode": "DESIGN",
                "status": "PREREGISTERED",
                "experiment_id": experiment_id,
                "candidate_id": candidate_id,
                "validation_target": "BEHAVIOR_FREQUENCY",
                "hypothesis": "Target sellers repeatedly perform manual inventory synchronization.",
                "sample": {"target": 5, "minimum_usable": 5},
                "primary_metric": {"name": "manual_sync_events", "unit": "events"},
                "success_threshold": {"metric": "manual_sync_events", "operator": ">=", "value": 3},
                "preregistration_locked": True,
            }
            db.preregister_experiment(experiment_id, candidate_id, contract)

            assessment = {
                "schema_version": "1.0",
                "mode": "ASSESS",
                "experiment_id": experiment_id,
                "candidate_id": candidate_id,
                "status": "EXPERIMENT_PASSED",
                "experiment_completed": True,
                "experiment_passed": True,
                "observed_result": {"sample_achieved": 5, "observed_value": 4},
                "artifact_review": {
                    "sha256": "a" * 64,
                    "audited_by": "reviewer",
                    "audit_date": "2026-09-26",
                },
                "validation_assessment": {
                    "problem_behavior_observed": True,
                    "market_demand_validated": False,
                    "willingness_to_pay_validated": False,
                    "solution_adoption_validated": False,
                    "retention_validated": False,
                },
            }
            db.record_experiment_assessment(experiment_id, assessment)

            db.finalize_solution(
                candidate_id,
                "INTEGRATION_SERVICE",
                {"status": "SOLUTION_ASSESSED", "solution_class": "INTEGRATION_SERVICE"},
            )

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                candidate = conn.execute(
                    "SELECT * FROM candidates WHERE candidate_id=?", (candidate_id,)
                ).fetchone()
                self.assertEqual(candidate["origin_research_id"], run_id)
                self.assertEqual(candidate["validation_status"], "PARTIALLY_VALIDATED")
                self.assertEqual(candidate["lifecycle_status"], "PILOT_READY")

                run = conn.execute(
                    "SELECT current_stage, status FROM research_runs WHERE research_id=?", (run_id,)
                ).fetchone()
                self.assertEqual(run["current_stage"], "COMPLETED")
                self.assertEqual(run["status"], "COMPLETED")

                dashboard = conn.execute(
                    "SELECT * FROM v_discovery_dashboard WHERE candidate_id=?", (candidate_id,)
                ).fetchone()
                self.assertEqual(dashboard["total_evidence_count"], 1)
                self.assertEqual(dashboard["passed_experiments"], 1)
                self.assertEqual(dashboard["latest_experiment_verdict"], "PASSED")

                pack = context_builder.build_discovery_query_context(conn, candidate_id)
                self.assertEqual(pack["task"], "DISCOVERY_QUERY")
                self.assertEqual(pack["deterministic_summary"]["matched_candidates"], 1)
                self.assertEqual(pack["matches"][0]["candidate"]["candidate_id"], candidate_id)
            finally:
                conn.close()

            # A later run can attach new evidence to the same stable candidate
            # without overwriting its origin or regressing an advanced lifecycle state.
            run2 = "RUN-2026-901"
            signal2 = "SIG-RUN-2026-901-001"
            db.create_research_run(run2, "Revisit ecommerce inventory sync", "ecommerce", plan_dict={})
            db.save_evidence_signals(
                run2,
                [
                    {
                        "signal_id": signal2,
                        "stream_id": "RS-001",
                        "platform": "FORUM",
                        "reported_issue": "Another seller reports repeated manual stock updates.",
                        "evidence_level": "UNASSESSED",
                    }
                ],
            )
            db.upsert_candidate(
                candidate_id=candidate_id,
                research_id=run2,
                title="Manual multi-channel inventory synchronization",
                domain="ecommerce",
                target_operator="ecommerce seller",
                research_score=29,
                evidence_level="L3",
                lifecycle_status="RESEARCH_PRIORITY",
                evaluation_dict={"supporting_signal_ids": [signal2]},
                supporting_signal_ids=[signal2],
            )

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                candidate = conn.execute(
                    "SELECT origin_research_id, lifecycle_status FROM candidates WHERE candidate_id=?",
                    (candidate_id,),
                ).fetchone()
                self.assertEqual(candidate["origin_research_id"], run_id)
                self.assertEqual(candidate["lifecycle_status"], "PILOT_READY")
                linked_runs = conn.execute(
                    "SELECT COUNT(DISTINCT research_id) FROM evidence_signals WHERE candidate_id=?",
                    (candidate_id,),
                ).fetchone()[0]
                self.assertEqual(linked_runs, 2)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
