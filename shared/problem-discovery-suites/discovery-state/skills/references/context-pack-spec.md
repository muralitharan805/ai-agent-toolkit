# Dynamic Context Pack Specification

## Purpose

Context Packs make every reasoning agent runnable from a fresh chat without depending on conversational memory. The state layer queries SQLite, performs deterministic aggregation, and returns only task-relevant JSON.

Reasoning agents do not receive raw DDL and should not be asked to count database rows.

## PROBLEM_EVALUATION

Input key: `research_id`.

Pack contains:
- research run metadata
- `research_plan.research_streams`
- currently unlinked signals
- deterministic platform/evidence-level counts
- existing candidate matches in the same domain

Important constraints:
- no fresh web research
- score is not validation
- reuse a stable candidate ID when the same root problem matches

## EXPERIMENT_VALIDATION

Input key: `candidate_id`, plus `mode=DESIGN|ASSESS`.

DESIGN contains:
- candidate state
- full evaluation snapshot
- supporting signal count
- prior experiment history

ASSESS additionally contains the actual persisted preregistered `experiment_contract`. Never reconstruct a locked experiment from new CLI defaults.

Experiment database verdicts are `PASSED/FAILED/INCOMPLETE/INVALID`; these are not candidate-wide validation labels.

## SOLUTION_STRATEGY

Input key: `candidate_id`.

Pack contains:
- candidate/evaluation state
- latest validation-scope flags
- deterministic passed/failed experiment counts
- latest experiment assessment

Unknown requirements may not justify architectural complexity.

## DISCOVERY_QUERY

Input key: natural-language `query`.

Use this when a user opens a fresh context and asks questions such as:
- "inventory sync problem current status enna?"
- "namma ecommerce research-la enna candidates irukku?"
- "CAND-001-ku failed experiments irukka?"

Flow:

```text
natural-language question
      ↓
FTS5 search
      ↓
candidate resolution
      ↓
v_discovery_dashboard + evaluation + solution + recent experiments
      ↓
bounded DISCOVERY_QUERY context pack
      ↓
AI answer grounded in persisted discovery state
```

The pack distinguishes persisted facts from interpretation and exposes `matches`, `search_hits`, and deterministic totals.

## Context-Pack Invariants

1. Never invent missing evidence.
2. Never treat FTS as source of truth.
3. Compute counts in Python/SQLite, not in the LLM.
4. Preserve evidence URLs and candidate IDs.
5. Keep task packs bounded; do not dump the entire database.
