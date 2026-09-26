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
import importlib.util
from pathlib import Path
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
    "L2": 35,
    "L3": 35,
    "L4": 7,
    "L5": 0,
    "UNASSESSED": 0
}

def _load_discovery_db_class():
    """Load the canonical discovery-state client across shared and .agents layouts."""
    candidates = [
        Path(__file__).resolve().parents[3] / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path(__file__).resolve().parents[2] / "discovery-state" / "scripts" / "discovery_db.py",
        Path(__file__).resolve().parents[3] / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path(__file__).resolve().parents[4] / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path.cwd() / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path.cwd() / ".agents" / "skills" / "discovery-state" / "scripts" / "discovery_db.py",
    ]
    for db_module_path in candidates:
        if db_module_path.exists():
            spec = importlib.util.spec_from_file_location("discovery_state_db", db_module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.DiscoveryDB
    raise RuntimeError(f"Unable to load discovery-state client from candidates: {[str(p) for p in candidates]}")

def calculate_candidate_score(
    scores: Dict[str, int],
    evidence_level: str = "UNASSESSED",
    stop_checks_triggered: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculate research priority only. Never promote a candidate to a build state."""
    level = (evidence_level or "UNASSESSED").upper()
    normalized = {d: max(0, min(5, int(scores.get(d, 0)))) for d in DIMENSIONS}

    # Canonical evidence gate from the original discovery framework:
    # L4 secondary interpretation contributes at most 1 point per dimension;
    # L5 and unassessed evidence contribute zero until stronger evidence exists.
    if level == "L4":
        gated_scores = {d: min(v, 1) for d, v in normalized.items()}
    elif level in {"L5", "UNASSESSED"}:
        gated_scores = {d: 0 for d in DIMENSIONS}
    else:
        gated_scores = normalized

    raw_total = sum(normalized.values())
    total = sum(gated_scores.values())
    triggered_stops = stop_checks_triggered or []

    if triggered_stops:
        lifecycle = "PARKED"
        tier = "STOP_CHECK_TRIGGERED"
    elif total >= 28:
        lifecycle = "RESEARCH_PRIORITY"
        tier = "HIGH_RESEARCH_PRIORITY"
    elif total >= 23:
        lifecycle = "RESEARCH_PRIORITY"
        tier = "QUALIFIED_RESEARCH_CANDIDATE"
    elif total >= 15:
        lifecycle = "PARKED"
        tier = "LOW_RESEARCH_PRIORITY"
    else:
        lifecycle = "PARKED"
        tier = "HALT_NO_PROBLEM_FALLBACK"

    return {
        "raw_total": raw_total,
        "capped_score": total,
        "maximum": 35,
        "evidence_level": level,
        "evidence_cap": EVIDENCE_CAPS.get(level, 0),
        "scores": gated_scores,
        "raw_scores": normalized,
        "stop_checks_triggered": triggered_stops,
        "lifecycle_status": lifecycle,
        "priority_tier": tier,
        "score_is_validation": False
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
    """Delegate all mutations to the canonical discovery-state client."""
    DiscoveryDB = _load_discovery_db_class()
    db = DiscoveryDB(db_path)
    db.upsert_candidate(
        candidate_id=candidate_id,
        research_id=research_id,
        title=title,
        domain=domain,
        target_operator=operator,
        track=track,
        research_score=research_score,
        evidence_level=evidence_level,
        lifecycle_status=lifecycle_status,
        evaluation_dict=evaluation_dict,
        supporting_signal_ids=supporting_signal_ids,
    )
    sys.stderr.write(f"[INFO] Persisted candidate {candidate_id} through discovery-state\n")

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
    parser.add_argument("--evidence-level", default="UNASSESSED", choices=list(EVIDENCE_CAPS.keys()), help="Highest verified evidence level")

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
    parser.add_argument("--input", help="Path to input ProblemEvaluation JSON file or inline JSON string")
    parser.add_argument("--output", help="Path to output JSON file")
    parser.add_argument("--sqlite-db", "--db", default=os.getenv("DISCOVERY_DB_PATH", "discovery.sqlite"), help="Path to SQLite database to persist candidate")
    parser.add_argument("--save-db", action="store_true", help="Persist candidate into SQLite database")
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
    candidate_payload: Dict[str, Any] = {}

    # If input JSON is provided, load from file or string
    if args.input:
        try:
            if os.path.isfile(args.input):
                with open(args.input, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(args.input)
            candidate = data.get("candidates", [{}])[0] if "candidates" in data else data
            candidate_payload = candidate
            c_scores = candidate.get("research_score", {}).get("scores", {})
            for d in DIMENSIONS:
                if d in c_scores:
                    scores[d] = c_scores[d]
            evidence_level = candidate.get("evidence_level") or evidence_level
            stop_checks = candidate.get("stop_checks", {}).get("reasons", []) or stop_checks

            # Populate slots from candidate payload if provided
            args.candidate_id = candidate.get("candidate_id") or candidate.get("candidate_ref") or args.candidate_id
            args.research_id = candidate.get("research_id") or candidate.get("origin_research_id") or args.research_id
            args.title = candidate.get("problem_title") or candidate.get("title") or args.title
            args.domain = candidate.get("domain") or args.domain
            args.operator = candidate.get("target_operator") or (candidate.get("actors", [None])[0] if candidate.get("actors") else None) or args.operator
            args.track = candidate.get("track") or args.track
            if not args.supporting_signals and candidate.get("supporting_signal_ids"):
                args.supporting_signals = ",".join(candidate["supporting_signal_ids"])
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to read --input: {e}\n")
            sys.exit(1)

    result = calculate_candidate_score(scores, evidence_level, stop_checks)

    # Preserve full candidate payload if available, else construct standard envelope
    output = dict(candidate_payload) if candidate_payload else {
        "candidate_id": args.candidate_id,
        "research_id": args.research_id,
        "title": args.title,
        "domain": args.domain,
        "operator": args.operator,
        "track": args.track,
    }
    output["calculated_score"] = result

    if args.save_db or (args.input and args.sqlite_db and os.path.exists(args.sqlite_db)):
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
