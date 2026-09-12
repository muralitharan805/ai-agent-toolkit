# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
score_problem_candidate.py
Authoritative CLI Candidate Scoring & Decision Engine for Universal Problem Discovery.
Implements the 35-Point Evidence Scoring Matrix, 5-Level Evidence Hard Gate,
Saturation Trap Gatekeeper, Batch Ranking Leaderboard, Search Dorking Generator,
and 3-Tier Solution Wedge Derivation.
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
    "no_meaningful_workaround": "2. No Meaningful Workaround / Free Tool Tolerated",
    "commercial_alternative_fits_well": "3. Commercial Alternative Fits Well (< $50/mo)",
    "single_source_bias": "4. Single Source Bias / Uncorroborated Anecdote",
    "internal_training_issue": "5. Internal Training / Policy Issue (Not Product Gap)",
    "unreachable_audience": "6. Unreachable Target Audience for Direct Validation",
}


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
class SolutionWedgeSpec:
    tier1_free_tool: Dict[str, str]
    tier2_micro_utility: Dict[str, Any]
    tier3_recurring_saas: Dict[str, Any]


@dataclass(frozen=True)
class EvaluationResult:
    candidate_id: str
    problem_title: str
    domain: str
    total_score: int
    evidence_level: int
    classification: str
    status: str
    stop_checks_triggered: List[str]
    scores: Dict[str, int]
    recommended_action: str
    rank: int = 1
    solution_wedge: Optional[Dict[str, Any]] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="35-Point Problem Candidate Evidence Scoring, Batch Ranking & Dorking Engine."
    )
    parser.add_argument("--id", default="CANDIDATE-001", help="Unique identifier for candidate.")
    parser.add_argument("--title", default="Operational Problem Candidate", help="Short problem title.")
    parser.add_argument("--domain", default="General", help="Industry domain or vertical.")
    parser.add_argument("--input-json", help="Path to input JSON file containing single candidate or batch list.")

    # 7 Core Scoring Dimensions (0 - 5)
    parser.add_argument("--freq", type=int, default=1, choices=range(0, 6), help="1. Frequency (0-5)")
    parser.add_argument("--severity", type=int, default=1, choices=range(0, 6), help="2. Financial Severity & Legal Risk (0-5)")
    parser.add_argument("--workaround", type=int, default=1, choices=range(0, 6), help="3. Existing Workaround Investment (0-5)")
    parser.add_argument("--wtp", type=int, default=1, choices=range(0, 6), help="4. Willingness to Pay (WTP) Clarity (0-5)")
    parser.add_argument("--decision-maker", type=int, default=1, choices=range(0, 6), help="5. Single Decision-Maker Workflow (0-5)")
    parser.add_argument("--feasibility", type=int, default=1, choices=range(0, 6), help="6. Technical Solo-Feasibility (0-5)")
    parser.add_argument("--discrepancy", type=int, default=1, choices=range(0, 6), help="7. Discrepancy & Data Fragility (0-5)")

    # Evidence Level Hard Gate (1 - 5)
    parser.add_argument("--evidence-level", type=int, default=1, choices=range(1, 6), help="Evidence Quality Ladder (1=Behavioral, 2=Verbal, 3=Corroboration, 4=Secondary, 5=Hypothesis)")

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
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero status if candidate fails.")
    parser.add_argument("--json", action="store_true", help="Output JSON result to stdout.")
    return parser.parse_args()


def generate_search_dorks(target: str) -> Dict[str, List[str]]:
    """Generate high-intent multi-platform search dorks for a domain or keyword."""
    clean_target = target.strip()
    return {
        "reddit_operator_queries": [
            f'site:reddit.com inurl:comments "{clean_target}" "spend hours every week"',
            f'site:reddit.com inurl:comments "{clean_target}" "our team is stuck using excel for"',
            f'site:reddit.com inurl:comments "{clean_target}" "nightmare to reconcile"',
            f'site:reddit.com inurl:comments "{clean_target}" "looking for a simple alternative to"',
        ],
        "review_gap_queries": [
            f'site:g2.com/products/* "{clean_target}" "what do you dislike" OR "missing"',
            f'site:capterra.com "{clean_target}" "manual export" OR "clunky" OR "sync"',
            f'site:trustpilot.com/review/* "{clean_target}" "broken sync" OR "lost data"',
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
    }


def print_search_dorks(target: str, dorks: Dict[str, List[str]], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"target": target, "dorks": dorks}, indent=2))
        return

    sys.stderr.write("========================================================\n")
    sys.stderr.write(f"🔎 HIGH-INTENT SEARCH DORKS: {target}\n")
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


def derive_solution_wedge(title: str, domain: str) -> Dict[str, Any]:
    return asdict(
        SolutionWedgeSpec(
            tier1_free_tool={
                "tool_name": f"{title} Quick Inspector",
                "format": "Client-Side Standalone Angular / Static Web Utility",
                "input_data": "Drag-and-drop CSV, PDF, or JSON payload",
                "delivered_value": "Instant discrepancy highlight table (Zero backend, SEO ready)",
                "monetization": "Free Forever Lead Magnet / Email Opt-in / AdSense",
            },
            tier2_micro_utility={
                "tool_name": f"{title} Workflow Extension",
                "format": "Chrome Extension (Manifest V3) or Standalone CLI Script",
                "pricing_one_time": "$19 - $49 one-time payment",
                "automation": "Direct DOM sync or one-click automated export/import",
            },
            tier3_recurring_saas={
                "product_name": f"{title} Cloud Platform",
                "format": "Full-Stack B2B Micro-SaaS (NestJS + PostgreSQL + Angular)",
                "monthly_subscription": "$49 - $199 / month",
                "features": "Automated background cron sync, multi-seat teams, webhook alerts, compliance audit logs",
            },
        )
    )


def evaluate_candidate(
    candidate_id: str,
    title: str,
    domain: str,
    raw_scores: ScoreDimensions,
    evidence_level: int,
    stops: StopCheckStatus,
    rank: int = 1,
) -> EvaluationResult:
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

    if triggered_stops:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            total_score=total,
            evidence_level=evidence_level,
            classification="PARKED / STOP_CHECK_TRIGGERED",
            status="PARKED",
            stop_checks_triggered=triggered_stops,
            scores=adjusted_scores,
            recommended_action="Halt research immediately. Candidate triggered mandatory stop checks.",
            rank=rank,
            solution_wedge=None,
        )

    if total < 15:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            total_score=total,
            evidence_level=evidence_level,
            classification="HALT / NO_PROBLEM_FALLBACK",
            status="REJECTED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            recommended_action="Could not find an evidence-backed operational problem in the supplied domain input. Failure reason: Existing workarounds are sufficient, or search signals represent cosmetic complaints without financial bleed.",
            rank=rank,
            solution_wedge=None,
        )
    elif total <= 22:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            total_score=total,
            evidence_level=evidence_level,
            classification="REJECT / KILL",
            status="KILLED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            recommended_action="Insufficient commercial urgency or excessive procurement friction. Archive finding; do NOT design solutions.",
            rank=rank,
            solution_wedge=None,
        )
    elif total <= 27:
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            total_score=total,
            evidence_level=evidence_level,
            classification="QUALIFIED OPPORTUNITY",
            status="QUALIFIED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            recommended_action="Solid candidate. Conduct 2–3 field customer interviews or operator shadowing sessions to verify WTP and decision-maker friction.",
            rank=rank,
            solution_wedge=None,
        )
    else:
        wedge = derive_solution_wedge(title, domain)
        return EvaluationResult(
            candidate_id=candidate_id,
            problem_title=title,
            domain=domain,
            total_score=total,
            evidence_level=evidence_level,
            classification="TIER-1 GOLD PROBLEM",
            status="VALIDATED",
            stop_checks_triggered=[],
            scores=adjusted_scores,
            recommended_action="High pain, immediate budget, and solo feasibility confirmed. Proceed directly to 3-tier prototype execution.",
            rank=rank,
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

    wedge_md = ""
    if result.solution_wedge:
        t1 = result.solution_wedge["tier1_free_tool"]
        t2 = result.solution_wedge["tier2_micro_utility"]
        t3 = result.solution_wedge["tier3_recurring_saas"]
        wedge_md = f"""
## 8. 3-Tier Solution Wedge Derivation
- **Tier 1 (Free Client-Side Utility)**: {t1['tool_name']} ({t1['format']})
  - Value: {t1['delivered_value']}
- **Tier 2 (Micro-Utility / Extension)**: {t2['tool_name']} ({t2['pricing_one_time']})
  - Automation: {t2['automation']}
- **Tier 3 (Production Micro-SaaS)**: {t3['product_name']} ({t3['monthly_subscription']})
  - Features: {t3['features']}
"""

    content = f"""---
tags: [discovery-log, candidate, {result.status.lower()}]
created: {datetime.now().strftime('%Y-%m-%d')}
candidate_id: {result.candidate_id}
domain: {result.domain}
evidence_level: Level {result.evidence_level}
total_score: {result.total_score}
status: {result.status.lower()}
rank: {result.rank}
---

# 📋 Problem Discovery Log: {result.problem_title}

## 1. Problem Statement & Operational Context
- **Candidate ID**: `{result.candidate_id}`
- **Domain**: {result.domain}
- **Classification**: {result.classification}
- **Status**: {result.status}
- **Recommended Action**: {result.recommended_action}

## 2. 35-Point Evidence Scoring Matrix
| Dimension | Score (0–5) |
|---|:---:|
| 1. Frequency | {result.scores['frequency']} pts |
| 2. Severity & Financial Risk | {result.scores['severity']} pts |
| 3. Workaround Investment | {result.scores['workaround']} pts |
| 4. Willingness to Pay (WTP) | {result.scores['wtp']} pts |
| 5. Single Decision-Maker | {result.scores['decision_maker']} pts |
| 6. Solo Feasibility | {result.scores['feasibility']} pts |
| 7. Data Discrepancy & Fragility | {result.scores['discrepancy']} pts |
| **TOTAL SCORE** | **{result.total_score} / 35 PTS** |

## 3. Evidence Quality & Stop Checks
- **Evidence Level**: Level {result.evidence_level}
- **Stop Checks Triggered**: {', '.join(result.stop_checks_triggered) if result.stop_checks_triggered else 'None (Clean)'}
{wedge_md}
"""
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    return file_path


def parse_candidate_dict(payload: Dict[str, Any], defaults: argparse.Namespace) -> tuple[str, str, str, ScoreDimensions, int, StopCheckStatus]:
    cid = payload.get("id", defaults.id)
    title = payload.get("title", defaults.title)
    dom = payload.get("domain", defaults.domain)
    sdata = payload.get("scores", {})
    raw = ScoreDimensions(
        frequency=sdata.get("frequency", 1),
        severity=sdata.get("severity", 1),
        workaround=sdata.get("workaround", 1),
        wtp=sdata.get("wtp", 1),
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
    return cid, title, dom, raw, e_lvl, stops


def process_batch(candidates_raw: List[Dict[str, Any]], args: argparse.Namespace) -> None:
    results: List[EvaluationResult] = []
    for c_raw in candidates_raw:
        cid, title, dom, raw, e_lvl, stops = parse_candidate_dict(c_raw, args)
        res = evaluate_candidate(cid, title, dom, raw, e_lvl, stops)
        results.append(res)

    results.sort(key=lambda x: x.total_score, reverse=True)
    ranked_results = [
        EvaluationResult(
            candidate_id=r.candidate_id,
            problem_title=r.problem_title,
            domain=r.domain,
            total_score=r.total_score,
            evidence_level=r.evidence_level,
            classification=r.classification,
            status=r.status,
            stop_checks_triggered=r.stop_checks_triggered,
            scores=r.scores,
            recommended_action=r.recommended_action,
            rank=idx + 1,
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
    sys.stderr.write(f"🏆 35-POINT PROBLEM CANDIDATE LEADERBOARD (Top {len(top_n)} of {len(ranked_results)} evaluated)\n")
    sys.stderr.write("========================================================================================\n")
    sys.stderr.write(f"{'Rank':<5} | {'Candidate ID':<16} | {'Domain':<15} | {'Score':<7} | {'Evidence':<8} | {'Status':<10} | {'Title'}\n")
    sys.stderr.write("----------------------------------------------------------------------------------------\n")
    for r in top_n:
        sys.stderr.write(f"{r.rank:<5} | {r.candidate_id:<16} | {r.domain[:14]:<15} | {r.total_score:<2}/35  | Level {r.evidence_level:<2} | {r.status:<10} | {r.problem_title}\n")
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

    if args.input_json:
        raw_content = Path(args.input_json).read_text(encoding="utf-8").strip()
        parsed_json = json.loads(raw_content)

        if isinstance(parsed_json, list) or args.batch:
            candidates_list = parsed_json if isinstance(parsed_json, list) else [parsed_json]
            process_batch(candidates_list, args)
            sys.exit(0)

        cid, title, domain, raw_scores, evidence_level, stops = parse_candidate_dict(parsed_json, args)
    else:
        cid = args.id
        title = args.title
        domain = args.domain
        raw_scores = ScoreDimensions(
            frequency=args.freq,
            severity=args.severity,
            workaround=args.workaround,
            wtp=args.wtp,
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

    result = evaluate_candidate(cid, title, domain, raw_scores, evidence_level, stops)

    if args.export_obsidian:
        out_dir = Path(args.export_obsidian)
        saved = export_to_obsidian(result, out_dir)
        sys.stderr.write(f"📝 Exported Obsidian dossier: {saved.name}\n")
        refresh_discovery_csv(out_dir)

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"📊 35-POINT PROBLEM CANDIDATE SCORING: {result.candidate_id}\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Title             : {result.problem_title}\n")
        sys.stderr.write(f"Domain            : {result.domain}\n")
        sys.stderr.write(f"Total Score       : {result.total_score} / 35 PTS\n")
        sys.stderr.write(f"Evidence Level    : Level {result.evidence_level}\n")
        sys.stderr.write(f"Classification    : {result.classification}\n")
        sys.stderr.write(f"Status            : {result.status}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Frequency         : {result.scores['frequency']} pts\n")
        sys.stderr.write(f"Severity & Risk   : {result.scores['severity']} pts\n")
        sys.stderr.write(f"Workaround Invest : {result.scores['workaround']} pts\n")
        sys.stderr.write(f"WTP Clarity       : {result.scores['wtp']} pts\n")
        sys.stderr.write(f"Single Decision   : {result.scores['decision_maker']} pts\n")
        sys.stderr.write(f"Solo Feasibility  : {result.scores['feasibility']} pts\n")
        sys.stderr.write(f"Data Discrepancy  : {result.scores['discrepancy']} pts\n")
        sys.stderr.write("--------------------------------------------------------\n")
        if result.stop_checks_triggered:
            sys.stderr.write("⚠️  Triggered Stop Checks:\n")
            for sc in result.stop_checks_triggered:
                sys.stderr.write(f"  - {sc}\n")
            sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Recommended Action: {result.recommended_action}\n")
        if result.solution_wedge:
            sys.stderr.write("--------------------------------------------------------\n")
            sys.stderr.write("🚀 3-Tier Solution Wedge Derivation:\n")
            sys.stderr.write(f"  Tier 1: {result.solution_wedge['tier1_free_tool']['tool_name']}\n")
            sys.stderr.write(f"  Tier 2: {result.solution_wedge['tier2_micro_utility']['tool_name']} ({result.solution_wedge['tier2_micro_utility']['pricing_one_time']})\n")
            sys.stderr.write(f"  Tier 3: {result.solution_wedge['tier3_recurring_saas']['product_name']} ({result.solution_wedge['tier3_recurring_saas']['monthly_subscription']})\n")
        sys.stderr.write("========================================================\n")

    if args.strict and result.status in ("PARKED", "REJECTED", "KILLED"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
