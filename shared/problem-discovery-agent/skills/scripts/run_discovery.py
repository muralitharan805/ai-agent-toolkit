# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Automated orchestration runner for the Problem Discovery lifecycle.

Coordinates lifecycle inspection, context pack generation, and dashboard queries.
Emits structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def resolve_paths() -> tuple[Path, Path, Path]:
    """Resolve paths to repo root, state script, and default db."""
    current = Path(__file__).resolve()
    # Find repo root
    repo_root = current.parents[4]
    state_builder = (
        repo_root
        / "shared"
        / "problem-discovery-suites"
        / "discovery-state"
        / "skills"
        / "scripts"
        / "build_agent_context.py"
    )
    default_db = (
        repo_root
        / "shared"
        / "problem-discovery-suites"
        / "discovery-state"
        / "data"
        / "discovery.sqlite"
    )
    return repo_root, state_builder, default_db


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Problem Discovery Orchestrator runner."
    )
    parser.add_argument("request", nargs="?", default="", help="User request or command string.")
    parser.add_argument("--db", type=str, help="Path to SQLite database.")
    parser.add_argument("--run-id", type=str, help="Specific research run ID.")
    parser.add_argument("--candidate-id", type=str, help="Specific candidate ID.")
    parser.add_argument("--prepare-context", action="store_true", help="Automatically generate the bounded context pack.")
    parser.add_argument("--status", action="store_true", help="Display discovery dashboard overview.")

    args = parser.parse_args()

    repo_root, state_builder, default_db = resolve_paths()
    db_path = Path(args.db).resolve() if args.db else default_db

    # Import determine_next_stage from sibling script
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    from determine_next_stage import determine_next_stage  # type: ignore

    decision = determine_next_stage(
        db_path=db_path,
        request=args.request,
        run_id=args.run_id,
        candidate_id=args.candidate_id,
    )

    output: Dict[str, Any] = {
        "decision": decision,
        "context_pack": None,
    }

    if args.prepare_context and decision.get("action") == "INVOKE_SKILL":
        target_task = decision.get("target_task")
        entity_id = decision.get("entity_id")
        mode = decision.get("mode")

        if target_task and target_task != "research-planning" and state_builder.exists():
            cmd = [
                sys.executable,
                str(state_builder),
                "--task",
                target_task,
                "--db",
                str(db_path),
            ]
            if target_task == "problem-evaluation" and entity_id:
                cmd.extend(["--research-id", entity_id])
            elif target_task == "experiment-validation":
                if decision.get("candidate_id"):
                    cmd.extend(["--candidate-id", decision["candidate_id"]])
                elif entity_id and entity_id.startswith("CAND-"):
                    cmd.extend(["--candidate-id", entity_id])
                if mode:
                    cmd.extend(["--mode", mode])
                if entity_id and entity_id.startswith("EXP-"):
                    cmd.extend(["--experiment-id", entity_id])
            elif target_task == "solution-strategy" and entity_id:
                cmd.extend(["--candidate-id", entity_id])

            code, stdout, stderr = run_command(cmd)
            if code == 0:
                try:
                    output["context_pack"] = json.loads(stdout)
                except Exception:
                    output["context_pack_raw"] = stdout
            else:
                output["context_pack_error"] = stderr.strip()

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
