#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Preregister and assess empirical experiments without collapsing experiment pass into candidate validation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional


def _load_discovery_db_class():
    db_module_path = Path(__file__).resolve().parents[3] / "discovery-state" / "skills" / "scripts" / "discovery_db.py"
    spec = importlib.util.spec_from_file_location("discovery_state_db", db_module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load discovery-state client from {db_module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DiscoveryDB


def compute_file_sha256(file_path: Optional[str]) -> Optional[str]:
    if not file_path or not os.path.isfile(file_path):
        return None
    hasher = hashlib.sha256()
    with open(file_path, "rb") as handle:
        while chunk := handle.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def design_experiment(
    candidate_id: str,
    hypothesis: str,
    primary_metric: str,
    target_threshold: float,
    validation_target: str = "BEHAVIOR_FREQUENCY",
    direction: str = ">=",
    sample_target: int = 5,
    minimum_usable: int = 5,
    duration_days: int = 7,
    artifact_type: str = "CSV observation log",
    experiment_id: Optional[str] = None,
) -> Dict[str, Any]:
    if minimum_usable > sample_target:
        raise ValueError("minimum_usable cannot exceed sample_target")
    exp_id = experiment_id or f"EXP-{uuid.uuid4().hex[:12].upper()}"
    return {
        "schema_version": "1.0",
        "mode": "DESIGN",
        "status": "PREREGISTERED",
        "experiment_id": exp_id,
        "candidate_id": candidate_id,
        "validation_target": validation_target,
        "hypothesis": hypothesis,
        "population": {
            "description": "Target qualified operators",
            "inclusion_criteria": ["Active in target workflow", "Directly responsible for task"],
            "exclusion_criteria": ["Inactive or unverified participants"],
        },
        "sample": {"target": sample_target, "minimum_usable": minimum_usable},
        "period": {"duration_days": duration_days, "start_at": "TO_BE_LOCKED_BEFORE_EXECUTION"},
        "primary_metric": {"name": primary_metric, "unit": "events"},
        "success_threshold": {"metric": primary_metric, "operator": direction, "value": target_threshold},
        "success_rule": f"Primary metric must satisfy {direction} {target_threshold} under the preregistered aggregation rule.",
        "failure_rule": f"Fail when the completed usable sample does not satisfy {direction} {target_threshold}.",
        "artifact_requirements": {"required": True, "expected_type": artifact_type},
        "review_requirements": {
            "human_review_required": True,
            "reviewer_name_required": True,
            "review_date_required": True,
            "sha256_required": True,
        },
        "preregistration_locked": True,
        "next_action": "EXECUTE_REAL_WORLD_EXPERIMENT",
    }


def _comparison(observed: float, threshold: float, direction: str) -> bool:
    if direction == ">=":
        return observed >= threshold
    if direction == "<=":
        return observed <= threshold
    if direction == ">":
        return observed > threshold
    if direction == "<":
        return observed < threshold
    if direction == "==":
        return observed == threshold
    raise ValueError(f"Unsupported direction: {direction}")


def _validation_scope(validation_target: str, passed: bool) -> Dict[str, bool]:
    return {
        "problem_behavior_observed": passed and validation_target in {
            "BEHAVIOR_FREQUENCY", "TIME_COST", "ERROR_RATE", "WORKAROUND_USE", "PROCESS_IMPROVEMENT"
        },
        "market_demand_validated": False,
        "willingness_to_pay_validated": passed and validation_target == "WILLINGNESS_TO_PAY",
        "solution_adoption_validated": passed and validation_target in {"ADOPTION", "USAGE", "CONVERSION"},
        "retention_validated": passed and validation_target == "RETENTION",
    }


def assess_experiment(
    contract: Dict[str, Any],
    observed_value: float,
    sample_achieved: int,
    artifact_path: Optional[str] = None,
    artifact_hash: Optional[str] = None,
    audited_by: Optional[str] = None,
    audit_date: Optional[str] = None,
) -> Dict[str, Any]:
    if contract.get("preregistration_locked") is not True:
        raise ValueError("Experiment contract is not locked/preregistered")

    exp_id = contract["experiment_id"]
    candidate_id = contract["candidate_id"]
    min_usable = int(contract.get("sample", {}).get("minimum_usable", 0))
    threshold = float(contract.get("success_threshold", {}).get("value"))
    direction = contract.get("success_threshold", {}).get("operator")
    validation_target = contract.get("validation_target", "BEHAVIOR_FREQUENCY")

    computed_hash = compute_file_sha256(artifact_path)
    final_hash = computed_hash or artifact_hash
    human_review = bool(audited_by and audit_date)
    artifact_required = bool(contract.get("artifact_requirements", {}).get("required", False))
    review_required = bool(contract.get("review_requirements", {}).get("human_review_required", False))

    artifact_review = {
        "artifact_path": artifact_path,
        "sha256": final_hash,
        "human_review_completed": human_review,
        "audited_by": audited_by,
        "audit_date": audit_date,
    }
    observed = {
        "sample_achieved": sample_achieved,
        "observed_value": observed_value,
        "target_threshold": threshold,
        "direction": direction,
    }

    if sample_achieved < min_usable:
        return {
            "schema_version": "1.0",
            "mode": "ASSESS",
            "experiment_id": exp_id,
            "candidate_id": candidate_id,
            "status": "INCOMPLETE",
            "experiment_completed": False,
            "experiment_passed": False,
            "observed_result": observed,
            "artifact_review": artifact_review,
            "validation_assessment": _validation_scope(validation_target, False),
            "supported_claims": [],
            "unsupported_claims": ["The preregistered minimum usable sample was not reached."],
            "remaining_unknowns": ["Primary experiment outcome", "Representativeness"],
            "next_action": "COMPLETE_OR_RESTART_EXPERIMENT",
        }

    if (artifact_required and not final_hash) or (review_required and not human_review):
        return {
            "schema_version": "1.0",
            "mode": "ASSESS",
            "experiment_id": exp_id,
            "candidate_id": candidate_id,
            "status": "INVALID_EXPERIMENT",
            "experiment_completed": True,
            "experiment_passed": False,
            "observed_result": observed,
            "artifact_review": artifact_review,
            "validation_assessment": _validation_scope(validation_target, False),
            "supported_claims": [],
            "unsupported_claims": [
                "Numeric threshold outcome cannot be accepted without the preregistered artifact/review requirements."
            ],
            "remaining_unknowns": ["Audited experiment authenticity"],
            "next_action": "FIX_AUDIT_GAP_OR_RESTART_EXPERIMENT",
        }

    passed = _comparison(observed_value, threshold, direction)
    status = "EXPERIMENT_PASSED" if passed else "EXPERIMENT_FAILED"
    supported = (
        [f"Observed value ({observed_value}) satisfied the preregistered threshold ({direction} {threshold})."]
        if passed
        else [f"Observed value ({observed_value}) did not satisfy the preregistered threshold ({direction} {threshold})."]
    )
    return {
        "schema_version": "1.0",
        "mode": "ASSESS",
        "experiment_id": exp_id,
        "candidate_id": candidate_id,
        "status": status,
        "experiment_completed": True,
        "experiment_passed": passed,
        "observed_result": observed,
        "artifact_review": artifact_review,
        "validation_assessment": _validation_scope(validation_target, passed),
        "supported_claims": supported,
        "unsupported_claims": [
            "Universal market prevalence beyond the tested sample.",
            "Market size.",
            "Any validation dimension not explicitly tested by this experiment.",
        ],
        "remaining_unknowns": [
            "Sample representativeness",
            "Untested validation dimensions",
        ],
        "next_action": "READY_FOR_SOLUTION_STRATEGY" if passed else "REVIEW_HYPOTHESIS_OR_SEGMENT",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment Validation DESIGN/ASSESS CLI")
    parser.add_argument("--mode", required=True, choices=["design", "assess"])
    parser.add_argument("--candidate-id")
    parser.add_argument("--experiment-id")
    parser.add_argument("--validation-target", default="BEHAVIOR_FREQUENCY")
    parser.add_argument("--hypothesis")
    parser.add_argument("--metric")
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--direction", default=">=", choices=[">=", "<=", ">", "<", "=="])
    parser.add_argument("--sample-target", type=int, default=5)
    parser.add_argument("--minimum-usable", type=int, default=5)
    parser.add_argument("--duration-days", type=int, default=7)
    parser.add_argument("--observed-value", type=float)
    parser.add_argument("--sample-achieved", type=int)
    parser.add_argument("--artifact-path")
    parser.add_argument("--artifact-hash")
    parser.add_argument("--audited-by")
    parser.add_argument("--audit-date")
    parser.add_argument("--input", help="ExperimentContract JSON path for ASSESS")
    parser.add_argument("--output")
    parser.add_argument("--sqlite-db")
    args = parser.parse_args()

    DiscoveryDB = _load_discovery_db_class() if args.sqlite_db else None
    db = DiscoveryDB(args.sqlite_db) if DiscoveryDB else None

    if args.mode == "design":
        if not all([args.candidate_id, args.hypothesis, args.metric, args.threshold is not None]):
            raise SystemExit("design requires --candidate-id --hypothesis --metric --threshold")
        contract = design_experiment(
            candidate_id=args.candidate_id,
            hypothesis=args.hypothesis,
            primary_metric=args.metric,
            target_threshold=args.threshold,
            validation_target=args.validation_target,
            direction=args.direction,
            sample_target=args.sample_target,
            minimum_usable=args.minimum_usable,
            duration_days=args.duration_days,
            experiment_id=args.experiment_id,
        )
        if db:
            db.preregister_experiment(contract["experiment_id"], contract["candidate_id"], contract)
        output = contract
    else:
        if args.observed_value is None or args.sample_achieved is None:
            raise SystemExit("assess requires --observed-value and --sample-achieved")

        if args.input:
            with open(args.input, "r", encoding="utf-8") as handle:
                contract = json.load(handle)
        elif db and args.experiment_id:
            contract = db.get_experiment_contract(args.experiment_id)
        else:
            raise SystemExit("assess requires --input, or --sqlite-db with --experiment-id; the locked contract is never reconstructed from CLI defaults")

        assessment = assess_experiment(
            contract=contract,
            observed_value=args.observed_value,
            sample_achieved=args.sample_achieved,
            artifact_path=args.artifact_path,
            artifact_hash=args.artifact_hash,
            audited_by=args.audited_by,
            audit_date=args.audit_date,
        )
        if db:
            db.record_experiment_assessment(
                assessment["experiment_id"],
                assessment,
                artifact_hash=assessment.get("artifact_review", {}).get("sha256"),
                audited_by=args.audited_by,
                audit_date=args.audit_date,
            )
        output = assessment

    encoded = json.dumps(output, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
    print(encoded)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"[ERROR] {exc}\n")
        raise SystemExit(2) from None
