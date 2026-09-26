"""Deterministic tests for the Problem Discovery Intent Router."""

from __future__ import annotations

import unittest
from agents.problem_discovery.orchestration.models import IntentType
from agents.problem_discovery.orchestration.router import IntentRouter


class ProblemDiscoveryAgentRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = IntentRouter()

    def test_new_research_intent_classification(self) -> None:
        """Test NEW_RESEARCH intent detection with natural language."""
        prompts = [
            "Research whether multi-channel ecommerce inventory synchronization is a real recurring operational problem.",
            "Research whether accountants have recurring month-end reconciliation problems.",
            "Investigate manual inventory sync failures across Shopify and Amazon.",
            "Find out if dental clinics face patient onboarding delays.",
        ]
        for p in prompts:
            result = self.router.route(p)
            self.assertEqual(
                result.intent,
                IntentType.NEW_RESEARCH,
                f"Failed for prompt: {p} (got {result.intent})",
            )

    def test_resume_candidate_intent(self) -> None:
        """Test RESUME_CANDIDATE intent with entity extraction."""
        prompts = [
            ("Continue CAND-001", "CAND-001"),
            ("resume CAND-007", "CAND-007"),
            ("CAND-012 continue pannu", "CAND-012"),
            ("proceed with candidate CAND-999", "CAND-999"),
        ]
        for p, expected_id in prompts:
            result = self.router.route(p)
            self.assertEqual(result.intent, IntentType.RESUME_CANDIDATE, f"Failed for: {p}")
            self.assertEqual(result.candidate_id, expected_id)

    def test_resume_run_intent(self) -> None:
        """Test RESUME_RUN intent with sequential run ID."""
        prompts = [
            ("Continue RUN-2026-004", "RUN-2026-004"),
            ("resume RUN-2026-001", "RUN-2026-001"),
            ("RUN-2026-010 continue pannu", "RUN-2026-010"),
        ]
        for p, expected_id in prompts:
            result = self.router.route(p)
            self.assertEqual(result.intent, IntentType.RESUME_RUN, f"Failed for: {p}")
            self.assertEqual(result.research_id, expected_id)

    def test_discovery_query_intent_english_and_thanglish(self) -> None:
        """Test DISCOVERY_QUERY intent in English, Thanglish, and question formats."""
        prompts = [
            "CAND-001 status enna?",
            "RUN-2026-003 current status enna?",
            "Inventory sync problem-ku namma enna evidence collect pannirukkom?",
            "Inventory sync-ku enna evidence irukku?",
            "Failed experiments irukka?",
            "Namma ecommerce research-la enna candidates irukku?",
            "Why do we believe this problem exists?",
            "Which experiment failed?",
            "What is the status of candidate CAND-005?",
            "Show me recent discovery dashboard summary",
        ]
        for p in prompts:
            result = self.router.route(p)
            self.assertEqual(
                result.intent,
                IntentType.DISCOVERY_QUERY,
                f"Failed for query prompt: {p} (got {result.intent})",
            )

    def test_experiment_result_intent(self) -> None:
        """Test EXPERIMENT_RESULT intent with observed data and trial indicators."""
        prompts = [
            ("EXP-009 results are ready. 5 participants, observed mean 4.2. Here is the artifact.", "EXP-009"),
            ("Experiment trial result recorded for EXP-001 with participants=10", "EXP-001"),
            ("EXP-015 observed mean 6.8 with artifact hash SHA256", "EXP-015"),
        ]
        for p, expected_exp in prompts:
            result = self.router.route(p)
            self.assertEqual(
                result.intent,
                IntentType.EXPERIMENT_RESULT,
                f"Failed for experiment result: {p}",
            )
            self.assertEqual(result.experiment_id, expected_exp)


if __name__ == "__main__":
    unittest.main()
