# Lifecycle Model & State Machine

## Research Run

A research run tracks the next workflow capability to execute.

```text
RESEARCH_PLANNING
      ↓ plan persisted
EVIDENCE_RESEARCH
      ↓ signals persisted
PROBLEM_EVALUATION
      ↓ candidate evaluation persisted
EXPERIMENT_VALIDATION
      ↓ audited experiment passes
SOLUTION_STRATEGY
      ↓ solution assessment persisted
COMPLETED
```

A failed, incomplete, or invalid experiment keeps the run at `EXPERIMENT_VALIDATION` until the orchestrator decides to retry, gather more evidence, or archive.

## Candidate Lifecycle

`lifecycle_status` is operational state, not truth.

Recommended states:
- `ACTIVE`: newly formed candidate.
- `RESEARCH_PRIORITY`: merits more primary research or experiment design.
- `VALIDATING`: a preregistered trial is active.
- `READY_FOR_SOLUTION`: at least one relevant audited claim passed; solution-shape reasoning may proceed.
- `PILOT_READY`: smallest justified intervention has been selected.
- `PARKED`: stop check or low-priority evidence pauses work.
- `ARCHIVED`: retired historical candidate.

Do not use research score alone to create `READY_FOR_SOLUTION` or `PILOT_READY`.

## Candidate Validation

`validation_status` is deliberately separate from experiment verdict.

Recommended states:
- `UNVERIFIED`
- `IN_PROGRESS`
- `PARTIALLY_VALIDATED`
- `VALIDATED` only when an explicit higher-level aggregation rule has been satisfied

One behavior experiment passing usually yields `PARTIALLY_VALIDATED`, because WTP, adoption, retention, and representativeness can remain unknown.

A failed experiment is preserved in `experiments`; it does not automatically erase or delete the candidate.

## Experiment Lifecycle

```text
PREREGISTERED
 ├─→ PASSED
 ├─→ FAILED
 ├─→ INCOMPLETE
 ├─→ INVALID
 └─→ CANCELLED
```

- `PASSED`: audited observed result satisfied the locked rule.
- `FAILED`: audited result missed the locked rule.
- `INCOMPLETE`: minimum usable sample was not reached.
- `INVALID`: preregistration or required audit/artifact integrity was not satisfied.
- `CANCELLED`: stopped before valid assessment.

The original contract is immutable. A material threshold/metric change requires a new experiment ID.

## Negative Knowledge

Never delete:
- failed experiments
- parked candidates
- contradictory evidence
- previously tested solution directions

Negative results are reusable discovery knowledge.
