"""Deterministic workflow state machine for the Problem Discovery lifecycle."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from agents.problem_discovery.config import get_default_db_path, get_discovery_db_class
from agents.problem_discovery.orchestration.models import (
    IntentType,
    OrchestrationResult,
    PauseReason,
    WorkflowStage,
    WorkflowStatus,
)


class DiscoveryStateMachine:
    """State machine governing discovery gates, stage transitions, and pause/resume."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or get_default_db_path())
        db_cls = get_discovery_db_class()
        self.db = db_cls(db_path=self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def evaluate_next_action(self, identifier: str) -> OrchestrationResult:
        """Inspect persistent SQLite state and determine the next justified workflow action."""
        clean_id = identifier.strip().upper()

        if clean_id.startswith("RUN-"):
            return self._evaluate_run_state(clean_id)
        elif clean_id.startswith("CAND-"):
            return self._evaluate_candidate_state(clean_id)
        else:
            return OrchestrationResult(
                intent=IntentType.RESUME_RUN,
                research_id=clean_id,
                current_stage=WorkflowStage.RESEARCH_PLANNING,
                action_taken="Unrecognized identifier format. Expected RUN-YYYY-NNN or CAND-NNN.",
                workflow_status=WorkflowStatus.ERROR,
                message=f"Invalid identifier format '{identifier}'.",
            )

    def _evaluate_run_state(self, research_id: str) -> OrchestrationResult:
        """Evaluate workflow state for a research run."""
        conn = self._get_connection()
        try:
            run = conn.execute(
                """
                SELECT research_id, original_request, domain, scope_type,
                       geography, current_stage, status, plan_json
                FROM research_runs WHERE research_id = ?
                """,
                (research_id,),
            ).fetchone()

            if not run:
                return OrchestrationResult(
                    intent=IntentType.RESUME_RUN,
                    research_id=research_id,
                    current_stage=WorkflowStage.RESEARCH_PLANNING,
                    action_taken="Run not found in SQLite. Initializing research planning.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="RUN_RESEARCH_PLANNING",
                    message=f"Research run '{research_id}' does not exist yet. Ready for planning.",
                )

            # Check evidence signals
            signals_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ?",
                (research_id,),
            ).fetchone()["cnt"]

            if signals_count == 0:
                return OrchestrationResult(
                    intent=IntentType.RESUME_RUN,
                    research_id=research_id,
                    current_stage=WorkflowStage.EVIDENCE_RESEARCH,
                    action_taken="Persisted run has zero evidence signals.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="RUN_EVIDENCE_RESEARCH",
                    message=(
                        f"Research run '{research_id}' is planned but has no evidence signals. "
                        "Next action: execute evidence research collection."
                    ),
                    data={"domain": run["domain"], "scope_type": run["scope_type"]},
                )

            # Check for unassigned signals needing clustering/evaluation
            unassigned_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM evidence_signals WHERE research_id = ? AND candidate_id IS NULL",
                (research_id,),
            ).fetchone()["cnt"]

            candidates = conn.execute(
                """
                SELECT candidate_id, title, validation_status, lifecycle_status,
                       research_score, evidence_level, solution_class
                FROM candidates WHERE origin_research_id = ?
                ORDER BY candidate_id ASC
                """,
                (research_id,),
            ).fetchall()

            if unassigned_count > 0 and len(candidates) == 0:
                return OrchestrationResult(
                    intent=IntentType.RESUME_RUN,
                    research_id=research_id,
                    current_stage=WorkflowStage.PROBLEM_EVALUATION,
                    action_taken=f"{unassigned_count} unassigned evidence signals collected.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="RUN_PROBLEM_EVALUATION",
                    message=(
                        f"Research run '{research_id}' has {unassigned_count} signals awaiting evaluation. "
                        "Next action: evaluate signals, map 14-node workflow, and cluster candidates."
                    ),
                    data={"unassigned_signals": unassigned_count},
                )

            if not candidates:
                return OrchestrationResult(
                    intent=IntentType.RESUME_RUN,
                    research_id=research_id,
                    current_stage=WorkflowStage.PROBLEM_EVALUATION,
                    action_taken="No candidates linked to research run.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="RUN_PROBLEM_EVALUATION",
                    message="Next action: cluster signals into problem candidates.",
                )

            # Evaluate each candidate associated with the run
            # Prioritize paused experiments or candidates needing action
            for cand in candidates:
                cid = cand["candidate_id"]
                cand_res = self._evaluate_candidate_state(cid)
                if cand_res.workflow_status == WorkflowStatus.PAUSED:
                    # Propagate pause with parent research_id attached
                    cand_res.research_id = research_id
                    return cand_res
                if cand_res.current_stage in (
                    WorkflowStage.EXPERIMENT_VALIDATION,
                    WorkflowStage.SOLUTION_STRATEGY,
                ) and cand_res.workflow_status == WorkflowStatus.CONTINUED:
                    cand_res.research_id = research_id
                    return cand_res

            # Check aggregate run completion across all candidates
            refreshed = self.db.refresh_research_run_state(research_id)
            if refreshed.get("run_status") == "COMPLETED":
                return OrchestrationResult(
                    intent=IntentType.RESUME_RUN,
                    research_id=research_id,
                    current_stage=WorkflowStage.COMPLETED,
                    action_taken="All associated candidates have reached terminal lifecycle status.",
                    workflow_status=WorkflowStatus.COMPLETED,
                    next_action="NONE",
                    message=f"Research run '{research_id}' is fully COMPLETED across all candidates.",
                    data=refreshed,
                )

            return OrchestrationResult(
                intent=IntentType.RESUME_RUN,
                research_id=research_id,
                current_stage=WorkflowStage.PROBLEM_EVALUATION,
                action_taken="Run active with multiple candidates in progress.",
                workflow_status=WorkflowStatus.CONTINUED,
                next_action="REVIEW_CANDIDATES",
                message=f"Research run '{research_id}' is ACTIVE. Candidates in progress.",
                data={"candidates": [dict(c) for c in candidates]},
            )

        finally:
            conn.close()

    def _evaluate_candidate_state(self, candidate_id: str) -> OrchestrationResult:
        """Evaluate workflow state for a specific problem candidate."""
        conn = self._get_connection()
        try:
            cand = conn.execute(
                """
                SELECT candidate_id, origin_research_id, title, domain, target_operator,
                       track, research_score, evidence_level, validation_status,
                       lifecycle_status, solution_class, evaluation_json, solution_json
                FROM candidates WHERE candidate_id = ?
                """,
                (candidate_id,),
            ).fetchone()

            if not cand:
                return OrchestrationResult(
                    intent=IntentType.RESUME_CANDIDATE,
                    candidate_id=candidate_id,
                    current_stage=WorkflowStage.PROBLEM_EVALUATION,
                    action_taken="Candidate not found in SQLite.",
                    workflow_status=WorkflowStatus.ERROR,
                    message=f"Candidate '{candidate_id}' does not exist in discovery database.",
                )

            origin_run = cand["origin_research_id"]

            # Terminal lifecycle check
            if cand["lifecycle_status"] in ("PILOT_READY", "PARKED", "ARCHIVED", "BUILT"):
                return OrchestrationResult(
                    intent=IntentType.RESUME_CANDIDATE,
                    research_id=origin_run,
                    candidate_id=candidate_id,
                    current_stage=WorkflowStage.COMPLETED,
                    action_taken=f"Candidate has reached terminal status {cand['lifecycle_status']}.",
                    workflow_status=WorkflowStatus.COMPLETED,
                    next_action="NONE",
                    message=(
                        f"Candidate '{candidate_id}' discovery is complete. "
                        f"Lifecycle: {cand['lifecycle_status']}, Solution Class: {cand['solution_class']}."
                    ),
                    data=dict(cand),
                )

            # Check existing experiments
            experiments = conn.execute(
                """
                SELECT experiment_id, hypothesis, metric_name, target_threshold,
                       direction, sample_target, sample_achieved, observed_value,
                       outcome_verdict, contract_json, audited_by, audit_date
                FROM experiments WHERE candidate_id = ?
                ORDER BY created_at DESC, experiment_id DESC
                """,
                (candidate_id,),
            ).fetchall()

            if not experiments:
                # No experiments designed yet: candidate needs experiment design
                return OrchestrationResult(
                    intent=IntentType.RESUME_CANDIDATE,
                    research_id=origin_run,
                    candidate_id=candidate_id,
                    current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                    action_taken="Candidate evaluated but no empirical experiment designed.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="DESIGN_EXPERIMENT_CONTRACT",
                    message=(
                        f"Candidate '{candidate_id}' ({cand['title']}) requires empirical validation. "
                        "Next action: design an immutable ExperimentContract (DESIGN mode)."
                    ),
                    data={"research_score": cand["research_score"], "evidence_level": cand["evidence_level"]},
                )

            # Check active / latest experiment states
            # Invariant: PREREGISTERED pauses workflow and requires real-world trial execution
            for exp in experiments:
                verdict = exp["outcome_verdict"]
                eid = exp["experiment_id"]
                contract = {}
                if exp["contract_json"]:
                    try:
                        contract = json.loads(exp["contract_json"])
                    except Exception:
                        pass

                if verdict == "PREREGISTERED":
                    req_sample = exp["sample_target"]
                    metric = exp["metric_name"]
                    agg_rule = contract.get("aggregation_rule", "MEAN_PER_PARTICIPANT")
                    return OrchestrationResult(
                        intent=IntentType.RESUME_CANDIDATE,
                        research_id=origin_run,
                        candidate_id=candidate_id,
                        experiment_id=eid,
                        current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                        action_taken=f"Experiment '{eid}' is PREREGISTERED. Real-world observation required.",
                        workflow_status=WorkflowStatus.PAUSED,
                        pause_reason=PauseReason.WAITING_FOR_REAL_WORLD_EXPERIMENT.value,
                        next_action="AWAIT_REAL_WORLD_TRIAL_DATA",
                        message=(
                            f"Workflow paused.\n\n"
                            f"research_id: {origin_run}\n"
                            f"candidate_id: {candidate_id}\n"
                            f"experiment_id: {eid}\n"
                            f"reason: WAITING_FOR_REAL_WORLD_EXPERIMENT\n\n"
                            f"Required result:\n"
                            f"- minimum usable sample: {req_sample}\n"
                            f"- metric: {metric}\n"
                            f"- aggregation rule: {agg_rule}\n"
                            f"- artifact: CSV observation log\n"
                            f"- named human reviewer\n"
                            f"- review date\n"
                            f"- SHA-256 integrity hash\n\n"
                            f"Please conduct the trial and provide observed participant data to proceed."
                        ),
                        data={
                            "experiment_id": eid,
                            "metric_name": metric,
                            "sample_target": req_sample,
                            "target_threshold": exp["target_threshold"],
                            "direction": exp["direction"],
                            "aggregation_rule": agg_rule,
                        },
                    )

                if verdict == "INCOMPLETE":
                    return OrchestrationResult(
                        intent=IntentType.RESUME_CANDIDATE,
                        research_id=origin_run,
                        candidate_id=candidate_id,
                        experiment_id=eid,
                        current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                        action_taken=f"Experiment '{eid}' was marked INCOMPLETE.",
                        workflow_status=WorkflowStatus.PAUSED,
                        pause_reason=PauseReason.INCOMPLETE_EXPERIMENT.value,
                        next_action="COLLECT_REMAINING_PARTICIPANT_DATA",
                        message=(
                            f"Experiment '{eid}' is INCOMPLETE (usable sample size threshold not met). "
                            "Workflow paused awaiting additional participant data."
                        ),
                        data={"experiment_id": eid},
                    )

                if verdict == "INVALID":
                    return OrchestrationResult(
                        intent=IntentType.RESUME_CANDIDATE,
                        research_id=origin_run,
                        candidate_id=candidate_id,
                        experiment_id=eid,
                        current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                        action_taken=f"Experiment '{eid}' is INVALID due to integrity or audit failure.",
                        workflow_status=WorkflowStatus.PAUSED,
                        pause_reason=PauseReason.INVALID_EXPERIMENT_AUDIT.value,
                        next_action="RESOLVE_AUDIT_INTEGRITY_GAP",
                        message=(
                            f"Experiment '{eid}' is marked INVALID. "
                            "Integrity gap detected (e.g. missing hash or reviewer). "
                            "Cannot proceed to solution strategy without valid audited evidence."
                        ),
                        data={"experiment_id": eid},
                    )

            # Check if candidate has passed experiment and can proceed to solution strategy
            passed_exps = [e for e in experiments if e["outcome_verdict"] == "PASSED"]
            failed_exps = [e for e in experiments if e["outcome_verdict"] == "FAILED"]

            if passed_exps and not any(
                e["outcome_verdict"] in ("PREREGISTERED", "INCOMPLETE") for e in experiments
            ):
                if cand["solution_class"] and cand["lifecycle_status"] in (
                    "SOLUTION_PROPOSED",
                    "PILOT_READY",
                ):
                    return OrchestrationResult(
                        intent=IntentType.RESUME_CANDIDATE,
                        research_id=origin_run,
                        candidate_id=candidate_id,
                        current_stage=WorkflowStage.COMPLETED,
                        action_taken="Solution finalized and candidate ready.",
                        workflow_status=WorkflowStatus.COMPLETED,
                        next_action="NONE",
                        message=f"Candidate '{candidate_id}' has finalized solution {cand['solution_class']}.",
                        data=dict(cand),
                    )

                return OrchestrationResult(
                    intent=IntentType.RESUME_CANDIDATE,
                    research_id=origin_run,
                    candidate_id=candidate_id,
                    experiment_id=passed_exps[0]["experiment_id"],
                    current_stage=WorkflowStage.SOLUTION_STRATEGY,
                    action_taken="Experiment passed and candidate partially validated.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="RUN_SOLUTION_STRATEGY",
                    message=(
                        f"Candidate '{candidate_id}' passed experiment '{passed_exps[0]['experiment_id']}'. "
                        f"Validation status: {cand['validation_status']}. "
                        "Next action: evaluate smallest justified solution class (Principle of Least Complexity)."
                    ),
                    data={"passed_experiments": len(passed_exps)},
                )

            if failed_exps and not passed_exps:
                return OrchestrationResult(
                    intent=IntentType.RESUME_CANDIDATE,
                    research_id=origin_run,
                    candidate_id=candidate_id,
                    experiment_id=failed_exps[0]["experiment_id"],
                    current_stage=WorkflowStage.PROBLEM_EVALUATION,
                    action_taken=f"Experiment '{failed_exps[0]['experiment_id']}' FAILED.",
                    workflow_status=WorkflowStatus.CONTINUED,
                    next_action="REVIEW_HYPOTHESIS_OR_DESIGN_ALTERNATIVE",
                    message=(
                        f"Experiment '{failed_exps[0]['experiment_id']}' for candidate '{candidate_id}' failed. "
                        "Preserving negative knowledge. Route to hypothesis review, segment adjustment, "
                        "or alternative experiment."
                    ),
                    data={"failed_experiment_id": failed_exps[0]["experiment_id"]},
                )

            return OrchestrationResult(
                intent=IntentType.RESUME_CANDIDATE,
                research_id=origin_run,
                candidate_id=candidate_id,
                current_stage=WorkflowStage.PROBLEM_EVALUATION,
                action_taken="Candidate in progress.",
                workflow_status=WorkflowStatus.CONTINUED,
                next_action="REVIEW_EVALUATION",
                message=f"Candidate '{candidate_id}' requires evaluation review.",
            )

        finally:
            conn.close()

    def handle_experiment_result(
        self, experiment_id: str, assessment_dict: Dict[str, Any]
    ) -> OrchestrationResult:
        """Process real-world trial outcome assessment against a preregistered experiment contract."""
        conn = self._get_connection()
        try:
            exp = conn.execute(
                "SELECT experiment_id, candidate_id, outcome_verdict FROM experiments WHERE experiment_id = ?",
                (experiment_id.strip().upper(),),
            ).fetchone()
            if not exp:
                return OrchestrationResult(
                    intent=IntentType.EXPERIMENT_RESULT,
                    experiment_id=experiment_id,
                    current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                    action_taken="Experiment not found.",
                    workflow_status=WorkflowStatus.ERROR,
                    message=f"Experiment '{experiment_id}' does not exist in SQLite.",
                )

            cid = exp["candidate_id"]

            from agents.problem_discovery.tools.discovery_state_tools import DiscoveryStateTools

            tools = DiscoveryStateTools(db_path=self.db_path)
            try:
                verdict = tools.record_experiment_assessment(
                    experiment_id=experiment_id,
                    assessment_dict=assessment_dict,
                )
            except ValueError as exc:
                return OrchestrationResult(
                    intent=IntentType.EXPERIMENT_RESULT,
                    candidate_id=cid,
                    experiment_id=experiment_id,
                    current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
                    action_taken="Experiment assessment was not persisted.",
                    workflow_status=WorkflowStatus.PAUSED,
                    pause_reason=PauseReason.HUMAN_INPUT_REQUIRED.value,
                    next_action="PROVIDE_REQUIRED_EXPERIMENT_EVIDENCE",
                    message=str(exc),
                )

            next_action_res = self._evaluate_candidate_state(cid)
            next_action_res.intent = IntentType.EXPERIMENT_RESULT
            next_action_res.experiment_id = experiment_id
            next_action_res.action_taken = f"Recorded trial assessment: outcome verdict '{verdict}'."
            return next_action_res

        finally:
            conn.close()

    def handle_query(self, query: str, limit: int = 5) -> OrchestrationResult:
        """Handle read-only discovery queries with zero state mutations."""
        from agents.problem_discovery.orchestration.intents import extract_entities
        from agents.problem_discovery.tools.discovery_state_tools import DiscoveryStateTools

        tools = DiscoveryStateTools(db_path=self.db_path)
        rid, cid, eid = extract_entities(query)

        # Direct candidate status lookup
        if cid:
            cand_info = tools.get_candidate(cid)
            if cand_info.get("found"):
                exps = cand_info.get("experiments", [])
                latest_exp = exps[0]["outcome_verdict"] if exps else "NONE"
                msg = (
                    f"Candidate {cid}:\n"
                    f"- Title: {cand_info['title']}\n"
                    f"- Domain: {cand_info['domain']} | Track: {cand_info['track']}\n"
                    f"- Research Score: {cand_info['research_score']}/35 (Evidence Level: {cand_info['evidence_level']})\n"
                    f"- Lifecycle Status: {cand_info['lifecycle_status']}\n"
                    f"- Validation Status: {cand_info['validation_status']}\n"
                    f"- Evidence Signals: {cand_info['evidence_count']}\n"
                    f"- Latest Experiment: {latest_exp}"
                )
                if cand_info.get("solution_class"):
                    msg += f"\n- Solution Class: {cand_info['solution_class']}"
                return OrchestrationResult(
                    intent=IntentType.DISCOVERY_QUERY,
                    candidate_id=cid,
                    research_id=cand_info.get("origin_research_id"),
                    current_stage=WorkflowStage.READ_ONLY,
                    action_taken="Read-only candidate status lookup.",
                    workflow_status=WorkflowStatus.READ_ONLY,
                    next_action="NONE",
                    message=msg,
                    data=cand_info,
                )

        # Direct research run status lookup
        if rid:
            run_info = tools.get_discovery_run(rid)
            if run_info.get("found"):
                conn = self._get_connection()
                try:
                    cands = conn.execute(
                        "SELECT candidate_id, title, lifecycle_status, validation_status FROM candidates WHERE origin_research_id=?",
                        (rid,),
                    ).fetchall()
                    cand_summary = ""
                    if cands:
                        cand_summary = "\nAssociated Candidates:\n" + "\n".join(
                            f"- {c['candidate_id']}: {c['title']} ({c['lifecycle_status']})" for c in cands
                        )
                    else:
                        cand_summary = "\nAssociated Candidates: None linked yet."
                finally:
                    conn.close()

                return OrchestrationResult(
                    intent=IntentType.DISCOVERY_QUERY,
                    research_id=rid,
                    current_stage=WorkflowStage.READ_ONLY,
                    action_taken="Read-only research run status lookup.",
                    workflow_status=WorkflowStatus.READ_ONLY,
                    next_action="NONE",
                    message=(
                        f"Research Run {rid}:\n"
                        f"- Request: \"{run_info['original_request']}\"\n"
                        f"- Domain: {run_info['domain']} ({run_info['scope_type']})\n"
                        f"- Stage: {run_info['current_stage']}\n"
                        f"- Status: {run_info['status']}{cand_summary}"
                    ),
                    data=run_info,
                )

        ctx = tools.build_discovery_query_context(query=query, limit=limit)
        matches = ctx.get("matches", [])

        if not matches:
            fts = ctx.get("search_hits", [])
            msg = f"No candidates directly matched '{query}'."
            if fts:
                msg += f" Found {len(fts)} matching text records in discovery index."
        else:
            summaries = []
            for m in matches:
                c = m["candidate"]
                exps = m.get("recent_experiments", [])
                latest_exp = exps[0]["outcome_verdict"] if exps else "NONE"
                summaries.append(
                    f"- {c['candidate_id']}: {c['title']} | Score: {c['research_score']}/35 | "
                    f"Level: {c['evidence_level']} | Status: {c['lifecycle_status']} | "
                    f"Validation: {c['validation_status']} | Latest Exp: {latest_exp}"
                )
            msg = f"Discovery status for query '{query}':\n" + "\n".join(summaries)

        return OrchestrationResult(
            intent=IntentType.DISCOVERY_QUERY,
            current_stage=WorkflowStage.READ_ONLY,
            action_taken="Read-only query executed via build_discovery_query_context. Zero mutations.",
            workflow_status=WorkflowStatus.READ_ONLY,
            next_action="NONE",
            message=msg,
            data=ctx,
        )
