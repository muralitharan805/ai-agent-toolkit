"""SeyaliCraft Build Verdict Engine.

Evaluates problem discovery candidates stored in SQLite against SeyaliCraft
portfolio criteria (client utilities, extensions, micro-SaaS, educational content)
and produces an objective Go / No-Go decision with technical and monetization guidance.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class BuildDecision(str, Enum):
    """Overall build recommendation verdict."""
    GO = "GO"
    HOLD = "HOLD"
    NO_GO = "NO_GO"


class RecommendedShape(str, Enum):
    """The smallest justified solution shape for SeyaliCraft."""
    CLIENT_SIDE_UTILITY = "CLIENT_SIDE_UTILITY"
    BROWSER_EXTENSION = "BROWSER_EXTENSION"
    STANDALONE_SAAS = "STANDALONE_SAAS"
    EDUCATIONAL_GUIDE = "EDUCATIONAL_GUIDE"
    NON_SOFTWARE = "NON_SOFTWARE"


@dataclass
class CandidateVerdict:
    """Represents a structured product decision for a single candidate."""
    candidate_id: str
    title: str
    domain: str
    target_operator: str
    research_score: int
    evidence_level: str
    validation_status: str
    lifecycle_status: str
    verified_signals_count: int
    decision: BuildDecision
    confidence: str
    recommended_shape: RecommendedShape
    reversibility: str
    justification: str
    seyalicraft_fit: Dict[str, str]
    next_steps: List[str]

    def format_terminal_card(self) -> str:
        """Format the verdict into a scannable executive card for terminal output."""
        lines = [
            "=" * 64,
            f" SEYALICRAFT BUILD VERDICT: {self.candidate_id}",
            "=" * 64,
            f"Title:             {self.title}",
            f"Domain:            {self.domain}",
            f"Target Audience:   {self.target_operator or 'General / Developers'}",
            f"Evidence Strength: Score: {self.research_score}/35 | Level: {self.evidence_level} ({self.verified_signals_count} signals)",
            f"Validation Status: {self.validation_status} (Lifecycle: {self.lifecycle_status})",
            "-" * 64,
            f"DECISION:          {self.decision.value} ({self._decision_tag()})",
            f"Confidence:        {self.confidence}",
            f"Recommended Shape: {self.recommended_shape.value}",
            f"Reversibility:     {self.reversibility}",
            "-" * 64,
            f"Justification:\n  {self.justification}",
            "",
            "SeyaliCraft Portfolio Fit:",
        ]
        for key, val in self.seyalicraft_fit.items():
            lines.append(f"  - {key}: {val}")

        lines.append("")
        lines.append("Next Concrete Steps:")
        for idx, step in enumerate(self.next_steps, 1):
            lines.append(f"  {idx}. {step}")
        lines.append("=" * 64)
        return "\n".join(lines)

    def _decision_tag(self) -> str:
        if self.decision == BuildDecision.GO:
            return "RECOMMENDED TO BUILD"
        if self.decision == BuildDecision.HOLD:
            return "VALIDATE FIRST BEFORE BUILDING"
        return "DO NOT BUILD (REJECTED)"


def _parse_json(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return cleaned[:35].strip("-") or "tool"


def _determine_solution_shape(
    title: str,
    domain: str,
    solution_class: Optional[str],
    evaluation: Dict[str, Any],
) -> RecommendedShape:
    """Determine the optimal solution class using keyword and constraint heuristics."""
    if solution_class:
        normalized = solution_class.upper()
        if "UTILITY" in normalized or "SCRIPT" in normalized:
            return RecommendedShape.CLIENT_SIDE_UTILITY
        if "EXTENSION" in normalized:
            return RecommendedShape.BROWSER_EXTENSION
        if "SAAS" in normalized:
            return RecommendedShape.STANDALONE_SAAS
        if "NON_SOFTWARE" in normalized:
            return RecommendedShape.NON_SOFTWARE

    text = f"{title} {domain}".lower()
    saas_keywords = ("inventory", "supply chain", "dental", "ehr", "billing", "multi-tenant", "crm")
    if any(kw in text for kw in saas_keywords):
        return RecommendedShape.STANDALONE_SAAS

    ext_keywords = ("browser", "dom", "chrome", "extension", "tab", "clipboard", "autofill")
    if any(kw in text for kw in ext_keywords):
        return RecommendedShape.BROWSER_EXTENSION

    utility_keywords = (
        "coordinate", "geospatial", "lat", "long", "converter", "formatter", "json",
        "calculator", "validator", "parser", "schema", "datum", "csv", "transform"
    )
    if any(kw in text for kw in utility_keywords):
        return RecommendedShape.CLIENT_SIDE_UTILITY

    return RecommendedShape.CLIENT_SIDE_UTILITY


def _evaluate_decision(
    score: int,
    evidence_level: str,
    shape: RecommendedShape,
    validation_status: str,
    has_passed_experiment: bool,
) -> Tuple[BuildDecision, str, str, str]:
    """Evaluate decision, confidence, reversibility, and justification."""
    if score < 15:
        return (
            BuildDecision.NO_GO,
            "HIGH",
            "N/A",
            f"Problem severity/frequency score ({score}/35) is below the viability threshold (15/35).",
        )

    if evidence_level in ("UNASSESSED", "L1"):
        return (
            BuildDecision.NO_GO,
            "MODERATE",
            "N/A",
            f"Evidence level is {evidence_level} (unverified/hearsay). Verified L2+ primary signals are mandatory.",
        )

    if shape == RecommendedShape.STANDALONE_SAAS:
        if has_passed_experiment or validation_status in ("VALIDATED", "PARTIALLY_VALIDATED"):
            return (
                BuildDecision.GO,
                "HIGH",
                "Type 1 (One-Way Door - High Resource Commitment)",
                "Problem is validated with passed empirical experiments. Proceed with pilot deployment.",
            )
        return (
            BuildDecision.HOLD,
            "MODERATE",
            "Type 1 (One-Way Door - High Resource Commitment)",
            f"Problem is real (Score: {score}/35), but SaaS requires ongoing database and auth infra. "
            "Validate with a manual concierge/spreadsheet trial before scaffolding full stack.",
        )

    if shape in (RecommendedShape.CLIENT_SIDE_UTILITY, RecommendedShape.BROWSER_EXTENSION):
        if score >= 18 and evidence_level in ("L2", "L3", "L4", "L5"):
            return (
                BuildDecision.GO,
                "HIGH",
                "Type 2 (Two-Way Door - Low Risk, Highly Reversible)",
                f"High utility value (Score: {score}/35) and recurring search demand. Pure client-side "
                "execution guarantees zero server maintenance and zero API vulnerabilities.",
            )
        return (
            BuildDecision.HOLD,
            "LOW",
            "Type 2 (Two-Way Door)",
            "Moderate interest, but corroborating signals are thin. Gather 2 more search queries first.",
        )

    return (
        BuildDecision.NO_GO,
        "MODERATE",
        "N/A",
        "Problem does not warrant software intervention.",
    )


def _build_seyalicraft_fit(shape: RecommendedShape, title: str, domain: str) -> Dict[str, str]:
    """Map the solution shape to SeyaliCraft's operational and monetization models."""
    slug = _slugify(title)
    if shape == RecommendedShape.CLIENT_SIDE_UTILITY:
        return {
            "Target Placement": f"seyalicraft.com/tools/{slug}",
            "Tech Architecture": "Static SPA (Angular 19+ Standalone / Vanilla TS) with zero backend",
            "Monthly Infra Cost": "$0 / month (Static hosting via Cloudflare Pages or Vercel)",
            "Monetization Strategy": "High-volume Organic SEO Keywords + Display Advertising (AdSense)",
        }
    if shape == RecommendedShape.BROWSER_EXTENSION:
        return {
            "Target Placement": f"Chrome Web Store (SeyaliCraft {title[:20]})",
            "Tech Architecture": "Manifest V3 Client Extension (Vanilla TypeScript + Content Scripts)",
            "Monthly Infra Cost": "$0 / month (Local client execution)",
            "Monetization Strategy": "Freemium / In-browser utility branding driving traffic to seyalicraft.com",
        }
    if shape == RecommendedShape.STANDALONE_SAAS:
        return {
            "Target Placement": f"app.seyalicraft.com or standalone domain",
            "Tech Architecture": "NestJS API + Next.js + PostgreSQL + Stripe billing",
            "Monthly Infra Cost": "$15 - $40 / month (VPS compute + Managed database)",
            "Monetization Strategy": "Recurring monthly/annual subscription ($19 - $49 / month)",
        }
    return {
        "Target Placement": "seyalicraft.com/blog or knowledge base",
        "Tech Architecture": "Educational guide / Static markdown article",
        "Monthly Infra Cost": "$0 / month",
        "Monetization Strategy": "Top-of-funnel SEO traffic and email newsletter signups",
    }


def _build_next_steps(decision: BuildDecision, shape: RecommendedShape, title: str) -> List[str]:
    """Generate concise, actionable next steps based on decision and shape."""
    slug = _slugify(title)
    if decision == BuildDecision.GO and shape == RecommendedShape.CLIENT_SIDE_UTILITY:
        return [
            f"Scaffold client-side converter/tool component under SeyaliCraft repository.",
            f"Target URL path: /tools/{slug} with proper OpenGraph and JSON-LD schema metadata.",
            "Deploy to static hosting with zero backend and verify zero memory leaks.",
        ]
    if decision == BuildDecision.HOLD and shape == RecommendedShape.STANDALONE_SAAS:
        return [
            "Do NOT write backend SaaS code or provision servers yet.",
            "Run a 7-day manual concierge experiment (e.g. Google Sheets / WhatsApp template).",
            "Verify if at least 2 operators commit to paying before architecting multi-tenant database.",
        ]
    if decision == BuildDecision.GO and shape == RecommendedShape.BROWSER_EXTENSION:
        return [
            "Initialize Manifest V3 boilerplate with minimal requested permissions.",
            "Test DOM interactions across target web pages.",
            "Publish to Chrome Web Store with SeyaliCraft branding.",
        ]
    return [
        "Record observation in discovery.sqlite and archive candidate.",
        "Focus development hours on higher-scoring, recurring utility candidates.",
    ]


def evaluate_candidate(conn: sqlite3.Connection, candidate_id: str) -> Optional[CandidateVerdict]:
    """Evaluate a single candidate by ID from an open SQLite connection."""
    row = conn.execute(
        """
        SELECT candidate_id, title, domain, target_operator, research_score,
               evidence_level, validation_status, lifecycle_status, solution_class,
               evaluation_json, solution_json
        FROM candidates WHERE candidate_id=?
        """,
        (candidate_id,),
    ).fetchone()

    if not row:
        return None

    signals_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM evidence_signals WHERE candidate_id=?",
        (candidate_id,),
    ).fetchone()["cnt"]

    exp_rows = conn.execute(
        "SELECT outcome_verdict FROM experiments WHERE candidate_id=?",
        (candidate_id,),
    ).fetchall()
    has_passed = any(r["outcome_verdict"] == "PASSED" for r in exp_rows)

    score = int(row["research_score"] or 0)
    level = str(row["evidence_level"] or "UNASSESSED")
    eval_dict = _parse_json(row["evaluation_json"])

    shape = _determine_solution_shape(
        title=row["title"],
        domain=row["domain"],
        solution_class=row["solution_class"],
        evaluation=eval_dict,
    )

    decision, confidence, reversibility, justification = _evaluate_decision(
        score=score,
        evidence_level=level,
        shape=shape,
        validation_status=row["validation_status"],
        has_passed_experiment=has_passed,
    )

    seyalicraft_fit = _build_seyalicraft_fit(shape, row["title"], row["domain"])
    next_steps = _build_next_steps(decision, shape, row["title"])

    return CandidateVerdict(
        candidate_id=row["candidate_id"],
        title=row["title"],
        domain=row["domain"],
        target_operator=row["target_operator"] or "",
        research_score=score,
        evidence_level=level,
        validation_status=row["validation_status"],
        lifecycle_status=row["lifecycle_status"],
        verified_signals_count=signals_count,
        decision=decision,
        confidence=confidence,
        recommended_shape=shape,
        reversibility=reversibility,
        justification=justification,
        seyalicraft_fit=seyalicraft_fit,
        next_steps=next_steps,
    )


def evaluate_all_candidates(db_path: str) -> List[CandidateVerdict]:
    """Evaluate all candidates present in the target discovery SQLite database."""
    if not Path(db_path).exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT candidate_id FROM candidates ORDER BY candidate_id ASC").fetchall()
        verdicts: List[CandidateVerdict] = []
        for r in rows:
            v = evaluate_candidate(conn, r["candidate_id"])
            if v:
                verdicts.append(v)
        return verdicts
    finally:
        conn.close()
