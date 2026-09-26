"""Command-line interface for the Problem Discovery Orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Optional

from agents.problem_discovery.agent import ProblemDiscoveryAgent
from agents.problem_discovery.config import ProblemDiscoveryConfig, get_default_db_path


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m agents.problem_discovery.cli",
        description="Problem Discovery Orchestrator powered by Google Antigravity SDK.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Research request, resume instruction, experiment submission, or read-only query.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Override DISCOVERY_DB_PATH/canonical discovery-state data/discovery.sqlite.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable orchestration metadata.",
    )
    parser.add_argument(
        "--until-blocked",
        "--end-to-end",
        "-e",
        dest="until_blocked",
        action="store_true",
        help=(
            "Run justified stages until the workflow pauses, completes, or errors. "
            "--end-to-end is retained as a compatibility alias; real-world experiments are never fabricated."
        ),
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Launch an interactive terminal session.",
    )
    return parser.parse_args(argv)


def _print_result(result, output_json: bool) -> None:
    if output_json:
        payload = result.to_summary_dict()
        payload["message"] = result.message
        print(json.dumps(payload, indent=2))
        return

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


async def run_single(
    prompt: str,
    db_path: Optional[str],
    output_json: bool,
    until_blocked: bool = False,
) -> int:
    config = ProblemDiscoveryConfig(db_path=str(db_path or get_default_db_path()))
    agent = ProblemDiscoveryAgent(config=config)

    if until_blocked:
        def on_stage(stage: str, data: dict) -> None:
            if not output_json:
                print(f"[{stage}] {data}")

        result = await agent.run_until_blocked(prompt, callback=on_stage)
    else:
        result = await agent.run(prompt)

    _print_result(result, output_json)
    return 0 if result.workflow_status.value != "ERROR" else 1


async def run_interactive(db_path: Optional[str]) -> int:
    config = ProblemDiscoveryConfig(db_path=str(db_path or get_default_db_path()))

    print("\n" + "=" * 65)
    print(" Problem Discovery Orchestrator Agent")
    print(f" Database: {config.db_path}")
    print(" Type 'exit' or 'quit' to end the session.")
    print("=" * 65 + "\n")

    async with ProblemDiscoveryAgent(config=config) as agent:
        while True:
            try:
                user_input = input("discovery> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"exit", "quit", "q"}:
                    break

                result = await agent.run(user_input)
                _print_result(result, output_json=False)
            except (KeyboardInterrupt, EOFError):
                print("\nSession interrupted.")
                break
            except Exception as exc:
                print(f"\nError: {exc}\n", file=sys.stderr)

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.interactive or not args.prompt:
        return asyncio.run(run_interactive(db_path=args.db_path))

    return asyncio.run(
        run_single(
            prompt=args.prompt,
            db_path=args.db_path,
            output_json=args.json,
            until_blocked=args.until_blocked,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
