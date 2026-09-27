"""Strict stage precondition checking and quality monitoring for the Problem Discovery lifecycle.

Enforces deterministic gating standards: no stage is permitted to execute if prerequisite
data is missing, unassessed, or out of lifecycle sequence.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agents.problem_discovery.config import get_default_db_path
from agents.problem_discovery.orchestration.models import WorkflowStage


class StagePreconditionResult(BaseModel):
    """Result of evaluating whether a target workflow stage is permitted to execute."""

    allowed: bool
    target_stage: WorkflowStage
    current_stage: Optional[WorkflowStage] = None
    reason: str = ""
    required_fix: str = ""
    diagnostics: Dict[str, Any] = Field(default_factory=dict)

    def format_terminal_card(self) -> str:
        """Format an informative terminal card summarizing the precondition result.

        @returns Human-readable multi-line formatted string.
        """
        status_text = "PASSED (PERMITTED)" if self.allowed else "BLOCKED (PRECONDITION FAILED)"
        lines: List[str] = [
            "=" * 64,
            f"  STAGE PRECONDITION MONITOR: {status_text}",
            f"  Target Stage : {self.target_stage.value}",
        ]
        if self.current_stage:
            lines.append(f"  Current Stage: {self.current_stage.value}")
        lines.append(f"  Status       : {'READY TO EXECUTE' if self.allowed else 'EXECUTION PREVENTED'}")
        if self.reason:
            lines.append(f"  Reason       : {self.reason}")
        if self.required_fix:
            lines.append(f"  Required Fix : {self.required_fix}")
        if self.diagnostics:
            lines.append("  Diagnostics  :")
            for key, val in self.diagnostics.items():
                lines.append(f"    - {key}: {val}")
        lines.append("=" * 64)
        return "\n".join(lines)


class StageVerificationResult(BaseModel):
    """Result of verifying that a stage execution successfully persisted valid state."""

    verified: bool
    stage: WorkflowStage
    message: str = ""
    warnings: List[str] = Field(default_factory=list)
    persisted_records: Dict[str, Any] = Field(default_factory=dict)


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open a SQLite connection with Row factory and busy timeout.

    @param db_path - Optional path to the discovery SQLite file.
    @returns sqlite3.Connection instance.
    """
    path = str(db_path or get_default_db_path())
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


def _check_planning_preconditions(
    conn: sqlite3.Connection,
    identifier: Optional[str],
    prompt: Optional[str],
) -> StagePreconditionResult:
    """Validate preconditions for the RESEARCH_PLANNING stage.

    @param conn - Active SQLite connection.
    @param identifier - Optional research run identifier.
    @param prompt - User prompt text.
    @returns StagePreconditionResult.
    """
    clean_prompt = (prompt or "").strip()
    if identifier and identifier.startswith("RUN-"):
        row = conn.execute(
            "SELECT research_id, plan_json, status FROM research_runs WHERE research_id = ?",
            (identifier,),
        ).fetchone()
        if row and row["plan_json"]:
            return StagePreconditionResult(
                allowed=True,
                target_stage=WorkflowStage.RESEARCH_PLANNING,
                current_stage=WorkflowStage.EVIDENCE_RESEARCH,
                reason=f"Research run '{identifier}' is already planned. Re-planning will update plan.",
                diagnostics={"research_id": identifier, "status": row["status"]},
            )

    if len(clean_prompt) < 10 and not identifier:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.RESEARCH_PLANNING,
            current_stage=WorkflowStage.RESEARCH_PLANNING,
            reason="Research prompt is too short or empty.",
            required_fix="Provide a detailed problem statement or operational friction description.",
        )

    return StagePreconditionResult(
        allowed=True,
        target_stage=WorkflowStage.RESEARCH_PLANNING,
        current_stage=WorkflowStage.RESEARCH_PLANNING,
        reason="Research prompt is valid and ready for planning.",
    )


def _check_evidence_preconditions(
    conn: sqlite3.Connection,
    identifier: Optional[str],
) -> StagePreconditionResult:
    """Validate preconditions for the EVIDENCE_RESEARCH stage.

    @param conn - Active SQLite connection.
    @param identifier - Required research run identifier.
    @returns StagePreconditionResult.
    """
    if not identifier or not identifier.startswith("RUN-"):
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EVIDENCE_RESEARCH,
            current_stage=WorkflowStage.RESEARCH_PLANNING,
            reason="Missing required research run identifier (e.g. RUN-2026-001).",
            required_fix="Specify a valid RUN-ID (e.g. --stage evidence-research RUN-2026-006).",
        )

    row = conn.execute(
        "SELECT research_id, plan_json, status FROM research_runs WHERE research_id = ?",
        (identifier,),
    ).fetchone()
    if not row:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EVIDENCE_RESEARCH,
            current_stage=WorkflowStage.RESEARCH_PLANNING,
            reason=f"Research run '{identifier}' does not exist in SQLite database.",
            required_fix=f"Execute 'research-planning' first to initialize run '{identifier}'.",
        )

    if row["status"] in ("COMPLETED", "ARCHIVED"):
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EVIDENCE_RESEARCH,
            current_stage=WorkflowStage.COMPLETED,
            reason=f"Research run '{identifier}' is {row['status']}.",
            required_fix="Initialize a new research run for new exploration.",
        )

    has_valid_plan = False
    query_count = 0
    stream_count = 0
    if row["plan_json"]:
        try:
            plan = json.loads(row["plan_json"])
            if isinstance(plan, dict):
                streams = plan.get("research_streams") or plan.get("streams") or []
                queries = plan.get("search_queries") or []
                questions = plan.get("investigation_questions") or []
                objectives = plan.get("primary_objectives") or plan.get("objective")

                if streams:
                    stream_count = len(streams)
                    query_count = sum(
                        len(s.get("search_queries", []))
                        for s in streams
                        if isinstance(s, dict)
                    )
                    has_valid_plan = True
                elif queries:
                    query_count = len(queries)
                    stream_count = 1
                    has_valid_plan = True
                elif questions or objectives:
                    has_valid_plan = True
                    stream_count = 1
        except Exception:
            has_valid_plan = False

    if not has_valid_plan:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EVIDENCE_RESEARCH,
            current_stage=WorkflowStage.RESEARCH_PLANNING,
            reason=f"Research run '{identifier}' has no valid research plan or search queries.",
            required_fix=f"Execute 'research-planning' for '{identifier}' first.",
        )

    sig_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ?",
        (identifier,),
    ).fetchone()["cnt"]

    summary_str = f"{query_count} query/queries" if query_count else f"{stream_count} stream(s)"
    return StagePreconditionResult(
        allowed=True,
        target_stage=WorkflowStage.EVIDENCE_RESEARCH,
        current_stage=WorkflowStage.EVIDENCE_RESEARCH,
        reason=f"Research run '{identifier}' has a valid plan with {summary_str}.",
        diagnostics={
            "existing_signals": sig_count,
            "streams_count": stream_count,
            "search_queries_count": query_count,
        },
    )


def _check_evaluation_preconditions(
    conn: sqlite3.Connection,
    identifier: Optional[str],
) -> StagePreconditionResult:
    """Validate preconditions for the PROBLEM_EVALUATION stage.

    @param conn - Active SQLite connection.
    @param identifier - Research run identifier or candidate identifier.
    @returns StagePreconditionResult.
    """
    clean_id = (identifier or "").strip().upper()
    research_id = clean_id if clean_id.startswith("RUN-") else None

    if clean_id.startswith("CAND-"):
        cand_row = conn.execute(
            "SELECT candidate_id, origin_research_id FROM candidates WHERE candidate_id = ?",
            (clean_id,),
        ).fetchone()
        if cand_row:
            research_id = cand_row["origin_research_id"]

    if not research_id:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.PROBLEM_EVALUATION,
            current_stage=WorkflowStage.EVIDENCE_RESEARCH,
            reason="Missing required research run identifier (e.g. RUN-2026-006).",
            required_fix="Specify a RUN-ID (e.g. --stage problem-evaluation RUN-2026-006).",
        )

    total_signals = conn.execute(
        "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ?",
        (research_id,),
    ).fetchone()["cnt"]

    if total_signals == 0:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.PROBLEM_EVALUATION,
            current_stage=WorkflowStage.EVIDENCE_RESEARCH,
            reason=f"Research run '{research_id}' has 0 evidence signals.",
            required_fix=f"Execute 'evidence-research {research_id}' first to collect authentic signals.",
        )

    assessed_count = conn.execute(
        """
        SELECT COUNT(*) as cnt FROM evidence_signals
        WHERE research_id = ? AND evidence_level IN ('L1', 'L2', 'L3', 'L4')
        """,
        (research_id,),
    ).fetchone()["cnt"]

    unassessed_count = total_signals - assessed_count

    if assessed_count == 0:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.PROBLEM_EVALUATION,
            current_stage=WorkflowStage.EVIDENCE_RESEARCH,
            reason=(
                f"All {total_signals} evidence signals for '{research_id}' are UNASSESSED. "
                "Epistemic hygiene forbids evaluating problem candidates on unverified claims."
            ),
            required_fix=(
                "Review authentic source URLs and extract verifiable workarounds to qualify "
                "signals to L1–L4 before problem evaluation."
            ),
            diagnostics={"unassessed_signals": unassessed_count, "assessed_signals": 0},
        )

    unassigned_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ? AND candidate_id IS NULL",
        (research_id,),
    ).fetchone()["cnt"]

    return StagePreconditionResult(
        allowed=True,
        target_stage=WorkflowStage.PROBLEM_EVALUATION,
        current_stage=WorkflowStage.PROBLEM_EVALUATION,
        reason=(
            f"Research run '{research_id}' has {assessed_count} qualified signal(s) "
            f"({unassigned_count} unassigned) ready for clustering."
        ),
        diagnostics={
            "total_signals": total_signals,
            "qualified_signals": assessed_count,
            "unassigned_signals": unassigned_count,
        },
    )


def _check_experiment_preconditions(
    conn: sqlite3.Connection,
    identifier: Optional[str],
    user_submission: Optional[str],
) -> StagePreconditionResult:
    """Validate preconditions for the EXPERIMENT_VALIDATION stage.

    @param conn - Active SQLite connection.
    @param identifier - Candidate identifier or research run identifier.
    @param user_submission - User-provided observation text for ASSESS mode.
    @returns StagePreconditionResult.
    """
    clean_id = (identifier or "").strip().upper()
    candidate_id = clean_id if clean_id.startswith("CAND-") else None

    if clean_id.startswith("EXP-"):
        exp = conn.execute(
            "SELECT candidate_id FROM experiments WHERE experiment_id = ?",
            (clean_id,),
        ).fetchone()
        if exp:
            candidate_id = exp["candidate_id"]

    if clean_id.startswith("RUN-"):
        cand = conn.execute(
            "SELECT candidate_id FROM candidates WHERE origin_research_id = ? ORDER BY candidate_id ASC LIMIT 1",
            (clean_id,),
        ).fetchone()
        if cand:
            candidate_id = cand["candidate_id"]
        else:
            return StagePreconditionResult(
                allowed=False,
                target_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                current_stage=WorkflowStage.PROBLEM_EVALUATION,
                reason=f"No problem candidates exist for research run '{clean_id}'.",
                required_fix=f"Execute 'problem-evaluation {clean_id}' first to form candidates.",
            )

    if not candidate_id:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            current_stage=WorkflowStage.PROBLEM_EVALUATION,
            reason="Missing required candidate identifier (e.g. CAND-001).",
            required_fix="Specify a CAND-ID (e.g. --stage experiment-validation CAND-001).",
        )

    cand_row = conn.execute(
        "SELECT candidate_id, research_score, evaluation_json, validation_status FROM candidates WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    if not cand_row:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            current_stage=WorkflowStage.PROBLEM_EVALUATION,
            reason=f"Candidate '{candidate_id}' does not exist in SQLite database.",
            required_fix="Execute problem evaluation first to create the candidate.",
        )

    if not cand_row["evaluation_json"] or cand_row["research_score"] is None:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            current_stage=WorkflowStage.PROBLEM_EVALUATION,
            reason=f"Candidate '{candidate_id}' has not been evaluated (missing research score).",
            required_fix=f"Execute 'problem-evaluation' on candidate '{candidate_id}' first.",
        )

    # Check existing experiments
    experiments = conn.execute(
        "SELECT experiment_id, outcome_verdict, sample_target, metric_name FROM experiments WHERE candidate_id = ? ORDER BY created_at DESC",
        (candidate_id,),
    ).fetchall()

    is_submitting_data = bool(user_submission and len(user_submission.strip()) > 15)

    if not is_submitting_data:
        # DESIGN mode check: if an experiment is already PREREGISTERED, do not allow duplicate design
        for exp in experiments:
            if exp["outcome_verdict"] == "PREREGISTERED":
                return StagePreconditionResult(
                    allowed=False,
                    target_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                    current_stage=WorkflowStage.PAUSED,
                    reason=(
                        f"Experiment '{exp['experiment_id']}' is already PREREGISTERED and awaiting "
                        f"real-world trial results (target sample: {exp['sample_target']})."
                    ),
                    required_fix=(
                        f"Conduct the trial and submit observed results using:\n"
                        f"python -m agents.problem_discovery.cli --stage experiment-validation "
                        f"\"{exp['experiment_id']}: observed_value=... sample=...\""
                    ),
                    diagnostics={
                        "experiment_id": exp["experiment_id"],
                        "metric_name": exp["metric_name"],
                        "sample_target": exp["sample_target"],
                    },
                )

    return StagePreconditionResult(
        allowed=True,
        target_stage=WorkflowStage.EXPERIMENT_VALIDATION,
        current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
        reason=(
            f"Candidate '{candidate_id}' is ready for experiment "
            f"{'assessment' if is_submitting_data else 'design'}."
        ),
        diagnostics={"existing_experiments": len(experiments)},
    )


def _check_solution_preconditions(
    conn: sqlite3.Connection,
    identifier: Optional[str],
) -> StagePreconditionResult:
    """Validate preconditions for the SOLUTION_STRATEGY stage.

    @param conn - Active SQLite connection.
    @param identifier - Candidate identifier or research run identifier.
    @returns StagePreconditionResult.
    """
    clean_id = (identifier or "").strip().upper()
    candidate_id = clean_id if clean_id.startswith("CAND-") else None

    if clean_id.startswith("RUN-"):
        cand = conn.execute(
            "SELECT candidate_id FROM candidates WHERE origin_research_id = ? ORDER BY candidate_id ASC LIMIT 1",
            (clean_id,),
        ).fetchone()
        if cand:
            candidate_id = cand["candidate_id"]

    if not candidate_id:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.SOLUTION_STRATEGY,
            current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            reason="Missing required candidate identifier (e.g. CAND-001).",
            required_fix="Specify a CAND-ID (e.g. --stage solution-strategy CAND-001).",
        )

    cand_row = conn.execute(
        "SELECT candidate_id, validation_status, lifecycle_status FROM candidates WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    if not cand_row:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.SOLUTION_STRATEGY,
            current_stage=WorkflowStage.PROBLEM_EVALUATION,
            reason=f"Candidate '{candidate_id}' does not exist in SQLite database.",
            required_fix="Execute problem evaluation first.",
        )

    experiments = conn.execute(
        "SELECT experiment_id, outcome_verdict FROM experiments WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchall()

    if not experiments:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.SOLUTION_STRATEGY,
            current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            reason=f"Candidate '{candidate_id}' has 0 experiments. Empirical validation is required.",
            required_fix=f"Execute 'experiment-validation {candidate_id}' to design and test an experiment first.",
        )

    pending = [e["experiment_id"] for e in experiments if e["outcome_verdict"] in ("PREREGISTERED", "INCOMPLETE")]
    if pending:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.SOLUTION_STRATEGY,
            current_stage=WorkflowStage.PAUSED,
            reason=(
                f"Candidate '{candidate_id}' has {len(pending)} pending experiment(s) ({', '.join(pending)}). "
                "Solution strategy strictly requires empirical validation completion."
            ),
            required_fix="Complete real-world trials and submit experiment observations first.",
            diagnostics={"pending_experiments": pending},
        )

    evaluated = [
        e for e in experiments
        if e["outcome_verdict"] in ("PASSED", "FAILED", "VALIDATED", "REFUTED", "INCONCLUSIVE")
    ]
    if not evaluated:
        return StagePreconditionResult(
            allowed=False,
            target_stage=WorkflowStage.SOLUTION_STRATEGY,
            current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            reason=f"Candidate '{candidate_id}' has no evaluated experiments with a valid outcome.",
            required_fix="Assess experiment trial results first.",
        )

    return StagePreconditionResult(
        allowed=True,
        target_stage=WorkflowStage.SOLUTION_STRATEGY,
        current_stage=WorkflowStage.SOLUTION_STRATEGY,
        reason=f"Candidate '{candidate_id}' has {len(evaluated)} evaluated experiment(s). Ready for solution strategy.",
        diagnostics={"evaluated_experiments": len(evaluated)},
    )


def validate_stage_preconditions(
    target_stage: WorkflowStage,
    identifier: Optional[str] = None,
    prompt: Optional[str] = None,
    db_path: Optional[str] = None,
) -> StagePreconditionResult:
    """Evaluate whether a target workflow stage satisfies all entry preconditions.

    @param target_stage - Desired WorkflowStage to execute.
    @param identifier - Optional entity identifier (RUN-xxx, CAND-xxx, EXP-xxx).
    @param prompt - Optional prompt or user submission text.
    @param db_path - Optional SQLite database path.
    @returns StagePreconditionResult detailing whether execution is permitted.
    """
    conn = _get_connection(db_path)
    try:
        if target_stage == WorkflowStage.RESEARCH_PLANNING:
            return _check_planning_preconditions(conn, identifier, prompt)
        elif target_stage == WorkflowStage.EVIDENCE_RESEARCH:
            return _check_evidence_preconditions(conn, identifier)
        elif target_stage == WorkflowStage.PROBLEM_EVALUATION:
            return _check_evaluation_preconditions(conn, identifier)
        elif target_stage == WorkflowStage.EXPERIMENT_VALIDATION:
            return _check_experiment_preconditions(conn, identifier, prompt)
        elif target_stage == WorkflowStage.SOLUTION_STRATEGY:
            return _check_solution_preconditions(conn, identifier)
        else:
            return StagePreconditionResult(
                allowed=True,
                target_stage=target_stage,
                reason="Read-only or terminal stage; no mutation preconditions.",
            )
    finally:
        conn.close()


def verify_stage_postconditions(
    stage: WorkflowStage,
    identifier: Optional[str] = None,
    db_path: Optional[str] = None,
) -> StageVerificationResult:
    """Verify that a stage successfully mutated and persisted valid SQLite state.

    @param stage - Executed WorkflowStage.
    @param identifier - Entity identifier (RUN-xxx or CAND-xxx).
    @param db_path - Optional SQLite database path.
    @returns StageVerificationResult.
    """
    conn = _get_connection(db_path)
    clean_id = (identifier or "").strip().upper()
    try:
        if stage == WorkflowStage.RESEARCH_PLANNING:
            row = conn.execute(
                "SELECT research_id, plan_json FROM research_runs WHERE research_id = ?",
                (clean_id,),
            ).fetchone()
            if not row or not row["plan_json"]:
                return StageVerificationResult(
                    verified=False,
                    stage=stage,
                    message=f"Research run '{clean_id}' was not persisted with a valid plan_json.",
                )
            return StageVerificationResult(
                verified=True,
                stage=stage,
                message=f"Research plan for '{clean_id}' successfully verified in SQLite.",
                persisted_records={"research_id": clean_id},
            )

        if stage == WorkflowStage.EVIDENCE_RESEARCH:
            count = conn.execute(
                "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ?",
                (clean_id,),
            ).fetchone()["cnt"]
            if count == 0:
                return StageVerificationResult(
                    verified=False,
                    stage=stage,
                    message=f"No evidence signals were persisted for '{clean_id}'.",
                )
            assessed = conn.execute(
                "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ? AND evidence_level IN ('L1','L2','L3','L4')",
                (clean_id,),
            ).fetchone()["cnt"]
            warnings = []
            if assessed == 0:
                warnings.append(
                    "All persisted signals are UNASSESSED. Signals need authentic source qualification."
                )
            return StageVerificationResult(
                verified=True,
                stage=stage,
                message=f"Successfully verified {count} signal(s) ({assessed} qualified) for '{clean_id}'.",
                warnings=warnings,
                persisted_records={"total_signals": count, "qualified_signals": assessed},
            )

        if stage == WorkflowStage.PROBLEM_EVALUATION:
            cands = conn.execute(
                "SELECT candidate_id, title, research_score FROM candidates WHERE origin_research_id = ?",
                (clean_id,),
            ).fetchall()
            if not cands:
                return StageVerificationResult(
                    verified=False,
                    stage=stage,
                    message=f"No problem candidates were persisted for research run '{clean_id}'.",
                )
            return StageVerificationResult(
                verified=True,
                stage=stage,
                message=f"Successfully verified {len(cands)} candidate(s) for '{clean_id}'.",
                persisted_records={"candidates": [dict(c) for c in cands]},
            )

        return StageVerificationResult(
            verified=True,
            stage=stage,
            message=f"Stage {stage.value} verification passed.",
        )
    finally:
        conn.close()
