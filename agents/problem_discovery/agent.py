"""Problem Discovery Orchestrator Agent using the official Google Antigravity Python SDK.

The orchestrator is intentionally thin:
- deterministic code chooses the next persisted workflow stage,
- Antigravity + the loaded modular skill performs that stage,
- custom discovery-state tools are the only mutation path,
- SQLite is re-read after every stage,
- real-world experiments always pause instead of being fabricated.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

try:
    from google.antigravity import Agent, LocalAgentConfig, types, BuiltinTools
    from google.antigravity.hooks import policy
    ANTIGRAVITY_AVAILABLE = True
except ImportError:
    ANTIGRAVITY_AVAILABLE = False
    Agent = None  # type: ignore
    LocalAgentConfig = None  # type: ignore
    types = None  # type: ignore
    BuiltinTools = None  # type: ignore
    policy = None  # type: ignore

from agents.problem_discovery.config import (
    ProblemDiscoveryConfig,
    get_canonical_skills_paths,
)
from agents.problem_discovery.orchestration.models import (
    IntentClassification,
    IntentType,
    OrchestrationResult,
    WorkflowStage,
    WorkflowStatus,
)
from agents.problem_discovery.orchestration.router import IntentRouter
from agents.problem_discovery.orchestration.state_machine import DiscoveryStateMachine
from agents.problem_discovery.prompts import get_system_prompt
from agents.problem_discovery.tools.discovery_state_tools import DiscoveryStateTools


class ProblemDiscoveryAgent:
    """Orchestrate the five reusable discovery reasoning capabilities.

    The agent never fabricates evidence or experiment results. A reasoning stage is
    executed only through the Antigravity SDK, using the relevant loaded skill and
    the narrow discovery-state tools. The deterministic state machine decides what
    stage may run next.
    """

    MAX_STAGE_STEPS = 8

    def __init__(
        self,
        config: Optional[ProblemDiscoveryConfig] = None,
        db_path: Optional[str] = None,
    ) -> None:
        self.config = config or ProblemDiscoveryConfig()
        if db_path:
            self.config.db_path = str(db_path)

        self.db_path = self.config.db_path
        self.tools_provider = DiscoveryStateTools(db_path=self.db_path)
        self.router = IntentRouter()
        self.state_machine = DiscoveryStateMachine(db_path=self.db_path)
        self._sdk_agent: Optional[Any] = None

    # ---------------------------------------------------------------------
    # Stable identifier allocation
    # ---------------------------------------------------------------------

    def _next_research_id(self) -> str:
        conn = self.tools_provider._get_connection()
        try:
            year = datetime.now(timezone.utc).year
            rows = conn.execute(
                "SELECT research_id FROM research_runs WHERE research_id LIKE ?",
                (f"RUN-{year}-%",),
            ).fetchall()
            max_seq = 0
            for row in rows:
                match = re.fullmatch(rf"RUN-{year}-(\d+)", row["research_id"])
                if match:
                    max_seq = max(max_seq, int(match.group(1)))
            return f"RUN-{year}-{max_seq + 1:03d}"
        finally:
            conn.close()

    def _next_candidate_id(self) -> str:
        conn = self.tools_provider._get_connection()
        try:
            rows = conn.execute("SELECT candidate_id FROM candidates").fetchall()
            max_seq = 0
            for row in rows:
                match = re.fullmatch(r"CAND-(\d+)", row["candidate_id"])
                if match:
                    max_seq = max(max_seq, int(match.group(1)))
            return f"CAND-{max_seq + 1:03d}"
        finally:
            conn.close()

    def _next_experiment_id(self) -> str:
        conn = self.tools_provider._get_connection()
        try:
            rows = conn.execute("SELECT experiment_id FROM experiments").fetchall()
            max_seq = 0
            for row in rows:
                match = re.fullmatch(r"EXP-(\d+)", row["experiment_id"])
                if match:
                    max_seq = max(max_seq, int(match.group(1)))
            return f"EXP-{max_seq + 1:03d}"
        finally:
            conn.close()

    # ---------------------------------------------------------------------
    # Antigravity runtime
    # ---------------------------------------------------------------------

    def build_sdk_config(self) -> Any:
        """Build the official Antigravity LocalAgentConfig with least privilege."""
        if not ANTIGRAVITY_AVAILABLE:
            raise RuntimeError(
                "google-antigravity is not installed. Install it before executing reasoning stages."
            )

        capabilities = types.CapabilitiesConfig(
            enabled_tools=[
                BuiltinTools.VIEW_FILE,
                BuiltinTools.READ_URL_CONTENT,
                BuiltinTools.SEARCH_WEB,
            ]
        )
        policies = [
            policy.deny("run_command"),
            policy.deny("create_file"),
            policy.deny("edit_file"),
        ]

        return LocalAgentConfig(
            system_instructions=get_system_prompt(),
            tools=self.tools_provider.get_all_tools(),
            skills_paths=self.config.skills_paths or get_canonical_skills_paths(),
            capabilities=capabilities,
            policies=policies,
            model=self.config.model,
            api_key=self.config.api_key,
        )

    def create_sdk_agent(self) -> Any:
        return Agent(self.build_sdk_config())

    async def __aenter__(self) -> "ProblemDiscoveryAgent":
        if not ANTIGRAVITY_AVAILABLE:
            return self
        self._sdk_agent = self.create_sdk_agent()
        await self._sdk_agent.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._sdk_agent is not None:
            try:
                await self._sdk_agent.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                self._sdk_agent = None

    async def _chat_sdk(self, prompt: str) -> str:
        """Execute one bounded reasoning turn through the real Antigravity Agent."""
        if not ANTIGRAVITY_AVAILABLE:
            raise RuntimeError(
                "Reasoning stage execution requires the google-antigravity package. "
                "No synthetic fallback is permitted."
            )

        if self._sdk_agent is not None:
            response = await self._sdk_agent.chat(prompt)
            return await response.text()

        async with self.create_sdk_agent() as agent:
            response = await agent.chat(prompt)
            return await response.text()

    # ---------------------------------------------------------------------
    # Stage prompts
    # ---------------------------------------------------------------------

    @staticmethod
    def _stage_header(stage: WorkflowStage) -> str:
        return (
            f"Execute exactly one Problem Discovery workflow stage: {stage.value}.\n"
            "Use the matching loaded skill. Inspect SQLite state first through the custom "
            "discovery-state tools. Persist only through those tools. Do not execute a later "
            "stage in the same turn. Never invent evidence, source URLs, interviews, trial "
            "participants, observed metrics, artifact hashes, reviewers, or audit dates.\n"
        )

    def _build_stage_prompt(
        self,
        stage: WorkflowStage,
        *,
        research_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        original_request: Optional[str] = None,
        user_submission: Optional[str] = None,
        next_action: Optional[str] = None,
    ) -> str:
        header = self._stage_header(stage)

        if stage == WorkflowStage.RESEARCH_PLANNING:
            if not research_id or not original_request:
                raise ValueError("Research planning requires research_id and original_request")
            return header + f"""
Use the research-planning skill.

Reserved research_id: {research_id}
Original user request:
{original_request}

Create a valid ResearchPlan from the user's actual request. Do not invent empirical facts.
Geography remains unknown/null unless supplied. Then persist the plan by calling
create_research_run with EXACTLY research_id={research_id}. Stop after the plan is persisted.
"""

        if stage == WorkflowStage.EVIDENCE_RESEARCH:
            return header + f"""
Use the evidence-research skill for research_id={research_id}.

Load the persisted ResearchPlan first. Execute real web/source research with the available
read-only web tools. A search hit or snippet is not verified evidence. Inspect sources before
qualification; raw/snippet-only hits remain UNASSESSED. Never invent a URL, quote, interview,
actor identity, frequency, consequence, or workaround.

Persist only genuinely collected normalized signals through save_evidence_signals.
If live research cannot be completed, do not manufacture signals; report the blocker and stop.
"""

        if stage == WorkflowStage.PROBLEM_EVALUATION:
            reserved_candidate = candidate_id or self._next_candidate_id()
            return header + f"""
Use the problem-evaluation skill.

research_id={research_id or 'resolve from candidate/state'}
candidate_id={candidate_id or 'not assigned yet'}
next_action={next_action or 'RUN_PROBLEM_EVALUATION'}
reserved_new_candidate_id={reserved_candidate}

Build the bounded problem-evaluation context from persisted state. Interpret only persisted
signals. Reuse an existing stable candidate when it matches the same actor/task/friction/root
workflow. If a new candidate is justified, use reserved_new_candidate_id. Unsupported workflow
nodes remain UNKNOWN. Root causes remain hypotheses unless supported. Score is research priority,
not validation.

Persist through upsert_candidate only after identifying the exact supporting signal IDs.
Stop after candidate/evaluation persistence or after reporting that more evidence is required.
"""

        if stage == WorkflowStage.EXPERIMENT_VALIDATION and user_submission is None:
            reserved_experiment = experiment_id or self._next_experiment_id()
            return header + f"""
Use experiment-validation in DESIGN mode.

candidate_id={candidate_id}
reserved_new_experiment_id={reserved_experiment}
next_action={next_action or 'DESIGN_EXPERIMENT_CONTRACT'}

Load the candidate evaluation and previous experiment history. Design one immutable experiment
with one atomic primary metric, one explicit aggregation rule, locked threshold, minimum usable
sample, artifact requirements, and human-review requirements. Do NOT execute the experiment.
Do NOT fabricate observations.

Persist the contract through preregister_experiment using reserved_new_experiment_id, then STOP.
The expected next workflow state is PAUSED / WAITING_FOR_REAL_WORLD_EXPERIMENT.
"""

        if stage == WorkflowStage.EXPERIMENT_VALIDATION and user_submission is not None:
            return header + f"""
Use experiment-validation in ASSESS mode for experiment_id={experiment_id}.

User-supplied result material:
{user_submission}

Load the immutable persisted experiment contract. Never reconstruct or modify the metric,
threshold, sample rule, or aggregation rule. Determine whether the supplied material contains
the actual observed value/sample plus every preregistered artifact and human-review field needed
for a final assessment.

If required information is missing, DO NOT call record_experiment_assessment. Explain exactly
what is missing and stop with the experiment still PREREGISTERED.

Only when the supplied evidence is sufficient, assess against the locked contract and persist
through record_experiment_assessment. Never invent an artifact hash, reviewer, audit date, sample,
or observed value.
"""

        if stage == WorkflowStage.SOLUTION_STRATEGY:
            return header + f"""
Use the solution-strategy skill for candidate_id={candidate_id}.

Build the solution-strategy context and verify solution_readiness before reasoning. If any
experiment is PREREGISTERED or INCOMPLETE, do not finalize. Prefer the least complex intervention
supported by known requirements. Problem evidence does not automatically justify software;
software does not automatically justify SaaS. Unknown requirements cannot justify complexity.

Persist through finalize_solution only when the readiness gate allows it. Stop after persistence.
"""

        raise ValueError(f"No executable prompt defined for stage {stage.value}")

    # ---------------------------------------------------------------------
    # Deterministic orchestration
    # ---------------------------------------------------------------------

    @staticmethod
    def _state_signature(result: OrchestrationResult) -> tuple:
        return (
            result.research_id,
            result.candidate_id,
            result.experiment_id,
            result.current_stage.value if result.current_stage else None,
            result.workflow_status.value,
            result.next_action,
            result.pause_reason,
        )

    def _execution_error(
        self,
        *,
        intent: IntentType,
        stage: WorkflowStage,
        message: str,
        research_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> OrchestrationResult:
        return OrchestrationResult(
            intent=intent,
            research_id=research_id,
            candidate_id=candidate_id,
            experiment_id=experiment_id,
            current_stage=stage,
            action_taken="No workflow mutation was fabricated.",
            workflow_status=WorkflowStatus.ERROR,
            next_action="FIX_RUNTIME_OR_REQUIRED_INPUT",
            message=message,
        )

    async def _execute_stage_and_refresh(
        self,
        state: OrchestrationResult,
        *,
        original_request: Optional[str] = None,
        user_submission: Optional[str] = None,
    ) -> OrchestrationResult:
        stage = state.current_stage
        if stage not in {
            WorkflowStage.RESEARCH_PLANNING,
            WorkflowStage.EVIDENCE_RESEARCH,
            WorkflowStage.PROBLEM_EVALUATION,
            WorkflowStage.EXPERIMENT_VALIDATION,
            WorkflowStage.SOLUTION_STRATEGY,
        }:
            return state

        prompt = self._build_stage_prompt(
            stage,
            research_id=state.research_id,
            candidate_id=state.candidate_id,
            experiment_id=state.experiment_id,
            original_request=original_request,
            user_submission=user_submission,
            next_action=state.next_action,
        )

        try:
            model_text = await self._chat_sdk(prompt)
        except Exception as exc:
            return self._execution_error(
                intent=state.intent,
                stage=stage,
                research_id=state.research_id,
                candidate_id=state.candidate_id,
                experiment_id=state.experiment_id,
                message=(
                    f"Antigravity could not execute {stage.value}: {exc}. "
                    "The workflow was not synthetically advanced."
                ),
            )

        identifier = state.candidate_id or state.research_id
        if not identifier:
            return self._execution_error(
                intent=state.intent,
                stage=stage,
                message="Stage completed without a resolvable persisted identifier.",
            )

        refreshed = self.state_machine.evaluate_next_action(identifier)
        refreshed.intent = state.intent
        refreshed.data = dict(refreshed.data)
        refreshed.data["stage_agent_response"] = model_text
        return refreshed

    async def _run_existing_state_until_blocked(
        self,
        initial: OrchestrationResult,
        *,
        original_request: Optional[str] = None,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> OrchestrationResult:
        state = initial

        for _ in range(self.MAX_STAGE_STEPS):
            if state.workflow_status in {
                WorkflowStatus.PAUSED,
                WorkflowStatus.COMPLETED,
                WorkflowStatus.READ_ONLY,
                WorkflowStatus.ERROR,
            }:
                return state

            if state.current_stage is None:
                return self._execution_error(
                    intent=state.intent,
                    stage=WorkflowStage.RESEARCH_PLANNING,
                    research_id=state.research_id,
                    candidate_id=state.candidate_id,
                    message="State machine returned no executable stage.",
                )

            before = self._state_signature(state)
            if callback:
                callback(
                    state.current_stage.value,
                    {
                        "research_id": state.research_id,
                        "candidate_id": state.candidate_id,
                        "experiment_id": state.experiment_id,
                        "next_action": state.next_action,
                    },
                )

            state = await self._execute_stage_and_refresh(
                state,
                original_request=original_request,
            )

            if self._state_signature(state) == before and state.workflow_status == WorkflowStatus.CONTINUED:
                return self._execution_error(
                    intent=state.intent,
                    stage=state.current_stage or WorkflowStage.PROBLEM_EVALUATION,
                    research_id=state.research_id,
                    candidate_id=state.candidate_id,
                    experiment_id=state.experiment_id,
                    message=(
                        "Antigravity returned without advancing persisted discovery state. "
                        "Stopping to avoid a loop or fabricated transition."
                    ),
                )

        return self._execution_error(
            intent=state.intent,
            stage=state.current_stage or WorkflowStage.PROBLEM_EVALUATION,
            research_id=state.research_id,
            candidate_id=state.candidate_id,
            experiment_id=state.experiment_id,
            message=f"Stopped after {self.MAX_STAGE_STEPS} stage transitions to avoid an unbounded loop.",
        )

    async def _start_new_research(
        self,
        user_prompt: str,
        *,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> OrchestrationResult:
        matches = self.tools_provider.search_discovery(user_prompt, entity_type="CANDIDATE")
        if matches:
            existing_cid = matches[0]["entity_id"]
            candidate = self.tools_provider.get_candidate(existing_cid)
            if candidate.get("found"):
                initial = self.state_machine.evaluate_next_action(existing_cid)
                initial.intent = IntentType.NEW_RESEARCH
                initial.message = (
                    f"Reusing existing stable candidate {existing_cid} instead of duplicating the "
                    f"same root problem.\n\n{initial.message}"
                )
                return await self._run_existing_state_until_blocked(
                    initial, original_request=user_prompt, callback=callback
                )

        run_id = self._next_research_id()
        initial = OrchestrationResult(
            intent=IntentType.NEW_RESEARCH,
            research_id=run_id,
            current_stage=WorkflowStage.RESEARCH_PLANNING,
            action_taken="Reserved a research ID; no database row exists until planning persists it.",
            workflow_status=WorkflowStatus.CONTINUED,
            next_action="RUN_RESEARCH_PLANNING",
            message=f"Starting evidence-first discovery as {run_id}.",
        )
        return await self._run_existing_state_until_blocked(
            initial, original_request=user_prompt, callback=callback
        )

    async def _assess_experiment_submission(
        self,
        experiment_id: str,
        user_prompt: str,
    ) -> OrchestrationResult:
        conn = self.tools_provider._get_connection()
        try:
            row = conn.execute(
                "SELECT candidate_id, outcome_verdict FROM experiments WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
        finally:
            conn.close()

        if not row:
            return self._execution_error(
                intent=IntentType.EXPERIMENT_RESULT,
                stage=WorkflowStage.EXPERIMENT_VALIDATION,
                experiment_id=experiment_id,
                message=f"Experiment {experiment_id} does not exist in the discovery database.",
            )

        if row["outcome_verdict"] != "PREREGISTERED":
            result = self.state_machine.evaluate_next_action(row["candidate_id"])
            result.intent = IntentType.EXPERIMENT_RESULT
            return result

        state = OrchestrationResult(
            intent=IntentType.EXPERIMENT_RESULT,
            candidate_id=row["candidate_id"],
            experiment_id=experiment_id,
            current_stage=WorkflowStage.EXPERIMENT_VALIDATION,
            action_taken="Received user-supplied experiment result material.",
            workflow_status=WorkflowStatus.CONTINUED,
            next_action="ASSESS_LOCKED_EXPERIMENT",
            message=f"Assessing {experiment_id} against its locked contract.",
        )
        return await self._execute_stage_and_refresh(state, user_submission=user_prompt)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def run(self, user_prompt: str) -> OrchestrationResult:
        """Route the request and execute justified stages until blocked/completed."""
        classification: IntentClassification = self.router.route(user_prompt)

        if classification.intent == IntentType.DISCOVERY_QUERY:
            return self.state_machine.handle_query(classification.query_text)

        if classification.intent == IntentType.NEW_RESEARCH:
            return await self._start_new_research(user_prompt)

        if classification.intent == IntentType.RESUME_RUN:
            if not classification.research_id:
                return self._execution_error(
                    intent=IntentType.RESUME_RUN,
                    stage=WorkflowStage.RESEARCH_PLANNING,
                    message="Please specify a research run ID such as RUN-2026-001.",
                )
            initial = self.state_machine.evaluate_next_action(classification.research_id)
            initial.intent = IntentType.RESUME_RUN
            return await self._run_existing_state_until_blocked(initial)

        if classification.intent == IntentType.RESUME_CANDIDATE:
            if not classification.candidate_id:
                return self._execution_error(
                    intent=IntentType.RESUME_CANDIDATE,
                    stage=WorkflowStage.PROBLEM_EVALUATION,
                    message="Please specify a candidate ID such as CAND-001.",
                )
            initial = self.state_machine.evaluate_next_action(classification.candidate_id)
            initial.intent = IntentType.RESUME_CANDIDATE
            return await self._run_existing_state_until_blocked(initial)

        if classification.intent == IntentType.EXPERIMENT_RESULT:
            if not classification.experiment_id:
                return self._execution_error(
                    intent=IntentType.EXPERIMENT_RESULT,
                    stage=WorkflowStage.EXPERIMENT_VALIDATION,
                    message="Please specify the experiment ID whose real result you are submitting.",
                )
            return await self._assess_experiment_submission(
                classification.experiment_id,
                user_prompt,
            )

        return self._execution_error(
            intent=classification.intent,
            stage=WorkflowStage.READ_ONLY,
            message="Unable to classify request.",
        )

    async def chat(self, user_prompt: str) -> str:
        """User-facing natural language interface."""
        result = await self.run(user_prompt)
        return result.message

    async def run_until_blocked(
        self,
        problem_prompt: str,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> OrchestrationResult:
        """Start a new discovery request and continue only until a real gate blocks it."""
        classification = self.router.route(problem_prompt)
        if classification.intent != IntentType.NEW_RESEARCH:
            return await self.run(problem_prompt)
        return await self._start_new_research(problem_prompt, callback=callback)

    async def run_full_lifecycle(
        self,
        problem_prompt: str,
        domain: Optional[str] = None,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Backward-compatible safe alias.

        Historical versions fabricated evidence and a passing experiment to force all
        stages to complete. That behavior is intentionally removed. This method now
        runs the genuine workflow only until it becomes PAUSED, COMPLETED, or ERROR.
        The optional domain argument is retained for API compatibility but is not used
        to inject facts into the research plan.
        """
        _ = domain
        result = await self.run_until_blocked(problem_prompt, callback=callback)
        summary = result.to_summary_dict()
        summary["message"] = result.message
        summary["data"] = result.data
        return summary
