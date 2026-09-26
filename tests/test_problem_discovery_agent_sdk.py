"""Smoke tests for Google Antigravity SDK integration with ProblemDiscoveryAgent."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from agents.problem_discovery.agent import ProblemDiscoveryAgent
from agents.problem_discovery.config import ProblemDiscoveryConfig, get_canonical_skills_paths


class ProblemDiscoveryAgentSDKTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "sdk_smoke_discovery.sqlite")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_canonical_skill_paths_exist_and_resolve(self) -> None:
        skill_paths = get_canonical_skills_paths()
        self.assertEqual(len(skill_paths), 6)
        for path in skill_paths:
            skill_dir = Path(path)
            self.assertTrue(skill_dir.exists(), f"Skill path does not exist: {path}")
            self.assertTrue((skill_dir / "SKILL.md").exists(), f"SKILL.md missing in {path}")

    def test_antigravity_sdk_import_and_local_agent_config(self) -> None:
        try:
            from google.antigravity import LocalAgentConfig
        except ImportError:
            self.skipTest("google-antigravity is not installed in the active environment.")

        agent = ProblemDiscoveryAgent(
            config=ProblemDiscoveryConfig(db_path=self.db_path)
        )
        sdk_config = agent.build_sdk_config()
        self.assertIsInstance(sdk_config, LocalAgentConfig)
        self.assertEqual(len(sdk_config.skills_paths), 6)
        self.assertEqual(len(sdk_config._get_all_custom_tools()), 15)

    def test_runtime_failure_never_creates_synthetic_research(self) -> None:
        """If Antigravity cannot execute planning, no fake plan/evidence is persisted."""
        agent = ProblemDiscoveryAgent(
            config=ProblemDiscoveryConfig(db_path=self.db_path)
        )
        agent._chat_sdk = AsyncMock(side_effect=RuntimeError("offline for test"))

        result = asyncio.run(
            agent.run("Research whether accounting reconciliation is an operational bottleneck.")
        )
        self.assertEqual(result.workflow_status.value, "ERROR")
        self.assertIn("not synthetically advanced", result.message)

        conn = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM research_runs").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM evidence_signals").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0], 0)
        finally:
            conn.close()

    def test_read_only_query_works_without_live_model(self) -> None:
        agent = ProblemDiscoveryAgent(
            config=ProblemDiscoveryConfig(db_path=self.db_path)
        )
        result = asyncio.run(agent.run("CAND-001 status enna?"))
        self.assertEqual(result.workflow_status.value, "READ_ONLY")

    def test_live_antigravity_chat_smoke(self) -> None:
        """Exercise the actual SDK ChatResponse API only when a key is configured."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            self.skipTest("Skipping live integration test: GEMINI_API_KEY not set.")

        async def run_live() -> None:
            config = ProblemDiscoveryConfig(db_path=self.db_path, api_key=api_key)
            async with ProblemDiscoveryAgent(config=config) as agent:
                text = await agent._chat_sdk(
                    "Reply with exactly READY. Do not call any tools for this smoke test."
                )
                self.assertTrue(text.strip())

        asyncio.run(run_live())


if __name__ == "__main__":
    unittest.main()
