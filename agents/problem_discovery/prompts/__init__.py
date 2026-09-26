"""Prompts package for ProblemDiscoveryAgent."""

from pathlib import Path

from typing import Optional, Union

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "system.md"

def get_system_prompt(path: Optional[Union[str, Path]] = None) -> str:
    """Read and return the orchestrator system prompt.
    
    Args:
        path: Optional file path to override the default system.md instructions.
    
    Returns:
        The text content of the system prompt.
    """
    target = Path(path).resolve() if path else SYSTEM_PROMPT_PATH
    return target.read_text(encoding="utf-8")
