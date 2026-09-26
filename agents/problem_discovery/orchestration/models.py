"""Domain models and data schemas for Problem Discovery Orchestration."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    """Supported user intent types for ProblemDiscoveryAgent."""
    NEW_RESEARCH = "NEW_RESEARCH"
    RESUME_RUN = "RESUME_RUN"
    RESUME_CANDIDATE = "RESUME_CANDIDATE"
    DISCOVERY_QUERY = "DISCOVERY_QUERY"
    EXPERIMENT_RESULT = "EXPERIMENT_RESULT"


class WorkflowStage(str, Enum):
    """Discrete stages in the Problem Discovery lifecycle."""
    RESEARCH_PLANNING = "RESEARCH_PLANNING"
    EVIDENCE_RESEARCH = "EVIDENCE_RESEARCH"
    PROBLEM_EVALUATION = "PROBLEM_EVALUATION"
    EXPERIMENT_VALIDATION = "EXPERIMENT_VALIDATION"
    SOLUTION_STRATEGY = "SOLUTION_STRATEGY"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    READ_ONLY = "READ_ONLY"


class WorkflowStatus(str, Enum):
    """Execution status returned by the state machine and orchestrator."""
    CONTINUED = "CONTINUED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    READ_ONLY = "READ_ONLY"
    ERROR = "ERROR"


class PauseReason(str, Enum):
    """Specific reasons why a discovery workflow paused execution."""
    WAITING_FOR_REAL_WORLD_EXPERIMENT = "WAITING_FOR_REAL_WORLD_EXPERIMENT"
    INCOMPLETE_EXPERIMENT = "INCOMPLETE_EXPERIMENT"
    INVALID_EXPERIMENT_AUDIT = "INVALID_EXPERIMENT_AUDIT"
    HUMAN_INPUT_REQUIRED = "HUMAN_INPUT_REQUIRED"
    NOT_READY = "NOT_READY"


class IntentClassification(BaseModel):
    """Structured output of the intent router."""
    intent: IntentType
    research_id: Optional[str] = None
    candidate_id: Optional[str] = None
    experiment_id: Optional[str] = None
    query_text: str = ""
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    rationale: str = ""


class OrchestrationResult(BaseModel):
    """Standard machine-readable and human-readable orchestration contract."""
    intent: IntentType
    research_id: Optional[str] = None
    candidate_id: Optional[str] = None
    experiment_id: Optional[str] = None
    current_stage: Optional[WorkflowStage] = None
    action_taken: Optional[str] = None
    workflow_status: WorkflowStatus
    pause_reason: Optional[str] = None
    next_action: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to the standard orchestrator JSON contract."""
        return {
            "intent": self.intent.value,
            "research_id": self.research_id,
            "candidate_id": self.candidate_id,
            "experiment_id": self.experiment_id,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "action_taken": self.action_taken,
            "workflow_status": self.workflow_status.value,
            "pause_reason": self.pause_reason,
            "next_action": self.next_action,
        }


class ExperimentContractValidation(BaseModel):
    """Validation guard for experiment contracts ensuring atomic primary metric."""
    metric_name: str
    target_threshold: float
    direction: str = ">="
    sample_target: int
    aggregation_rule: str

    @field_validator("metric_name")
    @classmethod
    def validate_atomic_metric(cls, v: str) -> str:
        """Reject compound metrics containing disjunctive or conjunctive joining operators."""
        lower = v.lower()
        forbidden_delimiters = ["_or_", "_and_", " or ", " and ", " / ", "/"]
        for delim in forbidden_delimiters:
            if delim in lower:
                raise ValueError(
                    f"Compound primary metric '{v}' is forbidden. "
                    f"Experiments must measure exactly one atomic observable metric. "
                    f"Split into separate experiments for each metric."
                )
        return v
