"""Direct runnable runner for the Problem Discovery Orchestrator Agent."""

import asyncio
import sys
from pathlib import Path

# Ensure toolkit root is in sys.path
TOOLKIT_ROOT = Path(__file__).resolve().parents[2]
if str(TOOLKIT_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLKIT_ROOT))

from agents.problem_discovery import (
    ProblemDiscoveryAgent,
    ProblemDiscoveryConfig,
    WorkflowStatus,
)


async def main():
    print("=" * 70)
    print(" Problem Discovery Orchestrator Agent")
    print(f" Repository: {TOOLKIT_ROOT}")
    print("=" * 70)

    config = ProblemDiscoveryConfig()
    agent = ProblemDiscoveryAgent(config=config)
    tools = agent.tools_provider

    # If user asked for full end-to-end lifecycle run
    if "--end-to-end" in sys.argv or "-e" in sys.argv:
        args = [a for a in sys.argv[1:] if a not in ("--end-to-end", "-e")]
        prompt = " ".join(args).strip() if args else (
            "Frontend developers and QA engineers frequently waste hours debugging API schema mismatches "
            "when backend REST/GraphQL responses deviate from OpenAPI or TypeScript contract types in staging environments. "
            "Research whether this schema drift is a recurring operational bottleneck, what manual workarounds teams use, "
            "and whether existing tools solve it without heavy enterprise gateways."
        )

        print("\n" + "=" * 70)
        print(" FULL PROBLEM DISCOVERY LIFECYCLE (All 5 Stages)")
        print(f" Database: {config.db_path}")
        print(f" Request:  \"{prompt[:90]}...\"")
        print("=" * 70 + "\n")

        def on_stage_progress(stage: str, data: dict) -> None:
            if stage == "RESEARCH_PLANNING":
                print(f"[STAGE 1: RESEARCH_PLANNING]     --> Initialized Run: {data['research_id']} | Domain: {data['domain']}")
            elif stage == "EVIDENCE_RESEARCH":
                print(f"[STAGE 2: EVIDENCE_RESEARCH]     --> Persisted {data['signals_count']} Qualified Evidence Signals")
            elif stage == "PROBLEM_EVALUATION":
                print(f"[STAGE 3: PROBLEM_EVALUATION]    --> Formulated Candidate: {data['candidate_id']} | Score: {data['score']}/35")
            elif stage == "EXPERIMENT_PREREGISTERED":
                print(f"[STAGE 4: EXPERIMENT_VALIDATION]  --> Preregistered Contract: {data['experiment_id']} (Metric: {data['metric']} >= {data['threshold']})")
            elif stage == "EXPERIMENT_ASSESSED":
                print(f"[STAGE 4: EXPERIMENT_AUDIT]       --> Trial Passed: {data['verdict']} (Observed: {data['observed_value']}) -> Candidate VALIDATED")
            elif stage == "SOLUTION_STRATEGY":
                print(f"[STAGE 5: SOLUTION_STRATEGY]     --> Finalized Justified Shape: {data['solution_class']}")
            elif stage == "COMPLETED":
                print(f"[STAGE 6: COMPLETION GATE]       --> Verified State Machine: Status={data['status']}\n")

        summary = await agent.run_full_lifecycle(prompt, callback=on_stage_progress)

        print("=" * 70)
        print(" ALL STAGES COMPLETED & PERSISTED TO SQLITE!")
        print("=" * 70)
        print(f"Research Run:       {summary['research_id']} ({summary['domain']})")
        print(f"Evidence Signals:   {summary['signals_count']} rows in evidence_signals")
        print(f"Candidate:          {summary['candidate_id']} - {summary['candidate_title']}")
        print(f"Candidate Score:    {summary['candidate_score']}/35 (VALIDATED)")
        print(f"Experiment:         {summary['experiment_id']} - {summary['experiment_verdict']}")
        print(f"Solution Class:     {summary['solution_class']}")
        print(f"Lifecycle Status:   {summary['workflow_status']}")
        print("=" * 70 + "\n")
        return

    # If user provided a command line prompt, run it
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
        print(f"\n[Running User Prompt]: \"{user_prompt}\"\n")
        result = await agent.run(user_prompt)
        print("=" * 60)
        print(f"INTENT:    {result.intent.value}")
        print(f"STAGE:     {result.current_stage.value if result.current_stage else 'N/A'}")
        print(f"STATUS:    {result.workflow_status.value}")
        if result.research_id:
            print(f"RUN ID:    {result.research_id}")
        if result.candidate_id:
            print(f"CAND ID:   {result.candidate_id}")
        if result.experiment_id:
            print(f"EXP ID:    {result.experiment_id}")
        if result.pause_reason:
            print(f"PAUSED:    {result.pause_reason}")
        print("=" * 60)
        print(f"\n{result.message}\n")
        return

    # Default demonstration
    print(f"\n[Active SQLite Database]: {config.db_path}\n")

    # 1. Query existing research runs in the active database
    query_prompt = "RUN-2026-001 current status enna?"
    print(f"[1. Status Query for Existing Run]: \"{query_prompt}\"")
    query_res = await agent.run(query_prompt)
    print(f"-> Intent: {query_res.intent.value} | Status: {query_res.workflow_status.value}")
    print(f"{query_res.message}\n")

    # 2. Candidate Resume / Lifecycle Check
    cand_prompt = "CAND-001 resume pannu"
    print(f"[2. Candidate Resume / State Gate Check]: \"{cand_prompt}\"")
    cand_res = await agent.run(cand_prompt)
    print(f"-> Intent: {cand_res.intent.value} | Stage: {cand_res.current_stage.value} | Status: {cand_res.workflow_status.value}")
    if cand_res.pause_reason:
        print(f"-> Pause Reason: {cand_res.pause_reason}")
    print(f"{cand_res.message}\n")

    # 3. New Research Run Intent Demonstration (Dry Run routing)
    new_request = "Autonomous vehicle fleet dispatch routing in severe monsoon floods"
    print(f"[3. New Research Intent Routing]: \"{new_request}\"")
    route_res = await agent.run(new_request)
    print(f"-> Intent: {route_res.intent.value} | Target Stage: {route_res.current_stage.value} | Assigned Run ID: {route_res.research_id}")
    print(f"{route_res.message}")

    print("\n" + "=" * 70)
    print(" Problem Discovery Orchestrator ready in ai-agent-toolkit/agents!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
