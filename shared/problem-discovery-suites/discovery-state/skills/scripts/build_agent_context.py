# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build bounded, task-specific context packs from the canonical discovery SQLite store."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


def _loads(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_problem_evaluation_context(conn: sqlite3.Connection, research_id: str) -> Dict[str, Any]:
    run = conn.execute(
        """
        SELECT research_id, domain, scope_type, original_request, geography, plan_json
        FROM research_runs WHERE research_id=?
        """,
        (research_id,),
    ).fetchone()
    if not run:
        raise ValueError(f"Research run '{research_id}' not found")

    plan = _loads(run["plan_json"])
    rows = conn.execute(
        """
        SELECT signal_id, stream_id, platform, source_url, actor_role,
               reported_issue, reported_workaround, evidence_level, payload_json
        FROM evidence_signals
        WHERE research_id=? AND candidate_id IS NULL
        ORDER BY retrieved_at ASC
        """,
        (research_id,),
    ).fetchall()

    signals: List[Dict[str, Any]] = []
    platforms: collections.Counter[str] = collections.Counter()
    levels: collections.Counter[str] = collections.Counter(
        {"UNASSESSED": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}
    )
    for row in rows:
        payload = _loads(row["payload_json"])
        signals.append(
            {
                "signal_id": row["signal_id"],
                "stream_id": row["stream_id"],
                "platform": row["platform"],
                "source_url": row["source_url"],
                "actor_role": row["actor_role"],
                "reported_issue": row["reported_issue"],
                "reported_workaround": row["reported_workaround"],
                "evidence_level": row["evidence_level"],
                "source_details": payload.get("source", {}),
                "evidence_details": payload.get("evidence", {}),
                "unknowns": payload.get("unknowns", []),
            }
        )
        platforms[row["platform"]] += 1
        levels[row["evidence_level"]] += 1

    candidate_matches = [
        dict(r)
        for r in conn.execute(
            """
            SELECT candidate_id, title, research_score, evidence_level,
                   validation_status, lifecycle_status
            FROM candidates
            WHERE domain=?
            ORDER BY updated_at DESC
            """,
            (run["domain"],),
        ).fetchall()
    ]

    return {
        "schema_version": "1.0",
        "task": "PROBLEM_EVALUATION",
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "research_run": {
            "research_id": run["research_id"],
            "domain": run["domain"],
            "scope_type": run["scope_type"],
            "geography": run["geography"],
            "original_request": run["original_request"],
        },
        "research_plan": {
            "research_streams": plan.get("research_streams", []),
            "unknowns": plan.get("unknowns", []),
            "assumptions": plan.get("assumptions", []),
        },
        "signals": signals,
        "deterministic_summary": {
            "total_signals": len(signals),
            "platform_breakdown": dict(platforms),
            "evidence_level_distribution": dict(levels),
            "existing_candidate_matches": candidate_matches,
        },
        "constraints": {
            "do_not_search_web": True,
            "enforce_14_nodes": True,
            "score_is_not_validation": True,
            "do_not_assign_new_stable_id_when_existing_root_problem_matches": True,
        },
    }


def build_experiment_validation_context(
    conn: sqlite3.Connection,
    candidate_id: str,
    mode: str = "DESIGN",
    experiment_id: Optional[str] = None,
) -> Dict[str, Any]:
    cand = conn.execute(
        """
        SELECT candidate_id, origin_research_id, title, domain, target_operator, track,
               research_score, evidence_level, validation_status, lifecycle_status,
               evaluation_json
        FROM candidates WHERE candidate_id=?
        """,
        (candidate_id,),
    ).fetchone()
    if not cand:
        raise ValueError(f"Candidate '{candidate_id}' not found")

    eval_data = _loads(cand["evaluation_json"])
    total_signals = conn.execute(
        "SELECT COUNT(*) AS cnt FROM evidence_signals WHERE candidate_id=?", (candidate_id,)
    ).fetchone()["cnt"]
    prior = [
        dict(r)
        for r in conn.execute(
            """
            SELECT experiment_id, hypothesis, metric_name, target_threshold, direction,
                   sample_target, sample_achieved, observed_value, outcome_verdict,
                   artifact_hash, created_at, updated_at
            FROM experiments
            WHERE candidate_id=?
            ORDER BY created_at DESC, experiment_id DESC
            """,
            (candidate_id,),
        ).fetchall()
    ]

    selected_contract: Optional[Dict[str, Any]] = None
    if mode.upper() == "ASSESS":
        if experiment_id:
            row = conn.execute(
                "SELECT contract_json FROM experiments WHERE experiment_id=? AND candidate_id=?",
                (experiment_id, candidate_id),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT contract_json FROM experiments
                WHERE candidate_id=? AND outcome_verdict='PREREGISTERED'
                ORDER BY created_at DESC, experiment_id DESC LIMIT 1
                """,
                (candidate_id,),
            ).fetchone()
        if not row:
            raise ValueError("ASSESS mode requires an existing preregistered experiment contract")
        selected_contract = _loads(row["contract_json"])

    pack: Dict[str, Any] = {
        "schema_version": "1.0",
        "task": "EXPERIMENT_VALIDATION",
        "mode": mode.upper(),
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "candidate_id": cand["candidate_id"],
            "origin_research_id": cand["origin_research_id"],
            "title": cand["title"],
            "domain": cand["domain"],
            "target_operator": cand["target_operator"],
            "track": cand["track"],
            "research_score": cand["research_score"],
            "evidence_level": cand["evidence_level"],
            "validation_status": cand["validation_status"],
            "lifecycle_status": cand["lifecycle_status"],
        },
        "evaluation": eval_data,
        "deterministic_summary": {
            "total_signals": total_signals,
            "prior_experiments_count": len(prior),
            "prior_experiments": prior,
        },
        "constraints": {
            "require_immutable_threshold": True,
            "single_primary_metric_only": True,
            "forbid_post_hoc_adjustments": True,
            "experiment_pass_does_not_equal_candidate_validation": True,
        },
    }
    if selected_contract is not None:
        pack["experiment_contract"] = selected_contract
    return pack


def build_solution_strategy_context(conn: sqlite3.Connection, candidate_id: str) -> Dict[str, Any]:
    cand = conn.execute(
        """
        SELECT candidate_id, origin_research_id, title, domain, target_operator, track,
               research_score, evidence_level, validation_status, lifecycle_status,
               evaluation_json, solution_json
        FROM candidates WHERE candidate_id=?
        """,
        (candidate_id,),
    ).fetchone()
    if not cand:
        raise ValueError(f"Candidate '{candidate_id}' not found")

    exp_rows = conn.execute(
        """
        SELECT experiment_id, metric_name, target_threshold, observed_value,
               outcome_verdict, assessment_json, audited_by, audit_date, created_at
        FROM experiments
        WHERE candidate_id=?
        ORDER BY created_at DESC, experiment_id DESC
        """,
        (candidate_id,),
    ).fetchall()
    experiments = []
    for row in exp_rows:
        item = dict(row)
        item["assessment"] = _loads(item.pop("assessment_json", None))
        experiments.append(item)

    passed = sum(1 for r in experiments if r["outcome_verdict"] == "PASSED")
    failed = sum(1 for r in experiments if r["outcome_verdict"] == "FAILED")
    total_signals = conn.execute(
        "SELECT COUNT(*) AS cnt FROM evidence_signals WHERE candidate_id=?", (candidate_id,)
    ).fetchone()["cnt"]

    latest_validation = {}
    if experiments:
        latest_validation = experiments[0].get("assessment", {}).get("validation_assessment", {})

    return {
        "schema_version": "1.0",
        "task": "SOLUTION_STRATEGY",
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "candidate_id": cand["candidate_id"],
            "origin_research_id": cand["origin_research_id"],
            "title": cand["title"],
            "domain": cand["domain"],
            "target_operator": cand["target_operator"],
            "track": cand["track"],
            "research_score": cand["research_score"],
            "evidence_level": cand["evidence_level"],
            "validation_status": cand["validation_status"],
            "lifecycle_status": cand["lifecycle_status"],
        },
        "evaluation": _loads(cand["evaluation_json"]),
        "validation_scope": latest_validation,
        "experiments_summary": {
            "total_trials": len(experiments),
            "passed": passed,
            "failed": failed,
            "latest_trial": experiments[0] if experiments else None,
        },
        "deterministic_summary": {
            "total_signals": total_signals,
            "prior_experiments_count": len(experiments),
        },
        "constraints": {
            "enforce_non_software_first": True,
            "unknown_requirements_cannot_justify_complexity": True,
            "gate_saas_speculation": True,
            "do_not_invent_pricing_or_wtp": True,
        },
    }


def build_discovery_query_context(conn: sqlite3.Connection, query: str, limit: int = 5) -> Dict[str, Any]:
    candidate_ids: List[str] = []
    direct_hits: List[Dict[str, Any]] = []

    exact = conn.execute(
        "SELECT candidate_id FROM candidates WHERE candidate_id=?",
        (query.strip(),),
    ).fetchone()
    if exact:
        candidate_ids.append(exact["candidate_id"])

    try:
        rows = conn.execute(
            """
            SELECT entity_id, entity_type, title_or_issue, body_text, rank
            FROM discovery_fts
            WHERE discovery_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, max(limit * 4, 20)),
        ).fetchall()
        direct_hits = [dict(r) for r in rows]
    except sqlite3.OperationalError:
        like = f"%{query}%"
        rows = conn.execute(
            """
            SELECT candidate_id AS entity_id, 'CANDIDATE' AS entity_type,
                   title AS title_or_issue, domain AS body_text, 0 AS rank
            FROM candidates
            WHERE candidate_id LIKE ? OR title LIKE ? OR domain LIKE ?
            LIMIT ?
            """,
            (like, like, like, max(limit * 4, 20)),
        ).fetchall()
        direct_hits = [dict(r) for r in rows]

    for hit in direct_hits:
        if hit["entity_type"] == "CANDIDATE":
            candidate_ids.append(hit["entity_id"])
        elif hit["entity_type"] == "SIGNAL":
            row = conn.execute(
                "SELECT candidate_id FROM evidence_signals WHERE signal_id=?", (hit["entity_id"],)
            ).fetchone()
            if row and row["candidate_id"]:
                candidate_ids.append(row["candidate_id"])

    # If FTS found only run-level text, surface recent candidates from those runs.
    run_ids = [h["entity_id"] for h in direct_hits if h["entity_type"] == "RUN"]
    for run_id in run_ids:
        rows = conn.execute(
            """
            SELECT DISTINCT candidate_id FROM evidence_signals
            WHERE research_id=? AND candidate_id IS NOT NULL
            """,
            (run_id,),
        ).fetchall()
        candidate_ids.extend(r["candidate_id"] for r in rows)

    deduped = []
    for cid in candidate_ids:
        if cid not in deduped:
            deduped.append(cid)
    deduped = deduped[:limit]

    matches: List[Dict[str, Any]] = []
    total_signals = 0
    for cid in deduped:
        dash = conn.execute(
            "SELECT * FROM v_discovery_dashboard WHERE candidate_id=?", (cid,)
        ).fetchone()
        if not dash:
            continue
        cand = conn.execute(
            "SELECT evaluation_json, solution_json, origin_research_id FROM candidates WHERE candidate_id=?",
            (cid,),
        ).fetchone()
        experiments = [
            dict(r)
            for r in conn.execute(
                """
                SELECT experiment_id, hypothesis, metric_name, target_threshold,
                       observed_value, outcome_verdict, audited_by, audit_date, created_at
                FROM experiments WHERE candidate_id=?
                ORDER BY created_at DESC, experiment_id DESC LIMIT 5
                """,
                (cid,),
            ).fetchall()
        ]
        summary = dict(dash)
        total_signals += summary["total_evidence_count"]
        matches.append(
            {
                "candidate": summary,
                "origin_research_id": cand["origin_research_id"],
                "evaluation": _loads(cand["evaluation_json"]),
                "solution": _loads(cand["solution_json"]),
                "recent_experiments": experiments,
            }
        )

    return {
        "schema_version": "1.0",
        "task": "DISCOVERY_QUERY",
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "matches": matches,
        "search_hits": direct_hits[: max(limit * 2, 10)],
        "deterministic_summary": {
            "total_signals": total_signals,
            "matched_candidates": len(matches),
        },
        "constraints": {
            "answer_from_persisted_discovery_state": True,
            "distinguish_database_facts_from_interpretation": True,
            "do_not_invent_missing_evidence": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build task-specific Problem Discovery context packs")
    parser.add_argument(
        "--task",
        required=True,
        choices=["problem-evaluation", "experiment-validation", "solution-strategy", "discovery-query"],
    )
    parser.add_argument("--db", default=os.getenv("DISCOVERY_DB_PATH", "discovery.sqlite"), help="Path to SQLite database")
    parser.add_argument("--research-id")
    parser.add_argument("--candidate-id")
    parser.add_argument("--experiment-id")
    parser.add_argument("--mode", default="DESIGN", choices=["DESIGN", "ASSESS"])
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output")
    args = parser.parse_args()

    conn = get_db_connection(args.db)
    try:
        if args.task == "problem-evaluation":
            if not args.research_id:
                raise ValueError("--research-id is required")
            pack = build_problem_evaluation_context(conn, args.research_id)
        elif args.task == "experiment-validation":
            if not args.candidate_id:
                raise ValueError("--candidate-id is required")
            pack = build_experiment_validation_context(conn, args.candidate_id, args.mode, args.experiment_id)
        elif args.task == "solution-strategy":
            if not args.candidate_id:
                raise ValueError("--candidate-id is required")
            pack = build_solution_strategy_context(conn, args.candidate_id)
        else:
            if not args.query:
                raise ValueError("--query is required for discovery-query")
            pack = build_discovery_query_context(conn, args.query, args.limit)

        encoded = json.dumps(pack, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(encoded + "\n")
        print(encoded)
    except ValueError as exc:
        sys.stderr.write(f"[ERROR] {exc}\n")
        raise SystemExit(2) from None
    finally:
        conn.close()


if __name__ == "__main__":
    main()
