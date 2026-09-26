"""Command-line interface for the Problem Discovery Orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from agents.problem_discovery.agent import ProblemDiscoveryAgent
from agents.problem_discovery.config import ProblemDiscoveryConfig, get_default_db_path
from agents.problem_discovery.verdict import evaluate_all_candidates, evaluate_candidate


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m agents.problem_discovery.cli",
        description="Problem Discovery Orchestrator powered by Google Antigravity SDK.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Research request, resume instruction, experiment submission, or read-only query (or @path/to/prompt.txt).",
    )
    parser.add_argument(
        "--file",
        "-f",
        default=None,
        help="Path to text file containing research prompt (useful for detailed multi-line prompts).",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Override DISCOVERY_DB_PATH/canonical discovery-state data/discovery.sqlite.",
    )
    parser.add_argument(
        "--verdict",
        nargs="?",
        const="ALL",
        default=None,
        metavar="CANDIDATE_ID",
        help="Display SeyaliCraft Build Verdict (Go/No-Go) for candidate(s) in SQLite (e.g. --verdict or --verdict CAND-001).",
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
    args = parser.parse_args(argv)
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            parser.error(f"Prompt file not found: {args.file}")
        args.prompt = file_path.read_text(encoding="utf-8").strip()
    elif args.prompt and args.prompt.startswith("@"):
        file_path = Path(args.prompt[1:])
        if file_path.exists():
            args.prompt = file_path.read_text(encoding="utf-8").strip()
    return args


def _print_result(result, output_json: bool, agent: Optional[ProblemDiscoveryAgent] = None) -> None:
    verdict = None
    if agent and result.candidate_id:
        try:
            import sqlite3
            conn = sqlite3.connect(agent.config.db_path)
            conn.row_factory = sqlite3.Row
            try:
                verdict = evaluate_candidate(conn, result.candidate_id)
            finally:
                conn.close()
        except Exception:
            verdict = None

    if output_json:
        payload = result.to_summary_dict()
        payload["message"] = result.message
        if agent and (agent.session_input_tokens > 0 or agent.session_output_tokens > 0):
            payload["token_usage"] = {
                "input_tokens": agent.session_input_tokens,
                "output_tokens": agent.session_output_tokens,
                "total_tokens": agent.session_input_tokens + agent.session_output_tokens,
            }
        if verdict:
            payload["build_verdict"] = {
                "candidate_id": verdict.candidate_id,
                "decision": verdict.decision.value,
                "confidence": verdict.confidence,
                "recommended_shape": verdict.recommended_shape.value,
                "reversibility": verdict.reversibility,
                "justification": verdict.justification,
                "seyalicraft_fit": verdict.seyalicraft_fit,
                "next_steps": verdict.next_steps,
            }
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
    if agent and (agent.session_input_tokens > 0 or agent.session_output_tokens > 0):
        tot = agent.session_input_tokens + agent.session_output_tokens
        cost_usd = (agent.session_input_tokens / 1_000_000 * 0.10) + (agent.session_output_tokens / 1_000_000 * 0.40)
        cost_inr = cost_usd * 85.0
        print(f"TOKENS:    Input: {agent.session_input_tokens:,} | Output: {agent.session_output_tokens:,} | Total: {tot:,} (~₹{cost_inr:.2f})")
    print("=" * 60)
    print(f"\n{result.message}\n")

    if verdict:
        print(verdict.format_terminal_card() + "\n")


async def run_single(
    prompt: str,
    db_path: Optional[str],
    output_json: bool,
    until_blocked: bool = False,
) -> int:
    from datetime import datetime

    config = ProblemDiscoveryConfig(db_path=str(db_path or get_default_db_path()))
    agent = ProblemDiscoveryAgent(config=config)

    if not output_json:
        print("\n" + "=" * 64)
        print("  PROBLEM DISCOVERY ORCHESTRATOR")
        print(f"  Active Database : {config.db_path}")
        print(f"  Reasoning Model : {config.model}")
        print("=" * 64 + "\n", flush=True)

    if until_blocked:
        def on_stage(stage: str, data: dict) -> None:
            if not output_json:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] [{stage}] {data}", flush=True)

        result = await agent.run_until_blocked(prompt, callback=on_stage)
    else:
        result = await agent.run(prompt)

    _print_result(result, output_json, agent=agent)
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

    if args.verdict:
        db_path = str(args.db_path or get_default_db_path())
        if args.verdict == "ALL":
            verdicts = evaluate_all_candidates(db_path)
            if not verdicts:
                print(f"\nNo candidates found in database: {db_path}\n")
                return 0
            for v in verdicts:
                print("\n" + v.format_terminal_card())
            return 0
        else:
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                v = evaluate_candidate(conn, args.verdict)
                if not v:
                    print(f"\nCandidate '{args.verdict}' not found in database: {db_path}\n", file=sys.stderr)
                    return 1
                print("\n" + v.format_terminal_card())
                return 0
            finally:
                conn.close()

    if args.interactive or (not args.prompt and not args.until_blocked and not args.json):
        return asyncio.run(run_interactive(db_path=args.db_path))

    prompt = args.prompt or (
        "Frontend developers and QA engineers frequently waste hours debugging API schema mismatches "
        "when backend REST/GraphQL responses deviate from OpenAPI or TypeScript contract types in staging environments. "
        "Research whether this schema drift is a recurring operational bottleneck, what manual workarounds teams use, "
        "and whether existing tools solve it without heavy enterprise gateways."
    )

    return asyncio.run(
        run_single(
            prompt=prompt,
            db_path=args.db_path,
            output_json=args.json,
            until_blocked=args.until_blocked,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
