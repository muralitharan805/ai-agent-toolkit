# Database Schema Reference

## Canonical Source

The authoritative SQLite DDL is:

`skills/assets/discovery-db-schema.sql`

Do **not** copy table DDL into reasoning-suite scripts. `discovery-state` is the single schema and mutation authority. Other suites emit structured JSON contracts and call the canonical `DiscoveryDB` client.

## Storage Model

The store uses a hybrid relational + JSON document model with four relational tables, one FTS5 virtual index, and one derived decision view.

### `research_runs`

One row per investigation intent.

Key fields:
- `research_id`: stable run identifier.
- `original_request`, `domain`, `scope_type`, `geography`.
- `current_stage`: next lifecycle stage.
- `plan_json`: complete ResearchPlan snapshot.

Canonical stages:

`RESEARCH_PLANNING → EVIDENCE_RESEARCH → PROBLEM_EVALUATION → EXPERIMENT_VALIDATION → SOLUTION_STRATEGY → COMPLETED`

### `candidates`

One row per long-lived root problem candidate.

Key fields:
- `candidate_id`: stable identity across research runs.
- `origin_research_id`: run in which the candidate was first created.
- `research_score`: 0–35 research-priority score; not validation.
- `validation_status`: empirical claim state.
- `lifecycle_status`: operational pipeline state.
- `evaluation_json`, `solution_json`: rich stage snapshots.

A later research run may attach new `evidence_signals` to an existing candidate without changing `origin_research_id`.

### `evidence_signals`

Signals are collected before candidate formation.

Key fields:
- `research_id`: mandatory parent run.
- `candidate_id`: nullable until problem evaluation.
- `evidence_level`: defaults to `UNASSESSED`.
- `payload_json`: full normalized signal with provenance.

A raw Reddit/HN/GitHub hit is never automatically L3.

### `experiments`

One candidate may have many preregistered experiments.

Canonical `outcome_verdict` values:
- `PREREGISTERED`
- `PASSED`
- `FAILED`
- `INCOMPLETE`
- `INVALID`
- `CANCELLED`

Experiment outcome is intentionally separate from candidate validation status.

## FTS5

`discovery_fts` is a derived search index over runs, candidates, and signals. It is disposable and must never be treated as the source of truth.

## Decision View

`v_discovery_dashboard` is the primary read model for dashboards and quick decisions. It exposes:
- candidate metadata and lifecycle
- evidence count
- number of contributing research runs
- experiment count
- pass/fail counts
- actual latest experiment verdict by `created_at`

Callers should start with this view and drill into evidence/experiment detail only when needed.

## Persistence Rules

1. No hard deletes for candidates, signals, or failed experiments.
2. No `INSERT OR REPLACE` for candidates; it can destroy lifecycle state.
3. Reasoning suites do not create tables.
4. `updated_at` is explicitly updated by the state client on mutations.
5. Stable candidate identity is preserved across runs.
6. JSON snapshots must pass SQLite `json_valid(...)` constraints.
