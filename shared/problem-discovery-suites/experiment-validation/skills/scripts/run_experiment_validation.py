#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
run_experiment_validation.py
Unified execution engine and SQLite helper for Experiment Validation.
Supports DESIGN mode (preregistering immutable trial contracts)
and ASSESS mode (evaluating observed results against locked rules).
"""

import sys
import os
import json
import sqlite3
import hashlib
import argparse
from datetime import datetime, date, timezone
from typing import Dict, List, Any, Optional

def compute_file_sha256(file_path: str) -> Optional[str]:
    """Computes SHA-256 hash of a local artifact file if accessible."""
    if not os.path.isfile(file_path):
        return None
    try:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower()
    except Exception:
        return None

def design_experiment(
    candidate_id: str,
    hypothesis: str,
    primary_metric: str,
    target_threshold: float,
    direction: str = ">=",
    sample_target: int = 5,
    minimum_usable: int = 5,
    duration_days: int = 7,
    artifact_type: str = "CSV observation log"
) -> Dict[str, Any]:
    """Designs an immutable ExperimentContract."""
    exp_id = f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')[-4:]}"
    return {
        "schema_version": "1.0",
        "mode": "DESIGN",
        "status": "PREREGISTERED",
        "experiment_id": exp_id,
        "candidate_id": candidate_id,
        "validation_target": "BEHAVIOR_FREQUENCY",
        "hypothesis": hypothesis,
        "population": {
            "description": "Target qualified operators",
            "inclusion_criteria": ["Active in target workflow", "Directly responsible for task"],
            "exclusion_criteria": ["Inactive or unverified accounts"]
        },
        "sample": {
            "target": sample_target,
            "minimum_usable": minimum_usable
        },
        "period": {
            "duration_days": duration_days,
            "start_at": "PRE_EXECUTION_LOCKED"
        },
        "primary_metric": {
            "name": primary_metric,
            "unit": "events"
        },
        "success_threshold": {
            "metric": primary_metric,
            "operator": direction,
            "value": target_threshold
        },
        "success_rule": f"At least {target_threshold} {primary_metric} achieved across sample.",
        "failure_rule": f"Fail if threshold of {target_threshold} is not satisfied or usable sample < {minimum_usable}.",
        "artifact_requirements": {
            "required": True,
            "expected_type": artifact_type
        },
        "review_requirements": {
            "human_review_required": True,
            "sha256_required": True
        },
        "preregistration_locked": True,
        "next_action": "EXECUTE_REAL_WORLD_EXPERIMENT"
    }

def assess_experiment(
    contract: Dict[str, Any],
    observed_value: float,
    sample_achieved: int,
    artifact_path: Optional[str] = None,
    artifact_hash: Optional[str] = None,
    audited_by: Optional[str] = None,
    audit_date: Optional[str] = None
) -> Dict[str, Any]:
    """Assesses observed trial data against the locked contract."""
    exp_id = contract.get("experiment_id", "EXP-001")
    candidate_id = contract.get("candidate_id", "CAND-001")
    min_usable = contract.get("sample", {}).get("minimum_usable", 5)
    threshold = float(contract.get("success_threshold", {}).get("value", 3.0))
    direction = contract.get("success_threshold", {}).get("operator", ">=")

    # 1. Sample check
    if sample_achieved < min_usable:
        return {
            "schema_version": "1.0",
            "mode": "ASSESS",
            "experiment_id": exp_id,
            "candidate_id": candidate_id,
            "status": "INCOMPLETE",
            "experiment_completed": False,
            "experiment_passed": False,
            "reason": f"Observed sample ({sample_achieved}) fell below minimum usable sample ({min_usable}).",
            "next_action": "COMPLETE_OR_RESTART_EXPERIMENT"
        }

    # 2. Evaluate threshold
    passed = False
    if direction == ">=":
        passed = (observed_value >= threshold)
    elif direction == "<=":
        passed = (observed_value <= threshold)
    elif direction == ">":
        passed = (observed_value > threshold)
    elif direction == "<":
        passed = (observed_value < threshold)
    elif direction == "==":
        passed = (observed_value == threshold)

    verdict = "EXPERIMENT_PASSED" if passed else "EXPERIMENT_FAILED"

    # 3. Artifact digest check
    computed_hash = compute_file_sha256(artifact_path) if artifact_path else None
    final_hash = computed_hash or artifact_hash

    has_human_review = bool(audited_by and audit_date)

    return {
        "schema_version": "1.0",
        "mode": "ASSESS",
        "experiment_id": exp_id,
        "candidate_id": candidate_id,
        "status": verdict,
        "experiment_completed": True,
        "experiment_passed": passed,
        "observed_result": {
            "sample_achieved": sample_achieved,
            "observed_value": observed_value,
            "target_threshold": threshold,
            "direction": direction
        },
        "artifact_review": {
            "artifact_path": artifact_path,
            "sha256": final_hash,
            "human_review_completed": has_human_review,
            "audited_by": audited_by,
            "audit_date": audit_date
        },
        "validation_assessment": {
            "problem_behavior_observed": passed,
            "market_demand_validated": False,
            "willingness_to_pay_validated": False,
            "solution_adoption_validated": False,
            "retention_validated": False
        },
        "supported_claims": [
            f"Observed value ({observed_value}) satisfied threshold ({direction} {threshold}) across tested cohort."
        ] if passed else [],
        "unsupported_claims": [
            "Widespread market demand beyond sample.",
            "Commercial willingness to pay."
        ],
        "remaining_unknowns": [
            "Statistical representativeness",
            "Willingness to pay",
            "Long-term retention"
        ],
        "next_action": "READY_FOR_SOLUTION_STRATEGY" if passed else "REVIEW_HYPOTHESIS_OR_SEGMENT"
    }

def persist_design_sqlite(db_path: str, contract: Dict[str, Any]) -> None:
    """Inserts preregistered contract into SQLite experiments table."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
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
                contract_json       TEXT,
                assessment_json     TEXT,
                artifact_hash       TEXT,
                audited_by          TEXT,
                audit_date          DATE,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        c_json = json.dumps(contract, indent=2)
        cursor.execute("""
            INSERT OR REPLACE INTO experiments (
                experiment_id, candidate_id, hypothesis, metric_name, target_threshold,
                direction, sample_target, outcome_verdict, contract_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'NOT_RUN', ?)
        """, (
            contract["experiment_id"], contract["candidate_id"], contract["hypothesis"],
            contract["primary_metric"]["name"], contract["success_threshold"]["value"],
            contract["success_threshold"]["operator"], contract["sample"]["target"], c_json
        ))
        cursor.execute("""
            UPDATE candidates 
            SET lifecycle_status = 'EXPERIMENT_DESIGNED', updated_at = CURRENT_TIMESTAMP 
            WHERE candidate_id = ?
        """, (contract["candidate_id"],))
        conn.commit()
        sys.stderr.write(f"[INFO] Preregistered experiment {contract['experiment_id']} in {db_path}\n")
    finally:
        conn.close()

def persist_assess_sqlite(db_path: str, assessment: Dict[str, Any]) -> None:
    """Updates SQLite experiments table with outcome and advances candidate status."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        a_json = json.dumps(assessment, indent=2)
        exp_id = assessment["experiment_id"]
        cand_id = assessment["candidate_id"]
        passed = assessment.get("experiment_passed", False)
        status = assessment.get("status", "EXPERIMENT_FAILED")

        obs = assessment.get("observed_result", {})
        rev = assessment.get("artifact_review", {})

        cursor.execute("""
            UPDATE experiments
            SET sample_achieved = ?, observed_value = ?, outcome_verdict = ?,
                assessment_json = ?, artifact_hash = ?, audited_by = ?, audit_date = ?
            WHERE experiment_id = ?
        """, (
            obs.get("sample_achieved"), obs.get("observed_value"), status,
            a_json, rev.get("sha256"), rev.get("audited_by"), rev.get("audit_date"), exp_id
        ))

        if passed:
            cursor.execute("""
                UPDATE candidates
                SET validation_status = 'VALIDATED', lifecycle_status = 'READY_FOR_SOLUTION', updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
            """, (cand_id,))
        elif status == "EXPERIMENT_FAILED":
            cursor.execute("""
                UPDATE candidates
                SET validation_status = 'EXPERIMENT_FAILED', lifecycle_status = 'PARKED', updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
            """, (cand_id,))

        conn.commit()
        sys.stderr.write(f"[INFO] Recorded assessment for {exp_id} ({status}) in {db_path}\n")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description="Unified Experiment Validation CLI for DESIGN and ASSESS modes.",
        epilog="Examples:\n  python3 run_experiment_validation.py --mode design --candidate-id CAND-001 --hypothesis 'Sellers sync manually' --metric 'sync_count' --threshold 3.0\n  python3 run_experiment_validation.py --mode assess --input contract.json --observed-value 4.0 --sample-achieved 5"
    )
    parser.add_argument("--mode", required=True, choices=["design", "assess"], help="Execution mode")
    parser.add_argument("--candidate-id", default="CAND-001", help="Target candidate ID")
    parser.add_argument("--experiment-id", default="EXP-001", help="Target experiment ID")
    parser.add_argument("--hypothesis", default="Qualified operators exhibit target friction", help="Testable hypothesis")
    parser.add_argument("--metric", default="events_per_week", help="Primary metric name")
    parser.add_argument("--threshold", type=float, default=3.0, help="Numeric success threshold")
    parser.add_argument("--direction", default=">=", choices=[">=", "<=", ">", "<", "=="], help="Threshold operator")
    parser.add_argument("--sample-target", type=int, default=5, help="Sample target size")
    parser.add_argument("--minimum-usable", type=int, default=5, help="Minimum usable sample size")
    parser.add_argument("--observed-value", type=float, help="Observed metric value for assessment")
    parser.add_argument("--sample-achieved", type=int, help="Actual usable sample size observed")
    parser.add_argument("--artifact-path", help="Path to local evidence artifact (CSV/log)")
    parser.add_argument("--artifact-hash", help="SHA-256 digest of artifact")
    parser.add_argument("--audited-by", help="Name of human reviewer")
    parser.add_argument("--audit-date", help="ISO-8601 audit date")
    parser.add_argument("--input", help="Path to input JSON file")
    parser.add_argument("--output", help="Path to output JSON file")
    parser.add_argument("--sqlite-db", help="Path to SQLite database")

    args = parser.parse_args()

    if args.mode == "design":
        contract = design_experiment(
            candidate_id=args.candidate_id,
            hypothesis=args.hypothesis,
            primary_metric=args.metric,
            target_threshold=args.threshold,
            direction=args.direction,
            sample_target=args.sample_target,
            minimum_usable=args.minimum_usable
        )
        if args.sqlite_db:
            persist_design_sqlite(args.sqlite_db, contract)
        out_json = json.dumps(contract, indent=2)

    elif args.mode == "assess":
        contract = {}
        if args.input and os.path.isfile(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                contract = json.load(f)
        else:
            contract = {
                "experiment_id": args.experiment_id,
                "candidate_id": args.candidate_id,
                "sample": {"minimum_usable": args.minimum_usable},
                "success_threshold": {"value": args.threshold, "operator": args.direction}
            }

        obs_val = args.observed_value if args.observed_value is not None else 0.0
        sample_ach = args.sample_achieved if args.sample_achieved is not None else args.minimum_usable

        assessment = assess_experiment(
            contract=contract,
            observed_value=obs_val,
            sample_achieved=sample_ach,
            artifact_path=args.artifact_path,
            artifact_hash=args.artifact_hash,
            audited_by=args.audited_by,
            audit_date=args.audit_date or date.today().isoformat()
        )
        if args.sqlite_db:
            persist_assess_sqlite(args.sqlite_db, assessment)
        out_json = json.dumps(assessment, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json + "\n")

    sys.stdout.write(out_json + "\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
