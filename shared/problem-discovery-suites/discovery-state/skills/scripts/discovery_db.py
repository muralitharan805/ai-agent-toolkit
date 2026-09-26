# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Canonical persistence client for the Problem Discovery suites.

All SQLite schema ownership and mutations flow through this module.
Reasoning suites emit structured contracts and delegate persistence here.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


DIMENSIONS = (
    "frequency",
    "severity",
    "workaround",
    "wtp",
    "decision_maker",
    "feasibility",
    "discrepancy",
)

EVIDENCE_RANK = {
    "UNASSESSED": 0,
    "L5": 1,
    "L4": 2,
    "L3": 3,
    "L2": 4,
    "L1": 5,
}

TERMINAL_CANDIDATE_STATES = {"PILOT_READY", "PARKED", "ARCHIVED", "BUILT"}


class DiscoveryDB:
    def __init__(self, db_path: str = "discovery.sqlite") -> None:
        self.db_path = db_path
        self._bootstrap()

    @property
    def _schema_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "discovery-db-schema.sql"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _bootstrap(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_connection()
        try:
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(candidates)").fetchall()]
            if cols and "research_id" in cols and "origin_research_id" not in cols:
                conn.execute("ALTER TABLE candidates RENAME COLUMN research_id TO origin_research_id")
                conn.commit()
            conn.executescript(self._schema_path.read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _json(value: Optional[Dict[str, Any]]) -> Optional[str]:
        return json.dumps(value, ensure_ascii=False, indent=2) if value is not None else None

    @staticmethod
    def _loads(value: Optional[str]) -> Dict[str, Any]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _extract_dimension_scores(evaluation: Optional[Dict[str, Any]]) -> Dict[str, int]:
        if not isinstance(evaluation, dict):
            return {}

        candidates: List[Dict[str, Any]] = []
        research_score = evaluation.get("research_score")
        if isinstance(research_score, dict):
            candidates.append(research_score)

        nested = evaluation.get("evaluation")
        if isinstance(nested, dict):
            candidates.append(nested)
            nested_rs = nested.get("research_score")
            if isinstance(nested_rs, dict):
                candidates.append(nested_rs)

        for obj in candidates:
            scores = obj.get("scores") or obj.get("raw_scores")
            if isinstance(scores, dict):
                normalized: Dict[str, int] = {}
                for dim in DIMENSIONS:
                    try:
                        normalized[dim] = max(0, min(5, int(scores.get(dim, 0))))
                    except (TypeError, ValueError):
                        normalized[dim] = 0
                return normalized
        return {}

    @staticmethod
    def _stop_checks_triggered(evaluation: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(evaluation, dict):
            return False
        stop = evaluation.get("stop_checks")
        if isinstance(stop, dict):
            if stop.get("triggered") is True:
                return True
            if stop.get("reasons"):
                return True
        nested = evaluation.get("evaluation")
        if isinstance(nested, dict) and nested.get("stop_checks_triggered"):
            return True
        return False

    @staticmethod
    def _qualified_signal_level(row: sqlite3.Row) -> str:
        """Return the level usable for candidate scoring, not merely source authority."""
        declared = (row["evidence_level"] or "UNASSESSED").upper()
        payload = DiscoveryDB._loads(row["payload_json"])
        source = payload.get("source", {}) if isinstance(payload.get("source"), dict) else {}
        evidence = payload.get("evidence", {}) if isinstance(payload.get("evidence"), dict) else {}
        actor = payload.get("actor", {}) if isinstance(payload.get("actor"), dict) else {}

        inspection = source.get("inspection_status")
        evidence_kind = evidence.get("evidence_kind") or payload.get("evidence_kind")
        corroborated = evidence.get("independently_corroborated") is True
        human_primary = evidence.get("human_audited_primary_evidence") is True
        self_reported = actor.get("role_is_self_reported") is True
        role_provenance = actor.get("role_provenance")

        if inspection != "FULL_SOURCE_REVIEWED":
            return "UNASSESSED"

        if declared == "L1":
            # Official policy/docs may be authoritative for rules, but do not by themselves
            # prove operator behavior/frequency. Only behavioral primary evidence earns
            # candidate-level L1.
            if human_primary and evidence_kind == "BEHAVIORAL_PRIMARY":
                return "L1"
            return "L4"

        if declared == "L2":
            if self_reported or role_provenance in {"SELF_REPORTED", "SOURCE_VERIFIED"}:
                return "L2"
            return "L4"

        if declared == "L3":
            return "L3" if corroborated else "L4"

        if declared in {"L4", "L5"}:
            return declared
        return "UNASSESSED"

    @staticmethod
    def _gate_score(scores: Dict[str, int], evidence_level: str) -> Tuple[int, Dict[str, int]]:
        level = evidence_level.upper()
        if level == "L4":
            gated = {d: min(scores.get(d, 0), 1) for d in DIMENSIONS}
        elif level in {"L5", "UNASSESSED"}:
            gated = {d: 0 for d in DIMENSIONS}
        else:
            gated = {d: scores.get(d, 0) for d in DIMENSIONS}
        return sum(gated.values()), gated

    @staticmethod
    def _lifecycle_from_score(score: int, stop_triggered: bool) -> str:
        if stop_triggered:
            return "PARKED"
        if score >= 23:
            return "RESEARCH_PRIORITY"
        return "PARKED"

    def derive_candidate_evidence_gate(
        self,
        research_id: str,
        supporting_signal_ids: Sequence[str],
        evaluation_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Derive candidate evidence/score only from persisted supporting signals."""
        ids = [s for s in supporting_signal_ids if s]
        if not ids:
            return {
                "evidence_level": "UNASSESSED",
                "research_score": 0,
                "scores": {d: 0 for d in DIMENSIONS},
                "supporting_signal_count": 0,
                "reason": "NO_SUPPORTING_SIGNALS",
            }

        conn = self._get_connection()
        try:
            placeholders = ",".join("?" for _ in ids)
            rows = conn.execute(
                f"""
                SELECT signal_id, research_id, evidence_level, payload_json
                FROM evidence_signals
                WHERE research_id=? AND signal_id IN ({placeholders})
                """,
                [research_id, *ids],
            ).fetchall()
        finally:
            conn.close()

        if len(rows) != len(set(ids)):
            found = {r["signal_id"] for r in rows}
            missing = [s for s in ids if s not in found]
            raise ValueError(
                "Supporting signals must already exist in the same research run; missing: "
                + ", ".join(missing)
            )

        qualified_levels = [self._qualified_signal_level(r) for r in rows]
        effective_level = max(qualified_levels, key=lambda x: EVIDENCE_RANK.get(x, 0))
        scores = self._extract_dimension_scores(evaluation_dict)
        if not scores:
            scores = {d: 0 for d in DIMENSIONS}
        total, gated_scores = self._gate_score(scores, effective_level)

        return {
            "evidence_level": effective_level,
            "research_score": total,
            "scores": gated_scores,
            "raw_scores": scores,
            "supporting_signal_count": len(rows),
            "qualified_signal_levels": qualified_levels,
            "reason": "DERIVED_FROM_PERSISTED_SIGNALS",
        }

    @staticmethod
    def _apply_gate_to_evaluation(
        evaluation: Optional[Dict[str, Any]],
        gate: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = dict(evaluation or {})
        result["deterministic_evidence_gate"] = {
            "evidence_level": gate["evidence_level"],
            "research_score": gate["research_score"],
            "supporting_signal_count": gate["supporting_signal_count"],
            "qualified_signal_levels": gate.get("qualified_signal_levels", []),
            "reason": gate["reason"],
        }

        if isinstance(result.get("research_score"), dict):
            rs = dict(result["research_score"])
            rs.setdefault("raw_scores", rs.get("scores", {}))
            rs["scores"] = gate["scores"]
            rs["total"] = gate["research_score"]
            rs["maximum"] = 35
            rs["evidence_level"] = gate["evidence_level"]
            result["research_score"] = rs

        nested = result.get("evaluation")
        if isinstance(nested, dict):
            nested_copy = dict(nested)
            nested_copy.setdefault("raw_scores", nested_copy.get("scores", {}))
            nested_copy["scores"] = gate["scores"]
            nested_copy["capped_score"] = gate["research_score"]
            nested_copy["evidence_level"] = gate["evidence_level"]
            result["evaluation"] = nested_copy

        return result

    def create_research_run(
        self,
        research_id: str,
        request: str,
        domain: str,
        scope_type: str = "BROAD",
        geography: Optional[str] = None,
        plan_dict: Optional[Dict[str, Any]] = None,
    ) -> str:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO research_runs (
                    research_id, original_request, domain, scope_type, geography,
                    current_stage, status, plan_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'EVIDENCE_RESEARCH', 'ACTIVE', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(research_id) DO UPDATE SET
                    original_request = excluded.original_request,
                    domain = excluded.domain,
                    scope_type = excluded.scope_type,
                    geography = excluded.geography,
                    plan_json = excluded.plan_json,
                    current_stage = 'EVIDENCE_RESEARCH',
                    status = 'ACTIVE',
                    updated_at = CURRENT_TIMESTAMP
                """,
                (research_id, request, domain, scope_type, geography, self._json(plan_dict)),
            )
            conn.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (research_id,))
            conn.execute(
                "INSERT INTO discovery_fts(entity_id, entity_type, title_or_issue, body_text) VALUES (?, 'RUN', ?, ?)",
                (research_id, f"Research Run: {domain}", request),
            )
            conn.commit()
            return research_id
        finally:
            conn.close()

    def save_evidence_signals(self, research_id: str, signals: List[Dict[str, Any]]) -> int:
        conn = self._get_connection()
        try:
            inserted = 0
            for index, sig in enumerate(signals, start=1):
                source = sig.get("source", {}) if isinstance(sig.get("source"), dict) else {}
                actor = sig.get("actor", {}) if isinstance(sig.get("actor"), dict) else {}
                observation = sig.get("observation", {}) if isinstance(sig.get("observation"), dict) else {}
                evidence = sig.get("evidence", {}) if isinstance(sig.get("evidence"), dict) else {}

                signal_id = sig.get("signal_id") or f"SIG-{research_id}-{index:03d}"
                stream_id = sig.get("stream_id")
                platform = sig.get("platform") or source.get("platform") or "WEB"
                source_url = sig.get("source_url") or source.get("url")
                reported_issue = sig.get("reported_issue") or observation.get("reported_issue")
                reported_workaround = sig.get("reported_workaround") or observation.get("reported_workaround")
                inspection = source.get("inspection_status")
                declared_level = (sig.get("evidence_level") or evidence.get("classification") or "UNASSESSED").upper()

                # Raw/snippet search hits can never be promoted by model assertion alone.
                if inspection != "FULL_SOURCE_REVIEWED":
                    effective_signal_level = "UNASSESSED"
                elif declared_level == "L3" and evidence.get("independently_corroborated") is not True:
                    effective_signal_level = "L4"
                elif declared_level == "L1" and evidence.get("human_audited_primary_evidence") is not True:
                    effective_signal_level = "L4"
                else:
                    effective_signal_level = declared_level if declared_level in EVIDENCE_RANK else "UNASSESSED"

                role_provenance = actor.get("role_provenance")
                actor_verified = (
                    actor.get("role_is_self_reported") is True
                    or role_provenance in {"SELF_REPORTED", "SOURCE_VERIFIED"}
                )
                actor_role = (sig.get("actor_role") or actor.get("role")) if actor_verified else None

                if not reported_issue:
                    raise ValueError(f"Signal {signal_id} has no reported_issue")

                normalized = dict(sig)
                normalized.setdefault("source", source)
                normalized.setdefault("actor", actor)
                normalized.setdefault("observation", observation)
                normalized.setdefault("evidence", evidence)
                normalized["evidence_level"] = effective_signal_level
                normalized["evidence"] = dict(evidence)
                normalized["evidence"]["classification"] = effective_signal_level

                conn.execute(
                    """
                    INSERT INTO evidence_signals (
                        signal_id, research_id, candidate_id, stream_id, platform,
                        source_url, actor_role, reported_issue, reported_workaround,
                        evidence_level, payload_json, retrieved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(signal_id) DO UPDATE SET
                        research_id = excluded.research_id,
                        stream_id = excluded.stream_id,
                        platform = excluded.platform,
                        source_url = excluded.source_url,
                        actor_role = excluded.actor_role,
                        reported_issue = excluded.reported_issue,
                        reported_workaround = excluded.reported_workaround,
                        evidence_level = excluded.evidence_level,
                        payload_json = excluded.payload_json,
                        retrieved_at = CURRENT_TIMESTAMP
                    """,
                    (
                        signal_id, research_id, sig.get("candidate_id"), stream_id, platform,
                        source_url, actor_role, reported_issue, reported_workaround,
                        effective_signal_level, self._json(normalized),
                    ),
                )
                conn.execute("DELETE FROM discovery_fts WHERE entity_id = ?", (signal_id,))
                conn.execute(
                    "INSERT INTO discovery_fts(entity_id, entity_type, title_or_issue, body_text) VALUES (?, 'SIGNAL', ?, ?)",
                    (signal_id, reported_issue, reported_workaround or ""),
                )
                inserted += 1

            conn.execute(
                """
                UPDATE research_runs
                SET current_stage='PROBLEM_EVALUATION', status='ACTIVE', updated_at=CURRENT_TIMESTAMP
                WHERE research_id=?
                """,
                (research_id,),
            )
            conn.commit()
            return inserted
        finally:
            conn.close()

    def upsert_candidate(
        self,
        candidate_id: str,
        research_id: str,
        title: str,
        domain: str,
        target_operator: Optional[str] = None,
        track: str = "COMMERCIAL",
        research_score: Optional[int] = None,
        evidence_level: str = "UNASSESSED",
        lifecycle_status: str = "ACTIVE",
        evaluation_dict: Optional[Dict[str, Any]] = None,
        supporting_signal_ids: Optional[List[str]] = None,
    ) -> str:
        ids = supporting_signal_ids or []
        gate = self.derive_candidate_evidence_gate(research_id, ids, evaluation_dict)
        gated_evaluation = self._apply_gate_to_evaluation(evaluation_dict, gate)
        gated_lifecycle = self._lifecycle_from_score(
            gate["research_score"], self._stop_checks_triggered(evaluation_dict)
        )

        conn = self._get_connection()
        try:
            existing = conn.execute(
                """
                SELECT origin_research_id, research_score, evidence_level, lifecycle_status,
                       evaluation_json
                FROM candidates WHERE candidate_id=?
                """,
                (candidate_id,),
            ).fetchone()

            final_score = gate["research_score"]
            final_level = gate["evidence_level"]
            final_lifecycle = gated_lifecycle
            final_evaluation_json = self._json(gated_evaluation)

            # A later weak rediscovery may add evidence to a stable candidate, but must not
            # erase stronger evidence or regress a more advanced lifecycle state.
            if existing and existing["origin_research_id"] != research_id:
                if EVIDENCE_RANK.get(existing["evidence_level"], 0) > EVIDENCE_RANK.get(final_level, 0):
                    final_level = existing["evidence_level"]
                    final_score = existing["research_score"]
                    final_evaluation_json = existing["evaluation_json"]
                if existing["lifecycle_status"] not in {"ACTIVE", "RESEARCH_PRIORITY", "PARKED"}:
                    final_lifecycle = existing["lifecycle_status"]

            conn.execute(
                """
                INSERT INTO candidates (
                    candidate_id, origin_research_id, title, domain, target_operator, track,
                    research_score, evidence_level, validation_status, lifecycle_status,
                    evaluation_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(candidate_id) DO UPDATE SET
                    title = excluded.title,
                    domain = excluded.domain,
                    target_operator = excluded.target_operator,
                    track = excluded.track,
                    research_score = excluded.research_score,
                    evidence_level = excluded.evidence_level,
                    lifecycle_status = excluded.lifecycle_status,
                    evaluation_json = excluded.evaluation_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    candidate_id,
                    research_id,
                    title,
                    domain,
                    target_operator,
                    track,
                    final_score,
                    final_level,
                    final_lifecycle,
                    final_evaluation_json,
                ),
            )

            if ids:
                placeholders = ",".join("?" for _ in ids)
                result = conn.execute(
                    f"""
                    UPDATE evidence_signals
                    SET candidate_id=?
                    WHERE research_id=? AND signal_id IN ({placeholders})
                    """,
                    [candidate_id, research_id, *ids],
                )
                if result.rowcount != len(set(ids)):
                    raise ValueError("Not all supporting signals could be linked to the candidate")

            conn.execute("DELETE FROM discovery_fts WHERE entity_id=?", (candidate_id,))
            conn.execute(
                """
                INSERT INTO discovery_fts(entity_id, entity_type, title_or_issue, body_text)
                VALUES (?, 'CANDIDATE', ?, ?)
                """,
                (candidate_id, title, f"{domain} {target_operator or ''}"),
            )
            conn.commit()
        finally:
            conn.close()

        self.refresh_research_run_state(research_id)
        return candidate_id

    def preregister_experiment(self, experiment_id: str, candidate_id: str, contract_dict: Dict[str, Any]) -> str:
        primary_metric = contract_dict.get("primary_metric", {})
        threshold = contract_dict.get("success_threshold", {})
        sample = contract_dict.get("sample", {})
        metric_name = primary_metric.get("name") or contract_dict.get("metric_name")
        target_threshold = threshold.get("value", contract_dict.get("target_threshold"))
        direction = threshold.get("operator", contract_dict.get("direction", ">="))
        sample_target = sample.get("target", contract_dict.get("sample_target"))
        hypothesis = contract_dict.get("hypothesis")
        aggregation_rule = contract_dict.get("aggregation_rule")

        if not all([hypothesis, metric_name, sample_target is not None, target_threshold is not None]):
            raise ValueError("Experiment contract is missing hypothesis, primary metric, threshold, or sample target")
        if not aggregation_rule:
            raise ValueError("Experiment contract requires an explicit aggregation_rule")
        metric_key = str(metric_name).strip().lower()
        if re.search(r"(?:^|_)or(?:_|$)|\\bor\\b|\\band\\b|/", metric_key):
            raise ValueError(
                "Experiment primary metric must be atomic; split compound outcomes into separate experiments"
            )

        conn = self._get_connection()
        try:
            existing = conn.execute(
                "SELECT contract_json FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            contract_json = self._json(contract_dict)
            if existing and existing["contract_json"] != contract_json:
                raise ValueError("Preregistered experiment is immutable; create a new experiment_id for material changes")

            conn.execute(
                """
                INSERT INTO experiments (
                    experiment_id, candidate_id, hypothesis, metric_name, target_threshold,
                    direction, sample_target, outcome_verdict, contract_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PREREGISTERED', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(experiment_id) DO NOTHING
                """,
                (
                    experiment_id,
                    candidate_id,
                    hypothesis,
                    metric_name,
                    float(target_threshold),
                    direction,
                    int(sample_target),
                    contract_json,
                ),
            )
            if conn.total_changes == 0 and not existing:
                raise ValueError(f"Unable to preregister experiment {experiment_id}")

            conn.execute(
                """
                UPDATE candidates
                SET validation_status='IN_PROGRESS', lifecycle_status='VALIDATING',
                    updated_at=CURRENT_TIMESTAMP
                WHERE candidate_id=?
                """,
                (candidate_id,),
            )
            if conn.execute("SELECT changes()").fetchone()[0] == 0:
                raise ValueError(f"Candidate '{candidate_id}' not found")
            conn.commit()
        finally:
            conn.close()

        for run_id in self._research_runs_for_candidate(candidate_id):
            self.refresh_research_run_state(run_id)
        return experiment_id

    def get_experiment_contract(self, experiment_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT contract_json FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Experiment '{experiment_id}' not found")
            return json.loads(row["contract_json"])
        finally:
            conn.close()

    def record_experiment_assessment(
        self,
        experiment_id: str,
        assessment_dict: Dict[str, Any],
        artifact_hash: Optional[str] = None,
        audited_by: Optional[str] = None,
        audit_date: Optional[str] = None,
    ) -> str:
        status = assessment_dict.get("status")
        verdict_map = {
            "EXPERIMENT_PASSED": "PASSED",
            "EXPERIMENT_FAILED": "FAILED",
            "INCOMPLETE": "INCOMPLETE",
            "INVALID_EXPERIMENT": "INVALID",
        }
        if status not in verdict_map:
            raise ValueError(f"Unsupported assessment status: {status}")

        verdict = verdict_map[status]
        observed = assessment_dict.get("observed_result", {}) or {}
        review = assessment_dict.get("artifact_review", {}) or {}

        conn = self._get_connection()
        try:
            exp = conn.execute(
                "SELECT candidate_id, contract_json FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            if not exp:
                raise ValueError(f"Experiment '{experiment_id}' not found")
            candidate_id = exp["candidate_id"]
            contract = self._loads(exp["contract_json"])
            sample = contract.get("sample", {}) if isinstance(contract.get("sample"), dict) else {}
            threshold = contract.get("success_threshold", {}) if isinstance(contract.get("success_threshold"), dict) else {}
            artifact_requirements = contract.get("artifact_requirements", {}) if isinstance(contract.get("artifact_requirements"), dict) else {}
            review_requirements = contract.get("review_requirements", {}) if isinstance(contract.get("review_requirements"), dict) else {}

            sample_achieved = observed.get("sample_achieved")
            observed_value = observed.get("observed_value")
            min_usable = int(sample.get("minimum_usable", 0) or 0)
            locked_threshold = threshold.get("value")
            direction = threshold.get("operator")
            final_hash = artifact_hash or review.get("sha256")
            final_auditor = audited_by or review.get("audited_by")
            final_audit_date = audit_date or review.get("audit_date")

            if sample_achieved is not None and int(sample_achieved) < min_usable and verdict != "INCOMPLETE":
                raise ValueError("Assessment verdict conflicts with preregistered minimum usable sample")

            if verdict in {"PASSED", "FAILED"}:
                if artifact_requirements.get("required") and not final_hash:
                    raise ValueError("Audited PASS/FAIL requires the preregistered evidence artifact hash")
                if review_requirements.get("human_review_required") and not (final_auditor and final_audit_date):
                    raise ValueError("Audited PASS/FAIL requires named reviewer and review date")
                if observed_value is None or locked_threshold is None or not direction:
                    raise ValueError("Audited PASS/FAIL requires observed value and locked threshold")
                observed_num = float(observed_value)
                threshold_num = float(locked_threshold)
                comparison = {
                    ">=": observed_num >= threshold_num,
                    "<=": observed_num <= threshold_num,
                    ">": observed_num > threshold_num,
                    "<": observed_num < threshold_num,
                    "==": observed_num == threshold_num,
                }.get(direction)
                if comparison is None:
                    raise ValueError(f"Unsupported experiment direction: {direction}")
                expected = "PASSED" if comparison else "FAILED"
                if verdict != expected:
                    raise ValueError(
                        f"Assessment verdict {verdict} conflicts with locked threshold; expected {expected}"
                    )

            conn.execute(
                """
                UPDATE experiments
                SET sample_achieved=?, observed_value=?, outcome_verdict=?,
                    assessment_json=?, artifact_hash=?, audited_by=?, audit_date=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE experiment_id=?
                """,
                (
                    observed.get("sample_achieved"),
                    observed.get("observed_value"),
                    verdict,
                    self._json(assessment_dict),
                    final_hash,
                    final_auditor,
                    final_audit_date,
                    experiment_id,
                ),
            )

            if verdict == "PASSED":
                validation_status, lifecycle = "PARTIALLY_VALIDATED", "READY_FOR_SOLUTION"
            elif verdict == "INCOMPLETE":
                validation_status, lifecycle = "IN_PROGRESS", "VALIDATING"
            elif verdict == "FAILED":
                validation_status, lifecycle = "IN_PROGRESS", "RESEARCH_PRIORITY"
            else:
                validation_status, lifecycle = "UNVERIFIED", "RESEARCH_PRIORITY"

            conn.execute(
                """
                UPDATE candidates
                SET validation_status=?, lifecycle_status=?, updated_at=CURRENT_TIMESTAMP
                WHERE candidate_id=?
                """,
                (validation_status, lifecycle, candidate_id),
            )
            conn.commit()
        finally:
            conn.close()

        for run_id in self._research_runs_for_candidate(candidate_id):
            self.refresh_research_run_state(run_id)
        return experiment_id

    def finalize_solution(self, candidate_id: str, solution_class: str, solution_dict: Dict[str, Any]) -> str:
        conn = self._get_connection()
        try:
            candidate = conn.execute(
                """
                SELECT origin_research_id, validation_status
                FROM candidates WHERE candidate_id=?
                """,
                (candidate_id,),
            ).fetchone()
            if not candidate:
                raise ValueError(f"Candidate '{candidate_id}' not found; refusing to fabricate a stub candidate")

            active_experiment = conn.execute(
                """
                SELECT experiment_id FROM experiments
                WHERE candidate_id=? AND outcome_verdict IN ('PREREGISTERED', 'INCOMPLETE')
                ORDER BY created_at DESC LIMIT 1
                """,
                (candidate_id,),
            ).fetchone()
            if active_experiment:
                raise ValueError(
                    f"Candidate '{candidate_id}' has unfinished experiment "
                    f"{active_experiment['experiment_id']}; solution strategy cannot finalize yet"
                )

            lifecycle = (
                "PILOT_READY"
                if candidate["validation_status"] in {"PARTIALLY_VALIDATED", "VALIDATED"}
                else "SOLUTION_PROPOSED"
            )
            conn.execute(
                """
                UPDATE candidates
                SET solution_class=?, lifecycle_status=?,
                    solution_json=?, updated_at=CURRENT_TIMESTAMP
                WHERE candidate_id=?
                """,
                (solution_class, lifecycle, self._json(solution_dict), candidate_id),
            )
            conn.commit()
        finally:
            conn.close()

        for run_id in self._research_runs_for_candidate(candidate_id):
            self.refresh_research_run_state(run_id)
        return candidate_id

    def _research_runs_for_candidate(self, candidate_id: str) -> List[str]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT origin_research_id AS research_id
                FROM candidates
                WHERE candidate_id=?
                UNION
                SELECT DISTINCT research_id
                FROM evidence_signals
                WHERE candidate_id=?
                """,
                (candidate_id, candidate_id),
            ).fetchall()
            return [r["research_id"] for r in rows if r["research_id"]]
        finally:
            conn.close()

    def refresh_research_run_state(self, research_id: str) -> Dict[str, Any]:
        """Aggregate every candidate attached to a run before deciding run completion."""
        conn = self._get_connection()
        try:
            candidates = conn.execute(
                """
                SELECT DISTINCT c.candidate_id, c.lifecycle_status, c.validation_status,
                       c.solution_class
                FROM candidates c
                WHERE c.origin_research_id=?
                   OR c.candidate_id IN (
                       SELECT DISTINCT candidate_id
                       FROM evidence_signals
                       WHERE research_id=? AND candidate_id IS NOT NULL
                   )
                """,
                (research_id, research_id),
            ).fetchall()

            if not candidates:
                state = {"current_stage": "PROBLEM_EVALUATION", "status": "ACTIVE"}
            else:
                ids = [r["candidate_id"] for r in candidates]
                placeholders = ",".join("?" for _ in ids)
                exp_rows = conn.execute(
                    f"""
                    SELECT candidate_id, outcome_verdict
                    FROM experiments
                    WHERE candidate_id IN ({placeholders})
                    """,
                    ids,
                ).fetchall()

                experiment_states: Dict[str, set[str]] = {cid: set() for cid in ids}
                for row in exp_rows:
                    experiment_states[row["candidate_id"]].add(row["outcome_verdict"])

                all_terminal = all(r["lifecycle_status"] in TERMINAL_CANDIDATE_STATES for r in candidates)
                has_unfinished_experiment = any(
                    bool(states & {"PREREGISTERED", "INCOMPLETE"})
                    for states in experiment_states.values()
                )
                has_solution_work = any(
                    r["lifecycle_status"] in {"READY_FOR_SOLUTION", "SOLUTION_PROPOSED"}
                    for r in candidates
                )

                if all_terminal and not has_unfinished_experiment:
                    state = {"current_stage": "COMPLETED", "status": "COMPLETED"}
                elif has_solution_work and not has_unfinished_experiment:
                    state = {"current_stage": "SOLUTION_STRATEGY", "status": "ACTIVE"}
                else:
                    state = {"current_stage": "EXPERIMENT_VALIDATION", "status": "ACTIVE"}

            conn.execute(
                """
                UPDATE research_runs
                SET current_stage=?, status=?, updated_at=CURRENT_TIMESTAMP
                WHERE research_id=?
                """,
                (state["current_stage"], state["status"], research_id),
            )
            conn.commit()
            return state
        finally:
            conn.close()

    def repair_integrity(self) -> Dict[str, Any]:
        """Repair rows created before evidence/run-state guardrails were enforced."""
        conn = self._get_connection()
        try:
            candidate_rows = conn.execute(
                """
                SELECT candidate_id, origin_research_id, evaluation_json, solution_json,
                       lifecycle_status, validation_status
                FROM candidates
                ORDER BY candidate_id
                """
            ).fetchall()
        finally:
            conn.close()

        repaired_candidates = 0
        for cand in candidate_rows:
            candidate_id = cand["candidate_id"]
            evaluation = self._loads(cand["evaluation_json"])
            conn = self._get_connection()
            try:
                signals = conn.execute(
                    """
                    SELECT signal_id, research_id, evidence_level, payload_json
                    FROM evidence_signals
                    WHERE candidate_id=?
                    ORDER BY retrieved_at
                    """,
                    (candidate_id,),
                ).fetchall()

                levels = [self._qualified_signal_level(r) for r in signals]
                effective_level = (
                    max(levels, key=lambda x: EVIDENCE_RANK.get(x, 0))
                    if levels else "UNASSESSED"
                )
                scores = self._extract_dimension_scores(evaluation)
                if not scores:
                    scores = {d: 0 for d in DIMENSIONS}
                total, gated_scores = self._gate_score(scores, effective_level)
                gate = {
                    "evidence_level": effective_level,
                    "research_score": total,
                    "scores": gated_scores,
                    "raw_scores": scores,
                    "supporting_signal_count": len(signals),
                    "qualified_signal_levels": levels,
                    "reason": "INTEGRITY_REPAIR_FROM_LINKED_SIGNALS",
                }
                repaired_eval = self._apply_gate_to_evaluation(evaluation, gate)

                experiments = conn.execute(
                    """
                    SELECT outcome_verdict FROM experiments
                    WHERE candidate_id=?
                    ORDER BY created_at DESC, experiment_id DESC
                    """,
                    (candidate_id,),
                ).fetchall()
                verdicts = [r["outcome_verdict"] for r in experiments]

                if "PREREGISTERED" in verdicts or "INCOMPLETE" in verdicts:
                    validation_status = "IN_PROGRESS"
                    lifecycle = "VALIDATING"
                elif "PASSED" in verdicts:
                    validation_status = "PARTIALLY_VALIDATED"
                    lifecycle = "PILOT_READY" if cand["solution_json"] else "READY_FOR_SOLUTION"
                elif "FAILED" in verdicts:
                    validation_status = "IN_PROGRESS"
                    lifecycle = self._lifecycle_from_score(total, self._stop_checks_triggered(evaluation))
                elif "INVALID" in verdicts:
                    validation_status = "UNVERIFIED"
                    lifecycle = self._lifecycle_from_score(total, self._stop_checks_triggered(evaluation))
                elif cand["solution_json"]:
                    validation_status = "UNVERIFIED"
                    lifecycle = "SOLUTION_PROPOSED"
                else:
                    validation_status = "UNVERIFIED"
                    lifecycle = self._lifecycle_from_score(total, self._stop_checks_triggered(evaluation))

                conn.execute(
                    """
                    UPDATE candidates
                    SET research_score=?, evidence_level=?, validation_status=?,
                        lifecycle_status=?, evaluation_json=?, updated_at=CURRENT_TIMESTAMP
                    WHERE candidate_id=?
                    """,
                    (
                        total,
                        effective_level,
                        validation_status,
                        lifecycle,
                        self._json(repaired_eval),
                        candidate_id,
                    ),
                )

                # Remove stream-target roles that were persisted as if they were observed actors.
                for signal in signals:
                    payload = self._loads(signal["payload_json"])
                    source = payload.get("source", {}) if isinstance(payload.get("source"), dict) else {}
                    actor = payload.get("actor", {}) if isinstance(payload.get("actor"), dict) else {}
                    if (
                        source.get("inspection_status") != "FULL_SOURCE_REVIEWED"
                        and actor.get("role_is_self_reported") is not True
                        and actor.get("role_provenance") not in {"SELF_REPORTED", "SOURCE_VERIFIED"}
                    ):
                        conn.execute(
                            "UPDATE evidence_signals SET actor_role=NULL WHERE signal_id=?",
                            (signal["signal_id"],),
                        )

                conn.commit()
                repaired_candidates += 1
            finally:
                conn.close()

        conn = self._get_connection()
        try:
            run_ids = [r["research_id"] for r in conn.execute("SELECT research_id FROM research_runs").fetchall()]
        finally:
            conn.close()
        for run_id in run_ids:
            self.refresh_research_run_state(run_id)

        return {
            "repaired_candidates": repaired_candidates,
            "refreshed_runs": len(run_ids),
        }

    def get_discovery_dashboard(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if status_filter:
                rows = conn.execute(
                    """
                    SELECT * FROM v_discovery_dashboard
                    WHERE lifecycle_status=? OR validation_status=?
                    ORDER BY updated_at DESC
                    """,
                    (status_filter, status_filter),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM v_discovery_dashboard ORDER BY updated_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search_fts(self, query: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            sql = """
                SELECT entity_id, entity_type, title_or_issue, body_text, rank
                FROM discovery_fts
                WHERE discovery_fts MATCH ?
            """
            params: List[Any] = [query]
            if entity_type:
                sql += " AND entity_type=?"
                params.append(entity_type)
            sql += " ORDER BY rank"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonical Problem Discovery state client")
    parser.add_argument("--db", default="discovery.sqlite")
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--filter-status")
    parser.add_argument("--search")
    parser.add_argument("--type")
    parser.add_argument(
        "--repair-integrity",
        action="store_true",
        help="Recompute candidate evidence/score/lifecycle and aggregate research-run state",
    )
    args = parser.parse_args()

    db = DiscoveryDB(args.db)
    if args.repair_integrity:
        print(json.dumps(db.repair_integrity(), indent=2))
    elif args.dashboard:
        print(json.dumps(db.get_discovery_dashboard(args.filter_status), indent=2))
    elif args.search:
        print(json.dumps(db.search_fts(args.search, args.type), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
