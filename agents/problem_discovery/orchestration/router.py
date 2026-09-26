"""User intent router for ProblemDiscoveryAgent."""

from __future__ import annotations

from typing import Optional
from agents.problem_discovery.orchestration.intents import classify_intent, extract_entities
from agents.problem_discovery.orchestration.models import IntentClassification, IntentType


class IntentRouter:
    """Deterministic intent router for incoming user prompts."""

    def route(self, user_input: str) -> IntentClassification:
        """Parse natural language user input into structured IntentClassification."""
        return classify_intent(user_input)
