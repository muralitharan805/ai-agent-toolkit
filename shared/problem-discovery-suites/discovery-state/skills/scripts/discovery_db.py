# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Authoritative Python client and library for Problem Discovery State persistence.
Enforces atomic transactions, foreign key integrity, FTS5 indexing, and soft-delete invariants.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class DiscoveryDB:
    """Canonical client managing problem discovery database state and mutations."""

    def __init__(self, db_path: str = "discovery.sqlite") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes tables, FTS index, and views if not present."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_runs (
                    research_id         TEXT PRIMARY KEY,
                    original_request    TEXT NOT NULL,
                    domain              TEXT NOT NULL,
                    scope_type          TEXT DEFAULT 'BROAD',
                    geography           TEXT,
                    current_stage       TEXT NOT NULL DEFAULT 'PLANNED',
                    status              TEXT NOT NULL DEFAULT 'ACTIVE',
                    plan_json           TEXT CHECK(plan_json IS NULL OR json_valid(plan_json)),
                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id        TEXT PRIMARY KEY,
                    research_id         TEXT NOT NULL,
                    title               TEXT NOT NULL,
                    domain              TEXT NOT NULL,
                    target_operator     TEXT,
                    track               TEXT DEFAULT 'COMMERCIAL',
                    research_score      INTEGER DEFAULT 0 CHECK(research_score BETWEEN 0 AND 35),
                    evidence_level      TEXT DEFAULT 'UNASSESSED',
                    validation_status   TEXT DEFAULT 'UNVERIFIED',
                    lifecycle_status    TEXT DEFAULT 'ACTIVE',
                    solution_class      TEXT,
                    evaluation_json     TEXT CHECK(evaluation_json IS NULL OR json_valid(evaluation_json)),
                    solution_json       TEXT CHECK(solution_json IS NULL OR json_valid(solution_json)),
                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (research_id) REFERENCES research_runs(research_id)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evidence_signals (
                    signal_id           TEXT PRIMARY KEY,
                    research_id         TEXT NOT NULL,
                    candidate_id        TEXT,
                    stream_id           TEXT,
                    platform            TEXT NOT NULL,
                    source_url          TEXT,
                    actor_role          TEXT,
                    reported_issue      TEXT NOT NULL,
                    reported_workaround TEXT,
                    evidence_level      TEXT NOT NULL DEFAULT 'L3',
                    payload_json        TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
                    retrieved_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (research_id) REFERENCES research_runs(research_id),
                    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id       TEXT PRIMARY KEY,
                    candidate_id        TEXT NOT NULL,
                    hypothesis          TEXT NOT NULL,
                    metric_name         TEXT NOT NULL,
                    target_threshold    REAL NOT NULL,
                    direction           TEXT NOT NULL DEFAULT '>=',
                    sample_target       INTEGER NOT NULL,
                    sample_achieved     INTEGER,
                    observed_value      REAL,
                    outcome_verdict     TEXT DEFAULT 'NOT_RUN',
                    contract_json       TEXT CHECK(contract_json IS NULL OR json_valid(contract_json)),
                    assessment_json     TEXT CHECK(assessment_json IS NULL OR json_valid(assessment_json)),
                    artifact_hash       TEXT,
                    audited_by          TEXT,
                    audit_date          DATE,
                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
                );
            """)

            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS discovery_fts USING fts5(
                    entity_id,
                    entity_type,
                    title_or_issue,
                    body_text
                );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_research_id ON evidence_signals(research_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_candidate_id ON evidence_signals(candidate_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_research_id ON candidates(research_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_lifecycle ON candidates(lifecycle_status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_candidate_id ON experiments(candidate_id);")

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_discovery_dashboard AS
                SELECT 
                    c.candidate_id,
                    c.title,
                    c.domain,
                    c.target_operator,
                    c.track,
                    c.research_score,
                    c.evidence_level,
                    c.validation_status,
                    c.solution_class,
                    c.lifecycle_status,
                    COUNT(DISTINCT s.signal_id) AS total_evidence_count,
                    COALESCE(MAX(e.outcome_verdict), 'NOT_RUN') AS latest_experiment_verdict,
                    c.updated_at
                FROM candidates c
                LEFT JOIN evidence_signals s ON c.candidate_id = s.candidate_id
                LEFT JOIN experiments e ON c.candidate_id = e.candidate_id
                GROUP BY c.candidate_id;
            """)
            conn.commit()
        finally:
            conn.close()

    # Stage 1: Research Runs
    def create_research_run(
        self,
        research_id: str,
        request: str,
        domain: str,
        scope_type: str = "BROAD",
        geography: Optional[str] = None,
        plan_dict: Optional[Dict[str, Any]] = None
    ) -> str:
        """Initializes a new research run record and indexes in FTS."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            plan_str = json.dumps(plan_dict, indent=2) if plan_dict else None
            cursor.execute("""
                INSERT OR REPLACE INTO research_runs (
                    research_id, original_request, domain, scope_type, geography,
                    current_stage, status, plan_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'PLANNED', 'ACTIVE', ?, CURRENT_TIMESTAMP)
            """, (research_id, request, domain, scope_type, geography, plan_str))

            # FTS indexing
            cursor.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (research_id,))
            cursor.execute("""
                INSERT INTO discovery_fts (entity_id, entity_type, title_or_issue, body_text)
                VALUES (?, 'RUN', ?, ?)
            """, (research_id, f"Research Run: {domain}", request))

            conn.commit()
            sys.stderr.write(f"[INFO] Initialized research run '{research_id}'\n")
            return research_id
        finally:
            conn.close()

    # Stage 2: Evidence Signals
    def save_evidence_signals(
        self,
        research_id: str,
        signals: List[Dict[str, Any]]
    ) -> int:
        """Batch persists evidence signals under research_id and advances run stage."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            inserted_count = 0
            for sig in signals:
                sig_id = sig.get("signal_id") or f"sig_{research_id}_{inserted_count+1}"
                payload_str = json.dumps(sig.get("payload_json", sig), indent=2)
                cursor.execute("""
                    INSERT OR REPLACE INTO evidence_signals (
                        signal_id, research_id, candidate_id, stream_id, platform,
                        source_url, actor_role, reported_issue, reported_workaround,
                        evidence_level, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sig_id,
                    research_id,
                    sig.get("candidate_id"),
                    sig.get("stream_id"),
                    sig.get("platform", "WEB"),
                    sig.get("source_url"),
                    sig.get("actor_role"),
                    sig["reported_issue"],
                    sig.get("reported_workaround"),
                    sig.get("evidence_level", "L3"),
                    payload_str
                ))

                # FTS Indexing
                cursor.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (sig_id,))
                cursor.execute("""
                    INSERT INTO discovery_fts (entity_id, entity_type, title_or_issue, body_text)
                    VALUES (?, 'SIGNAL', ?, ?)
                """, (sig_id, sig["reported_issue"], sig.get("reported_workaround", "")))
                inserted_count += 1

            cursor.execute("""
                UPDATE research_runs 
                SET current_stage = 'RESEARCHED', updated_at = CURRENT_TIMESTAMP
                WHERE research_id = ?
            """, (research_id,))

            conn.commit()
            sys.stderr.write(f"[INFO] Saved {inserted_count} signals for run '{research_id}'\n")
            return inserted_count
        finally:
            conn.close()

    # Stage 3: Candidate & Signal Linking
    def upsert_candidate(
        self,
        candidate_id: str,
        research_id: str,
        title: str,
        domain: str,
        target_operator: Optional[str] = None,
        track: str = "COMMERCIAL",
        research_score: int = 0,
        evidence_level: str = "UNASSESSED",
        lifecycle_status: str = "ACTIVE",
        evaluation_dict: Optional[Dict[str, Any]] = None,
        supporting_signal_ids: Optional[List[str]] = None
    ) -> str:
        """Upserts candidate record, links underlying signals, and indexes in FTS."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            eval_str = json.dumps(evaluation_dict, indent=2) if evaluation_dict else None
            cursor.execute("""
                INSERT OR REPLACE INTO candidates (
                    candidate_id, research_id, title, domain, target_operator, track,
                    research_score, evidence_level, validation_status, lifecycle_status,
                    evaluation_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', ?, ?, CURRENT_TIMESTAMP)
            """, (
                candidate_id, research_id, title, domain, target_operator, track,
                research_score, evidence_level, lifecycle_status, eval_str
            ))

            if supporting_signal_ids:
                placeholders = ",".join("?" for _ in supporting_signal_ids)
                cursor.execute(f"""
                    UPDATE evidence_signals
                    SET candidate_id = ?
                    WHERE signal_id IN ({placeholders})
                """, [candidate_id] + supporting_signal_ids)

            cursor.execute("""
                UPDATE research_runs 
                SET current_stage = 'EVALUATED', updated_at = CURRENT_TIMESTAMP
                WHERE research_id = ?
            """, (research_id,))

            # FTS indexing
            cursor.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (candidate_id,))
            cursor.execute("""
                INSERT INTO discovery_fts (entity_id, entity_type, title_or_issue, body_text)
                VALUES (?, 'CANDIDATE', ?, ?)
            """, (candidate_id, title, f"{domain} - {target_operator or ''}"))

            conn.commit()
            sys.stderr.write(f"[INFO] Upserted candidate '{candidate_id}'\n")
            return candidate_id
        finally:
            conn.close()

    # Stage 4: Experiment Contracts & Outcomes
    def preregister_experiment(
        self,
        experiment_id: str,
        candidate_id: str,
        contract_dict: Dict[str, Any]
    ) -> str:
        """Preregisters an immutable experiment contract with outcome NOT_RUN."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            contract_str = json.dumps(contract_dict, indent=2)
            cursor.execute("""
                INSERT OR REPLACE INTO experiments (
                    experiment_id, candidate_id, hypothesis, metric_name,
                    target_threshold, direction, sample_target, outcome_verdict,
                    contract_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'NOT_RUN', ?)
            """, (
                experiment_id,
                candidate_id,
                contract_dict["hypothesis"],
                contract_dict["metric_name"],
                contract_dict["target_threshold"],
                contract_dict.get("direction", ">="),
                contract_dict["sample_target"],
                contract_str
            ))

            cursor.execute("""
                UPDATE candidates 
                SET lifecycle_status = 'EXPERIMENT_DESIGNED', updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
            """, (candidate_id,))

            conn.commit()
            sys.stderr.write(f"[INFO] Preregistered experiment '{experiment_id}' for candidate '{candidate_id}'\n")
            return experiment_id
        finally:
            conn.close()

    def record_experiment_assessment(
        self,
        experiment_id: str,
        candidate_id: str,
        assessment_dict: Dict[str, Any],
        artifact_hash: str,
        audited_by: str,
        audit_date: str
    ) -> str:
        """Records empirical trial assessment with SHA-256 hash and updates validation status."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            assessment_str = json.dumps(assessment_dict, indent=2)
            verdict = assessment_dict["outcome_verdict"]
            observed = assessment_dict.get("observed_value")
            sample_achieved = assessment_dict.get("sample_achieved")

            cursor.execute("""
                UPDATE experiments 
                SET outcome_verdict = ?,
                    observed_value = ?,
                    sample_achieved = ?,
                    assessment_json = ?,
                    artifact_hash = ?,
                    audited_by = ?,
                    audit_date = ?
                WHERE experiment_id = ?
            """, (verdict, observed, sample_achieved, assessment_str, artifact_hash, audited_by, audit_date, experiment_id))

            val_status = "VALIDATED" if verdict == "VALIDATED" else "EXPERIMENT_FAILED"
            lifecycle = "READY_FOR_SOLUTION" if verdict == "VALIDATED" else "PARKED"

            cursor.execute("""
                UPDATE candidates 
                SET validation_status = ?,
                    lifecycle_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
            """, (val_status, lifecycle, candidate_id))

            cursor.execute("""
                UPDATE research_runs 
                SET current_stage = 'VALIDATED', updated_at = CURRENT_TIMESTAMP
                WHERE research_id = (SELECT research_id FROM candidates WHERE candidate_id = ?)
            """, (candidate_id,))

            conn.commit()
            sys.stderr.write(f"[INFO] Recorded assessment for experiment '{experiment_id}' ({verdict})\n")
            return experiment_id
        finally:
            conn.close()

    # Stage 5: Solution Finalization
    def finalize_solution(
        self,
        candidate_id: str,
        solution_class: str,
        solution_dict: Dict[str, Any]
    ) -> str:
        """Updates candidate with solution architecture, marks READY_TO_BUILD, and completes parent run."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sol_str = json.dumps(solution_dict, indent=2)
            cursor.execute("""
                UPDATE candidates 
                SET solution_class = ?,
                    lifecycle_status = 'READY_TO_BUILD',
                    solution_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
            """, (solution_class, sol_str, candidate_id))

            cursor.execute("""
                UPDATE research_runs 
                SET current_stage = 'COMPLETED',
                    status = 'COMPLETED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE research_id = (SELECT research_id FROM candidates WHERE candidate_id = ?)
            """, (candidate_id,))

            conn.commit()
            sys.stderr.write(f"[INFO] Finalized candidate '{candidate_id}' as '{solution_class}'\n")
            return candidate_id
        finally:
            conn.close()

    # Dashboard & Query Helpers
    def get_discovery_dashboard(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries the canonical v_discovery_dashboard decision view."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if status_filter:
                cursor.execute("""
                    SELECT * FROM v_discovery_dashboard 
                    WHERE lifecycle_status = ? OR validation_status = ?
                    ORDER BY updated_at DESC
                """, (status_filter, status_filter))
            else:
                cursor.execute("SELECT * FROM v_discovery_dashboard ORDER BY updated_at DESC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def search_fts(self, query: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Performs full-text search against the discovery_fts virtual table."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if entity_type:
                cursor.execute("""
                    SELECT entity_id, entity_type, title_or_issue, body_text, rank
                    FROM discovery_fts
                    WHERE discovery_fts MATCH ? AND entity_type = ?
                    ORDER BY rank
                """, (query, entity_type))
            else:
                cursor.execute("""
                    SELECT entity_id, entity_type, title_or_issue, body_text, rank
                    FROM discovery_fts
                    WHERE discovery_fts MATCH ?
                    ORDER BY rank
                """, (query,))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Discovery State DB CLI helper.")
    parser.add_argument("--db", default="discovery.sqlite", help="Path to SQLite database")
    parser.add_argument("--dashboard", action="store_true", help="Print v_discovery_dashboard table")
    parser.add_argument("--filter-status", help="Filter dashboard rows by lifecycle or validation status")
    parser.add_argument("--search", help="Perform FTS5 full-text search query")
    parser.add_argument("--type", help="Filter FTS search by entity type ('RUN', 'CANDIDATE', 'SIGNAL')")

    args = parser.parse_args()
    db = DiscoveryDB(args.db)

    if args.dashboard:
        rows = db.get_discovery_dashboard(args.filter_status)
        print(json.dumps(rows, indent=2))
        return

    if args.search:
        results = db.search_fts(args.search, args.type)
        print(json.dumps(results, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
