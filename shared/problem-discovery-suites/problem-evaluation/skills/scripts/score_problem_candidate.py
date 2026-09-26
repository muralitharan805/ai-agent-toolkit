#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
score_problem_candidate.py
Deterministic 35-point scoring engine and SQLite persistence helper for Problem Evaluation.
Calculates research priority scores across 7 dimensions, enforces evidence caps (L1-L5),
evaluates stop checks, links evidence signals to candidates, and records to SQLite.
"""

import sys
import os
import json
import sqlite3
import argparse
from typing import Dict, List, Any, Optional

DIMENSIONS = ("frequency", "severity", "workaround", "wtp", "decision_maker", "feasibility", "discrepancy")
STOP_CHECKS = (
    "infrequent_low_impact",
    "no_meaningful_workaround",
    "commercial_alternative_fits_well",
    "single_source_bias",
    "internal_training_issue",
    "unreachable_audience"
)

EVIDENCE_CAPS = {
    "L1": 35,
    "L2": 28,
    "L3": 20,
    "L4": 15,
    "L5": 10,
    "UNASSESSED": 15
}

def calculate_candidate_score(
    scores: Dict[str, int],
    evidence_level: str = "L3",
    stop_checks_triggered: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculates deterministic 35-point score with evidence caps and stop checks."""
    total = sum(max(0, min(5, scores.get(d, 0))) for d in DIMENSIONS)
    level = evidence_level.upper() if evidence_level else "UNASSESSED"
    cap = EVIDENCE_CAPS.get(level, 15)

    triggered_stops = stop_checks_triggered or []
    capped_score = min(total, cap)
    if triggered_stops:
        capped_score = min(capped_score, 14)

    status = "RESEARCH_PRIORITY"
    if triggered_stops or capped_score < 15:
        status = "PARKED"
    elif level == "L1" and capped_score >= 28:
        status = "READY_TO_BUILD"

    return {
        "raw_total": total,
        "capped_score": capped_score,
        "maximum": 35,
        "evidence_level": level,
        "evidence_cap": cap,
        "scores": {d: scores.get(d, 0) for d in DIMENSIONS},
        "stop_checks_triggered": triggered_stops,
        "lifecycle_status": status
    }

def persist_candidate_to_sqlite(
    db_path: str,
    candidate_id: str,
    research_id: str,
    title: str,
    domain: str,
    operator: Optional[str],
    track: str,
    research_score: int,
    evidence_level: str,
    lifecycle_status: str,
    evaluation_dict: Dict[str, Any],
    supporting_signal_ids: List[str]
) -> None:
    """Inserts candidate record, links underlying signals, and updates research_runs stage."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id        TEXT PRIMARY KEY,
                research_id         TEXT NOT NULL,
                title               TEXT NOT NULL,
                domain              TEXT NOT NULL,
                target_operator     TEXT,
                track               TEXT DEFAULT 'COMMERCIAL',
                research_score      INTEGER DEFAULT 0,
                evidence_level      TEXT DEFAULT 'UNASSESSED',
                validation_status   TEXT DEFAULT 'UNVERIFIED',
                lifecycle_status    TEXT DEFAULT 'ACTIVE',
                evaluation_json     TEXT,
                solution_json       TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        eval_str = json.dumps(evaluation_dict, indent=2)
        cursor.execute("""
            INSERT OR REPLACE INTO candidates (
                candidate_id, research_id, title, domain, target_operator, track,
                research_score, evidence_level, validation_status, lifecycle_status, evaluation_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', ?, ?, CURRENT_TIMESTAMP)
        """, (
            candidate_id, research_id, title, domain, operator, track,
            research_score, evidence_level, lifecycle_status, eval_str
        ))

        # Link supporting signals
        if supporting_signal_ids:
            placeholders = ",".join("?" for _ in supporting_signal_ids)
            cursor.execute(f"""
                UPDATE evidence_signals
                SET candidate_id = ?
                WHERE signal_id IN ({placeholders})
            """, [candidate_id] + supporting_signal_ids)
            sys.stderr.write(f"[INFO] Linked {cursor.rowcount} signals to candidate {candidate_id}\n")

        # Update parent run stage
        cursor.execute("""
            UPDATE research_runs
            SET current_stage = 'EVALUATED', updated_at = CURRENT_TIMESTAMP
            WHERE research_id = ?
        """, (research_id,))

        conn.commit()
        sys.stderr.write(f"[INFO] Persisted candidate {candidate_id} in {db_path}\n")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic 35-point scoring engine and SQLite helper for Problem Evaluation.",
        epilog="Examples:\n  python3 score_problem_candidate.py --frequency 4 --severity 4 --workaround 4 --wtp 3 --decision-maker 3 --feasibility 4 --discrepancy 4 --evidence-level L3"
    )
    parser.add_argument("--candidate-id", default="CAND-001", help="Candidate identifier")
    parser.add_argument("--research-id", default="RUN-2026-001", help="Parent research run ID")
    parser.add_argument("--title", default="Problem Candidate", help="Candidate title")
    parser.add_argument("--domain", default="general", help="Operational domain")
    parser.add_argument("--operator", help="Target operator role")
    parser.add_argument("--track", default="COMMERCIAL", choices=["COMMERCIAL", "FREE_UTILITY"], help="Evaluation track")
    parser.add_argument("--evidence-level", default="L3", choices=list(EVIDENCE_CAPS.keys()), help="Highest verified evidence level")

    # 7 dimensions
    parser.add_argument("--frequency", type=int, default=0)
    parser.add_argument("--severity", type=int, default=0)
    parser.add_argument("--workaround", type=int, default=0)
    parser.add_argument("--wtp", type=int, default=0)
    parser.add_argument("--decision-maker", type=int, default=0)
    parser.add_argument("--feasibility", type=int, default=0)
    parser.add_argument("--discrepancy", type=int, default=0)

    # Stop checks
    parser.add_argument("--stop-check", action="append", default=[], help="Triggered stop check keys")

    # Evaluation JSON file input
    parser.add_argument("--input", help="Path to input ProblemEvaluation JSON file")
    parser.add_argument("--output", help="Path to output JSON file")
    parser.add_argument("--sqlite-db", help="Path to SQLite database to persist candidate")
    parser.add_argument("--supporting-signals", help="Comma-separated supporting signal IDs (e.g. SIG-001,SIG-002)")

    args = parser.parse_args()

    scores = {
        "frequency": args.frequency,
        "severity": args.severity,
        "workaround": args.workaround,
        "wtp": args.wtp,
        "decision_maker": args.decision_maker,
        "feasibility": args.feasibility,
        "discrepancy": args.discrepancy
    }

    evidence_level = args.evidence_level
    stop_checks = args.stop_check

    # If input JSON is provided, load from file
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)
            candidate = data.get("candidates", [{}])[0] if "candidates" in data else data
            c_scores = candidate.get("research_score", {}).get("scores", {})
            for d in DIMENSIONS:
                if d in c_scores:
                    scores[d] = c_scores[d]
            evidence_level = candidate.get("evidence_level") or evidence_level
            stop_checks = candidate.get("stop_checks", {}).get("reasons", []) or stop_checks
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to read --input: {e}\n")
            sys.exit(1)

    result = calculate_candidate_score(scores, evidence_level, stop_checks)

    output = {
        "candidate_id": args.candidate_id,
        "research_id": args.research_id,
        "title": args.title,
        "domain": args.domain,
        "operator": args.operator,
        "track": args.track,
        "evaluation": result
    }

    if args.sqlite_db:
        signals = [s.strip() for s in args.supporting_signals.split(",") if s.strip()] if args.supporting_signals else []
        persist_candidate_to_sqlite(
            db_path=args.sqlite_db,
            candidate_id=args.candidate_id,
            research_id=args.research_id,
            title=args.title,
            domain=args.domain,
            operator=args.operator,
            track=args.track,
            research_score=result["capped_score"],
            evidence_level=result["evidence_level"],
            lifecycle_status=result["lifecycle_status"],
            evaluation_dict=output,
            supporting_signal_ids=signals
        )

    formatted = json.dumps(output, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted + "\n")

    sys.stdout.write(formatted + "\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
