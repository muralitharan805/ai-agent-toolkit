# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Canonical persistence client for the Problem Discovery suites.

All SQLite schema ownership and mutations flow through this module.
Reasoning suites emit structured contracts and delegate persistence here.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class DiscoveryDB:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or os.getenv("DISCOVERY_DB_PATH", "discovery.sqlite")
        self._bootstrap()

    @property
    def _schema_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "discovery-db-schema.sql"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _bootstrap(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_connection()
        try:
            # Lightweight v1 migration: preserve stable candidate identity semantics.
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(candidates)").fetchall()]
            if cols and "research_id" in cols and "origin_research_id" not in cols:
                conn.execute("ALTER TABLE candidates RENAME COLUMN research_id TO origin_research_id")
                conn.commit()
            conn.executescript(self._schema_path.read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _json(value: Optional[Dict[str, Any]]) -> Optional[str]:
        return json.dumps(value, ensure_ascii=False, indent=2) if value is not None else None

    def create_research_run(
        self,
        research_id: str,
        request: str,
        domain: str,
        scope_type: str = "BROAD",
        geography: Optional[str] = None,
        plan_dict: Optional[Dict[str, Any]] = None,
    ) -> str:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO research_runs (
                    research_id, original_request, domain, scope_type, geography,
                    current_stage, status, plan_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'EVIDENCE_RESEARCH', 'ACTIVE', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(research_id) DO UPDATE SET
                    original_request = excluded.original_request,
                    domain = excluded.domain,
                    scope_type = excluded.scope_type,
                    geography = excluded.geography,
                    plan_json = excluded.plan_json,
                    current_stage = 'EVIDENCE_RESEARCH',
                    status = 'ACTIVE',
                    updated_at = CURRENT_TIMESTAMP
                """,
                (research_id, request, domain, scope_type, geography, self._json(plan_dict)),
            )
            conn.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (research_id,))
            conn.execute(
                "INSERT INTO discovery_fts(entity_id, entity_type, title_or_issue, body_text) VALUES (?, 'RUN', ?, ?)",
                (research_id, f"Research Run: {domain}", request),
            )
            conn.commit()
            return research_id
        finally:
            conn.close()

    def save_evidence_signals(self, research_id: str, signals: List[Dict[str, Any]]) -> int:
        conn = self._get_connection()
        try:
            inserted = 0
            for index, sig in enumerate(signals, start=1):
                source = sig.get("source", {}) if isinstance(sig.get("source"), dict) else {}
                actor = sig.get("actor", {}) if isinstance(sig.get("actor"), dict) else {}
                observation = sig.get("observation", {}) if isinstance(sig.get("observation"), dict) else {}
                evidence = sig.get("evidence", {}) if isinstance(sig.get("evidence"), dict) else {}

                signal_id = sig.get("signal_id") or f"SIG-{research_id}-{index:03d}"
                stream_id = sig.get("stream_id")
                platform = sig.get("platform") or source.get("platform") or "WEB"
                source_url = sig.get("source_url") or source.get("url")
                actor_role = sig.get("actor_role") or actor.get("role")
                reported_issue = sig.get("reported_issue") or observation.get("reported_issue")
                reported_workaround = sig.get("reported_workaround") or observation.get("reported_workaround")
                evidence_level = sig.get("evidence_level") or evidence.get("classification") or "UNASSESSED"
                if not reported_issue:
                    raise ValueError(f"Signal {signal_id} has no reported_issue")

                conn.execute(
                    """
                    INSERT INTO evidence_signals (
                        signal_id, research_id, candidate_id, stream_id, platform,
                        source_url, actor_role, reported_issue, reported_workaround,
                        evidence_level, payload_json, retrieved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(signal_id) DO UPDATE SET
                        research_id = excluded.research_id,
                        stream_id = excluded.stream_id,
                        platform = excluded.platform,
                        source_url = excluded.source_url,
                        actor_role = excluded.actor_role,
                        reported_issue = excluded.reported_issue,
                        reported_workaround = excluded.reported_workaround,
                        evidence_level = excluded.evidence_level,
                        payload_json = excluded.payload_json,
                        retrieved_at = CURRENT_TIMESTAMP
                    """,
                    (
                        signal_id, research_id, sig.get("candidate_id"), stream_id, platform,
                        source_url, actor_role, reported_issue, reported_workaround,
                        evidence_level, self._json(sig),
                    ),
                )
                conn.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (signal_id,))
                conn.execute(
                    "INSERT INTO discovery_fts(entity_id, entity_type, title_or_issue, body_text) VALUES (?, 'SIGNAL', ?, ?)",
                    (signal_id, reported_issue, reported_workaround or ""),
                )
                inserted += 1

            conn.execute(
                "UPDATE research_runs SET current_stage='PROBLEM_EVALUATION', updated_at=CURRENT_TIMESTAMP WHERE research_id=?",
                (research_id,),
            )
            conn.commit()
            return inserted
        finally:
            conn.close()

    def upsert_candidate(
        self,
        candidate_id: str,
        research_id: str,
        title: str,
        domain: str,
        target_operator: Optional[str] = None,
        track: str = "COMMERCIAL",
        research_score: Optional[int] = None,
        evidence_level: str = "UNASSESSED",
        lifecycle_status: str = "ACTIVE",
        evaluation_dict: Optional[Dict[str, Any]] = None,
        supporting_signal_ids: Optional[List[str]] = None,
    ) -> str:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO candidates (
                    candidate_id, origin_research_id, title, domain, target_operator, track,
                    research_score, evidence_level, validation_status, lifecycle_status,
                    evaluation_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(candidate_id) DO UPDATE SET
                    title = excluded.title,
                    domain = excluded.domain,
                    target_operator = excluded.target_operator,
                    track = excluded.track,
                    research_score = excluded.research_score,
                    evidence_level = excluded.evidence_level,
                    lifecycle_status = CASE
                        WHEN candidates.lifecycle_status IN ('ACTIVE', 'RESEARCH_PRIORITY', 'PARKED')
                            THEN excluded.lifecycle_status
                        ELSE candidates.lifecycle_status
                    END,
                    evaluation_json = excluded.evaluation_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    candidate_id, research_id, title, domain, target_operator, track,
                    research_score, evidence_level, lifecycle_status, self._json(evaluation_dict),
                ),
            )
            if supporting_signal_ids:
                placeholders = ",".join("?" for _ in supporting_signal_ids)
                params: List[Any] = [candidate_id, research_id, *supporting_signal_ids]
                conn.execute(
                    f"""
                    UPDATE evidence_signals
                    SET candidate_id = ?
                    WHERE research_id = ? AND signal_id IN ({placeholders})
                    """,
                    params,
                )

            conn.execute(
                "UPDATE research_runs SET current_stage='EXPERIMENT_VALIDATION', updated_at=CURRENT_TIMESTAMP WHERE research_id=?",
                (research_id,),
            )
            conn.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (candidate_id,))
            conn.execute(
                "INSERT INTO discovery_fts(entity_id, entity_type, title_or_issue, body_text) VALUES (?, 'CANDIDATE', ?, ?)",
                (candidate_id, title, f"{domain} {target_operator or ''}"),
            )
            conn.commit()
            return candidate_id
        finally:
            conn.close()

    def preregister_experiment(self, experiment_id: str, candidate_id: str, contract_dict: Dict[str, Any]) -> str:
        primary_metric = contract_dict.get("primary_metric", {})
        threshold = contract_dict.get("success_threshold", {})
        sample = contract_dict.get("sample", {})
        metric_name = primary_metric.get("name") or contract_dict.get("metric_name")
        target_threshold = threshold.get("value", contract_dict.get("target_threshold"))
        direction = threshold.get("operator", contract_dict.get("direction", ">="))
        sample_target = sample.get("target", contract_dict.get("sample_target"))
        hypothesis = contract_dict.get("hypothesis")
        if not all([hypothesis, metric_name, sample_target is not None, target_threshold is not None]):
            raise ValueError("Experiment contract is missing hypothesis, primary metric, threshold, or sample target")

        conn = self._get_connection()
        try:
            existing = conn.execute(
                "SELECT contract_json FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            contract_json = self._json(contract_dict)
            if existing and existing["contract_json"] != contract_json:
                raise ValueError("Preregistered experiment is immutable; create a new experiment_id for material changes")

            conn.execute(
                """
                INSERT INTO experiments (
                    experiment_id, candidate_id, hypothesis, metric_name, target_threshold,
                    direction, sample_target, outcome_verdict, contract_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PREREGISTERED', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(experiment_id) DO NOTHING
                """,
                (
                    experiment_id, candidate_id, hypothesis, metric_name,
                    float(target_threshold), direction, int(sample_target), contract_json,
                ),
            )
            conn.execute(
                """
                UPDATE candidates
                SET validation_status='IN_PROGRESS', lifecycle_status='VALIDATING', updated_at=CURRENT_TIMESTAMP
                WHERE candidate_id=?
                """,
                (candidate_id,),
            )
            conn.commit()
            return experiment_id
        finally:
            conn.close()

    def get_experiment_contract(self, experiment_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT contract_json FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Experiment '{experiment_id}' not found")
            return json.loads(row["contract_json"])
        finally:
            conn.close()

    def record_experiment_assessment(
        self,
        experiment_id: str,
        assessment_dict: Dict[str, Any],
        artifact_hash: Optional[str] = None,
        audited_by: Optional[str] = None,
        audit_date: Optional[str] = None,
    ) -> str:
        status = assessment_dict.get("status")
        verdict_map = {
            "EXPERIMENT_PASSED": "PASSED",
            "EXPERIMENT_FAILED": "FAILED",
            "INCOMPLETE": "INCOMPLETE",
            "INVALID_EXPERIMENT": "INVALID",
        }
        if status not in verdict_map:
            raise ValueError(f"Unsupported assessment status: {status}")
        verdict = verdict_map[status]
        observed = assessment_dict.get("observed_result", {}) or {}
        review = assessment_dict.get("artifact_review", {}) or {}

        conn = self._get_connection()
        try:
            exp = conn.execute(
                "SELECT candidate_id FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            if not exp:
                raise ValueError(f"Experiment '{experiment_id}' not found")
            candidate_id = exp["candidate_id"]

            conn.execute(
                """
                UPDATE experiments
                SET sample_achieved=?, observed_value=?, outcome_verdict=?,
                    assessment_json=?, artifact_hash=?, audited_by=?, audit_date=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE experiment_id=?
                """,
                (
                    observed.get("sample_achieved"),
                    observed.get("observed_value"),
                    verdict,
                    self._json(assessment_dict),
                    artifact_hash or review.get("sha256"),
                    audited_by or review.get("audited_by"),
                    audit_date or review.get("audit_date"),
                    experiment_id,
                ),
            )

            if verdict == "PASSED":
                validation_status, lifecycle, next_stage = "PARTIALLY_VALIDATED", "READY_FOR_SOLUTION", "SOLUTION_STRATEGY"
            elif verdict == "FAILED":
                validation_status, lifecycle, next_stage = "IN_PROGRESS", "RESEARCH_PRIORITY", "EXPERIMENT_VALIDATION"
            elif verdict == "INCOMPLETE":
                validation_status, lifecycle, next_stage = "IN_PROGRESS", "VALIDATING", "EXPERIMENT_VALIDATION"
            else:
                validation_status, lifecycle, next_stage = "UNVERIFIED", "RESEARCH_PRIORITY", "EXPERIMENT_VALIDATION"

            conn.execute(
                """
                UPDATE candidates
                SET validation_status=?, lifecycle_status=?, updated_at=CURRENT_TIMESTAMP
                WHERE candidate_id=?
                """,
                (validation_status, lifecycle, candidate_id),
            )
            conn.execute(
                """
                UPDATE research_runs
                SET current_stage=?, updated_at=CURRENT_TIMESTAMP
                WHERE research_id = (
                    SELECT COALESCE(
                        (
                            SELECT s.research_id
                            FROM evidence_signals s
                            WHERE s.candidate_id = ?
                            ORDER BY s.retrieved_at DESC
                            LIMIT 1
                        ),
                        c.origin_research_id
                    )
                    FROM candidates c
                    WHERE c.candidate_id = ?
                )
                """,
                (next_stage, candidate_id, candidate_id),
            )
            conn.commit()
            return experiment_id
        finally:
            conn.close()

    def finalize_solution(self, candidate_id: str, solution_class: str, solution_dict: Dict[str, Any]) -> str:
        conn = self._get_connection()
        try:
            candidate = conn.execute(
                "SELECT origin_research_id, validation_status FROM candidates WHERE candidate_id=?", (candidate_id,)
            ).fetchone()
            if not candidate:
                raise ValueError(f"Candidate '{candidate_id}' not found; refusing to fabricate a stub candidate")

            lifecycle = (
                "PILOT_READY"
                if candidate["validation_status"] in {"PARTIALLY_VALIDATED", "VALIDATED"}
                else "SOLUTION_PROPOSED"
            )
            conn.execute(
                """
                UPDATE candidates
                SET solution_class=?, lifecycle_status=?,
                    solution_json=?, updated_at=CURRENT_TIMESTAMP
                WHERE candidate_id=?
                """,
                (solution_class, lifecycle, self._json(solution_dict), candidate_id),
            )
            active_run = conn.execute(
                """
                SELECT rr.research_id
                FROM research_runs rr
                WHERE rr.status='ACTIVE'
                  AND (
                    rr.research_id = ?
                    OR rr.research_id IN (
                        SELECT DISTINCT research_id FROM evidence_signals WHERE candidate_id=?
                    )
                  )
                ORDER BY rr.updated_at DESC
                LIMIT 1
                """,
                (candidate["origin_research_id"], candidate_id),
            ).fetchone()
            run_id = active_run["research_id"] if active_run else candidate["origin_research_id"]
            conn.execute(
                """
                UPDATE research_runs
                SET current_stage='COMPLETED', status='COMPLETED', updated_at=CURRENT_TIMESTAMP
                WHERE research_id=?
                """,
                (run_id,),
            )
            conn.commit()
            return candidate_id
        finally:
            conn.close()

    def get_discovery_dashboard(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if status_filter:
                rows = conn.execute(
                    """
                    SELECT * FROM v_discovery_dashboard
                    WHERE lifecycle_status=? OR validation_status=?
                    ORDER BY updated_at DESC
                    """,
                    (status_filter, status_filter),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM v_discovery_dashboard ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search_fts(self, query: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            sql = """
                SELECT entity_id, entity_type, title_or_issue, body_text, rank
                FROM discovery_fts
                WHERE discovery_fts MATCH ?
            """
            params: List[Any] = [query]
            if entity_type:
                sql += " AND entity_type=?"
                params.append(entity_type)
            sql += " ORDER BY rank"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonical Problem Discovery state client")
    parser.add_argument("--db", default=os.getenv("DISCOVERY_DB_PATH", "discovery.sqlite"), help="Path to SQLite database")
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--filter-status")
    parser.add_argument("--search")
    parser.add_argument("--type")
    args = parser.parse_args()

    db = DiscoveryDB(args.db)
    if args.dashboard:
        print(json.dumps(db.get_discovery_dashboard(args.filter_status), indent=2))
    elif args.search:
        print(json.dumps(db.search_fts(args.search, args.type), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
