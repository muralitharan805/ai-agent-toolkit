"""Compatibility runner for the Problem Discovery Orchestrator CLI."""

import sys
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parents[2]
if str(TOOLKIT_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLKIT_ROOT))

from agents.problem_discovery.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
