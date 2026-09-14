# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
score_problem_candidate.py
Authoritative CLI Candidate Scoring & Evidence Verification Engine for Universal Problem Discovery.
Implements the 35-Point Research Prioritization Matrix, 5-Level Evidence Hard Gate,
Dual-Track Prioritization (Commercial vs Free Utility), Unverified Input Detection,
Multi-Dimensional Alternative Audits, Search Dorking, and Smallest Suitable Solution Scoping.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional
import urllib.parse

SATURATION_TRAP_PATTERN = re.compile(
    r"(mygate|nobrokerhood|classpro|tuitionplus|gym-management|apartment-rwa|society-management)",
    re.IGNORECASE,
)

STOP_CHECK_LABELS = {
    "infrequent_low_impact": "1. Infrequent & Low Operational Impact",
    "no_meaningful_workaround": "2. No Meaningful Workaround / Inaction with Low Consequence",
    "commercial_alternative_fits_well": "3. Commercial Alternative Fits Well (Multi-dimensional fit)",
    "single_source_bias": "4. Single Source Bias / Uncorroborated Anecdote",
    "internal_training_issue": "5. Internal Training / Policy Issue (Not Product Gap)",
    "unreachable_audience": "6. Unreachable Target Audience for Direct Validation",
}


@dataclass(frozen=True)
class ScoreDimensions:
    frequency: int
    severity: int
    workaround: int
    wtp: int  # In Track B, interpreted as Utility & Repeat Adoption
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
class SmallestSuitableSolution:
    format: str
    tool_name: str
    architecture: str
    distribution: str
    monetization: str


@dataclass(frozen=True)
class SolutionWedgeSpec:
    tier1_free_tool: Dict[str, str]
    tier2_micro_utility: Dict[str, Any]
    tier3_recurring_saas: Dict[str, Any]


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
    stop_checks_triggered: List[str]
    scores: Dict[str, int]
    evidence_sources: List[str]
    evidence_artifacts: List[str]
    recommended_action: str
    rank: int = 1
    smallest_solution: Optional[Dict[str, Any]] = None
    solution_wedge: Optional[Dict[str, Any]] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="35-Point Research Prioritization, Evidence Verification & Solution Scoping Engine."
    )
    parser.add_argument("--id", default="CANDIDATE-001", help="Unique identifier for candidate.")
    parser.add_argument("--title", default="Operational Problem Candidate", help="Short problem title.")
    parser.add_argument("--domain", default="General", help="Industry domain or vertical.")
    parser.add_argument(
        "--track",
        choices=["commercial", "free_utility"],
        default="commercial",
        help="Evaluation track: commercial (SaaS/WTP) or free_utility (Civic/Public/Local).",
    )
    parser.add_argument("--input-json", help="Path to input JSON file containing single candidate or batch list.")

    # 7 Core Scoring Dimensions (0 - 5)
    parser.add_argument("--freq", type=int, default=1, choices=range(0, 6), help="1. Frequency (0-5)")
    parser.add_argument("--severity", type=int, default=1, choices=range(0, 6), help="2. Severity & Risk (0-5)")
    parser.add_argument("--workaround", type=int, default=1, choices=range(0, 6), help="3. Workaround Investment (0-5)")
    parser.add_argument("--wtp", type=int, default=1, choices=range(0, 6), help="4. WTP (Commercial) or Utility (Free) (0-5)")
    parser.add_argument("--utility-impact", type=int, choices=range(0, 6), help="Alias for dimension 4 in free_utility track.")
    parser.add_argument("--decision-maker", type=int, default=1, choices=range(0, 6), help="5. Single Decision-Maker (0-5)")
    parser.add_argument("--feasibility", type=int, default=1, choices=range(0, 6), help="6. Technical Solo-Feasibility (0-5)")
    parser.add_argument("--discrepancy", type=int, default=1, choices=range(0, 6), help="7. Process Discrepancy (0-5)")

    # Evidence Level Hard Gate (1 - 5)
    parser.add_argument(
        "--evidence-level",
        type=int,
        default=1,
        choices=range(1, 6),
        help="Evidence Ladder (1=Behavioral, 2=Verbal, 3=Corroboration/Forum JSON, 4=Secondary, 5=Hypothesis)",
    )

    # Evidence Verification Inputs
    parser.add_argument(
        "--evidence-source",
        action="append",
        help="URL, transcript, or source quote backing candidate claims (can specify multiple times).",
    )
    parser.add_argument(
        "--evidence-artifact",
        action="append",
        help="Path to verified file artifact (screenshot, spreadsheet, error log) backing candidate claims.",
    )
    parser.add_argument(
        "--experiment-outcome",
        type=str,
        help="Observed results from concierge test, prototype trial, or landing page experiment.",
    )

    # 6 Mandatory Stop Checks
    parser.add_argument("--stop-infrequent", action="store_true", help="Trigger Stop Check 1: Infrequent & low impact.")
    parser.add_argument("--stop-no-workaround", action="store_true", help="Trigger Stop Check 2: No meaningful workaround.")
    parser.add_argument("--stop-alternative-fits", action="store_true", help="Trigger Stop Check 3: Commercial alternative fits well.")
    parser.add_argument("--stop-single-source", action="store_true", help="Trigger Stop Check 4: Single source bias.")
    parser.add_argument("--stop-training-issue", action="store_true", help="Trigger Stop Check 5: Internal training issue.")
    parser.add_argument("--stop-unreachable", action="store_true", help="Trigger Stop Check 6: Unreachable audience.")

    # Batch and Utility Modes
    parser.add_argument("--batch", action="store_true", help="Process input-json as a list of candidates and generate ranked leaderboard.")
    parser.add_argument("--top", type=int, default=10, help="Filter top N candidates in batch mode (default: 10).")
    parser.add_argument("--dorks", type=str, help="Generate multi-platform Google search dorks for target keyword/domain.")
    parser.add_argument("--export-obsidian", type=str, help="Export scored candidates as standardized Obsidian notes into directory.")
    parser.add_argument("--sync-csv", type=str, help="Rebuild or refresh discovery_matrix.csv in the target directory.")

    # Output formatting
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero status if candidate fails or is unverified.")
    parser.add_argument("--json", action="store_true", help="Output JSON result to stdout.")
    return parser.parse_args()


def generate_search_dorks(target: str) -> Dict[str, List[str]]:
    """Generate high-intent multi-platform search dorks and refinement queries."""
    clean_target = target.strip()
    return {
        "reddit_operator_queries": [
            f'site:reddit.com inurl:comments "{clean_target}" "spend hours every week"',
            f'site:reddit.com inurl:comments "{clean_target}" "our team is stuck using excel for"',
            f'site:reddit.com inurl:comments "{clean_target}" "nightmare to reconcile"',
            f'site:reddit.com inurl:comments "{clean_target}" "looking for a simple alternative to"',
        ],
        "relaxed_refinement_queries": [
            f"site:reddit.com {clean_target} manual spreadsheet problem",
            f"site:reddit.com {clean_target} took hours broke export",
            f"{clean_target} workaround template excel",
        ],
        "review_gap_queries": [
            f'site:g2.com/products/* "{clean_target}" "what do you dislike" OR "missing"',
            f'site:capterra.com "{clean_target}" "manual export" OR "clunky" OR "sync"',
            f'site:trustpilot.com/review/* "{clean_target}" "broken sync" OR "lost data"',
        ],
        "workflow_sop_and_templates": [
            f'filetype:pdf "standard operating procedure" "{clean_target}" reconciliation',
            f'filetype:xlsx template "{clean_target}" inventory OR audit',
            f'filetype:docx checklist compliance "{clean_target}" "step by step"',
            f'"{clean_target}" "submit" "portal" "Excel" "download CSV" "upload" "manually"',
        ],
        "vertical_store_queries": [
            f'site:apps.shopify.com/reviews "{clean_target}" "fails to sync" OR "broken"',
            f'site:wordpress.org/plugins "{clean_target}" "fatal error" OR "refund"',
            f'site:chromewebstore.google.com/detail "{clean_target}" "no longer works"',
        ],
        "paid_glue_work_jobs": [
            f'site:indeed.com "{clean_target}" "must have advanced Excel" "reconciliation"',
            f'site:linkedin.com/jobs "{clean_target}" "daily data entry" "cross-reference"',
        ],
        "github_and_hacker_news": [
            f'site:github.com/issues "{clean_target}" "feature request" OR "manual workaround"',
            f'site:github.com/issues "{clean_target}" "bulk import" OR "currently not supported"',
            f'site:news.ycombinator.com "Ask HN" "{clean_target}" "how do you manage"',
            f'site:producthunt.com/posts "{clean_target}" "alternative" OR "too expensive"',
        ],
        "local_and_india_queries": [
            f'"{clean_target}" complaint application process',
            f'"{clean_target}" documents required confusion',
            f'"{clean_target}" register Excel India',
            f'"{clean_target}" grievance report PDF',
        ],
    }


def print_search_dorks(target: str, dorks: Dict[str, List[str]], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"target": target, "dorks": dorks}, indent=2))
        return

    sys.stderr.write("========================================================\n")
    sys.stderr.write(f"🔎 SEARCH DORKS & REFINEMENT QUERIES: {target}\n")
    sys.stderr.write("========================================================\n")
    for category, queries in dorks.items():
        title = category.replace("_", " ").title()
        sys.stderr.write(f"\n📂 {title}:\n")
        for q in queries:
            encoded_query = urllib.parse.quote(q)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            sys.stderr.write(f"  • Query: {q}\n")
            sys.stderr.write(f"    URL  : {search_url}\n")
    sys.stderr.write("========================================================\n")


def derive_smallest_solution(title: str, domain: str, track: str) -> Dict[str, Any]:
    """Derive the smallest suitable solution without forcing SaaS progression."""
    clean_domain = domain.lower()
    clean_title = title.lower()

    if track == "free_utility" or any(k in clean_domain or k in clean_title for k in ["local", "village", "offline", "civic", "retail", "ration"]):
        return asdict(
            SmallestSuitableSolution(
                format="Static Web Utility (Zero Backend)",
                tool_name=f"{title} Quick Inspector",
                architecture="Standalone Angular / Vanilla Web App (Client-Side Only, Offline PWA)",
                distribution="Cloudflare Pages / GitHub Pages ($0 hosting)",
                monetization="Free Public Tool / Optional AdSense Passive Income",
            )
        )

    if any(k in clean_domain or k in clean_title for k in ["dev", "cli", "api", "git", "schema", "linter"]):
        return asdict(
            SmallestSuitableSolution(
                format="CLI Automation Tool",
                tool_name=f"{title.lower().replace(' ', '-')}-cli",
                architecture="Standalone Python (PEP 723) or Node.js Executable",
                distribution="Package Registry (npm/pnpm/pip) or GitHub Release",
                monetization="Open Core / Free Developer Tool",
            )
        )

    if any(k in clean_domain or k in clean_title for k in ["portal", "extension", "export", "scrape", "admin"]):
        return asdict(
            SmallestSuitableSolution(
                format="Browser Extension",
                tool_name=f"{title} Helper",
                architecture="Chrome Extension (Manifest V3 DOM Injection)",
                distribution="Chrome Web Store",
                monetization="$19 - $39 One-Time Payment",
            )
        )

    return asdict(
        SmallestSuitableSolution(
            format="Full-Stack Micro-SaaS",
            tool_name=f"{title} Platform",
            architecture="NestJS API + PostgreSQL (Prisma) + Angular UI",
            distribution="Self-Serve Web Application",
            monetization="$29 - $99 / month Recurring Subscription",
        )
    )


def derive_solution_wedge(title: str, domain: str) -> Dict[str, Any]:
    return asdict(
        SolutionWedgeSpec(
            tier1_free_tool={
                "tool_name": f"{title} Quick Inspector",
                "format": "Client-Side Standalone Angular / Static Web Utility",
                "input_data": "Drag-and-drop CSV, PDF, or text payload",
                "delivered_value": "Instant variance report (Zero backend, SEO ready)",
                "monetization": "Free Forever / Lead Magnet / AdSense",
            },
            tier2_micro_utility={
                "tool_name": f"{title} Workflow Extension",
                "format": "Chrome Extension (Manifest V3) or Standalone CLI Script",
                "pricing_one_time": "$19 - $49 one-time payment",
                "automation": "Direct DOM sync or one-click automated export/import",
            },
            tier3_recurring_saas={
                "product_name": f"{title} Cloud Platform",
                "format": "Full-Stack Micro-SaaS (NestJS + PostgreSQL + Angular)",
                "monthly_subscription": "$49 - $199 / month",
                "features": "Automated background cron sync, multi-seat teams, webhook alerts, compliance audit logs",
            },
        )
    )


def evaluate_candidate(
    candidate_id: str,
    title: str,
    domain: str,
    track: str,
    raw_scores: ScoreDimensions,
    evidence_level: int,
    stops: StopCheckStatus,
    evidence_sources: Optional[List[str]] = None,
    evidence_artifacts: Optional[List[str]] = None,
    experiment_outcome: Optional[str] = None,
    rank: int = 1,
) -> EvaluationResult:
    sources = evidence_sources or []
    artifacts = evidence_artifacts or []

    triggered_stops: List[str] = []

    if SATURATION_TRAP_PATTERN.search(title) or SATURATION_TRAP_PATTERN.search(domain):
        triggered_stops.append("Saturation Trap Gatekeeper: Market is brutally saturated by funded players.")

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

    if evidence_level == 5:
        adjusted_scores = {k: 0 for k in asdict(raw_scores)}
    elif evidence_level == 4:
        adjusted_scores = {k: min(v, 1) for k, v in asdict(raw_scores).items()}
    else:
        adjusted_scores = asdict(raw_scores)

    total = sum(adjusted_scores.values())

    # 1. Stop checks triggered -> Park immediately
    if triggered_stops:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            track=track,
            total_score=total,
            evidence_level=evidence_level,
            classification="PARKED / STOP_CHECK_TRIGGERED",
            status="PARKED",
            stop_checks_triggered=triggered_stops,
            scores=adjusted_scores,
            evidence_sources=sources,
            evidence_artifacts=artifacts,
            recommended_action="Halt research immediately. Candidate triggered mandatory stop checks.",
            rank=rank,
            smallest_solution=None,
            solution_wedge=None,
        )

    # 2. Score < 15 -> No problem fallback
    if total < 15:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            track=track,
            total_score=total,
            evidence_level=evidence_level,
            classification="HALT / NO_PROBLEM_FALLBACK",
            status="REJECTED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            evidence_sources=sources,
            evidence_artifacts=artifacts,
            recommended_action="Could not find an evidence-backed operational problem in the supplied domain input. Failure reason: Existing workarounds are sufficient, or search signals represent cosmetic complaints without operational consequence.",
            rank=rank,
            smallest_solution=None,
            solution_wedge=None,
        )

    # 3. Score 15 to 22 -> Low priority
    if total <= 22:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            track=track,
            total_score=total,
            evidence_level=evidence_level,
            classification="REJECT / LOW_RESEARCH_PRIORITY",
            status="KILLED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            evidence_sources=sources,
            evidence_artifacts=artifacts,
            recommended_action="Insufficient operational urgency or consequence. Archive finding; do NOT design solutions.",
            rank=rank,
            smallest_solution=None,
            solution_wedge=None,
        )

    # 4. Score >= 23: Crucial Evidence Verification Hard Gate
    has_primary_evidence = len(sources) > 0 or len(artifacts) > 0

    smallest = derive_smallest_solution(title, domain, track)
    wedge = derive_solution_wedge(title, domain)

    # If score is high but caller supplied ZERO evidence sources or artifacts
    if not has_primary_evidence:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            track=track,
            total_score=total,
            evidence_level=evidence_level,
            classification="UNVERIFIED_INPUT / RESEARCH_PRIORITY",
            status="UNVERIFIED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            evidence_sources=sources,
            evidence_artifacts=artifacts,
            recommended_action="Input scores are unverified assertions without attached evidence artifacts. High score indicates research priority, NOT validated customer demand. Attach primary evidence or interview notes before proceeding.",
            rank=rank,
            smallest_solution=smallest,
            solution_wedge=wedge,
        )

    # If primary evidence exists AND an experiment outcome was supplied and verified
    if experiment_outcome and experiment_outcome.strip():
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            track=track,
            total_score=total,
            evidence_level=evidence_level,
            classification="EXPERIMENT_VALIDATED OPPORTUNITY",
            status="VALIDATED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            evidence_sources=sources,
            evidence_artifacts=artifacts,
            recommended_action=f"Empirical validation confirmed via experiment outcome: '{experiment_outcome}'. Proceed to build Smallest Suitable Solution.",
            rank=rank,
            smallest_solution=smallest,
            solution_wedge=wedge,
        )

    # Primary evidence attached, but no experiment completed yet
    if total <= 27:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            track=track,
            total_score=total,
            evidence_level=evidence_level,
            classification="QUALIFIED RESEARCH CANDIDATE",
            status="QUALIFIED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            evidence_sources=sources,
            evidence_artifacts=artifacts,
            recommended_action="Solid candidate supported by evidence. Conduct 2–3 field user shadow sessions or design a concierge trial.",
            rank=rank,
            smallest_solution=smallest,
            solution_wedge=wedge,
        )

    # Total >= 28 with primary evidence -> High Research Priority (NOT validated yet!)
    return EvaluationResult(
        candidate_id=candidate_id,
        problem_title=title,
        domain=domain,
        track=track,
        total_score=total,
        evidence_level=evidence_level,
        classification="HIGH RESEARCH PRIORITY",
        status="RESEARCH_PRIORITY",
        stop_checks_triggered=[],
        scores=adjusted_scores,
        evidence_sources=sources,
        evidence_artifacts=artifacts,
        recommended_action="High acute pain supported by primary evidence. Execute low-cost experiment (Concierge MVP / Static Utility) to verify adoption before writing full-stack code.",
        rank=rank,
        smallest_solution=smallest,
        solution_wedge=wedge,
    )


def refresh_discovery_csv(out_dir: Path) -> Optional[Path]:
    """Automatically generate or refresh discovery_matrix.csv in the target directory."""
    try:
        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from export_discovery_matrix import generate_matrix

        csv_path = out_dir / "discovery_matrix.csv"
        generate_matrix(out_dir, csv_path)
        sys.stderr.write(f"📊 Auto-updated Discovery Matrix CSV: {csv_path.name}\n")
        return csv_path
    except Exception as err:
        sys.stderr.write(f"⚠️  Notice: Could not auto-refresh matrix CSV: {err}\n")
        return None


def export_to_obsidian(result: EvaluationResult, target_dir: Path) -> Path:
    """Export scored candidate as a standardized Obsidian discovery log note."""
    target_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    filename = f"PROB-{today}-{result.total_score}PTS-{result.candidate_id}.md"
    file_path = target_dir / filename

    sol_md = ""
    if result.smallest_solution:
        sol = result.smallest_solution
        sol_md = f"""
## 7. Smallest Suitable Solution Scoping
- **Format**: {sol['format']}
- **Tool Name**: {sol['tool_name']}
- **Architecture**: {sol['architecture']}
- **Distribution**: {sol['distribution']}
- **Monetization**: {sol['monetization']}
"""

    dim4_label = "Willingness to Pay (WTP)" if result.track == "commercial" else "Utility, Repeat Adoption & Time Saved"

    content = f"""---
tags: [discovery-log, candidate, {result.status.lower()}]
created: {datetime.now().strftime('%Y-%m-%d')}
candidate_id: {result.candidate_id}
track: {result.track}
validation_status: {result.status.lower()}
priority_score: {result.total_score}
domain: {result.domain}
evidence_level: Level {result.evidence_level}
rank: {result.rank}
---

# 📋 Problem Discovery Log: {result.problem_title}

## 1. Problem Statement & Operational Context
- **Candidate ID**: `{result.candidate_id}`
- **Domain**: {result.domain}
- **Track**: {result.track.upper()}
- **Classification**: {result.classification}
- **Status**: {result.status}
- **Recommended Action**: {result.recommended_action}

## 2. 35-Point Research Prioritization Matrix
| Dimension | Score (0–5) |
|---|:---:|
| 1. Frequency | {result.scores['frequency']} pts |
| 2. Severity & Risk | {result.scores['severity']} pts |
| 3. Workaround Investment | {result.scores['workaround']} pts |
| 4. {dim4_label} | {result.scores['wtp']} pts |
| 5. Single Decision-Maker | {result.scores['decision_maker']} pts |
| 6. Solo Feasibility | {result.scores['feasibility']} pts |
| 7. Process Discrepancy | {result.scores['discrepancy']} pts |
| **TOTAL RESEARCH PRIORITY** | **{result.total_score} / 35 PTS** |

## 3. Evidence Verification & Stop Checks
- **Evidence Level**: Level {result.evidence_level}
- **Sources Recorded**: {', '.join(result.evidence_sources) if result.evidence_sources else 'None provided'}
- **Artifacts Attached**: {', '.join(result.evidence_artifacts) if result.evidence_artifacts else 'None provided'}
- **Stop Checks Triggered**: {', '.join(result.stop_checks_triggered) if result.stop_checks_triggered else 'None (Clean)'}
{sol_md}
"""
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    return file_path


def parse_candidate_dict(
    payload: Dict[str, Any], defaults: argparse.Namespace
) -> tuple[str, str, str, str, ScoreDimensions, int, StopCheckStatus, List[str], List[str], Optional[str]]:
    cid = payload.get("id", defaults.id)
    title = payload.get("title", defaults.title)
    dom = payload.get("domain", defaults.domain)
    track = payload.get("track", defaults.track)
    sdata = payload.get("scores", {})

    dim4_val = sdata.get("utility_impact", sdata.get("track_dimension", sdata.get("wtp", 1)))

    raw = ScoreDimensions(
        frequency=sdata.get("frequency", 1),
        severity=sdata.get("severity", 1),
        workaround=sdata.get("workaround", 1),
        wtp=dim4_val,
        decision_maker=sdata.get("decision_maker", 1),
        feasibility=sdata.get("feasibility", 1),
        discrepancy=sdata.get("discrepancy", 1),
    )
    e_lvl = payload.get("evidence_level", defaults.evidence_level)
    stop_data = payload.get("stop_checks", {})
    stops = StopCheckStatus(
        infrequent_low_impact=stop_data.get("infrequent_low_impact", False),
        no_meaningful_workaround=stop_data.get("no_meaningful_workaround", False),
        commercial_alternative_fits_well=stop_data.get("commercial_alternative_fits_well", False),
        single_source_bias=stop_data.get("single_source_bias", False),
        internal_training_issue=stop_data.get("internal_training_issue", False),
        unreachable_audience=stop_data.get("unreachable_audience", False),
    )
    sources = payload.get("evidence_sources", [])
    artifacts = payload.get("evidence_artifacts", [])
    experiment = payload.get("experiment_outcome", None)
    return cid, title, dom, track, raw, e_lvl, stops, sources, artifacts, experiment


def process_batch(candidates_raw: List[Dict[str, Any]], args: argparse.Namespace) -> None:
    results: List[EvaluationResult] = []
    for c_raw in candidates_raw:
        cid, title, dom, track, raw, e_lvl, stops, sources, artifacts, exp = parse_candidate_dict(c_raw, args)
        res = evaluate_candidate(cid, title, dom, track, raw, e_lvl, stops, sources, artifacts, exp)
        results.append(res)

    results.sort(key=lambda x: x.total_score, reverse=True)
    ranked_results = [
        EvaluationResult(
            candidate_id=r.candidate_id,
            problem_title=r.problem_title,
            domain=r.domain,
            track=r.track,
            total_score=r.total_score,
            evidence_level=r.evidence_level,
            classification=r.classification,
            status=r.status,
            stop_checks_triggered=r.stop_checks_triggered,
            scores=r.scores,
            evidence_sources=r.evidence_sources,
            evidence_artifacts=r.evidence_artifacts,
            recommended_action=r.recommended_action,
            rank=idx + 1,
            smallest_solution=r.smallest_solution,
            solution_wedge=r.solution_wedge,
        )
        for idx, r in enumerate(results)
    ]

    top_n = ranked_results[: args.top] if args.top > 0 else ranked_results

    if args.export_obsidian:
        out_dir = Path(args.export_obsidian)
        for cand in top_n:
            if cand.total_score >= 23:
                saved = export_to_obsidian(cand, out_dir)
                sys.stderr.write(f"📝 Exported Obsidian dossier: {saved.name}\n")
        refresh_discovery_csv(out_dir)

    if args.json:
        print(json.dumps([asdict(r) for r in top_n], indent=2))
        return

    sys.stderr.write("========================================================================================\n")
    sys.stderr.write(f"🏆 35-POINT CANDIDATE PRIORITIZATION LEADERBOARD (Top {len(top_n)} of {len(ranked_results)})\n")
    sys.stderr.write("========================================================================================\n")
    sys.stderr.write(f"{'Rank':<5} | {'Candidate ID':<16} | {'Domain':<15} | {'Track':<10} | {'Score':<7} | {'Status':<12} | {'Title'}\n")
    sys.stderr.write("----------------------------------------------------------------------------------------\n")
    for r in top_n:
        sys.stderr.write(f"{r.rank:<5} | {r.candidate_id:<16} | {r.domain[:14]:<15} | {r.track[:9]:<10} | {r.total_score:<2}/35  | {r.status:<12} | {r.problem_title}\n")
    sys.stderr.write("========================================================================================\n")


def main() -> None:
    args = parse_args()

    if getattr(args, "sync_csv", None):
        target_dir = Path(args.sync_csv)
        refresh_discovery_csv(target_dir)
        sys.exit(0)

    if args.dorks:
        dorks = generate_search_dorks(args.dorks)
        print_search_dorks(args.dorks, dorks, args.json)
        sys.exit(0)

    sources: List[str] = args.evidence_source or []
    artifacts: List[str] = args.evidence_artifact or []
    exp_outcome: Optional[str] = args.experiment_outcome

    if args.input_json:
        raw_content = Path(args.input_json).read_text(encoding="utf-8").strip()
        parsed_json = json.loads(raw_content)

        if isinstance(parsed_json, list) or args.batch:
            candidates_list = parsed_json if isinstance(parsed_json, list) else [parsed_json]
            process_batch(candidates_list, args)
            sys.exit(0)

        cid, title, domain, track, raw_scores, evidence_level, stops, j_sources, j_artifacts, j_exp = parse_candidate_dict(parsed_json, args)
        sources.extend(j_sources)
        artifacts.extend(j_artifacts)
        if j_exp and not exp_outcome:
            exp_outcome = j_exp
    else:
        cid = args.id
        title = args.title
        domain = args.domain
        track = args.track

        dim4_val = args.utility_impact if args.utility_impact is not None else args.wtp

        raw_scores = ScoreDimensions(
            frequency=args.freq,
            severity=args.severity,
            workaround=args.workaround,
            wtp=dim4_val,
            decision_maker=args.decision_maker,
            feasibility=args.feasibility,
            discrepancy=args.discrepancy,
        )
        evidence_level = args.evidence_level
        stops = StopCheckStatus(
            infrequent_low_impact=args.stop_infrequent,
            no_meaningful_workaround=args.stop_no_workaround,
            commercial_alternative_fits_well=args.stop_alternative_fits,
            single_source_bias=args.stop_single_source,
            internal_training_issue=args.stop_training_issue,
            unreachable_audience=args.stop_unreachable,
        )

    result = evaluate_candidate(
        cid,
        title,
        domain,
        track,
        raw_scores,
        evidence_level,
        stops,
        evidence_sources=sources,
        evidence_artifacts=artifacts,
        experiment_outcome=exp_outcome,
    )

    if args.export_obsidian:
        out_dir = Path(args.export_obsidian)
        saved = export_to_obsidian(result, out_dir)
        sys.stderr.write(f"📝 Exported Obsidian dossier: {saved.name}\n")
        refresh_discovery_csv(out_dir)

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"📊 35-POINT CANDIDATE PRIORITIZATION: {result.candidate_id}\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Title             : {result.problem_title}\n")
        sys.stderr.write(f"Domain            : {result.domain}\n")
        sys.stderr.write(f"Track             : {result.track.upper()}\n")
        sys.stderr.write(f"Priority Score    : {result.total_score} / 35 PTS\n")
        sys.stderr.write(f"Evidence Level    : Level {result.evidence_level}\n")
        sys.stderr.write(f"Classification    : {result.classification}\n")
        sys.stderr.write(f"Validation Status : {result.status}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Frequency         : {result.scores['frequency']} pts\n")
        sys.stderr.write(f"Severity & Risk   : {result.scores['severity']} pts\n")
        sys.stderr.write(f"Workaround Invest : {result.scores['workaround']} pts\n")
        dim4_name = "WTP Clarity      " if result.track == "commercial" else "Utility & Adoption"
        sys.stderr.write(f"{dim4_name} : {result.scores['wtp']} pts\n")
        sys.stderr.write(f"Single Decision   : {result.scores['decision_maker']} pts\n")
        sys.stderr.write(f"Solo Feasibility  : {result.scores['feasibility']} pts\n")
        sys.stderr.write(f"Process Discrep   : {result.scores['discrepancy']} pts\n")
        sys.stderr.write("--------------------------------------------------------\n")
        if result.stop_checks_triggered:
            sys.stderr.write("⚠️  Triggered Stop Checks:\n")
            for sc in result.stop_checks_triggered:
                sys.stderr.write(f"  - {sc}\n")
            sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Recommended Action: {result.recommended_action}\n")
        if result.smallest_solution:
            sys.stderr.write("--------------------------------------------------------\n")
            sys.stderr.write("🎯 Smallest Suitable Solution:\n")
            sys.stderr.write(f"  Format      : {result.smallest_solution['format']}\n")
            sys.stderr.write(f"  Tool Name   : {result.smallest_solution['tool_name']}\n")
            sys.stderr.write(f"  Architecture: {result.smallest_solution['architecture']}\n")
            sys.stderr.write(f"  Distribution: {result.smallest_solution['distribution']}\n")
        sys.stderr.write("========================================================\n")

    if args.strict and result.status in ("PARKED", "REJECTED", "KILLED", "UNVERIFIED"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
