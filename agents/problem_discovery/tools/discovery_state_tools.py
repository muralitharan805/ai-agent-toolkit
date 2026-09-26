"""Custom Python tools wrapping discovery-state SQLite repository for Antigravity Agent."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable, Dict, List, Optional
from agents.problem_discovery.config import get_default_db_path, get_discovery_db_class, get_build_agent_context_module
from agents.problem_discovery.orchestration.models import ExperimentContractValidation


class DiscoveryStateTools:
    """Tool provider wrapping canonical DiscoveryDB and context pack builders."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or get_default_db_path())
        db_cls = get_discovery_db_class()
        self.db = db_cls(db_path=self.db_path)
        self.context_builder = get_build_agent_context_module()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # Read-Only Tools
    # =========================================================================

    def get_discovery_run(self, research_id: str) -> Dict[str, Any]:
        """Retrieve complete details for a research run by its sequential identifier.

        Args:
            research_id: The research run identifier (e.g. 'RUN-2026-001').

        Returns:
            Dictionary containing run record, plan, current stage, and status.
        """
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT research_id, original_request, domain, scope_type,
                       geography, current_stage, status, plan_json, created_at, updated_at
                FROM research_runs WHERE research_id = ?
                """,
                (research_id.strip().upper(),),
            ).fetchone()
            if not row:
                return {"found": False, "error": f"Research run '{research_id}' not found"}

            plan = {}
            if row["plan_json"]:
                try:
                    plan = json.loads(row["plan_json"])
                except Exception:
                    plan = {}

            return {
                "found": True,
                "research_id": row["research_id"],
                "original_request": row["original_request"],
                "domain": row["domain"],
                "scope_type": row["scope_type"],
                "geography": row["geography"],
                "current_stage": row["current_stage"],
                "status": row["status"],
                "plan": plan,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        finally:
            conn.close()

    def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Retrieve candidate record, evaluation details, solution, and related experiments.

        Args:
            candidate_id: Unique candidate problem identifier (e.g. 'CAND-001').

        Returns:
            Dictionary containing candidate metadata, scores, evaluation, and experiment history.
        """
        conn = self._get_connection()
        try:
            cand = conn.execute(
                """
                SELECT candidate_id, origin_research_id, title, domain, target_operator,
                       track, research_score, evidence_level, validation_status,
                       lifecycle_status, solution_class, evaluation_json, solution_json,
                       created_at, updated_at
                FROM candidates WHERE candidate_id = ?
                """,
                (candidate_id.strip().upper(),),
            ).fetchone()
            if not cand:
                return {"found": False, "error": f"Candidate '{candidate_id}' not found"}

            eval_dict = {}
            if cand["evaluation_json"]:
                try:
                    eval_dict = json.loads(cand["evaluation_json"])
                except Exception:
                    pass

            solution_dict = {}
            if cand["solution_json"]:
                try:
                    solution_dict = json.loads(cand["solution_json"])
                except Exception:
                    pass

            experiments = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT experiment_id, hypothesis, metric_name, target_threshold,
                           direction, sample_target, sample_achieved, observed_value,
                           outcome_verdict, artifact_hash, audited_by, audit_date, created_at
                    FROM experiments WHERE candidate_id = ?
                    ORDER BY created_at DESC, experiment_id DESC
                    """,
                    (cand["candidate_id"],),
                ).fetchall()
            ]

            signals_count = conn.execute(
                "SELECT COUNT(*) as count FROM evidence_signals WHERE candidate_id = ?",
                (cand["candidate_id"],),
            ).fetchone()["count"]

            return {
                "found": True,
                "candidate_id": cand["candidate_id"],
                "origin_research_id": cand["origin_research_id"],
                "title": cand["title"],
                "domain": cand["domain"],
                "target_operator": cand["target_operator"],
                "track": cand["track"],
                "research_score": cand["research_score"],
                "evidence_level": cand["evidence_level"],
                "validation_status": cand["validation_status"],
                "lifecycle_status": cand["lifecycle_status"],
                "solution_class": cand["solution_class"],
                "evaluation": eval_dict,
                "solution": solution_dict,
                "evidence_count": signals_count,
                "experiments": experiments,
                "created_at": cand["created_at"],
                "updated_at": cand["updated_at"],
            }
        finally:
            conn.close()

    def search_discovery(self, query: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search discovery artifacts across candidates, signals, and runs using Full-Text Search.

        Args:
            query: Search query text.
            entity_type: Optional filter ('CANDIDATE', 'SIGNAL', 'RUN').

        Returns:
            List of matching records with entity_id, entity_type, title_or_issue, and body_text.
        """
        import re

        clean_tokens = [re.sub(r"[^\w]", "", token) for token in query.split()]
        clean_tokens = [t for t in clean_tokens if len(t) > 2]
        if not clean_tokens:
            return []
        fts_query = " OR ".join(f'"{t}"' for t in clean_tokens[:8])
        try:
            return self.db.search_fts(query=fts_query, entity_type=entity_type)
        except Exception:
            return []

    def build_discovery_query_context(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Build a bounded, read-only discovery context pack answering a user status/state query.

        Args:
            query: The user's natural language query or entity identifier.
            limit: Maximum candidate matches to assemble.

        Returns:
            Context dictionary with candidate summaries, recent experiments, and direct hits.
        """
        conn = self._get_connection()
        try:
            return self.context_builder.build_discovery_query_context(conn=conn, query=query, limit=limit)
        finally:
            conn.close()

    def build_problem_evaluation_context(self, research_id: str) -> Dict[str, Any]:
        """Build the bounded context pack for the Problem Evaluation reasoning capability.

        Args:
            research_id: The research run identifier.

        Returns:
            Context dictionary containing research plan, unassigned signals, and existing candidate matches.
        """
        conn = self._get_connection()
        try:
            return self.context_builder.build_problem_evaluation_context(conn=conn, research_id=research_id)
        finally:
            conn.close()

    def build_experiment_context(
        self, candidate_id: str, mode: str = "DESIGN", experiment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build the bounded context pack for Experiment Validation (DESIGN or ASSESS mode).

        Args:
            candidate_id: Candidate identifier.
            mode: 'DESIGN' to prepare a contract, or 'ASSESS' to audit real-world trial outcomes.
            experiment_id: Required when mode is 'ASSESS'.

        Returns:
            Context dictionary with candidate metrics, locked contract, and validation boundaries.
        """
        conn = self._get_connection()
        try:
            return self.context_builder.build_experiment_validation_context(
                conn=conn, candidate_id=candidate_id, mode=mode, experiment_id=experiment_id
            )
        finally:
            conn.close()

    def build_solution_context(self, candidate_id: str) -> Dict[str, Any]:
        """Build the bounded context pack for the Solution Strategy reasoning capability.

        Args:
            candidate_id: Candidate identifier.

        Returns:
            Context dictionary with validation scope, constraints, and candidate readiness.
        """
        conn = self._get_connection()
        try:
            return self.context_builder.build_solution_strategy_context(conn=conn, candidate_id=candidate_id)
        finally:
            conn.close()

    def get_discovery_dashboard(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve aggregated candidate lifecycle metrics from the v_discovery_dashboard view.

        Args:
            status_filter: Optional lifecycle status filter (e.g. 'ACTIVE', 'PILOT_READY').

        Returns:
            List of candidate dashboard summary dictionaries.
        """
        return self.db.get_discovery_dashboard(status_filter=status_filter)

    def get_next_workflow_action(self, identifier: str) -> Dict[str, Any]:
        """Inspect persistent SQLite discovery state and determine the next deterministic action.

        Args:
            identifier: Either a research_id ('RUN-2026-001') or a candidate_id ('CAND-001').

        Returns:
            Dictionary specifying current_stage, next_action, pause_reason if paused, and rationale.
        """
        from agents.problem_discovery.orchestration.state_machine import DiscoveryStateMachine
        sm = DiscoveryStateMachine(db_path=self.db_path)
        return sm.evaluate_next_action(identifier).model_dump()

    # =========================================================================
    # Mutation Tools (All route exclusively through DiscoveryDB methods)
    # =========================================================================

    def create_research_run(
        self,
        research_id: str,
        prompt: Optional[str] = None,
        plan_dict: Optional[Dict[str, Any]] = None,
        request: Optional[str] = None,
        domain: Optional[str] = None,
        scope_type: str = "BROAD",
        geography: Optional[str] = None,
    ) -> str:
        """Initialize a new research run in SQLite with a validated ResearchPlan.

        Args:
            research_id: Sequential identifier (e.g. 'RUN-2026-001').
            prompt: Verbatim original user request (alias for request).
            plan_dict: Structured ResearchPlan dictionary adhering to research-plan.schema.json.
            request: Verbatim original user request.
            domain: Problem domain (e.g. 'ecommerce').
            scope_type: Scope classification ('BROAD', 'NARROW', etc.).
            geography: Target geography or None.

        Returns:
            Created research_id token.
        """
        plan = plan_dict or {}
        req = request or prompt or plan.get("original_request") or ""
        dom = domain or plan.get("scope", {}).get("domain") or plan.get("domain") or "general"
        scope = plan.get("scope", {}).get("scope_type") or scope_type or "BROAD"
        geo = geography or plan.get("scope", {}).get("geography")
        return self.db.create_research_run(
            research_id=research_id,
            request=req,
            domain=dom,
            scope_type=scope,
            geography=geo,
            plan_dict=plan,
        )

    def save_evidence_signals(self, research_id: str, signals: List[Dict[str, Any]]) -> int:
        """Batch persist qualified evidence signals into evidence_signals table.

        Args:
            research_id: Parent research run ID.
            signals: List of normalized ResearchSignal dictionaries.

        Returns:
            Count of signals successfully persisted.
        """
        return self.db.save_evidence_signals(research_id=research_id, signals=signals)

    def upsert_candidate(
        self,
        candidate_id: str,
        research_id: Optional[str] = None,
        title: Optional[str] = None,
        domain: Optional[str] = None,
        origin_research_id: Optional[str] = None,
        problem_statement: Optional[str] = None,
        evaluation_dict: Optional[Dict[str, Any]] = None,
        signal_ids: Optional[List[str]] = None,
        supporting_signal_ids: Optional[List[str]] = None,
        target_operator: Optional[str] = None,
        track: str = "COMMERCIAL",
        lifecycle_status: str = "ACTIVE",
    ) -> str:
        """Persist or update a problem candidate, recomputing evidence gates and linking signals.

        Args:
            candidate_id: Unique candidate ID (e.g. 'CAND-001').
            research_id: Originating research run ID (or origin_research_id).
            title: Candidate title or problem statement.
            domain: Domain name. If omitted, looked up from research_runs.
            origin_research_id: Alias for research_id.
            problem_statement: Alias for title.
            evaluation_dict: Problem evaluation dictionary including dimension scores.
            signal_ids: List of signal IDs supporting this candidate.
            supporting_signal_ids: Alias for signal_ids.
            target_operator: Target operational role.
            track: Track type ('COMMERCIAL', etc.).
            lifecycle_status: Initial candidate lifecycle status.

        Returns:
            Candidate ID token.
        """
        rid = research_id or origin_research_id or ""
        t = title or problem_statement or "Candidate Problem"
        d = domain
        if not d and rid:
            conn = self._get_connection()
            try:
                row = conn.execute("SELECT domain FROM research_runs WHERE research_id=?", (rid,)).fetchone()
                if row:
                    d = row["domain"]
            finally:
                conn.close()
        if not d:
            d = "general"

        s_ids = supporting_signal_ids if supporting_signal_ids is not None else (signal_ids or [])

        return self.db.upsert_candidate(
            candidate_id=candidate_id,
            research_id=rid,
            title=t,
            domain=d,
            target_operator=target_operator,
            track=track,
            lifecycle_status=lifecycle_status,
            evaluation_dict=evaluation_dict,
            supporting_signal_ids=s_ids,
        )

    def preregister_experiment(
        self, experiment_id: str, candidate_id: str, contract_dict: Dict[str, Any]
    ) -> str:
        """Preregister an immutable empirical experiment contract for a candidate.

        Enforces atomic primary metric rules: compound metrics (e.g. metric1_or_metric2)
        are strictly prohibited and will raise ValueError.

        Args:
            experiment_id: Unique experiment ID (e.g. 'EXP-001').
            candidate_id: Target candidate ID.
            contract_dict: Immutable ExperimentContract dictionary.

        Returns:
            Experiment ID token.
        """
        # Validate atomic metric
        metric_name = (
            contract_dict.get("metric_name")
            or contract_dict.get("metric")
            or (contract_dict.get("contract", {}).get("metric_name"))
            or ""
        )
        threshold = (
            contract_dict.get("target_threshold")
            or contract_dict.get("threshold")
            or (contract_dict.get("contract", {}).get("target_threshold"))
            or 0.0
        )
        sample_target = (
            contract_dict.get("sample_target")
            or (contract_dict.get("contract", {}).get("sample_target"))
            or 5
        )
        aggregation_rule = (
            contract_dict.get("aggregation_rule")
            or (contract_dict.get("contract", {}).get("aggregation_rule"))
            or "MEAN_PER_PARTICIPANT"
        )

        ExperimentContractValidation(
            metric_name=metric_name,
            target_threshold=float(threshold),
            direction=contract_dict.get("direction", ">="),
            sample_target=int(sample_target),
            aggregation_rule=aggregation_rule,
        )

        contract_copy = dict(contract_dict)
        if not contract_copy.get("hypothesis"):
            contract_copy["hypothesis"] = f"Empirical validation hypothesis for candidate {candidate_id}."
        if "success_threshold" not in contract_copy:
            contract_copy["success_threshold"] = {
                "value": float(threshold),
                "operator": contract_dict.get("direction", ">="),
            }
        if "sample" not in contract_copy:
            contract_copy["sample"] = {
                "target": int(sample_target),
                "minimum_usable": int(contract_dict.get("minimum_usable", sample_target)),
            }
        if "artifact_requirements" not in contract_copy:
            contract_copy["artifact_requirements"] = {
                "required": True,
                "format": "CSV",
            }
        if "review_requirements" not in contract_copy:
            contract_copy["review_requirements"] = {
                "human_review_required": True,
            }

        return self.db.preregister_experiment(
            experiment_id=experiment_id, candidate_id=candidate_id, contract_dict=contract_copy
        )

    def record_experiment_assessment(
        self,
        experiment_id: str,
        result_dict: Optional[Dict[str, Any]] = None,
        assessment_dict: Optional[Dict[str, Any]] = None,
        artifact_hash: Optional[str] = None,
        audited_by: Optional[str] = None,
        audit_date: Optional[str] = None,
    ) -> str:
        """Audit and record empirical experiment results against the locked contract in SQLite.

        Args:
            experiment_id: Target experiment identifier.
            result_dict: Audited ValidationAssessment dictionary (or alias for assessment_dict).
            assessment_dict: Structured assessment dictionary adhering to validation-assessment.schema.json.
            artifact_hash: SHA-256 evidence digest.
            audited_by: Named human reviewer.
            audit_date: Audit date string (YYYY-MM-DD).

        Returns:
            Experiment outcome verdict string ('PASSED', 'FAILED', 'INCOMPLETE', 'INVALID').
        """
        data = dict(assessment_dict or result_dict or {})
        raw_status = data.get("status") or data.get("outcome_verdict") or "EXPERIMENT_PASSED"

        # Normalize status to DiscoveryDB expected values
        status_norm_map = {
            "PASSED": "EXPERIMENT_PASSED",
            "FAILED": "EXPERIMENT_FAILED",
            "INCOMPLETE": "INCOMPLETE",
            "INVALID": "INVALID_EXPERIMENT",
            "INVALID_EXPERIMENT": "INVALID_EXPERIMENT",
            "EXPERIMENT_PASSED": "EXPERIMENT_PASSED",
            "EXPERIMENT_FAILED": "EXPERIMENT_FAILED",
        }
        data["status"] = status_norm_map.get(raw_status.upper(), raw_status)

        a_hash = artifact_hash or data.get("artifact_hash")
        auditor = audited_by or data.get("audited_by")
        a_date = audit_date or data.get("audit_date")

        if "observed_result" not in data:
            data["observed_result"] = {
                "sample_achieved": data.get("sample_achieved"),
                "observed_value": data.get("observed_value"),
            }
        if "artifact_review" not in data:
            data["artifact_review"] = {
                "sha256": a_hash,
                "audited_by": auditor,
                "audit_date": a_date,
            }

        return self.db.record_experiment_assessment(
            experiment_id=experiment_id,
            assessment_dict=data,
            artifact_hash=a_hash,
            audited_by=auditor,
            audit_date=a_date,
        )

    def finalize_solution(
        self, candidate_id: str, solution_class: str, solution_dict: Dict[str, Any]
    ) -> str:
        """Finalize the smallest justified solution shape for a validated candidate.

        Guards:
            Blocks finalization if any unfinished (PREREGISTERED or INCOMPLETE) experiments exist.

        Args:
            candidate_id: Candidate ID.
            solution_class: Selected class (e.g. 'PROCESS_SOP', 'BROWSER_EXTENSION', 'API').
            solution_dict: Solution specification dictionary.

        Returns:
            Resulting candidate lifecycle status ('SOLUTION_PROPOSED' or 'PILOT_READY').
        """
        # Guard: Check for unfinished experiments
        conn = self._get_connection()
        try:
            blocking = conn.execute(
                """
                SELECT experiment_id, outcome_verdict FROM experiments
                WHERE candidate_id = ? AND outcome_verdict IN ('PREREGISTERED', 'INCOMPLETE')
                """,
                (candidate_id.strip().upper(),),
            ).fetchall()
            if blocking:
                block_ids = [f"{b['experiment_id']} ({b['outcome_verdict']})" for b in blocking]
                raise ValueError(
                    f"Solution finalization blocked for candidate '{candidate_id}'. "
                    f"Unfinished experiments exist: {', '.join(block_ids)}. "
                    f"Audit or resolve experiments before finalizing solution."
                )
        finally:
            conn.close()

        return self.db.finalize_solution(
            candidate_id=candidate_id, solution_class=solution_class, solution_dict=solution_dict
        )

    def get_read_tools(self) -> List[Callable[..., Any]]:
        """Return all read-only tool functions."""
        return [
            self.get_discovery_run,
            self.get_candidate,
            self.search_discovery,
            self.build_discovery_query_context,
            self.build_problem_evaluation_context,
            self.build_experiment_context,
            self.build_solution_context,
            self.get_discovery_dashboard,
            self.get_next_workflow_action,
        ]

    def get_write_tools(self) -> List[Callable[..., Any]]:
        """Return all state mutation tool functions."""
        return [
            self.create_research_run,
            self.save_evidence_signals,
            self.upsert_candidate,
            self.preregister_experiment,
            self.record_experiment_assessment,
            self.finalize_solution,
        ]

    def get_all_tools(self) -> List[Callable[..., Any]]:
        """Return all registered discovery tools."""
        return self.get_read_tools() + self.get_write_tools()
