# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Research-priority CLI with explicit local artifact and experiment integrity gates.

File hashes are an integrity check; a named human must also audit authenticity and claims.
This CLI does not search the web, verify interview identities, or certify product demand.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import quote

DIMENSIONS = ("frequency", "severity", "workaround", "wtp", "decision_maker", "feasibility", "discrepancy")
STOP_KEYS = ("infrequent_low_impact", "no_meaningful_workaround", "commercial_alternative_fits_well", "single_source_bias", "internal_training_issue", "unreachable_audience")


@dataclass(frozen=True)
class ScoreDimensions:
    frequency: int
    severity: int
    workaround: int
    wtp: int
    decision_maker: int
    feasibility: int
    discrepancy: int


@dataclass(frozen=True)
class StopCheckStatus:
    infrequent_low_impact: bool = False
    no_meaningful_workaround: bool = False
    commercial_alternative_fits_well: bool = False
    single_source_bias: bool = False
    internal_training_issue: bool = False
    unreachable_audience: bool = False


@dataclass(frozen=True)
class EvaluationResult:
    candidate_id: str
    problem_title: str
    domain: str
    track: str
    total_score: int
    evidence_level: int
    classification: str
    status: str
    stop_checks_triggered: list[str]
    scores: dict[str, int]
    evidence_sources: list[str]
    evidence_artifacts: list[str]
    recommended_action: str
    rank: int = 1
    smallest_solution: dict[str, Any] | None = None
    solution_wedge: dict[str, Any] | None = None
    evidence_verified: bool = False
    experiment_completed: bool = False
    experiment_passed: bool = False
    evidence_audit: list[dict[str, Any]] | None = None
    experiment: dict[str, Any] | None = None


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _audited_artifact(record: Any) -> bool:
    """Reject absent, tampered, remote or unreviewed files; authenticity still requires human review."""
    if not isinstance(record, dict):
        return False
    path, digest, reviewer = (record.get(k) for k in ("artifact_path", "sha256", "reviewed_by"))
    reviewed = _date(record.get("reviewed_on"))
    if not all(isinstance(x, str) and x.strip() for x in (path, digest, reviewer)):
        return False
    if not re.fullmatch(r"[a-fA-F0-9]{64}", digest) or not reviewed or reviewed > date.today():
        return False
    file = Path(path).expanduser()
    try:
        if not file.is_file() or file.is_symlink() or file.stat().st_size > 25_000_000:
            return False
        return hashlib.sha256(file.read_bytes()).hexdigest().lower() == digest.lower()
    except OSError:
        return False


def audit_evidence(records: Any) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    if not isinstance(records, list):
        return False, checks
    for record in records:
        ok = False
        if isinstance(record, dict):
            observed, reviewed = _date(record.get("observed_on")), _date(record.get("reviewed_on"))
            ok = (type(record.get("level")) is int and record["level"] in (1, 2)
                  and isinstance(record.get("claim"), str) and bool(record["claim"].strip())
                  and observed is not None and reviewed is not None
                  and observed <= reviewed and _audited_artifact(record))
        checks.append({"claim": record.get("claim", "") if isinstance(record, dict) else "",
                       "integrity_passed": bool(ok)})
    return any(item["integrity_passed"] for item in checks), checks


def audit_experiment(exp: Any) -> tuple[bool, bool]:
    """Check the pre-recorded metric and a locally reviewed outcome artifact, not prose."""
    if not isinstance(exp, dict):
        return False, False
    preregistered, started, ended, reviewed = (_date(exp.get(k)) for k in
                                                ("preregistered_on", "started_on", "ended_on", "reviewed_on"))
    if any(value is None for value in (preregistered, started, ended, reviewed)):
        return False, False
    if not preregistered <= started <= ended <= reviewed <= date.today():
        return False, False
    if not all(isinstance(exp.get(k), str) and exp[k].strip() for k in ("hypothesis", "metric", "failure_rule")):
        return False, False
    if type(exp.get("sample_size")) is not int or exp["sample_size"] < 1:
        return False, False
    if exp.get("direction") not in ("at_least", "at_most"):
        return False, False
    threshold, observed = exp.get("success_threshold"), exp.get("observed_value")
    if any(type(x) not in (int, float) or not float("-inf") < x < float("inf") for x in (threshold, observed)):
        return False, False
    if not _audited_artifact(exp):
        return False, False
    return True, (observed >= threshold if exp["direction"] == "at_least" else observed <= threshold)


def derive_smallest_solution(constraints: Any) -> dict[str, Any] | None:
    """Require observed operational needs; never select SaaS from title keywords."""
    if not isinstance(constraints, dict) or not constraints:
        return None
    allowed = {"non_software_sufficient", "needs_interactive_ui", "needs_batch_automation",
               "needs_browser_integration", "needs_multi_user_sync", "needs_server_storage",
               "needs_background_jobs", "offline_required", "notes"}
    if any(key not in allowed for key in constraints):
        raise ValueError("Unknown solution_constraints field")
    if any(type(value) is not bool for key, value in constraints.items() if key != "notes"):
        raise ValueError("Solution requirements must be explicit booleans")
    if constraints.get("non_software_sufficient"):
        fmt, rationale = "template_sop", "A documented non-software workaround sufficiently resolves the measured problem."
    elif any(constraints.get(k) for k in ("needs_multi_user_sync", "needs_server_storage", "needs_background_jobs")):
        fmt, rationale = "micro_saas", "Shared state, server persistence, or unattended background processing is required."
    elif constraints.get("needs_browser_integration"):
        fmt, rationale = "browser_extension", "The task must act inside an existing browser page."
    elif constraints.get("needs_batch_automation") and not constraints.get("needs_interactive_ui"):
        fmt, rationale = "cli_tool", "A repeatable local batch job needs no UI or hosted service."
    elif constraints.get("needs_interactive_ui"):
        fmt, rationale = "static_web_utility", "Client-side interaction is enough; no server need was documented."
    else:
        return None
    return {"format": fmt, "reason": rationale, "offline_required": constraints.get("offline_required", False),
            "requirements": constraints, "review_required": True}


def evaluate_candidate(candidate_id: str, title: str, domain: str, track: str,
                       raw_scores: ScoreDimensions, evidence_level: int, stops: StopCheckStatus,
                       evidence_sources: list[str] | None = None, evidence_artifacts: list[str] | None = None,
                       experiment_outcome: str | None = None, rank: int = 1,
                       evidence_records: list[dict[str, Any]] | None = None,
                       experiment: dict[str, Any] | None = None,
                       solution_constraints: dict[str, Any] | None = None) -> EvaluationResult:
    if track not in ("commercial", "free_utility") or type(evidence_level) is not int or evidence_level not in range(1, 6):
        raise ValueError("Invalid track or evidence_level")
    raw = asdict(raw_scores)
    if any(type(value) is not int or not 0 <= value <= 5 for value in raw.values()):
        raise ValueError("Scores must be integers between 0 and 5")
    scores = {key: (0 if evidence_level == 5 else min(value, 1) if evidence_level == 4 else value)
              for key, value in raw.items()}
    total = sum(scores.values())
    triggered = [key for key in STOP_KEYS if getattr(stops, key)]
    verified, audit = audit_evidence(evidence_records or [])
    completed, passed = audit_experiment(experiment)
    smallest = derive_smallest_solution(solution_constraints)
    if triggered:
        status, classification, action = "PARKED", "PARKED / STOP_CHECK_TRIGGERED", "Review stop checks and root causes before continuing."
    elif total < 15:
        status, classification, action = "REJECTED", "HALT / NO_PROBLEM_FALLBACK", "Could not find an evidence-backed operational problem in the supplied domain input."
    elif total <= 22:
        status, classification, action = "KILLED", "LOW_RESEARCH_PRIORITY", "Archive the candidate; improve evidence before proposing a solution."
    elif not verified:
        status, classification, action = "UNVERIFIED", "UNVERIFIED_INPUT / RESEARCH_PRIORITY", "Attach primary evidence with a local artifact, SHA-256 and dated named manual review. URLs and raw scores cannot verify a claim."
    elif completed and passed:
        status, classification, action = "VALIDATED", "EXPERIMENT_VALIDATED OPPORTUNITY", "Human reviewer must confirm actual behavior and scope only the evidenced solution."
    elif completed:
        status, classification, action = "EXPERIMENT_FAILED", "EXPERIMENT_FAILED / REVISE_OR_PARK", "Observed result missed the preregistered threshold; revise or park."
    elif total <= 27:
        status, classification, action = "QUALIFIED", "QUALIFIED RESEARCH CANDIDATE", "Run 2-3 shadow sessions and preregister a small trial."
    else:
        status, classification, action = "RESEARCH_PRIORITY", "HIGH RESEARCH PRIORITY", "Run a preregistered trial; score is not proof of demand."
    if experiment_outcome:
        action += " Legacy free-text experiment_outcome ignored: provide a reviewed structured experiment."
    if smallest is None and total >= 23:
        action += " Collect solution_constraints before choosing an architecture."
    return EvaluationResult(candidate_id, title, domain, track, total, evidence_level, classification,
                            status, triggered, scores, evidence_sources or [], evidence_artifacts or [],
                            action, rank, smallest, None, verified, completed, passed, audit,
                            experiment if isinstance(experiment, dict) else None)


def generate_search_dorks(target: str) -> dict[str, list[str]]:
    """Return queries only; no network operations performed."""
    return {"reddit": [f'site:reddit.com "{target}" manual workaround', f'site:reddit.com "{target}" reconciliation'],
            "reviews": [f'site:g2.com "{target}" missing export', f'site:capterra.com "{target}" manual data entry'],
            "field_search": [f'"{target}" Excel WhatsApp India', f'"{target}" operator error handoff']}


def export_to_obsidian(result: EvaluationResult, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "-", result.candidate_id)
    path = target_dir / f"PROB-{datetime.now():%Y%m%d}-{result.total_score}PTS-{safe_id}.md"
    header = {"candidate_id": result.candidate_id, "title": result.problem_title, "domain": result.domain,
              "track": result.track, "priority_score": result.total_score, "classification": result.classification,
              "validation_status": result.status, "evidence_level": result.evidence_level,
              "evidence_verified": str(result.evidence_verified).lower(),
              "experiment_completed": str(result.experiment_completed).lower(),
              "experiment_passed": str(result.experiment_passed).lower()}
    # JSON strings are valid YAML quoted scalars, including titles containing punctuation.
    frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in header.items())
    content = (f"---\n{frontmatter}\n---\n\n# Problem Discovery Log: {result.problem_title}\n\n"
               f"## Research priority: {result.total_score}/35\n\n## Status: {result.status}\n\n{result.recommended_action}\n\n"
               f"## Dimension scores\n\n```json\n{json.dumps(result.scores, indent=2)}\n```\n\n"
               f"## Sources and evidence\n\n```json\n{json.dumps({'sources': result.evidence_sources, 'artifacts': result.evidence_artifacts, 'audit': result.evidence_audit}, indent=2)}\n```\n\n"
               f"## Experiment contract and observations\n\n```json\n{json.dumps(result.experiment, indent=2)}\n```\n\n"
               f"## Smallest suitable solution (requires human review)\n\n```json\n{json.dumps(result.smallest_solution, indent=2)}\n```\n")
    path.write_text(content, encoding="utf-8")
    return path


def refresh_discovery_csv(out_dir: Path) -> Path:
    from export_discovery_matrix import generate_matrix
    path = out_dir / "discovery_matrix.csv"
    generate_matrix(out_dir, path)
    return path


def parse_candidate_dict(payload: dict[str, Any], defaults: argparse.Namespace) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("scores", {}), dict):
        raise ValueError("Candidate and scores must be objects")
    s = payload.get("scores", {})
    dim4 = s.get("utility_impact", s.get("track_dimension", s.get("wtp", 1)))
    raw = ScoreDimensions(*(dim4 if key == "wtp" else s.get(key, 1) for key in DIMENSIONS))
    flags = payload.get("stop_checks", {})
    if not isinstance(flags, dict) or any(type(value) is not bool for value in flags.values()):
        raise ValueError("stop_checks must be a boolean-valued object")
    return dict(candidate_id=payload.get("id", defaults.id), title=payload.get("title", defaults.title),
                domain=payload.get("domain", defaults.domain), track=payload.get("track", defaults.track),
                raw_scores=raw, evidence_level=payload.get("evidence_level", defaults.evidence_level),
                stops=StopCheckStatus(**flags), evidence_sources=payload.get("evidence_sources", []),
                evidence_artifacts=payload.get("evidence_artifacts", []),
                experiment_outcome=payload.get("experiment_outcome"),
                evidence_records=payload.get("evidence_records", []), experiment=payload.get("experiment"),
                solution_constraints=payload.get("solution_constraints"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="35-point research priority and audited experiment gate")
    for flag, default in (("id", "CANDIDATE-001"), ("title", "Operational Problem Candidate"), ("domain", "General")):
        parser.add_argument("--" + flag, default=default)
    parser.add_argument("--track", choices=("commercial", "free_utility"), default="commercial")
    parser.add_argument("--input-json")
    for flag in ("freq", "severity", "workaround", "wtp", "decision-maker", "feasibility", "discrepancy"):
        parser.add_argument("--" + flag, type=int, choices=range(6), default=1)
    parser.add_argument("--utility-impact", type=int, choices=range(6))
    parser.add_argument("--evidence-level", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--evidence-source", action="append", default=[])
    parser.add_argument("--evidence-artifact", action="append", default=[])
    parser.add_argument("--experiment-outcome")  # Legacy prose never validates.
    parser.add_argument("--evidence-json", help="JSON file with evidence_records, experiment and solution_constraints")
    for flag in ("infrequent", "no-workaround", "alternative-fits", "single-source", "training-issue", "unreachable"):
        parser.add_argument("--stop-" + flag, action="store_true")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--dorks")
    parser.add_argument("--export-obsidian")
    parser.add_argument("--sync-csv")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.sync_csv:
        path = refresh_discovery_csv(Path(args.sync_csv).expanduser())
        print(json.dumps({"csv": str(path)}) if args.json else f"Updated: {path}")
        return
    if args.dorks:
        suggestions = generate_search_dorks(args.dorks)
        print(json.dumps({"target": args.dorks, "dorks": suggestions}, indent=2) if args.json else
              "\n".join(f"{q} -> https://www.google.com/search?q={quote(q)}" for group in suggestions.values() for q in group))
        return
    if args.input_json:
        data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        if not isinstance(data, (dict, list)):
            raise ValueError("input-json must be a candidate object or array")
        if isinstance(data, list) or args.batch:
            payloads = data if isinstance(data, list) else [data]
            results = [evaluate_candidate(**parse_candidate_dict(item, args)) for item in payloads]
        else:
            results = [evaluate_candidate(**parse_candidate_dict(data, args))]
    else:
        dim4 = args.utility_impact if args.utility_impact is not None else args.wtp
        scores = ScoreDimensions(args.freq, args.severity, args.workaround, dim4,
                                 args.decision_maker, args.feasibility, args.discrepancy)
        flags = StopCheckStatus(args.stop_infrequent, args.stop_no_workaround,
                                args.stop_alternative_fits, args.stop_single_source,
                                args.stop_training_issue, args.stop_unreachable)
        extra = json.loads(Path(args.evidence_json).read_text(encoding="utf-8")) if args.evidence_json else {}
        if not isinstance(extra, dict):
            raise ValueError("evidence-json must be an object")
        results = [evaluate_candidate(args.id, args.title, args.domain, args.track, scores,
                                      args.evidence_level, flags, args.evidence_source,
                                      args.evidence_artifact, args.experiment_outcome,
                                      evidence_records=extra.get("evidence_records"),
                                      experiment=extra.get("experiment"),
                                      solution_constraints=extra.get("solution_constraints"))]
    results.sort(key=lambda result: result.total_score, reverse=True)
    results = [EvaluationResult(**{**asdict(result), "rank": index + 1}) for index, result in enumerate(results)]
    selected = results[:args.top] if args.top > 0 else results
    if args.export_obsidian:
        directory = Path(args.export_obsidian).expanduser()
        for result in selected:
            export_to_obsidian(result, directory)
        refresh_discovery_csv(directory)
    if args.json:
        print(json.dumps([asdict(item) for item in selected] if args.batch or len(selected) != 1 else asdict(selected[0]), indent=2))
    else:
        for result in selected:
            print(f"{result.rank}. {result.candidate_id}: {result.total_score}/35 | {result.status} | {result.classification}\n   {result.recommended_action}")
    if args.strict and any(item.status not in ("QUALIFIED", "RESEARCH_PRIORITY", "VALIDATED") for item in selected):
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
