"""Command-Line Interface for the Problem Discovery Orchestrator Agent."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

from agents.problem_discovery.agent import ProblemDiscoveryAgent
from agents.problem_discovery.config import ProblemDiscoveryConfig, get_default_db_path


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m agents.problem_discovery.cli",
        description="Problem Discovery Orchestrator CLI powered by Google Antigravity SDK.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Natural language instruction, research request, continue command, or discovery query.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Override SQLite database path (default: DISCOVERY_DB_PATH or canonical data/discovery.sqlite).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw machine-readable orchestration JSON contract instead of formatted text.",
    )
    parser.add_argument(
        "--end-to-end",
        "-e",
        action="store_true",
        help="Execute all 5 stages of the Problem Discovery lifecycle end-to-end in a single command.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Launch an interactive terminal session.",
    )
    return parser.parse_args(argv)


async def run_single(
    prompt: str, db_path: Optional[str], output_json: bool, end_to_end: bool = False
) -> int:
    config = ProblemDiscoveryConfig(db_path=str(db_path or get_default_db_path()))
    agent = ProblemDiscoveryAgent(config=config)

    if end_to_end:
        def on_stage_progress(stage: str, data: dict) -> None:
            if not output_json:
                print(f"[{stage}] {data}")

        summary = await agent.run_full_lifecycle(prompt, callback=on_stage_progress)
        if output_json:
            print(json.dumps(summary, indent=2))
        else:
            print("\n" + "=" * 60)
            print(" ALL 5 STAGES COMPLETED & PERSISTED TO SQLITE")
            print("=" * 60)
            for k, v in summary.items():
                print(f"{k:20}: {v}")
            print("=" * 60 + "\n")
        return 0

    result = await agent.run(prompt)

    if output_json:
        print(json.dumps(result.to_summary_dict(), indent=2))
    else:
        print("\n" + "=" * 60)
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

    return 0 if result.workflow_status.value != "ERROR" else 1


async def run_interactive(db_path: Optional[str]) -> int:
    config = ProblemDiscoveryConfig(db_path=str(db_path or get_default_db_path()))
    agent = ProblemDiscoveryAgent(config=config)

    print("\n" + "=" * 65)
    print(" Problem Discovery Orchestrator Agent (Interactive Session)")
    print(f" Database: {agent.db_path}")
    print(" Type 'exit' or 'quit' to end the session.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("discovery> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Exiting Problem Discovery Orchestrator. Goodbye!")
                break

            result = await agent.run(user_input)
            print("\n" + "-" * 50)
            print(f"[{result.workflow_status.value}] Stage: {result.current_stage.value if result.current_stage else 'N/A'}")
            print("-" * 50)
            print(result.message)
            print()

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            print(f"\nError: {e}\n", file=sys.stderr)

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.end_to_end:
        prompt = args.prompt or (
            "Frontend developers and QA engineers frequently waste hours debugging API schema mismatches "
            "when backend REST/GraphQL responses deviate from OpenAPI or TypeScript contract types in staging environments. "
            "Research whether this schema drift is a recurring operational bottleneck, what manual workarounds teams use, "
            "and whether existing tools solve it without heavy enterprise gateways."
        )
        return asyncio.run(
            run_single(prompt=prompt, db_path=args.db_path, output_json=args.json, end_to_end=True)
        )

    if args.interactive or not args.prompt:
        return asyncio.run(run_interactive(db_path=args.db_path))

    return asyncio.run(
        run_single(prompt=args.prompt, db_path=args.db_path, output_json=args.json, end_to_end=False)
    )


if __name__ == "__main__":
    sys.exit(main())
