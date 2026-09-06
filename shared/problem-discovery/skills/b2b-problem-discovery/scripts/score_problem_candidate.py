# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Score Problem Candidate CLI Tool.

Evaluates problem discovery candidates across the 7-dimension 35-point evidence rubric,
evaluates the 6 mandatory stop checks, enforces commercial pre-scoring audit rules,
and determines validation status and next actions.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ScoreBreakdown:
    frequency: int = 1
    consequence_wtp: int = 1
    workaround_strength: int = 1
    evidence_quality: int = 1
    segment_reach: int = 1
    alternative_gap: int = 1
    access_to_validation: int = 1


@dataclass
class StopCheckStatus:
    infrequent_low_impact: bool = False
    no_meaningful_workaround: bool = False
    commercial_alternative_fits_well: bool = False
    single_source_bias: bool = False
    internal_training_issue: bool = False
    unreachable_audience: bool = False


@dataclass
class EvaluationResult:
    candidate_id: str
    total_score: int
    classification: str  # REJECTED, INVESTIGATE, EVIDENCE_BACKED_HYPOTHESIS, STRONG_VALIDATION_CANDIDATE
    status: str  # PARKED, INVESTIGATING, HYPOTHESIS, VALIDATED, REJECTED
    stop_checks_triggered: List[str]
    scores: Dict[str, int]
    recommended_action: str
    recommended_tier: Optional[str] = None


STOP_CHECK_LABELS = {
    "infrequent_low_impact": "Stop Check #1: Infrequent pain with no material consequence",
    "no_meaningful_workaround": "Stop Check #2: Target users have no meaningful workaround",
    "commercial_alternative_fits_well": "Stop Check #3: Commercial alternative fits well (< $50/mo)",
    "single_source_bias": "Stop Check #4: Evidence originates from only single source",
    "internal_training_issue": "Stop Check #5: Issue is internal training/adoption rather than product gap",
    "unreachable_audience": "Stop Check #6: Target decision-makers cannot realistically be reached",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate problem discovery candidates against the 35-point scoring rubric and 6 stop checks."
    )
    parser.add_argument("--id", type=str, default="CANDIDATE-001", help="Candidate identifier.")
    parser.add_argument("--input-json", type=str, help="Path to JSON file containing scoring payload.")
    parser.add_argument("--freq", type=int, choices=[1, 3, 5], default=1, help="Frequency (1, 3, 5).")
    parser.add_argument("--consequence", type=int, choices=[1, 3, 5], default=1, help="Consequence & WTP (1, 3, 5).")
    parser.add_argument("--workaround", type=int, choices=[1, 3, 5], default=1, help="Workaround strength (1, 3, 5).")
    parser.add_argument("--evidence", type=int, choices=[1, 3, 5], default=1, help="Evidence quality ladder (1, 3, 5).")
    parser.add_argument("--reach", type=int, choices=[1, 3, 5], default=1, help="Segment reach (1, 3, 5).")
    parser.add_argument("--gap", type=int, choices=[1, 3, 5], default=1, help="Alternative gap (1, 3, 5).")
    parser.add_argument("--access", type=int, choices=[1, 3, 5], default=1, help="Access to validation (1, 3, 5).")

    # Stop check flags
    parser.add_argument("--stop-infrequent", action="store_true", help="Trigger Stop Check #1.")
    parser.add_argument("--stop-no-workaround", action="store_true", help="Trigger Stop Check #2.")
    parser.add_argument("--stop-alternative-fits", action="store_true", help="Trigger Stop Check #3.")
    parser.add_argument("--stop-single-source", action="store_true", help="Trigger Stop Check #4.")
    parser.add_argument("--stop-training-issue", action="store_true", help="Trigger Stop Check #5.")
    parser.add_argument("--stop-unreachable", action="store_true", help="Trigger Stop Check #6.")

    parser.add_argument("--strict", action="store_true", help="Exit code 1 if candidate is rejected or parked.")
    parser.add_argument("--json", action="store_true", help="Output JSON result to stdout.")
    return parser.parse_args()


def load_from_json(file_path: Path) -> tuple[str, ScoreBreakdown, StopCheckStatus]:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    candidate_id = data.get("id", "CANDIDATE-JSON")
    scores_data = data.get("scores", {})
    breakdown = ScoreBreakdown(
        frequency=scores_data.get("frequency", 1),
        consequence_wtp=scores_data.get("consequence_wtp", 1),
        workaround_strength=scores_data.get("workaround_strength", 1),
        evidence_quality=scores_data.get("evidence_quality", 1),
        segment_reach=scores_data.get("segment_reach", 1),
        alternative_gap=scores_data.get("alternative_gap", 1),
        access_to_validation=scores_data.get("access_to_validation", 1),
    )
    stops_data = data.get("stop_checks", {})
    stops = StopCheckStatus(
        infrequent_low_impact=stops_data.get("infrequent_low_impact", False),
        no_meaningful_workaround=stops_data.get("no_meaningful_workaround", False),
        commercial_alternative_fits_well=stops_data.get("commercial_alternative_fits_well", False),
        single_source_bias=stops_data.get("single_source_bias", False),
        internal_training_issue=stops_data.get("internal_training_issue", False),
        unreachable_audience=stops_data.get("unreachable_audience", False),
    )
    return candidate_id, breakdown, stops


def evaluate_candidate(
    candidate_id: str, scores: ScoreBreakdown, stops: StopCheckStatus
) -> EvaluationResult:
    triggered_stops: List[str] = []
    if stops.infrequent_low_impact:
        triggered_stops.append(STOP_CHECK_LABELS["infrequent_low_impact"])
    if stops.no_meaningful_workaround:
        triggered_stops.append(STOP_CHECK_LABELS["no_meaningful_workaround"])
    if stops.commercial_alternative_fits_well:
        triggered_stops.append(STOP_CHECK_LABELS["commercial_alternative_fits_well"])
    if stops.single_source_bias:
        triggered_stops.append(STOP_CHECK_LABELS["single_source_bias"])
    if stops.internal_training_issue:
        triggered_stops.append(STOP_CHECK_LABELS["internal_training_issue"])
    if stops.unreachable_audience:
        triggered_stops.append(STOP_CHECK_LABELS["unreachable_audience"])

    total = (
        scores.frequency
        + scores.consequence_wtp
        + scores.workaround_strength
        + scores.evidence_quality
        + scores.segment_reach
        + scores.alternative_gap
        + scores.access_to_validation
    )

    scores_dict = asdict(scores)

    if triggered_stops:
        return EvaluationResult(
            candidate_id=candidate_id,
            total_score=total,
            classification="REJECTED_OR_PARKED",
            status="PARKED",
            stop_checks_triggered=triggered_stops,
            scores=scores_dict,
            recommended_action="Stop research immediately. Problem triggered mandatory stop checks.",
            recommended_tier=None,
        )

    if total < 15:
        return EvaluationResult(
            candidate_id=candidate_id,
            total_score=total,
            classification="REJECT / PARK",
            status="REJECTED",
            stop_checks_triggered=[],
            scores=scores_dict,
            recommended_action="Could not find a valid, evidence-backed problem in the supplied input. Park finding.",
            recommended_tier=None,
        )
    elif total <= 22:
        return EvaluationResult(
            candidate_id=candidate_id,
            total_score=total,
            classification="INVESTIGATE",
            status="INVESTIGATING",
            stop_checks_triggered=[],
            scores=scores_dict,
            recommended_action="Collect stronger primary behavioral evidence. Do NOT design a solution yet.",
            recommended_tier=None,
        )
    elif total <= 28:
        return EvaluationResult(
            candidate_id=candidate_id,
            total_score=total,
            classification="EVIDENCE-BACKED HYPOTHESIS",
            status="HYPOTHESIS",
            stop_checks_triggered=[],
            scores=scores_dict,
            recommended_action="Run focused user validation interviews and deeper alternative audits.",
            recommended_tier="Tier 1 or Tier 2 (Utility Tool / Chrome Extension)",
        )
    else:
        return EvaluationResult(
            candidate_id=candidate_id,
            total_score=total,
            classification="STRONG VALIDATION CANDIDATE",
            status="VALIDATED",
            stop_checks_triggered=[],
            scores=scores_dict,
            recommended_action="Confirm with independent users and begin 3-tier production tech stack prototype scoping.",
            recommended_tier="Tier 1 (Angular Client Tool) & Tier 3 (NestJS B2B Micro-SaaS)",
        )


def main() -> None:
    args = parse_args()

    if args.input_json:
        candidate_id, scores, stops = load_from_json(Path(args.input_json))
    else:
        candidate_id = args.id
        scores = ScoreBreakdown(
            frequency=args.freq,
            consequence_wtp=args.consequence,
            workaround_strength=args.workaround,
            evidence_quality=args.evidence,
            segment_reach=args.reach,
            alternative_gap=args.gap,
            access_to_validation=args.access,
        )
        stops = StopCheckStatus(
            infrequent_low_impact=args.stop_infrequent,
            no_meaningful_workaround=args.stop_no_workaround,
            commercial_alternative_fits_well=args.stop_alternative_fits,
            single_source_bias=args.stop_single_source,
            internal_training_issue=args.stop_training_issue,
            unreachable_audience=args.stop_unreachable,
        )

    result = evaluate_candidate(candidate_id, scores, stops)

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"📊 35-POINT PROBLEM CANDIDATE SCORING: {result.candidate_id}\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Total Score       : {result.total_score} / 35 PTS\n")
        sys.stderr.write(f"Classification    : {result.classification}\n")
        sys.stderr.write(f"Status            : {result.status}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Frequency         : {result.scores['frequency']} pts\n")
        sys.stderr.write(f"Consequence & WTP : {result.scores['consequence_wtp']} pts\n")
        sys.stderr.write(f"Workaround        : {result.scores['workaround_strength']} pts\n")
        sys.stderr.write(f"Evidence Quality  : {result.scores['evidence_quality']} pts\n")
        sys.stderr.write(f"Segment Reach     : {result.scores['segment_reach']} pts\n")
        sys.stderr.write(f"Alternative Gap   : {result.scores['alternative_gap']} pts\n")
        sys.stderr.write(f"Validation Access : {result.scores['access_to_validation']} pts\n")
        sys.stderr.write("--------------------------------------------------------\n")
        if result.stop_checks_triggered:
            sys.stderr.write("⚠️  Triggered Stop Checks:\n")
            for sc in result.stop_checks_triggered:
                sys.stderr.write(f"  - {sc}\n")
            sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Recommended Action: {result.recommended_action}\n")
        if result.recommended_tier:
            sys.stderr.write(f"Prototype Tier    : {result.recommended_tier}\n")
        sys.stderr.write("========================================================\n")

    if args.strict and result.status in ("PARKED", "REJECTED"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
