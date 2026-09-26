# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Dynamic Context Pack Builder.
Assembles task-specific, bounded, JSON-serializable Context Packs for downstream reasoning agents.
Eliminates SQL boilerplate in prompts and computes quantitative distributions deterministically.
"""

from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def build_problem_evaluation_context(
    conn: sqlite3.Connection,
    research_id: str
) -> Dict[str, Any]:
    """Assembles Context Pack for problem-evaluation agent."""
    cursor = conn.cursor()

    # 1. Fetch Research Run
    cursor.execute("""
        SELECT research_id, domain, scope_type, original_request, plan_json
        FROM research_runs WHERE research_id = ?
    """, (research_id,))
    run_row = cursor.fetchone()
    if not run_row:
        raise ValueError(f"Research run '{research_id}' not found in database.")

    plan_data = json.loads(run_row["plan_json"]) if run_row["plan_json"] else {}

    # 2. Fetch Unlinked Signals for this run
    cursor.execute("""
        SELECT signal_id, stream_id, platform, source_url, actor_role,
               reported_issue, reported_workaround, evidence_level, payload_json
        FROM evidence_signals
        WHERE research_id = ? AND (candidate_id IS NULL OR candidate_id = '')
        ORDER BY retrieved_at ASC
    """, (research_id,))
    signal_rows = cursor.fetchall()

    signals: List[Dict[str, Any]] = []
    platform_counter: collections.Counter = collections.Counter()
    evidence_counter: collections.Counter = collections.Counter({"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0})

    for row in signal_rows:
        sig = {
            "signal_id": row["signal_id"],
            "stream_id": row["stream_id"],
            "platform": row["platform"],
            "source_url": row["source_url"],
            "actor_role": row["actor_role"],
            "reported_issue": row["reported_issue"],
            "reported_workaround": row["reported_workaround"],
            "evidence_level": row["evidence_level"]
        }
        signals.append(sig)
        platform_counter[row["platform"]] += 1
        evidence_counter[row["evidence_level"]] += 1

    # 3. Check for existing candidates in domain
    cursor.execute("""
        SELECT candidate_id, title, research_score, validation_status
        FROM candidates WHERE domain = ?
    """, (run_row["domain"],))
    candidate_matches = [dict(r) for r in cursor.fetchall()]

    return {
        "schema_version": "1.0",
        "task": "PROBLEM_EVALUATION",
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "research_run": {
            "research_id": run_row["research_id"],
            "domain": run_row["domain"],
            "scope_type": run_row["scope_type"],
            "original_request": run_row["original_request"]
        },
        "research_plan": {
            "streams": plan_data.get("streams", []),
            "unknowns": plan_data.get("unknowns", [])
        },
        "signals": signals,
        "deterministic_summary": {
            "total_signals": len(signals),
            "platform_breakdown": dict(platform_counter),
            "evidence_level_distribution": dict(evidence_counter),
            "existing_candidate_matches": candidate_matches
        },
        "constraints": {
            "do_not_search_web": True,
            "max_allowed_evidence_score_per_dim": 3 if evidence_counter.get("L3", 0) > 0 and evidence_counter.get("L1", 0) == 0 else 5,
            "enforce_14_nodes": True
        }
    }


def build_experiment_validation_context(
    conn: sqlite3.Connection,
    candidate_id: str,
    mode: str = "DESIGN"
) -> Dict[str, Any]:
    """Assembles Context Pack for experiment-validation agent."""
    cursor = conn.cursor()

    # 1. Fetch Candidate
    cursor.execute("""
        SELECT candidate_id, research_id, title, domain, target_operator, track,
               research_score, evidence_level, validation_status, lifecycle_status,
               evaluation_json
        FROM candidates WHERE candidate_id = ?
    """, (candidate_id,))
    cand_row = cursor.fetchone()
    if not cand_row:
        raise ValueError(f"Candidate '{candidate_id}' not found in database.")

    eval_data = json.loads(cand_row["evaluation_json"]) if cand_row["evaluation_json"] else {}

    # 2. Fetch Supporting Signals Count
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM evidence_signals WHERE candidate_id = ?
    """, (candidate_id,))
    signals_count = cursor.fetchone()["cnt"]

    # 3. Fetch Prior Experiments
    cursor.execute("""
        SELECT experiment_id, hypothesis, metric_name, target_threshold,
               observed_value, outcome_verdict, artifact_hash
        FROM experiments WHERE candidate_id = ?
        ORDER BY created_at DESC
    """, (candidate_id,))
    prior_exps = [dict(r) for r in cursor.fetchall()]

    return {
        "schema_version": "1.0",
        "task": "EXPERIMENT_VALIDATION",
        "mode": mode.upper(),
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "candidate_id": cand_row["candidate_id"],
            "research_id": cand_row["research_id"],
            "title": cand_row["title"],
            "domain": cand_row["domain"],
            "target_operator": cand_row["target_operator"],
            "track": cand_row["track"],
            "research_score": cand_row["research_score"],
            "evidence_level": cand_row["evidence_level"],
            "validation_status": cand_row["validation_status"],
            "lifecycle_status": cand_row["lifecycle_status"]
        },
        "evaluation_summary": {
            "core_friction": eval_data.get("core_friction") or eval_data.get("root_cause_analysis", {}).get("root_cause"),
            "target_operator": cand_row["target_operator"],
            "current_glue_work": eval_data.get("current_glue_work"),
            "observed_costs": eval_data.get("observed_costs")
        },
        "deterministic_summary": {
            "total_signals": signals_count,
            "prior_experiments_count": len(prior_exps),
            "prior_experiments": prior_exps
        },
        "constraints": {
            "require_immutable_threshold": True,
            "single_primary_metric_only": True,
            "require_symmetrical_failure_rule": True,
            "forbid_post_hoc_adjustments": True
        }
    }


def build_solution_strategy_context(
    conn: sqlite3.Connection,
    candidate_id: str
) -> Dict[str, Any]:
    """Assembles Context Pack for solution-strategy agent."""
    cursor = conn.cursor()

    # 1. Fetch Candidate
    cursor.execute("""
        SELECT candidate_id, research_id, title, domain, target_operator, track,
               research_score, evidence_level, validation_status, lifecycle_status,
               evaluation_json
        FROM candidates WHERE candidate_id = ?
    """, (candidate_id,))
    cand_row = cursor.fetchone()
    if not cand_row:
        raise ValueError(f"Candidate '{candidate_id}' not found in database.")

    eval_data = json.loads(cand_row["evaluation_json"]) if cand_row["evaluation_json"] else {}

    # 2. Fetch Experiments Summary
    cursor.execute("""
        SELECT experiment_id, metric_name, target_threshold, observed_value,
               outcome_verdict, audited_by, audit_date
        FROM experiments WHERE candidate_id = ?
        ORDER BY created_at DESC
    """, (candidate_id,))
    exp_rows = cursor.fetchall()

    passed_count = sum(1 for r in exp_rows if r["outcome_verdict"] == "VALIDATED")
    failed_count = sum(1 for r in exp_rows if r["outcome_verdict"] == "EXPERIMENT_FAILED")
    latest_trial = dict(exp_rows[0]) if exp_rows else None

    # 3. Fetch Signal Count
    cursor.execute("SELECT COUNT(*) AS cnt FROM evidence_signals WHERE candidate_id = ?", (candidate_id,))
    sig_count = cursor.fetchone()["cnt"]

    return {
        "schema_version": "1.0",
        "task": "SOLUTION_STRATEGY",
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "candidate_id": cand_row["candidate_id"],
            "research_id": cand_row["research_id"],
            "title": cand_row["title"],
            "domain": cand_row["domain"],
            "target_operator": cand_row["target_operator"],
            "track": cand_row["track"],
            "research_score": cand_row["research_score"],
            "evidence_level": cand_row["evidence_level"],
            "validation_status": cand_row["validation_status"],
            "lifecycle_status": cand_row["lifecycle_status"]
        },
        "evaluation_summary": {
            "symptom": eval_data.get("symptom"),
            "root_cause": eval_data.get("root_cause_analysis", {}).get("root_cause"),
            "current_glue_work": eval_data.get("current_glue_work"),
            "observed_costs": eval_data.get("observed_costs")
        },
        "experiments_summary": {
            "total_trials": len(exp_rows),
            "passed": passed_count,
            "failed": failed_count,
            "latest_trial": latest_trial
        },
        "deterministic_summary": {
            "total_signals": sig_count,
            "prior_experiments_count": len(exp_rows)
        },
        "constraints": {
            "enforce_non_software_first": True,
            "enforce_15_operational_flags": True,
            "gate_saas_speculation": True,
            "require_sts_under_14_days": True
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assembles Dynamic Context Packs for AI reasoning agents.")
    parser.add_argument("--task", required=True, choices=["problem-evaluation", "experiment-validation", "solution-strategy"],
                        help="Target reasoning agent task")
    parser.add_argument("--db", default="discovery.sqlite", help="Path to SQLite database")
    parser.add_argument("--research-id", help="Research Run ID (required for problem-evaluation)")
    parser.add_argument("--candidate-id", help="Candidate ID (required for experiment-validation and solution-strategy)")
    parser.add_argument("--mode", default="DESIGN", choices=["DESIGN", "ASSESS"], help="Mode for experiment-validation")
    parser.add_argument("--output", help="Optional path to write output JSON")

    args = parser.parse_args()

    conn = get_db_connection(args.db)
    try:
        if args.task == "problem-evaluation":
            if not args.research_id:
                sys.stderr.write("[ERROR] --research-id is required for task 'problem-evaluation'\n")
                sys.exit(1)
            pack = build_problem_evaluation_context(conn, args.research_id)
        elif args.task == "experiment-validation":
            if not args.candidate_id:
                sys.stderr.write("[ERROR] --candidate-id is required for task 'experiment-validation'\n")
                sys.exit(1)
            pack = build_experiment_validation_context(conn, args.candidate_id, args.mode)
        elif args.task == "solution-strategy":
            if not args.candidate_id:
                sys.stderr.write("[ERROR] --candidate-id is required for task 'solution-strategy'\n")
                sys.exit(1)
            pack = build_solution_strategy_context(conn, args.candidate_id)
        else:
            sys.stderr.write(f"[ERROR] Unsupported task: {args.task}\n")
            sys.exit(1)

        output_str = json.dumps(pack, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_str + "\n")
            sys.stderr.write(f"[INFO] Context pack written to '{args.output}'\n")

        print(output_str)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
