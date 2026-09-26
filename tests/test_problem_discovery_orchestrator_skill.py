"""Unit tests for Problem Discovery Orchestrator Skill scripts and lifecycle transitions."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORCH_SCRIPTS = ROOT / "shared" / "problem-discovery-agent" / "skills" / "scripts"
STATE_SCRIPTS = ROOT / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


determine_next_stage_mod = load_module("determine_next_stage_under_test", ORCH_SCRIPTS / "determine_next_stage.py")
determine_next_stage = determine_next_stage_mod.determine_next_stage


class TestProblemDiscoveryOrchestratorSkill(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_discovery.sqlite"
        schema_file = (
            ROOT
            / "shared"
            / "problem-discovery-suites"
            / "discovery-state"
            / "skills"
            / "assets"
            / "discovery-db-schema.sql"
        )
        conn = sqlite3.connect(str(self.db_path))
        with open(schema_file, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_fresh_research_request_routes_to_planning(self) -> None:
        result = determine_next_stage(
            db_path=self.db_path,
            request="Research whether accounting firms struggle with recurring bank reconciliation",
        )
        self.assertEqual(result["action"], "INVOKE_SKILL")
        self.assertEqual(result["target_skill"], "research-planning")
        self.assertEqual(result["status"], "READY")

    def test_read_only_query_routes_to_query_database(self) -> None:
        result = determine_next_stage(
            db_path=self.db_path,
            request="CAND-001 status enna bro?",
        )
        self.assertEqual(result["action"], "QUERY_DATABASE")
        self.assertEqual(result["target_skill"], "discovery-state")
        self.assertEqual(result["target_task"], "discovery-query")
        self.assertEqual(result["status"], "READY")

    def test_run_with_plan_and_zero_signals_routes_to_evidence_research(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            INSERT INTO research_runs (research_id, original_request, domain, current_stage, plan_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("RUN-2026-001", "Test request", "FinTech", "RESEARCH_PLANNING", json.dumps({"status": "READY"})),
        )
        conn.commit()
        conn.close()

        result = determine_next_stage(
            db_path=self.db_path,
            run_id="RUN-2026-001",
        )
        self.assertEqual(result["action"], "INVOKE_SKILL")
        self.assertEqual(result["target_skill"], "evidence-research")
        self.assertEqual(result["entity_id"], "RUN-2026-001")

    def test_unverified_candidate_without_experiment_routes_to_experiment_design(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO research_runs (research_id, original_request, domain, current_stage) VALUES (?, ?, ?, ?)",
            ("RUN-2026-001", "Test", "FinTech", "EVALUATED"),
        )
        conn.execute(
            """
            INSERT INTO candidates (candidate_id, origin_research_id, title, domain, validation_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("CAND-001", "RUN-2026-001", "Reconciliation Friction", "FinTech", "UNVERIFIED"),
        )
        conn.commit()
        conn.close()

        result = determine_next_stage(
            db_path=self.db_path,
            candidate_id="CAND-001",
        )
        self.assertEqual(result["action"], "INVOKE_SKILL")
        self.assertEqual(result["target_skill"], "experiment-validation")
        self.assertEqual(result["mode"], "DESIGN")

    def test_preregistered_experiment_triggers_mandatory_pause(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO research_runs (research_id, original_request, domain, current_stage) VALUES (?, ?, ?, ?)",
            ("RUN-2026-001", "Test", "FinTech", "VALIDATING"),
        )
        conn.execute(
            """
            INSERT INTO candidates (candidate_id, origin_research_id, title, domain, validation_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("CAND-001", "RUN-2026-001", "Reconciliation Friction", "FinTech", "UNVERIFIED"),
        )
        conn.execute(
            """
            INSERT INTO experiments (experiment_id, candidate_id, hypothesis, metric_name, target_threshold, sample_target, outcome_verdict, contract_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("EXP-001", "CAND-001", "Test hypothesis", "mismatch_rate", 0.05, 10, "PREREGISTERED", json.dumps({"metric": "mismatch_rate"})),
        )
        conn.commit()
        conn.close()

        result = determine_next_stage(
            db_path=self.db_path,
            candidate_id="CAND-001",
            request="continue CAND-001",
        )
        self.assertEqual(result["action"], "PAUSE_FOR_HUMAN")
        self.assertEqual(result["status"], "PAUSED")
        self.assertEqual(result["pause_reason"], "WAITING_FOR_REAL_WORLD_EXPERIMENT")

    def test_preregistered_experiment_with_results_routes_to_assessment(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO research_runs (research_id, original_request, domain, current_stage) VALUES (?, ?, ?, ?)",
            ("RUN-2026-001", "Test", "FinTech", "VALIDATING"),
        )
        conn.execute(
            """
            INSERT INTO candidates (candidate_id, origin_research_id, title, domain, validation_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("CAND-001", "RUN-2026-001", "Reconciliation Friction", "FinTech", "UNVERIFIED"),
        )
        conn.execute(
            """
            INSERT INTO experiments (experiment_id, candidate_id, hypothesis, metric_name, target_threshold, sample_target, outcome_verdict, contract_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("EXP-001", "CAND-001", "Test hypothesis", "mismatch_rate", 0.05, 10, "PREREGISTERED", json.dumps({"metric": "mismatch_rate"})),
        )
        conn.commit()
        conn.close()

        result = determine_next_stage(
            db_path=self.db_path,
            candidate_id="CAND-001",
            request="continue CAND-001 results are ready. observed mean=0.03, sample_achieved=10",
        )
        self.assertEqual(result["action"], "INVOKE_SKILL")
        self.assertEqual(result["target_skill"], "experiment-validation")
        self.assertEqual(result["mode"], "ASSESS")

    def test_validated_candidate_routes_to_solution_strategy(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO research_runs (research_id, original_request, domain, current_stage) VALUES (?, ?, ?, ?)",
            ("RUN-2026-001", "Test", "FinTech", "VALIDATING"),
        )
        conn.execute(
            """
            INSERT INTO candidates (candidate_id, origin_research_id, title, domain, validation_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("CAND-001", "RUN-2026-001", "Reconciliation Friction", "FinTech", "VALIDATED"),
        )
        conn.commit()
        conn.close()

        result = determine_next_stage(
            db_path=self.db_path,
            candidate_id="CAND-001",
        )
        self.assertEqual(result["action"], "INVOKE_SKILL")
        self.assertEqual(result["target_skill"], "solution-strategy")
        self.assertEqual(result["status"], "READY")

    def test_finalized_candidate_reports_completed(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO research_runs (research_id, original_request, domain, current_stage) VALUES (?, ?, ?, ?)",
            ("RUN-2026-001", "Test", "FinTech", "COMPLETED"),
        )
        conn.execute(
            """
            INSERT INTO candidates (candidate_id, origin_research_id, title, domain, validation_status, solution_class, solution_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("CAND-001", "RUN-2026-001", "Reconciliation Friction", "FinTech", "VALIDATED", "INTEGRATION_CONNECTOR", json.dumps({"class": "INTEGRATION_CONNECTOR"})),
        )
        conn.commit()
        conn.close()

        result = determine_next_stage(
            db_path=self.db_path,
            candidate_id="CAND-001",
        )
        self.assertEqual(result["action"], "COMPLETE")
        self.assertEqual(result["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
