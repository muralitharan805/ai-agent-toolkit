"""Intent classification logic and pattern matching for Problem Discovery."""

from __future__ import annotations

import re
from typing import Optional, Tuple
from agents.problem_discovery.orchestration.models import IntentClassification, IntentType


RUN_ID_REGEX = re.compile(r"\b(RUN-\d{4}-\d{3,})\b", re.IGNORECASE)
CANDIDATE_ID_REGEX = re.compile(r"\b(CAND-\d{3,})\b", re.IGNORECASE)
EXPERIMENT_ID_REGEX = re.compile(r"\b(EXP-\d{3,})\b", re.IGNORECASE)

# Keywords indicating experiment outcomes or observations
EXPERIMENT_RESULT_PATTERNS = [
    r"results?\s+(?:are\s+)?ready",
    r"observed\s+(?:mean|value|metric|data)",
    r"trial\s+result",
    r"(?:\d+\s+participants?|participants?\s*[:=]\s*\d+)",
    r"artifact\s+hash",
    r"here\s+is\s+the\s+artifact",
    r"recorded\s+(?:observation|measurement)",
    r"outcome\s+verdict",
]

# Keywords indicating resume / advance workflow
RESUME_ACTION_PATTERNS = [
    r"\bcontinue\b",
    r"\bresume\b",
    r"\bproceed\b",
    r"\badvance\b",
    r"\bcontinue\s+pannu\b",
    r"\bnext\s+step\b",
    r"\bforward\b",
]

# Keywords indicating read-only query / inspection
QUERY_PATTERNS = [
    r"\bstatus\b",
    r"\benna\b",
    r"\birukku\b",
    r"\birukka\b",
    r"\bwhat\s+is\b",
    r"\bwhy\s+do\s+we\b",
    r"\bwhich\s+experiment\b",
    r"\bfailed\s+experiments?\b",
    r"\bhow\s+many\b",
    r"\bshow\s+me\b",
    r"\blist\b",
    r"\bdetails\b",
    r"\bexplain\b",
    r"\bcurrent\s+status\b",
    r"\bevidence\b",
    r"\bhistory\b",
    r"-ah\b",
    r"\bah\b",
    r"\?\s*$",
]

# Keywords indicating initiation of new research
NEW_RESEARCH_PATTERNS = [
    r"^research\b",
    r"^investigate\b",
    r"^find\s+out\b",
    r"^explore\b",
    r"^check\s+whether\b",
    r"^check\s+if\b",
    r"\brecurring\s+operational\s+problem\b",
    r"\bresearch\s+whether\b",
    r"\bexplore\s+if\b",
    r"\bresearch\s+pannu\b",
    r"\bresearch\s+pannunga\b",
    r"\bcheck\s+pannu\b",
    r"\binvestigate\s+pannu\b",
    r"\bexplore\s+pannu\b",
]


def extract_entities(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract standard entity IDs (research_id, candidate_id, experiment_id) from text."""
    run_match = RUN_ID_REGEX.search(text)
    cand_match = CANDIDATE_ID_REGEX.search(text)
    exp_match = EXPERIMENT_ID_REGEX.search(text)

    research_id = run_match.group(1).upper() if run_match else None
    candidate_id = cand_match.group(1).upper() if cand_match else None
    experiment_id = exp_match.group(1).upper() if exp_match else None

    return research_id, candidate_id, experiment_id


def classify_intent(user_input: str) -> IntentClassification:
    """Classify incoming natural language user prompt into an IntentClassification.

    Deterministic routing precedence:
    1. EXPERIMENT_RESULT (declarative outcome/observation submission)
    2. Explicit RESUME with entity ID (Continue CAND-xxx or Continue RUN-xxx)
    3. Explicit QUERY / status question (irukka, enna, status, why, what is, ?)
    4. Implicit entity mention with status words -> DISCOVERY_QUERY
    5. NEW_RESEARCH (Research whether..., explore problem, etc.)
    6. General fallback -> DISCOVERY_QUERY if question/interrogative, else NEW_RESEARCH
    """
    text = user_input.strip()
    lower_text = text.lower()
    research_id, candidate_id, experiment_id = extract_entities(text)

    has_query_intent = any(re.search(pat, lower_text) for pat in QUERY_PATTERNS)
    is_new_research = any(re.search(pat, lower_text) for pat in NEW_RESEARCH_PATTERNS)

    # 1. Experiment Result Detection (declarative result submission, not queries)
    is_exp_result = False
    for pat in EXPERIMENT_RESULT_PATTERNS:
        if re.search(pat, lower_text):
            is_exp_result = True
            break
    if (experiment_id or "experiment" in lower_text) and is_exp_result and not has_query_intent:
        return IntentClassification(
            intent=IntentType.EXPERIMENT_RESULT,
            research_id=research_id,
            candidate_id=candidate_id,
            experiment_id=experiment_id,
            query_text=text,
            rationale="Prompt contains experiment identifier and outcome/observation data.",
        )

    # 2. Check for explicit resume / advance command
    has_resume_action = any(re.search(pat, lower_text) for pat in RESUME_ACTION_PATTERNS)

    if has_resume_action and not has_query_intent:
        if candidate_id:
            return IntentClassification(
                intent=IntentType.RESUME_CANDIDATE,
                research_id=research_id,
                candidate_id=candidate_id,
                experiment_id=experiment_id,
                query_text=text,
                rationale=f"Explicit request to resume workflow for candidate {candidate_id}.",
            )
        if research_id:
            return IntentClassification(
                intent=IntentType.RESUME_RUN,
                research_id=research_id,
                candidate_id=candidate_id,
                experiment_id=experiment_id,
                query_text=text,
                rationale=f"Explicit request to resume workflow for research run {research_id}.",
            )

    # 3. Explicit new research command (e.g. "Research whether ...?", "Investigate ...?")
    # An explicit directive to initiate research takes precedence over generic question marks
    if is_new_research and not (research_id or candidate_id or experiment_id):
        return IntentClassification(
            intent=IntentType.NEW_RESEARCH,
            query_text=text,
            rationale="Explicit directive to initiate research on a problem domain.",
        )

    # 4. Check for discovery query / status inspection
    if has_query_intent:
        return IntentClassification(
            intent=IntentType.DISCOVERY_QUERY,
            research_id=research_id,
            candidate_id=candidate_id,
            experiment_id=experiment_id,
            query_text=text,
            rationale="Prompt asks a read-only question regarding persisted discovery state.",
        )

    # 5. If an entity is present but no action verb, treat as status query
    if candidate_id or research_id or experiment_id:
        return IntentClassification(
            intent=IntentType.DISCOVERY_QUERY,
            research_id=research_id,
            candidate_id=candidate_id,
            experiment_id=experiment_id,
            query_text=text,
            rationale="Entity ID specified without explicit continuation command; defaulting to read-only query.",
        )

    # 6. Fallback
    if is_new_research:
        return IntentClassification(
            intent=IntentType.NEW_RESEARCH,
            query_text=text,
            rationale="Prompt asks to research a problem domain or validate market recurrence.",
        )

    if text.endswith("?") or any(w in lower_text for w in ["what", "how", "why", "where", "who", "when"]):
        return IntentClassification(
            intent=IntentType.DISCOVERY_QUERY,
            query_text=text,
            rationale="Interrogative sentence interpreted as a read-only discovery query.",
        )

    return IntentClassification(
        intent=IntentType.NEW_RESEARCH,
        query_text=text,
        rationale="Defaulting open-ended problem exploration request to new research.",
    )
