"""Smoke tests for Google Antigravity SDK integration with ProblemDiscoveryAgent."""

from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from agents.problem_discovery.agent import ProblemDiscoveryAgent
from agents.problem_discovery.config import (
    ProblemDiscoveryConfig,
    get_canonical_skills_paths,
    get_repo_root,
)


class ProblemDiscoveryAgentSDKTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "sdk_smoke_discovery.sqlite")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_canonical_skill_paths_exist_and_resolve(self) -> None:
        """Verify that all 6 Problem Discovery modular skills resolve to real directories."""
        skill_paths = get_canonical_skills_paths()
        self.assertEqual(len(skill_paths), 6)
        for p in skill_paths:
            path_obj = Path(p)
            self.assertTrue(path_obj.exists(), f"Skill path does not exist: {p}")
            self.assertTrue(path_obj.is_dir(), f"Skill path must be a directory: {p}")
            skill_md = path_obj / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"SKILL.md missing in {p}")

    def test_antigravity_sdk_import_and_local_agent_config(self) -> None:
        """Verify google-antigravity imports, LocalAgentConfig builds, and tools register."""
        try:
            from google.antigravity import Agent, LocalAgentConfig
        except ImportError:
            self.skipTest("google-antigravity is not installed in the active environment.")

        config = ProblemDiscoveryConfig(db_path=self.db_path)
        agent = ProblemDiscoveryAgent(config=config)

        sdk_config = agent.build_sdk_config()
        self.assertIsInstance(sdk_config, LocalAgentConfig)
        self.assertEqual(len(sdk_config.skills_paths), 6)
        self.assertEqual(len(sdk_config._get_all_custom_tools()), 15)

    def test_offline_agent_run_execution(self) -> None:
        """Verify ProblemDiscoveryAgent handles offline state machine runs cleanly."""
        config = ProblemDiscoveryConfig(db_path=self.db_path)
        agent = ProblemDiscoveryAgent(config=config)

        # Run natural language new research
        res = asyncio.run(
            agent.run("Research whether accounting reconciliation is an operational bottleneck.")
        )
        self.assertEqual(res.workflow_status.value, "CONTINUED")
        self.assertIn("RUN-", res.research_id or "")

        # Run query on empty state
        query_res = asyncio.run(agent.run("CAND-001 status enna?"))
        self.assertEqual(query_res.workflow_status.value, "READ_ONLY")

    def test_live_agent_chat_smoke(self) -> None:
        """Run live Gemini agent chat only if GEMINI_API_KEY is explicitly configured.

        To run live:
            export GEMINI_API_KEY="your-api-key"
            python -m unittest tests/test_problem_discovery_agent_sdk.py -k test_live_agent_chat_smoke
        """
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            self.skipTest("Skipping live integration test: GEMINI_API_KEY not set.")

        async def run_live() -> None:
            config = ProblemDiscoveryConfig(db_path=self.db_path, api_key=api_key)
            async with ProblemDiscoveryAgent(config=config) as agent:
                resp = await agent.chat("CAND-001 status enna?")
                self.assertTrue(len(resp) > 0)

        asyncio.run(run_live())


if __name__ == "__main__":
    unittest.main()
