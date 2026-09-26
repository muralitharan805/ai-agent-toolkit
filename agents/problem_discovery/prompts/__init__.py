"""Prompts package for ProblemDiscoveryAgent."""

from pathlib import Path

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "system.md"

def get_system_prompt() -> str:
    """Read and return the orchestrator system prompt."""
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
