from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "shared" / "problem-discovery-suites"
STATE_SCRIPTS = SUITES / "discovery-state" / "skills" / "scripts"
EXPERIMENT_SCRIPT = (
    SUITES / "experiment-validation" / "skills" / "scripts" / "run_experiment_validation.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


discovery_db = load_module("discovery_db_under_test", STATE_SCRIPTS / "discovery_db.py")
context_builder = load_module("context_builder_under_test", STATE_SCRIPTS / "build_agent_context.py")
experiment_validation = load_module("experiment_validation_under_test", EXPERIMENT_SCRIPT)


def scored_evaluation(total: int = 28):
    # Total parameter is documentary only; persistence recomputes from dimensions.
    return {
        "problem_statement": "Observed operational friction.",
        "research_score": {
            "status": "SCORED",
            "total": total,
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


def corroborated_signal(signal_id: str, issue: str = "Repeated manual inventory synchronization."):
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


def experiment_contract(experiment_id: str, candidate_id: str):
    return {
        "schema_version": "1.0",
        "mode": "DESIGN",
        "status": "PREREGISTERED",
        "experiment_id": experiment_id,
        "candidate_id": candidate_id,
        "validation_target": "BEHAVIOR_FREQUENCY",
        "hypothesis": "Target sellers repeatedly perform manual inventory synchronization.",
        "sample": {"target": 5, "minimum_usable": 5},
        "period": {"duration_days": 7, "start_at": "2026-10-01"},
        "primary_metric": {"name": "manual_sync_events", "unit": "events"},
        "aggregation_rule": "MEAN_PER_PARTICIPANT",
        "success_threshold": {"metric": "manual_sync_events", "operator": ">=", "value": 3},
        "preregistration_locked": True,
    }


class DiscoveryStateLifecycleTest(unittest.TestCase):
    def test_full_lifecycle_and_fresh_context_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "discovery.sqlite")
            db = discovery_db.DiscoveryDB(db_path)

            run_id = "RUN-2026-900"
            signal_id = "SIG-RUN-2026-900-001"
            candidate_id = "CAND-STATE-001"
            experiment_id = "EXP-STATE-001"

            db.create_research_run(
                run_id,
                "Find ecommerce inventory workflow problems",
                "ecommerce",
                plan_dict={
                    "research_streams": [{"stream_id": "RS-001", "name": "Inventory operations"}]
                },
            )
            db.save_evidence_signals(run_id, [corroborated_signal(signal_id)])

            db.upsert_candidate(
                candidate_id=candidate_id,
                research_id=run_id,
                title="Manual multi-channel inventory synchronization",
                domain="ecommerce",
                target_operator="ecommerce seller",
                research_score=35,  # proposal is ignored in favor of deterministic dimensions
                evidence_level="L1",  # proposal is ignored in favor of supporting signals
                lifecycle_status="RESEARCH_PRIORITY",
                evaluation_dict=scored_evaluation(),
                supporting_signal_ids=[signal_id],
            )

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                candidate = conn.execute(
                    "SELECT research_score, evidence_level FROM candidates WHERE candidate_id=?",
                    (candidate_id,),
                ).fetchone()
                self.assertEqual(candidate["research_score"], 28)
                self.assertEqual(candidate["evidence_level"], "L3")
            finally:
                conn.close()

            contract = experiment_contract(experiment_id, candidate_id)
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
            finally:
                conn.close()

            # Weak rediscovery must not erase stronger existing candidate state.
            run2 = "RUN-2026-901"
            signal2 = "SIG-RUN-2026-901-001"
            db.create_research_run(run2, "Revisit ecommerce inventory sync", "ecommerce", plan_dict={})
            db.save_evidence_signals(
                run2,
                [
                    {
                        "signal_id": signal2,
                        "stream_id": "RS-001",
                        "source": {
                            "platform": "GITHUB",
                            "url": "https://example.test/raw",
                            "inspection_status": "SNIPPET_ONLY",
                        },
                        "actor": {
                            "role": "ecommerce seller",
                            "role_is_self_reported": False,
                            "role_provenance": "INFERRED",
                        },
                        "observation": {"reported_issue": "Possible stock update issue."},
                        "evidence": {
                            "classification": "L3",
                            "evidence_kind": "RAW_SEARCH_HIT",
                            "independently_corroborated": False,
                            "human_audited_primary_evidence": False,
                            "verification_status": "UNVERIFIED",
                        },
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
                evaluation_dict=scored_evaluation(),
                supporting_signal_ids=[signal2],
            )

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                candidate = conn.execute(
                    "SELECT origin_research_id, lifecycle_status, evidence_level, research_score "
                    "FROM candidates WHERE candidate_id=?",
                    (candidate_id,),
                ).fetchone()
                self.assertEqual(candidate["origin_research_id"], run_id)
                self.assertEqual(candidate["lifecycle_status"], "PILOT_READY")
                self.assertEqual(candidate["evidence_level"], "L3")
                self.assertEqual(candidate["research_score"], 28)
            finally:
                conn.close()

    def test_unassessed_snippet_cannot_be_promoted_or_claim_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = discovery_db.DiscoveryDB(str(Path(tmp) / "discovery.sqlite"))
            run_id = "RUN-RAW-001"
            signal_id = "SIG-RUN-RAW-001-001"
            db.create_research_run(run_id, "Find geocoding problems", "geo", plan_dict={})
            db.save_evidence_signals(
                run_id,
                [
                    {
                        "signal_id": signal_id,
                        "stream_id": "RS-001",
                        "source": {
                            "platform": "GITHUB",
                            "url": "https://example.test/raw-signal",
                            "inspection_status": "SNIPPET_ONLY",
                        },
                        "actor": {
                            "role": "logistics data analyst",
                            "role_is_self_reported": False,
                            "role_provenance": "INFERRED",
                        },
                        "observation": {"reported_issue": "A repository mentions a geocoding API."},
                        "evidence": {
                            "classification": "L3",
                            "evidence_kind": "RAW_SEARCH_HIT",
                            "independently_corroborated": False,
                            "human_audited_primary_evidence": False,
                            "verification_status": "UNVERIFIED",
                        },
                    }
                ],
            )
            db.upsert_candidate(
                "CAND-RAW-001",
                run_id,
                "Geocoding friction",
                "geo",
                target_operator="logistics data analyst",
                research_score=28,
                evidence_level="L3",
                lifecycle_status="RESEARCH_PRIORITY",
                evaluation_dict=scored_evaluation(),
                supporting_signal_ids=[signal_id],
            )

            conn = sqlite3.connect(db.db_path)
            conn.row_factory = sqlite3.Row
            try:
                signal = conn.execute(
                    "SELECT actor_role, evidence_level FROM evidence_signals WHERE signal_id=?",
                    (signal_id,),
                ).fetchone()
                candidate = conn.execute(
                    "SELECT research_score, evidence_level, lifecycle_status FROM candidates "
                    "WHERE candidate_id='CAND-RAW-001'"
                ).fetchone()
                self.assertIsNone(signal["actor_role"])
                self.assertEqual(signal["evidence_level"], "UNASSESSED")
                self.assertEqual(candidate["evidence_level"], "UNASSESSED")
                self.assertEqual(candidate["research_score"], 0)
                self.assertEqual(candidate["lifecycle_status"], "PARKED")
            finally:
                conn.close()

    def test_official_policy_does_not_promote_behavior_candidate_to_l1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = discovery_db.DiscoveryDB(str(Path(tmp) / "discovery.sqlite"))
            run_id = "RUN-POLICY-001"
            db.create_research_run(run_id, "Inventory policy and behavior", "ecommerce", plan_dict={})
            policy_id = "SIG-POLICY-001"
            community_id = "SIG-COMMUNITY-001"
            policy = {
                "signal_id": policy_id,
                "stream_id": "RS-001",
                "source": {
                    "platform": "WEB",
                    "url": "https://example.test/policy",
                    "inspection_status": "FULL_SOURCE_REVIEWED",
                },
                "actor": {
                    "role": None,
                    "role_is_self_reported": False,
                    "role_provenance": "SOURCE_VERIFIED",
                },
                "observation": {"reported_issue": "Official cancellation-rate policy."},
                "evidence": {
                    "classification": "L1",
                    "evidence_kind": "OFFICIAL_POLICY",
                    "independently_corroborated": True,
                    "human_audited_primary_evidence": True,
                    "verification_status": "CORROBORATED",
                },
            }
            db.save_evidence_signals(run_id, [policy, corroborated_signal(community_id)])
            db.upsert_candidate(
                "CAND-POLICY-001",
                run_id,
                "Inventory desynchronization",
                "ecommerce",
                research_score=30,
                evidence_level="L1",
                evaluation_dict=scored_evaluation(),
                supporting_signal_ids=[policy_id, community_id],
            )

            conn = sqlite3.connect(db.db_path)
            conn.row_factory = sqlite3.Row
            try:
                candidate = conn.execute(
                    "SELECT evidence_level FROM candidates WHERE candidate_id='CAND-POLICY-001'"
                ).fetchone()
                self.assertEqual(candidate["evidence_level"], "L3")
            finally:
                conn.close()

    def test_run_does_not_complete_while_another_candidate_is_validating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = discovery_db.DiscoveryDB(str(Path(tmp) / "discovery.sqlite"))
            run_id = "RUN-MULTI-001"
            db.create_research_run(run_id, "Find multiple problems", "ops", plan_dict={})

            for n in (1, 2):
                signal_id = f"SIG-RUN-MULTI-001-00{n}"
                candidate_id = f"CAND-MULTI-00{n}"
                db.save_evidence_signals(run_id, [corroborated_signal(signal_id, f"Problem {n}")])
                db.upsert_candidate(
                    candidate_id,
                    run_id,
                    f"Problem {n}",
                    "ops",
                    research_score=28,
                    evidence_level="L3",
                    evaluation_dict=scored_evaluation(),
                    supporting_signal_ids=[signal_id],
                )

            c1 = experiment_contract("EXP-MULTI-001", "CAND-MULTI-001")
            db.preregister_experiment("EXP-MULTI-001", "CAND-MULTI-001", c1)
            db.record_experiment_assessment(
                "EXP-MULTI-001",
                {
                    "status": "EXPERIMENT_PASSED",
                    "observed_result": {"sample_achieved": 5, "observed_value": 4},
                    "artifact_review": {
                        "sha256": "b" * 64,
                        "audited_by": "reviewer",
                        "audit_date": "2026-09-26",
                    },
                },
            )
            db.finalize_solution("CAND-MULTI-001", "LOCAL_SCRIPT", {"solution_class": "LOCAL_SCRIPT"})

            c2 = experiment_contract("EXP-MULTI-002", "CAND-MULTI-002")
            db.preregister_experiment("EXP-MULTI-002", "CAND-MULTI-002", c2)

            conn = sqlite3.connect(db.db_path)
            conn.row_factory = sqlite3.Row
            try:
                run = conn.execute(
                    "SELECT current_stage, status FROM research_runs WHERE research_id=?",
                    (run_id,),
                ).fetchone()
                self.assertEqual(run["current_stage"], "EXPERIMENT_VALIDATION")
                self.assertEqual(run["status"], "ACTIVE")
            finally:
                conn.close()

            with self.assertRaises(ValueError):
                db.finalize_solution(
                    "CAND-MULTI-002",
                    "LOCAL_SCRIPT",
                    {"solution_class": "LOCAL_SCRIPT"},
                )

    def test_compound_experiment_metric_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            experiment_validation.design_experiment(
                candidate_id="CAND-001",
                hypothesis="Manual sync or stockout events recur.",
                primary_metric="manual_sync_or_stockout_events_per_week",
                target_threshold=3,
                aggregation_rule="MEAN_PER_PARTICIPANT",
            )

    def test_integrity_repair_downgrades_legacy_unassessed_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = discovery_db.DiscoveryDB(str(Path(tmp) / "discovery.sqlite"))
            run_id = "RUN-LEGACY-001"
            signal_id = "SIG-LEGACY-001"
            db.create_research_run(run_id, "Legacy research", "geo", plan_dict={})
            db.save_evidence_signals(
                run_id,
                [
                    {
                        "signal_id": signal_id,
                        "stream_id": "RS-001",
                        "source": {
                            "platform": "GITHUB",
                            "url": "https://example.test/legacy",
                            "inspection_status": "SNIPPET_ONLY",
                        },
                        "actor": {
                            "role": "survey technician",
                            "role_is_self_reported": False,
                            "role_provenance": "INFERRED",
                        },
                        "observation": {"reported_issue": "Possible CRS issue."},
                        "evidence": {
                            "classification": "UNASSESSED",
                            "evidence_kind": "RAW_SEARCH_HIT",
                            "independently_corroborated": False,
                            "human_audited_primary_evidence": False,
                            "verification_status": "UNVERIFIED",
                        },
                    }
                ],
            )
            db.upsert_candidate(
                "CAND-LEGACY-001",
                run_id,
                "CRS issue",
                "geo",
                evaluation_dict=scored_evaluation(),
                supporting_signal_ids=[signal_id],
            )

            # Simulate a pre-guardrail corrupt row.
            conn = sqlite3.connect(db.db_path)
            try:
                conn.execute(
                    """
                    UPDATE candidates
                    SET evidence_level='L3', research_score=19,
                        lifecycle_status='SOLUTION_PROPOSED',
                        solution_json='{"solution_class":"STATIC_SITE_OR_JAMSTACK"}'
                    WHERE candidate_id='CAND-LEGACY-001'
                    """
                )
                conn.execute(
                    "UPDATE evidence_signals SET actor_role='survey technician' WHERE signal_id=?",
                    (signal_id,),
                )
                conn.execute(
                    "UPDATE research_runs SET current_stage='COMPLETED', status='COMPLETED' WHERE research_id=?",
                    (run_id,),
                )
                conn.commit()
            finally:
                conn.close()

            result = db.repair_integrity()
            self.assertEqual(result["repaired_candidates"], 1)

            conn = sqlite3.connect(db.db_path)
            conn.row_factory = sqlite3.Row
            try:
                candidate = conn.execute(
                    "SELECT evidence_level, research_score FROM candidates WHERE candidate_id='CAND-LEGACY-001'"
                ).fetchone()
                signal = conn.execute(
                    "SELECT actor_role FROM evidence_signals WHERE signal_id=?", (signal_id,)
                ).fetchone()
                run = conn.execute(
                    "SELECT current_stage, status FROM research_runs WHERE research_id=?", (run_id,)
                ).fetchone()
                self.assertEqual(candidate["evidence_level"], "UNASSESSED")
                self.assertEqual(candidate["research_score"], 0)
                self.assertIsNone(signal["actor_role"])
                self.assertEqual(run["current_stage"], "SOLUTION_STRATEGY")
                self.assertEqual(run["status"], "ACTIVE")
            finally:
                conn.close()

    def test_sample_count_omission_cannot_pass_experiment(self) -> None:
        """Audited PASSED/FAILED cannot bypass sample_achieved threshold validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = discovery_db.DiscoveryDB(str(Path(tmpdir) / "sample_test.sqlite"))
            run_id = "RUN-2026-001"
            db.create_research_run(run_id, "Test request", "ecommerce", plan_dict={})
            db.upsert_candidate(
                "CAND-001",
                run_id,
                "Test problem",
                "ecommerce",
                evaluation_dict=scored_evaluation(),
            )
            db.preregister_experiment(
                "EXP-001",
                "CAND-001",
                {
                    "hypothesis": "Test hypothesis",
                    "metric_name": "intervention_rate",
                    "aggregation_rule": "MEAN_PER_PARTICIPANT",
                    "success_threshold": {"value": 3.0, "operator": ">="},
                    "sample": {"target": 5, "minimum_usable": 5},
                    "artifact_requirements": {"required": True},
                    "review_requirements": {"human_review_required": True},
                },
            )

            # Attempting to PASS with sample_achieved omitted/None must raise ValueError
            with self.assertRaises(ValueError) as ctx:
                db.record_experiment_assessment(
                    "EXP-001",
                    {
                        "status": "EXPERIMENT_PASSED",
                        "observed_result": {"sample_achieved": None, "observed_value": 4.5},
                        "artifact_review": {
                            "sha256": "a" * 64,
                            "audited_by": "Murali",
                            "audit_date": "2026-09-26",
                        },
                    },
                )
            self.assertIn("requires sample_achieved", str(ctx.exception))

            # Attempting to PASS with sample_achieved < minimum_usable (e.g. 2 < 5) must raise ValueError
            with self.assertRaises(ValueError) as ctx2:
                db.record_experiment_assessment(
                    "EXP-001",
                    {
                        "status": "EXPERIMENT_PASSED",
                        "observed_result": {"sample_achieved": 2, "observed_value": 4.5},
                        "artifact_review": {
                            "sha256": "a" * 64,
                            "audited_by": "Murali",
                            "audit_date": "2026-09-26",
                        },
                    },
                )
            self.assertIn("minimum usable", str(ctx2.exception).lower())

    def test_successive_signal_saves_do_not_overwrite_earlier_batches(self) -> None:
        """Batch 2 without explicit IDs must append new unique signal IDs instead of overwriting batch 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = discovery_db.DiscoveryDB(str(Path(tmpdir) / "signals_test.sqlite"))
            run_id = "RUN-2026-001"
            db.create_research_run(run_id, "Test request", "ecommerce", plan_dict={})

            def make_raw_sig(issue: str) -> dict:
                return {
                    "source": {"platform": "WEB", "url": "https://example.test", "inspection_status": "FULL_SOURCE_REVIEWED"},
                    "actor": {"role": "ops seller", "role_is_self_reported": True},
                    "observation": {"reported_issue": issue},
                    "evidence": {"classification": "L4"},
                }

            # Batch 1: 2 signals
            db.save_evidence_signals(run_id, [make_raw_sig("Issue 1"), make_raw_sig("Issue 2")])
            # Batch 2: 2 more signals without explicit signal_ids
            db.save_evidence_signals(run_id, [make_raw_sig("Issue 3"), make_raw_sig("Issue 4")])

            conn = sqlite3.connect(db.db_path)
            try:
                rows = conn.execute(
                    "SELECT signal_id, reported_issue FROM evidence_signals WHERE research_id=? ORDER BY signal_id",
                    (run_id,),
                ).fetchall()
                self.assertEqual(len(rows), 4)
                ids = [r[0] for r in rows]
                self.assertEqual(
                    ids,
                    [
                        f"SIG-{run_id}-001",
                        f"SIG-{run_id}-002",
                        f"SIG-{run_id}-003",
                        f"SIG-{run_id}-004",
                    ],
                )
                issues = [r[1] for r in rows]
                self.assertEqual(issues, ["Issue 1", "Issue 2", "Issue 3", "Issue 4"])
            finally:
                conn.close()

    def test_unassigned_signals_prevent_run_completion_even_if_candidate_parked(self) -> None:
        """Unassigned evidence signals must prevent research_runs from prematurely becoming COMPLETED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = discovery_db.DiscoveryDB(str(Path(tmpdir) / "completion_test.sqlite"))
            run_id = "RUN-2026-001"
            db.create_research_run(run_id, "Test request", "ecommerce", plan_dict={})

            # Candidate 1 is PARKED (terminal)
            db.upsert_candidate(
                "CAND-001",
                run_id,
                "Candidate 1",
                "ecommerce",
                lifecycle_status="PARKED",
                evaluation_dict=scored_evaluation(),
            )

            # Add an unassigned signal
            db.save_evidence_signals(
                run_id,
                [
                    {
                        "source": {"platform": "WEB", "url": "https://example.test", "inspection_status": "FULL_SOURCE_REVIEWED"},
                        "actor": {"role": "ops seller", "role_is_self_reported": True},
                        "observation": {"reported_issue": "Pending unassigned friction"},
                        "evidence": {"classification": "L4"},
                    }
                ],
            )

            state = db.refresh_research_run_state(run_id)
            self.assertEqual(state["current_stage"], "PROBLEM_EVALUATION")
            self.assertEqual(state["status"], "ACTIVE")
            self.assertNotEqual(state["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
