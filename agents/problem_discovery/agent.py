"""Problem Discovery Orchestrator Agent using the official Google Antigravity Python SDK.

The orchestrator is intentionally thin:
- deterministic code chooses the next persisted workflow stage,
- Antigravity + the loaded modular skill performs that stage,
- custom discovery-state tools are the only mutation path,
- SQLite is re-read after every stage,
- real-world experiments always pause instead of being fabricated.
"""

from __future__ import annotations

import asyncio
import re
import sys
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
    get_stage_skills_paths,
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
from agents.problem_discovery.orchestration.preconditions import (
    validate_stage_preconditions,
    verify_stage_postconditions,
)
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
        self.session_input_tokens: int = 0
        self.session_output_tokens: int = 0
        self.session_thinking_tokens: int = 0
        self.session_total_tokens: int = 0

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

    def build_sdk_config(
        self,
        stage: Optional[WorkflowStage] = None,
        mode: Optional[str] = None,
    ) -> Any:
        """Build the official Antigravity LocalAgentConfig with least privilege.

        When stage is specified, only read tools and the single authorized mutation tool
        for that stage are registered.
        """
        if not ANTIGRAVITY_AVAILABLE:
            raise RuntimeError(
                "google-antigravity is not installed. Install it before executing reasoning stages."
            )

        stage_val = stage.value if hasattr(stage, "value") else str(stage) if stage else None
        if stage_val == "EVIDENCE_RESEARCH":
            enabled_caps = [
                BuiltinTools.SEARCH_WEB,
                BuiltinTools.READ_URL_CONTENT,
            ]
        elif stage is None:
            enabled_caps = [
                BuiltinTools.VIEW_FILE,
                BuiltinTools.READ_URL_CONTENT,
                BuiltinTools.SEARCH_WEB,
            ]
        else:
            # Deterministic reasoning stages operate purely on bounded SQLite context packs.
            # Disabling VIEW_FILE prevents massive token bloat from recursive reference reading.
            enabled_caps = []

        trunc_config = types.ToolOutputTruncationConfig(max_tokens=3000) if types else None
        capabilities = types.CapabilitiesConfig(
            enabled_tools=enabled_caps,
            tool_output_truncation_config=trunc_config,
        )
        policies = [
            policy.deny("run_command"),
            policy.deny("create_file"),
            policy.deny("edit_file"),
            policy.allow("*"),
        ]

        stage_tools = (
            self.tools_provider.get_stage_tools(stage=stage, mode=mode)
            if stage is not None
            else self.tools_provider.get_all_tools()
        )

        return LocalAgentConfig(
            system_instructions=get_system_prompt(self.config.system_instruction_path),
            tools=stage_tools,
            skills_paths=self.config.skills_paths or get_stage_skills_paths(stage),
            capabilities=capabilities,
            policies=policies,
            model=self.config.model,
            api_key=self.config.api_key,
        )

    def create_sdk_agent(
        self,
        stage: Optional[WorkflowStage] = None,
        mode: Optional[str] = None,
    ) -> Any:
        return Agent(self.build_sdk_config(stage=stage, mode=mode))

    async def __aenter__(self) -> "ProblemDiscoveryAgent":
        # Keep read-only SQLite usage available without model credentials.
        # Reasoning stages will still fail explicitly rather than fabricate data.
        if not ANTIGRAVITY_AVAILABLE or not self.config.api_key:
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

    async def _chat_sdk(
        self,
        prompt: str,
        stage: Optional[WorkflowStage] = None,
        mode: Optional[str] = None,
    ) -> str:
        """Execute one bounded reasoning turn through the real Antigravity Agent with rate-limit backoff."""
        if not ANTIGRAVITY_AVAILABLE:
            raise RuntimeError(
                "Reasoning stage execution requires the google-antigravity package. "
                "No synthetic fallback is permitted."
            )

        max_retries = 3
        stage_val = stage.value if hasattr(stage, "value") else str(stage) if stage else None
        timeout_seconds = 300.0 if stage_val == "EVIDENCE_RESEARCH" else 180.0
        for attempt in range(max_retries):
            try:
                async def _invoke(target_agent: Any) -> tuple[str, Any]:
                    resp = await target_agent.chat(prompt)
                    text_parts = []
                    async for chunk in resp.chunks:
                        if types and isinstance(chunk, types.ToolCall):
                            now_ts = datetime.now().strftime("%H:%M:%S")
                            args_repr = ""
                            if hasattr(chunk, "args") and isinstance(chunk.args, dict) and chunk.args:
                                if "query" in chunk.args:
                                    args_repr = f'(query="{chunk.args["query"]}")'
                                elif "url" in chunk.args:
                                    args_repr = f'(url="{chunk.args["url"]}")'
                                elif "research_id" in chunk.args and len(chunk.args) <= 2:
                                    args_repr = f'(research_id="{chunk.args["research_id"]}")'
                                elif "candidate_id" in chunk.args and len(chunk.args) <= 2:
                                    args_repr = f'(candidate_id="{chunk.args["candidate_id"]}")'
                                elif len(chunk.args) == 1:
                                    k, v = next(iter(chunk.args.items()))
                                    val_str = str(v)
                                    if len(val_str) > 50:
                                        val_str = val_str[:47] + "..."
                                    args_repr = f'({k}={val_str!r})'
                            print(
                                f"[{now_ts}]   [Stage Tool Dispatched] Invoking `{chunk.name}{args_repr}`...",
                                flush=True,
                            )
                        elif types and isinstance(chunk, types.Text):
                            text_parts.append(chunk.text)
                    txt = "".join(text_parts) if text_parts else await resp.text()
                    return txt, getattr(resp, "usage_metadata", None)

                if self._sdk_agent is not None:
                    text_content, meta = await asyncio.wait_for(
                        _invoke(self._sdk_agent), timeout=timeout_seconds
                    )
                else:
                    async with self.create_sdk_agent(stage=stage, mode=mode) as agent:
                        text_content, meta = await asyncio.wait_for(
                            _invoke(agent), timeout=timeout_seconds
                        )

                if meta is not None:
                    inp = getattr(meta, "prompt_token_count", 0) or 0
                    out = getattr(meta, "candidates_token_count", 0) or 0
                    thn = getattr(meta, "thoughts_token_count", 0) or 0
                    tot = getattr(meta, "total_token_count", 0) or (inp + out + thn)
                    self.session_input_tokens += inp
                    self.session_output_tokens += out
                    self.session_thinking_tokens += thn
                    self.session_total_tokens += tot
                    cost_usd = (inp / 1_000_000 * 0.10) + ((out + thn) / 1_000_000 * 0.40)
                    cost_inr = cost_usd * 85.0
                    now_ts = datetime.now().strftime("%H:%M:%S")
                    detail = f"Input: {inp:,} | Output: {out:,}"
                    if thn > 0:
                        detail += f" | Thinking: {thn:,}"
                    detail += f" | Total: {tot:,} tokens (~₹{cost_inr:.3f})"
                    print(
                        f"[{now_ts}]   [Tokens] {detail}",
                        flush=True,
                    )

                return text_content
            except (asyncio.TimeoutError, TimeoutError):
                now_ts = datetime.now().strftime("%H:%M:%S")
                if attempt < max_retries - 1:
                    print(
                        f"\n[{now_ts}]   [Network / API Timeout: Gemini did not respond within {int(timeout_seconds)}s. Retrying attempt {attempt + 2}/{max_retries}...]",
                        file=sys.stderr,
                        flush=True,
                    )
                    await asyncio.sleep(5)
                    continue
                raise TimeoutError(f"Gemini API request timed out after {max_retries} attempts.")
            except Exception as exc:
                err_str = str(exc)
                is_rate_limit = any(k in err_str for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"))
                if is_rate_limit and attempt < max_retries - 1:
                    match = re.search(r"retry(?:Delay:\s*|.*?in\s*)([0-9]+)", err_str, re.IGNORECASE)
                    wait_sec = int(match.group(1)) + 2 if match else 25
                    wait_sec = max(5, min(wait_sec, 60))
                    print(
                        f"\n[Gemini Free Tier Rate Limit / High Demand. Waiting {wait_sec}s for quota reset (attempt {attempt + 1}/{max_retries})...]",
                        file=sys.stderr,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                raise

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
            if not original_request and research_id:
                conn = self.tools_provider._get_connection()
                try:
                    row = conn.execute(
                        "SELECT original_request FROM research_runs WHERE research_id=?", (research_id,)
                    ).fetchone()
                    if row and row["original_request"]:
                        original_request = row["original_request"]
                finally:
                    conn.close()
            if not research_id or not original_request:
                raise ValueError("Research planning requires research_id and original_request")
            return header + f"""
Use the research-planning skill.

Reserved research_id: {research_id}
Original user request:
{original_request}

Create a valid ResearchPlan from the user's actual request. Do not invent empirical facts.
Geography remains unknown/null unless supplied.

CRITICAL INSTRUCTIONS:
1. You MUST invoke the custom tool `create_research_run` with arguments:
   - research_id="{research_id}"
   - request="{original_request}"
   - plan_dict={{...your generated ResearchPlan...}}
2. TERMINATION RULE: Once `create_research_run` completes, STOP immediately. Do NOT call read tools (`get_discovery_run`, `get_discovery_dashboard`, etc.) to re-verify state. Provide a brief 1-sentence confirmation and conclude your turn.
"""

        if stage == WorkflowStage.EVIDENCE_RESEARCH:
            return header + f"""
Use the evidence-research skill for research_id={research_id}.

Load the persisted ResearchPlan first using `get_discovery_run(research_id="{research_id}")`.

EXECUTION SEQUENCE & HARD QUANTITATIVE BUDGET:
1. Review the search queries in the research plan streams.
2. Execute at most 2 or 3 high-precision web searches using `search_web`.
3. Inspect at most 2 authoritative URLs using `read_url_content` to extract authentic practitioner testimony and workarounds.
4. Normalize 2 to 4 authentic ResearchSignals (each signal containing signal_id, source_url, observed_actor, evidence, etc.).
5. Immediately persist them by calling `save_evidence_signals(research_id="{research_id}", signals=[...])`.
6. TERMINATION RULE: Once `save_evidence_signals` completes, provide a brief 2-sentence summary and STOP immediately. Do NOT perform additional searches, URL reads, or database re-verification calls.

CRITICAL INSTRUCTIONS:
- Do NOT browse local files; focus directly on live web research.
- Never invent URLs, quotes, metrics, or actor identities.
- Persist signals through `save_evidence_signals` to advance the workflow stage to PROBLEM_EVALUATION.
"""

        if stage == WorkflowStage.PROBLEM_EVALUATION:
            reserved_candidate = candidate_id or self._next_candidate_id()
            rid_param = f'research_id="{research_id}"' if research_id else ""
            return header + f"""
Use the problem-evaluation skill.

research_id={research_id or 'resolve from candidate/state'}
candidate_id={candidate_id or 'not assigned yet'}
next_action={next_action or 'RUN_PROBLEM_EVALUATION'}
reserved_new_candidate_id={reserved_candidate}

EXECUTION SEQUENCE:
1. Invoke `build_problem_evaluation_context({rid_param})` to load all signals and context.
2. Group the signals into distinct problem candidate(s). Reuse an existing stable candidate when it matches the same actor/task/friction/root workflow. If a new candidate is justified, use reserved_new_candidate_id.
3. Unsupported workflow nodes remain UNKNOWN. Root causes remain hypotheses unless supported. Score is research priority, not validation.
4. Call `upsert_candidate(...)` to persist each candidate with its exact supporting signal IDs.
5. CRITICAL TERMINATION RULE: Once `upsert_candidate` succeeds, STOP immediately. Do NOT call any read tools (`get_candidate`, `get_discovery_run`, etc.) to re-verify state. Provide a concise 2-sentence summary and conclude your turn.
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

        # Strict Stage Precondition Gate
        target_id = state.candidate_id or state.research_id
        precond = validate_stage_preconditions(
            stage,
            identifier=target_id,
            prompt=user_submission or original_request,
            db_path=self.config.db_path,
        )
        if not precond.allowed:
            return OrchestrationResult(
                intent=state.intent,
                research_id=state.research_id,
                candidate_id=state.candidate_id,
                experiment_id=state.experiment_id,
                current_stage=stage,
                action_taken="Stage execution blocked by strict precondition monitor.",
                workflow_status=WorkflowStatus.PAUSED if precond.current_stage == WorkflowStage.PAUSED else WorkflowStatus.ERROR,
                pause_reason="PRECONDITION_FAILED",
                next_action=precond.required_fix or "RESOLVE_STAGE_PRECONDITION",
                message=(
                    f"BLOCKED: Stage Precondition Failed for {stage.value}.\n\n"
                    f"Reason: {precond.reason}\n"
                    f"Required Action: {precond.required_fix}"
                ),
                data={"precondition_diagnostics": precond.diagnostics},
            )

        prompt = self._build_stage_prompt(
            stage,
            research_id=state.research_id,
            candidate_id=state.candidate_id,
            experiment_id=state.experiment_id,
            original_request=original_request,
            user_submission=user_submission,
            next_action=state.next_action,
        )

        now_ts = datetime.now().strftime("%H:%M:%S")
        if stage == WorkflowStage.EVIDENCE_RESEARCH:
            print(f"[{now_ts}]   --> [Stage: {stage.value}] Gemini is searching the web and qualifying evidence signals (takes ~30-60s)...", flush=True)
        else:
            print(f"[{now_ts}]   --> [Stage: {stage.value}] Gemini reasoning in progress...", flush=True)

        try:
            mode = "ASSESS" if user_submission is not None else "DESIGN"
            try:
                model_text = await self._chat_sdk(prompt, stage=stage, mode=mode)
            except TypeError as type_err:
                if "unexpected keyword argument" in str(type_err):
                    model_text = await self._chat_sdk(prompt)
                else:
                    raise
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

        # Post-Stage Quality Verification
        post_verify = verify_stage_postconditions(stage, identifier=identifier, db_path=self.config.db_path)
        if not post_verify.verified:
            return self._execution_error(
                intent=state.intent,
                stage=stage,
                research_id=state.research_id,
                candidate_id=state.candidate_id,
                experiment_id=state.experiment_id,
                message=f"Stage post-verification failed: {post_verify.message}",
            )
        if post_verify.warnings:
            refreshed.data["stage_warnings"] = post_verify.warnings

        return refreshed

    async def _run_existing_state_until_blocked(
        self,
        initial: OrchestrationResult,
        *,
        original_request: Optional[str] = None,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        single_stage: bool = False,
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

            if state.candidate_id:
                legacy = self.tools_provider.detect_legacy_synthetic_state(state.candidate_id)
                if legacy.get("detected"):
                    records = legacy.get("records", [])
                    experiment_ids = ", ".join(
                        str(record.get("experiment_id")) for record in records
                    )
                    return OrchestrationResult(
                        intent=state.intent,
                        research_id=state.research_id,
                        candidate_id=state.candidate_id,
                        experiment_id=state.experiment_id,
                        current_stage=state.current_stage,
                        action_taken="Blocked execution because legacy synthetic state was detected.",
                        workflow_status=WorkflowStatus.ERROR,
                        next_action="AUDIT_OR_RESET_LEGACY_SYNTHETIC_STATE",
                        message=(
                            "This candidate contains the exact fingerprint of the removed synthetic "
                            f"end-to-end demo experiment ({experiment_ids}). No further reasoning or "
                            "solution finalization was executed. Audit/reset that legacy test data, "
                            "then resume the candidate."
                        ),
                        data={"legacy_synthetic_state": legacy},
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

            if single_stage:
                state.workflow_status = WorkflowStatus.PAUSED
                return state

            if self._state_signature(state) == before and state.workflow_status == WorkflowStatus.CONTINUED:
                model_reply = state.data.get("stage_agent_response", "") if state.data else ""
                err_msg = (
                    "Antigravity returned without advancing persisted discovery state. "
                    "Stopping to avoid a loop or fabricated transition."
                )
                if model_reply:
                    err_msg += f"\n\nModel reasoning output:\n{model_reply}"
                return self._execution_error(
                    intent=state.intent,
                    stage=state.current_stage or WorkflowStage.PROBLEM_EVALUATION,
                    research_id=state.research_id,
                    candidate_id=state.candidate_id,
                    experiment_id=state.experiment_id,
                    message=err_msg,
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
        single_stage: bool = False,
    ) -> OrchestrationResult:
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
            initial, original_request=user_prompt, callback=callback, single_stage=single_stage
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

        if row["outcome_verdict"] not in ("PREREGISTERED", "INCOMPLETE"):
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

    async def run(
        self,
        user_prompt: str,
        *,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        single_stage: bool = False,
    ) -> OrchestrationResult:
        """Route the request and execute justified stages until blocked/completed."""
        classification: IntentClassification = self.router.route(user_prompt)

        if classification.intent == IntentType.DISCOVERY_QUERY:
            return self.state_machine.handle_query(classification.query_text)

        if classification.intent == IntentType.NEW_RESEARCH:
            return await self._start_new_research(
                user_prompt, callback=callback, single_stage=single_stage
            )

        if classification.intent == IntentType.RESUME_RUN:
            if not classification.research_id:
                return self._execution_error(
                    intent=IntentType.RESUME_RUN,
                    stage=WorkflowStage.RESEARCH_PLANNING,
                    message="Please specify a research run ID such as RUN-2026-001.",
                )
            target_stage_str = classification.extracted_parameters.get("target_stage")
            if target_stage_str:
                target_stage = WorkflowStage(target_stage_str)
                precond = validate_stage_preconditions(
                    target_stage,
                    identifier=classification.research_id,
                    prompt=user_prompt,
                    db_path=self.config.db_path,
                )
                if not precond.allowed:
                    return OrchestrationResult(
                        intent=IntentType.RESUME_RUN,
                        research_id=classification.research_id,
                        current_stage=precond.current_stage or target_stage,
                        action_taken="Stage execution blocked by strict precondition monitor.",
                        workflow_status=WorkflowStatus.PAUSED if precond.current_stage == WorkflowStage.PAUSED else WorkflowStatus.ERROR,
                        pause_reason="PRECONDITION_FAILED",
                        next_action=precond.required_fix or "RESOLVE_STAGE_PRECONDITION",
                        message=(
                            f"BLOCKED: Stage Precondition Failed for {target_stage.value}.\n\n"
                            f"Reason: {precond.reason}\n"
                            f"Required Action: {precond.required_fix}"
                        ),
                        data={"precondition_diagnostics": precond.diagnostics},
                    )
                initial = self.state_machine.evaluate_next_action(classification.research_id)
                initial.intent = IntentType.RESUME_RUN
                initial.current_stage = target_stage
                initial.workflow_status = WorkflowStatus.CONTINUED
                return await self._run_existing_state_until_blocked(
                    initial, callback=callback, single_stage=single_stage
                )

            initial = self.state_machine.evaluate_next_action(classification.research_id)
            initial.intent = IntentType.RESUME_RUN
            return await self._run_existing_state_until_blocked(
                initial, callback=callback, single_stage=single_stage
            )

        if classification.intent == IntentType.RESUME_CANDIDATE:
            if not classification.candidate_id:
                return self._execution_error(
                    intent=IntentType.RESUME_CANDIDATE,
                    stage=WorkflowStage.PROBLEM_EVALUATION,
                    message="Please specify a candidate ID such as CAND-001.",
                )
            target_stage_str = classification.extracted_parameters.get("target_stage")
            if target_stage_str:
                target_stage = WorkflowStage(target_stage_str)
                precond = validate_stage_preconditions(
                    target_stage,
                    identifier=classification.candidate_id,
                    prompt=user_prompt,
                    db_path=self.config.db_path,
                )
                if not precond.allowed:
                    return OrchestrationResult(
                        intent=IntentType.RESUME_CANDIDATE,
                        candidate_id=classification.candidate_id,
                        current_stage=precond.current_stage or target_stage,
                        action_taken="Stage execution blocked by strict precondition monitor.",
                        workflow_status=WorkflowStatus.PAUSED if precond.current_stage == WorkflowStage.PAUSED else WorkflowStatus.ERROR,
                        pause_reason="PRECONDITION_FAILED",
                        next_action=precond.required_fix or "RESOLVE_STAGE_PRECONDITION",
                        message=(
                            f"BLOCKED: Stage Precondition Failed for {target_stage.value}.\n\n"
                            f"Reason: {precond.reason}\n"
                            f"Required Action: {precond.required_fix}"
                        ),
                        data={"precondition_diagnostics": precond.diagnostics},
                    )
                initial = self.state_machine.evaluate_next_action(classification.candidate_id)
                initial.intent = IntentType.RESUME_CANDIDATE
                initial.current_stage = target_stage
                initial.workflow_status = WorkflowStatus.CONTINUED
                return await self._run_existing_state_until_blocked(
                    initial, callback=callback, single_stage=single_stage
                )

            initial = self.state_machine.evaluate_next_action(classification.candidate_id)
            initial.intent = IntentType.RESUME_CANDIDATE
            return await self._run_existing_state_until_blocked(
                initial, callback=callback, single_stage=single_stage
            )

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
