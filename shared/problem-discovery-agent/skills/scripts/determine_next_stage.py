# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deterministic state machine & routing inspector for Problem Discovery.

Inspects persistent SQLite state and determines the exact next justified workflow action,
target skill, context pack task, and human-in-the-loop pause gates.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


RUN_ID_REGEX = re.compile(r"\b(RUN-\d{4}-\d{3,})\b", re.IGNORECASE)
CANDIDATE_ID_REGEX = re.compile(r"\b(CAND-\d{3,})\b", re.IGNORECASE)
EXPERIMENT_ID_REGEX = re.compile(r"\b(EXP-\d{3,})\b", re.IGNORECASE)

QUERY_KEYWORDS = [
    r"\bstatus\b",
    r"\benna\b",
    r"\birukku\b",
    r"\birukka\b",
    r"\bwhat\s+is\b",
    r"\bhow\s+many\b",
    r"\blist\b",
    r"\bdetails\b",
    r"\bshow\s+me\b",
    r"\bexplain\b",
    r"\bevidence\b",
    r"\?\s*$",
]

EXPERIMENT_RESULT_KEYWORDS = [
    r"results?\s+(?:are\s+)?ready",
    r"observed\s+(?:mean|value|metric|data)",
    r"experiment\s+result",
    r"trial\s+result",
    r"artifact\s+hash",
    r"recorded\s+(?:observation|measurement)",
    r"outcome\s+verdict",
]


def resolve_default_db_path() -> Path:
    """Locate canonical discovery SQLite database relative to repo."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "shared" / "problem-discovery-suites" / "discovery-state" / "data" / "discovery.sqlite"
        if candidate.exists() or (parent / "shared" / "problem-discovery-suites").exists():
            candidate.parent.mkdir(parents=True, exist_ok=True)
            return candidate
    return Path("discovery.sqlite").resolve()


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


def _loads(val: Optional[str]) -> Dict[str, Any]:
    if not val:
        return {}
    try:
        data = json.loads(val)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def determine_next_stage(
    db_path: Path,
    request: Optional[str] = None,
    run_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspects SQLite state and decides next operational action."""
    req_text = (request or "").strip()

    # Extract IDs if not explicitly passed
    if not run_id:
        match_run = RUN_ID_REGEX.search(req_text)
        if match_run:
            run_id = match_run.group(1).upper()

    if not candidate_id:
        match_cand = CANDIDATE_ID_REGEX.search(req_text)
        if match_cand:
            candidate_id = match_cand.group(1).upper()

    # 1. Read-only query check
    is_query = any(re.search(pat, req_text, re.IGNORECASE) for pat in QUERY_KEYWORDS)
    if is_query and not any(k in req_text.lower() for k in ["continue", "resume", "proceed", "advance"]):
        return {
            "action": "QUERY_DATABASE",
            "target_skill": "discovery-state",
            "target_task": "discovery-query",
            "entity_id": candidate_id or run_id or None,
            "status": "READY",
            "reason": "User requested read-only status or exploratory information query.",
            "pause_reason": None,
            "next_step_hint": f"Run build_agent_context.py --task discovery-query --query '{req_text}'",
        }

    # 2. Check if experiment results are provided in prompt
    has_exp_results = any(re.search(pat, req_text, re.IGNORECASE) for pat in EXPERIMENT_RESULT_KEYWORDS)

    if not db_path.exists():
        if req_text:
            return {
                "action": "INVOKE_SKILL",
                "target_skill": "research-planning",
                "target_task": "research-planning",
                "entity_id": None,
                "status": "READY",
                "reason": "Database uninitialized; starting initial research run.",
                "pause_reason": None,
                "next_step_hint": "Execute research-planning to initialize research_runs record.",
            }

    conn = get_connection(db_path)
    try:
        # Check if tables exist
        table_check = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_runs'"
        ).fetchone()
        if not table_check:
            return {
                "action": "INVOKE_SKILL",
                "target_skill": "research-planning",
                "target_task": "research-planning",
                "entity_id": None,
                "status": "READY",
                "reason": "Schema uninitialized; starting initial research run.",
                "pause_reason": None,
                "next_step_hint": "Execute research-planning to bootstrap run.",
            }

        # 3. Candidate-specific lifecycle inspection
        if candidate_id:
            cand = conn.execute(
                """
                SELECT candidate_id, origin_research_id, title, research_score,
                       evidence_level, validation_status, lifecycle_status,
                       solution_class, evaluation_json, solution_json
                FROM candidates WHERE candidate_id = ?
                """,
                (candidate_id,),
            ).fetchone()

            if not cand:
                return {
                    "action": "ERROR",
                    "target_skill": None,
                    "target_task": None,
                    "entity_id": candidate_id,
                    "status": "ERROR",
                    "reason": f"Candidate '{candidate_id}' not found in database.",
                    "pause_reason": None,
                    "next_step_hint": "Verify candidate_id exists in discovery dashboard.",
                }

            val_status = cand["validation_status"]
            sol_class = cand["solution_class"]

            # Check experiments for this candidate
            exps = conn.execute(
                """
                SELECT experiment_id, hypothesis, outcome_verdict, sample_target,
                       sample_achieved, observed_value
                FROM experiments WHERE candidate_id = ?
                ORDER BY created_at DESC
                """,
                (candidate_id,),
            ).fetchall()

            if val_status in ("UNVERIFIED", "IN_PROGRESS"):
                if not exps:
                    return {
                        "action": "INVOKE_SKILL",
                        "target_skill": "experiment-validation",
                        "target_task": "experiment-validation",
                        "mode": "DESIGN",
                        "entity_id": candidate_id,
                        "status": "READY",
                        "reason": f"Candidate {candidate_id} is evaluated but unverified; experiment design required.",
                        "pause_reason": None,
                        "next_step_hint": f"Run build_agent_context.py --task experiment-validation --candidate-id {candidate_id} --mode DESIGN",
                    }

                latest_exp = exps[0]
                if latest_exp["outcome_verdict"] == "PREREGISTERED":
                    if has_exp_results:
                        return {
                            "action": "INVOKE_SKILL",
                            "target_skill": "experiment-validation",
                            "target_task": "experiment-validation",
                            "mode": "ASSESS",
                            "entity_id": latest_exp["experiment_id"],
                            "candidate_id": candidate_id,
                            "status": "READY",
                            "reason": f"Observed experiment results provided for preregistered {latest_exp['experiment_id']}.",
                            "pause_reason": None,
                            "next_step_hint": f"Run build_agent_context.py --task experiment-validation --candidate-id {candidate_id} --experiment-id {latest_exp['experiment_id']} --mode ASSESS",
                        }
                    return {
                        "action": "PAUSE_FOR_HUMAN",
                        "target_skill": "experiment-validation",
                        "target_task": None,
                        "entity_id": latest_exp["experiment_id"],
                        "candidate_id": candidate_id,
                        "status": "PAUSED",
                        "reason": f"Experiment {latest_exp['experiment_id']} is PREREGISTERED. Real-world trial observations required before assessment.",
                        "pause_reason": "WAITING_FOR_REAL_WORLD_EXPERIMENT",
                        "next_step_hint": f"Execute real-world trial, then resume: /problem-discovery continue {candidate_id} with observed data and artifact hash.",
                    }

            if val_status in ("PARTIALLY_VALIDATED", "VALIDATED"):
                if not sol_class or not cand["solution_json"]:
                    return {
                        "action": "INVOKE_SKILL",
                        "target_skill": "solution-strategy",
                        "target_task": "solution-strategy",
                        "entity_id": candidate_id,
                        "status": "READY",
                        "reason": f"Candidate {candidate_id} is validated ({val_status}); solution-strategy gating required.",
                        "pause_reason": None,
                        "next_step_hint": f"Run build_agent_context.py --task solution-strategy --candidate-id {candidate_id}",
                    }

                return {
                    "action": "COMPLETE",
                    "target_skill": "discovery-state",
                    "target_task": "discovery-query",
                    "entity_id": candidate_id,
                    "status": "COMPLETED",
                    "reason": f"Candidate {candidate_id} lifecycle complete (Validated & Solution Shape finalized: {sol_class}).",
                    "pause_reason": None,
                    "next_step_hint": "Single-pane dashboard updated. Candidate ready for product execution.",
                }

        # 4. Research Run inspection
        if run_id:
            run = conn.execute(
                """
                SELECT research_id, original_request, domain, scope_type,
                       current_stage, status, plan_json
                FROM research_runs WHERE research_id = ?
                """,
                (run_id,),
            ).fetchone()

            if not run:
                return {
                    "action": "ERROR",
                    "target_skill": None,
                    "target_task": None,
                    "entity_id": run_id,
                    "status": "ERROR",
                    "reason": f"Research run '{run_id}' not found.",
                    "pause_reason": None,
                    "next_step_hint": "Verify run_id in discovery database.",
                }

            current_stage = run["current_stage"]
            plan_json = run["plan_json"]

            if current_stage in ("RESEARCH_PLANNING", "EVIDENCE_RESEARCH"):
                if not plan_json:
                    return {
                        "action": "INVOKE_SKILL",
                        "target_skill": "research-planning",
                        "target_task": "research-planning",
                        "entity_id": run_id,
                        "status": "READY",
                        "reason": f"Research run {run_id} missing structured ResearchPlan.",
                        "pause_reason": None,
                        "next_step_hint": "Execute research-planning skill to save plan contract.",
                    }

                # Plan exists, check signals
                sig_count = conn.execute(
                    "SELECT COUNT(*) FROM evidence_signals WHERE research_id = ?",
                    (run_id,),
                ).fetchone()[0]

                if sig_count == 0:
                    return {
                        "action": "INVOKE_SKILL",
                        "target_skill": "evidence-research",
                        "target_task": "evidence-research",
                        "entity_id": run_id,
                        "status": "READY",
                        "reason": f"Research run {run_id} has plan but 0 evidence signals collected.",
                        "pause_reason": None,
                        "next_step_hint": f"Execute evidence-research using search queries from {run_id} plan.",
                    }
                else:
                    return {
                        "action": "INVOKE_SKILL",
                        "target_skill": "problem-evaluation",
                        "target_task": "problem-evaluation",
                        "entity_id": run_id,
                        "status": "READY",
                        "reason": f"Research run {run_id} has {sig_count} signals; problem-evaluation required.",
                        "pause_reason": None,
                        "next_step_hint": f"Run build_agent_context.py --task problem-evaluation --research-id {run_id}",
                    }

            if current_stage in ("RESEARCHED", "PROBLEM_EVALUATION"):
                cands = conn.execute(
                    "SELECT candidate_id FROM candidates WHERE origin_research_id = ?",
                    (run_id,),
                ).fetchall()

                if not cands:
                    return {
                        "action": "INVOKE_SKILL",
                        "target_skill": "problem-evaluation",
                        "target_task": "problem-evaluation",
                        "entity_id": run_id,
                        "status": "READY",
                        "reason": f"Research run {run_id} is in stage '{current_stage}' with signals collected, but has no evaluated candidates.",
                        "pause_reason": None,
                        "next_step_hint": f"Run build_agent_context.py --task problem-evaluation --research-id {run_id}",
                    }

                # Evaluate first candidate that needs progress
                return determine_next_stage(db_path, request=req_text, candidate_id=cands[0]["candidate_id"])

            if current_stage in ("EVALUATED", "VALIDATING", "EXPERIMENT_VALIDATION", "SOLUTION_STRATEGY"):
                cands = conn.execute(
                    "SELECT candidate_id FROM candidates WHERE origin_research_id = ? ORDER BY candidate_id ASC",
                    (run_id,),
                ).fetchall()
                for c in cands:
                    res = determine_next_stage(db_path, request=req_text, candidate_id=c["candidate_id"])
                    if res.get("status") in ("READY", "PAUSED"):
                        return res

                return {
                    "action": "COMPLETE",
                    "target_skill": "discovery-state",
                    "target_task": "discovery-query",
                    "entity_id": run_id,
                    "status": "COMPLETED",
                    "reason": f"All candidates under run {run_id} have finalized lifecycles.",
                    "pause_reason": None,
                    "next_step_hint": "Check dashboard for final outcome summary.",
                }

        # 5. Fallback for new topic or plain request
        if req_text:
            return {
                "action": "INVOKE_SKILL",
                "target_skill": "research-planning",
                "target_task": "research-planning",
                "entity_id": None,
                "status": "READY",
                "reason": "New research inquiry received. Initiating research-planning.",
                "pause_reason": None,
                "next_step_hint": "Parse user intent, classify scope, and generate ResearchPlan contract.",
            }

        return {
            "action": "QUERY_DATABASE",
            "target_skill": "discovery-state",
            "target_task": "discovery-query",
            "entity_id": None,
            "status": "READY",
            "reason": "No active request or entity ID provided; defaulting to discovery dashboard query.",
            "pause_reason": None,
            "next_step_hint": "Display discovery dashboard overview.",
        }

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect SQLite state and determine next Problem Discovery action."
    )
    parser.add_argument("--db", type=str, help="Path to SQLite discovery database.")
    parser.add_argument("--request", type=str, help="Raw user request / prompt.")
    parser.add_argument("--run-id", type=str, help="Active research run ID (RUN-YYYY-NNN).")
    parser.add_argument("--candidate-id", type=str, help="Candidate ID (CAND-NNN).")
    parser.add_argument("--json", action="store_true", default=True, help="Emit output as JSON (default).")

    args = parser.parse_args()

    db_path = Path(args.db).resolve() if args.db else resolve_default_db_path()
    decision = determine_next_stage(
        db_path=db_path,
        request=args.request,
        run_id=args.run_id,
        candidate_id=args.candidate_id,
    )

    print(json.dumps(decision, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
