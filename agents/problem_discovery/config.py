"""Configuration and path resolution for ProblemDiscoveryAgent."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, List, Optional
from pydantic import BaseModel, Field


def get_repo_root() -> Path:
    """Find and return the canonical ai-agent-toolkit repository root."""
    # Start looking from this file's directory upwards
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() and (parent / "shared" / "problem-discovery-suites").exists():
            return parent
        if (parent / "shared" / "problem-discovery-suites").exists():
            return parent
    # Fallback to current working directory if recognizable
    cwd = Path(os.getcwd()).resolve()
    if (cwd / "shared" / "problem-discovery-suites").exists():
        return cwd
    # Final fallback
    return Path(__file__).resolve().parents[2]


def get_default_db_path() -> Path:
    """Resolve the canonical SQLite path.

    Precedence:
    1. DISCOVERY_DB_PATH environment variable if set.
    2. shared/problem-discovery-suites/discovery-state/data/discovery.sqlite

    The path is intentionally independent of the process working directory so the
    agent cannot silently create multiple discovery databases.
    """
    env_path = os.environ.get("DISCOVERY_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    root = get_repo_root()
    return root / "shared" / "problem-discovery-suites" / "discovery-state" / "data" / "discovery.sqlite"



def get_canonical_skills_paths() -> List[str]:
    """Return absolute paths to the 6 Problem Discovery skills for SDK skills_paths."""
    root = get_repo_root()
    suites = root / "shared" / "problem-discovery-suites"
    candidates = [
        suites / "research-planning" / "skills",
        suites / "evidence-research" / "skills",
        suites / "problem-evaluation" / "skills",
        suites / "experiment-validation" / "skills",
        suites / "solution-strategy" / "skills",
        suites / "discovery-state" / "skills",
    ]
    resolved = []
    for c in candidates:
        if c.exists():
            resolved.append(str(c.resolve()))
    return resolved


def load_module_from_path(name: str, path: Path) -> Any:
    """Dynamically load a python module given an absolute Path."""
    if not path.exists():
        raise FileNotFoundError(f"Target module file does not exist: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_discovery_db_class() -> Any:
    """Load and return the canonical DiscoveryDB class."""
    root = get_repo_root()
    script_path = (
        root
        / "shared"
        / "problem-discovery-suites"
        / "discovery-state"
        / "skills"
        / "scripts"
        / "discovery_db.py"
    )
    mod = load_module_from_path("discovery_db_canonical", script_path)
    return getattr(mod, "DiscoveryDB")


def get_build_agent_context_module() -> Any:
    """Load and return the canonical build_agent_context module."""
    root = get_repo_root()
    script_path = (
        root
        / "shared"
        / "problem-discovery-suites"
        / "discovery-state"
        / "skills"
        / "scripts"
        / "build_agent_context.py"
    )
    return load_module_from_path("build_agent_context_canonical", script_path)


class ProblemDiscoveryConfig(BaseModel):
    """Runtime configuration for ProblemDiscoveryAgent."""
    db_path: str = Field(default_factory=lambda: str(get_default_db_path()))
    skills_paths: List[str] = Field(default_factory=get_canonical_skills_paths)
    model: Optional[str] = Field(
        default_factory=lambda: os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
    )
    api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    system_instruction_path: Optional[str] = Field(
        default_factory=lambda: str(Path(__file__).resolve().parent / "prompts" / "system.md")
    )
