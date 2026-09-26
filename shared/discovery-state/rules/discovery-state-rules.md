---
description: "Enforces SQLite 4-table schema integrity, deterministic factual context pack assembly, zero hard deletes, and the single-pane discovery dashboard."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Discovery State & Context Builder Rules

## Description
This rule governs the dedicated infrastructure capability (`shared/discovery-state`) for the modular problem discovery ecosystem. It enforces strict SQLite schema integrity, the hybrid relational + JSON document architecture, deterministic Python aggregation (eliminating LLM counting hallucinations), task-specific Dynamic Context Pack generation, full-text search (FTS5) deduplication, zero hard deletes, negative knowledge preservation, and the canonical `v_discovery_dashboard` decision view.

## Constraints

### 1. Dedicated Infrastructure Separation
- The `discovery-state` module is an **infrastructure capability**, not a cognitive reasoning agent.
- It manages physical SQLite persistence, schema migrations, and context compilation.
- Reasoning agents (`research-planning`, `evidence-research`, `problem-evaluation`, `experiment-validation`, `solution-strategy`) MUST NOT execute raw SQL `CREATE TABLE`, `ALTER TABLE`, or multi-table JOINs in prompts.
- All database state mutations and query aggregations MUST execute through the deterministic Python interface (`DiscoveryDB`).

### 2. Authoritative 4-Table Schema Invariant
- The persistence store MUST maintain exactly 4 relational tables, 1 FTS5 virtual table, and 1 canonical dashboard view:
  1. `research_runs`: Root entity (1 run = 1 domain/intent exploration).
  2. `candidates`: Formed problem candidates with 35-point scores, evidence levels, and lifecycle status.
  3. `evidence_signals`: Collected research observations (FK to `research_runs`; nullable FK to `candidates`).
  4. `experiments`: Preregistered empirical trial contracts, thresholds, and artifact digests.
  5. `discovery_fts`: Full-text search index over runs, candidates, and signal issues.
  6. `v_discovery_dashboard`: Pre-joined, single-pane decision view.
- Every database connection MUST immediately execute:
  ```sql
  PRAGMA foreign_keys = ON;
  PRAGMA journal_mode = WAL;
  ```
- All JSON document columns (`plan_json`, `evaluation_json`, `solution_json`, `payload_json`, `contract_json`, `assessment_json`) MUST include `CHECK(column IS NULL OR json_valid(column))` constraints.

### 3. Factual Math vs. Cognitive Reasoning Boundary
- LLMs MUST NEVER be tasked with numerical counting, platform grouping, or aggregate status math.
- The Context Builder MUST deterministically compute and inject:
  - Total signal counts (`len(signals)`)
  - Platform distribution breakdown (`collections.Counter`)
  - Evidence level distributions (L1–L5 counts)
  - Experiment pass/fail counts and latest outcome verdicts
  - Candidate title similarity / duplicate matches
- Cognitive reasoning agents focus exclusively on forensic workflow mapping, root-cause isolation, scoring judgments, and solution class selection.

### 4. Task-Specific Dynamic Context Pack Protocol
- Downstream reasoning agents MUST receive bounded, task-specific JSON Context Packs assembled by `build_agent_context.py`:
  - `problem-evaluation` pack: Ingests run metadata, plan unknowns, and unlinked signals for the target run.
  - `experiment-validation` pack: Ingests candidate evaluation summary, current friction metrics, and target operator.
  - `solution-strategy` pack: Ingests validated candidate, evaluation summary, experiment outcome verdicts, and known technical constraints.
- Agents MUST NOT depend on conversational chat history. Every task pack must enable clean, independent turn invocation.

### 5. Strict Prohibition of Hard Deletes & Negative Knowledge Asset Preservation
- Executing `DELETE FROM candidates`, `DELETE FROM evidence_signals`, or `DELETE FROM experiments` is STRICTLY FORBIDDEN during normal operations.
- **Candidate Rejection**: When a candidate is disqualified or superseded:
  - Update `lifecycle_status = 'PARKED'` or `'ARCHIVED'`.
  - Record the explicit disqualification rationale in `evaluation_json`.
- **Negative Knowledge Preservation**: Failed trials (`outcome_verdict = 'EXPERIMENT_FAILED'`) are valuable organizational assets that prove what does not work.
  - Failed experiment records MUST NEVER be deleted, hidden, or overwritten.
  - Associated candidates MUST transition to `validation_status = 'EXPERIMENT_FAILED'`.

### 6. The Master Decision View Contract (`v_discovery_dashboard`)
- Product builders and leadership MUST NEVER write custom multi-table SQL queries to inspect discovery status.
- All portfolio decision queries MUST read from `v_discovery_dashboard`.
- The view flattens candidate records with their total evidence count and latest experiment verdict:
  ```sql
  SELECT candidate_id, title, solution_class, research_score 
  FROM v_discovery_dashboard 
  WHERE validation_status = 'VALIDATED' AND lifecycle_status = 'READY_TO_BUILD';
  ```

### 7. Atomic Transaction & Error Handling Standards
- Multi-row operations (such as upserting a candidate and linking supporting signal IDs) MUST execute inside an atomic SQLite transaction (`BEGIN TRANSACTION` / `COMMIT`).
- In the event of a constraint failure or payload validation error, the transaction MUST automatically roll back (`ROLLBACK`), emitting diagnostics to `stderr` and returning a non-zero exit code.

## Examples

### 1. Deterministic Context Pack Injection vs. LLM Hallucination
```text
❌ FORBIDDEN:
Agent prompt: "Here are 45 raw signals scraped from Reddit. Count how many mention QuickBooks, group them by platform, and calculate the average score."
(Risks severe LLM counting hallucinations and token waste).

✅ CORRECT:
Context Builder executes Python aggregation:
{
  "deterministic_summary": {
    "total_signals": 45,
    "platform_breakdown": { "REDDIT": 38, "HACKERNEWS": 7 },
    "quickbooks_mention_count": 29,
    "evidence_level_distribution": { "L1": 0, "L2": 0, "L3": 45, "L4": 0, "L5": 0 }
  }
}
Agent receives pre-computed facts and focuses purely on qualitative workflow deconstruction.
```

### 2. Negative Knowledge Preservation vs. Destructive Hard Delete
```text
❌ FORBIDDEN:
"Experiment failed with observed 1.2 vs threshold 3.0. Deleting experiment EXP-002 from database to keep the dashboard clean."

✅ CORRECT:
UPDATE experiments SET outcome_verdict = 'EXPERIMENT_FAILED', observed_value = 1.2 WHERE experiment_id = 'EXP-002';
UPDATE candidates SET validation_status = 'EXPERIMENT_FAILED', lifecycle_status = 'PARKED' WHERE candidate_id = 'CAND-001';
(Preserves empirical trail and prevents future teams from wasting capital on the same failed assumption).
```
