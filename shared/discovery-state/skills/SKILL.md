---
name: discovery-state
description: "Manages SQLite state persistence, schema integrity, deterministic factual aggregations, and dynamic context pack assembly for problem discovery agents. Triggered by 'discovery-state:', 'discovery-db:', or '/discovery-state'."
metadata:
  dependencies: "pydantic>=2.0,pyyaml>=6.0"
  framework_version: "1.0.0"
  last_verified_date: "2026-09-26"
---

# Discovery State & Context Builder

## Persona
Act as a Principal Data Infrastructure Architect and State Persistence Specialist. You specialize in managing SQLite storage for multi-agent reasoning systems, enforcing relational and document schema integrity, eliminating LLM counting hallucinations through deterministic Python math, assembling bounded task-specific Dynamic Context Packs, preserving negative knowledge assets, and providing single-pane-of-glass decision views.

---

## Overview
`discovery-state` is the **dedicated infrastructure capability** for the problem discovery lifecycle. Implementing a **Hybrid Relational + JSON Document Model** and the **Blackboard / Claim-Check Architecture**, it manages physical database persistence across 4 core tables, 1 FTS5 virtual table, and 1 canonical decision view. It ensures cognitive reasoning agents never see raw DDL boilerplate or perform error-prone mathematical counting.

---

## 6-Phase Infrastructure Execution Pipeline

```text
[Phase 1: Database Bootstrapping & PRAGMAs]
                     │
                     ▼
[Phase 2: Multi-Stage Lifecycle Mutation Pipeline]
     ├── Stage 1: create_research_run()
     ├── Stage 2: save_evidence_signals()
     ├── Stage 3: upsert_candidate() (Dynamic Signal Linkage)
     ├── Stage 4: preregister_experiment() & record_experiment_assessment()
     └── Stage 5: finalize_solution()
                     │
                     ▼
[Phase 3: Deterministic Factual Math & Count Aggregation]
                     │
                     ▼
[Phase 4: Dynamic Task Context Pack Assembly]
     ├── problem-evaluation Context Pack
     ├── experiment-validation Context Pack
     └── solution-strategy Context Pack
                     │
                     ▼
[Phase 5: Full-Text Search (FTS5) & Deduplication]
                     │
                     ▼
[Phase 6: Negative Knowledge Preservation & Dashboard View]
```

---

### Phase 1: Database Bootstrapping & PRAGMAs
1. Bootstrap or verify the SQLite database file:
   ```bash
   python3 scripts/init_db.py --db "discovery.sqlite"
   ```
2. Verify connection PRAGMAs on every connection:
   - `PRAGMA foreign_keys = ON;`
   - `PRAGMA journal_mode = WAL;`
   - `PRAGMA synchronous = NORMAL;`
   - `PRAGMA busy_timeout = 5000;`
3. Verify table DDL and JSON check constraints in [database-schema.md](references/database-schema.md) and [discovery-db-schema.sql](assets/discovery-db-schema.sql).

---

### Phase 2: Multi-Stage Lifecycle Mutation Pipeline
Execute mutations through the canonical client [discovery_db.py](scripts/discovery_db.py):
- **Stage 1 (Research Run)**:
  `DiscoveryDB.create_research_run(research_id, request, domain, scope_type, geography, plan_dict)`
  Advances `current_stage` to `PLANNED`.
- **Stage 2 (Evidence Signals)**:
  `DiscoveryDB.save_evidence_signals(research_id, signals)`
  Advances `current_stage` to `RESEARCHED`.
- **Stage 3 (Candidate Upsert & Signal Linkage)**:
  `DiscoveryDB.upsert_candidate(candidate_id, research_id, title, ..., supporting_signal_ids)`
  Updates `evidence_signals.candidate_id` and advances `current_stage` to `EVALUATED`.
- **Stage 4 (Experiment Contract & Assessment)**:
  `DiscoveryDB.preregister_experiment(experiment_id, candidate_id, contract_dict)`
  `DiscoveryDB.record_experiment_assessment(experiment_id, candidate_id, assessment_dict, artifact_hash, ...)`
  Advances `current_stage` to `VALIDATED`.
- **Stage 5 (Solution Finalization)**:
  `DiscoveryDB.finalize_solution(candidate_id, solution_class, solution_dict)`
  Sets `candidates.lifecycle_status = 'READY_TO_BUILD'` and completes parent run (`COMPLETED`).
- Reference: [lifecycle-model.md](references/lifecycle-model.md) and [entity-relationships.md](references/entity-relationships.md).

---

### Phase 3: Deterministic Factual Math & Count Aggregation
1. The infrastructure engine computes all metrics deterministically in Python:
   - Total signals count (`len(signals)`)
   - Platform breakdown (`collections.Counter`)
   - Evidence level distribution (L1–L5 counts)
   - Experiment pass/fail totals
2. **Strict Invariant**: Reasoning agents MUST NEVER be asked to count rows, calculate proportions, or group database categories in prompts.
3. Reference: [field-semantics.md](references/field-semantics.md).

---

### Phase 4: Dynamic Task Context Pack Assembly
1. Assemble self-contained Context Packs for downstream reasoning tasks using [build_agent_context.py](scripts/build_agent_context.py):
   ```bash
   # For problem-evaluation
   python3 scripts/build_agent_context.py --task problem-evaluation --research-id "run_001" --db "discovery.sqlite"

   # For experiment-validation
   python3 scripts/build_agent_context.py --task experiment-validation --candidate-id "cand_001" --mode DESIGN --db "discovery.sqlite"

   # For solution-strategy
   python3 scripts/build_agent_context.py --task solution-strategy --candidate-id "cand_001" --db "discovery.sqlite"
   ```
2. Validate assembled context against [agent-context-pack.schema.json](assets/agent-context-pack.schema.json).
3. Sample packs: [context-pack-problem-evaluation-sample.json](assets/context-pack-problem-evaluation-sample.json) and [context-pack-solution-strategy-sample.json](assets/context-pack-solution-strategy-sample.json).
4. Reference: [context-pack-spec.md](references/context-pack-spec.md).

---

### Phase 5: Full-Text Search (FTS5) & Deduplication
1. Query the virtual full-text index `discovery_fts` using [search_discovery.py](scripts/search_discovery.py):
   ```bash
   python3 scripts/search_discovery.py "courier AND dispute" --db "discovery.sqlite"
   ```
2. Check for duplicate problem candidates before clustering new signals.
3. Automatically updates FTS5 entries during run creation, signal ingestion, and candidate upsert.

---

### Phase 6: Soft Deletion, Negative Knowledge & Single-Pane Dashboard
1. **Zero Hard Deletes**: Never execute `DELETE FROM candidates` or `DELETE FROM evidence_signals`.
2. **Negative Knowledge Preservation**:
   - Failed experiments retain `outcome_verdict = 'EXPERIMENT_FAILED'`.
   - Associated candidates transition to `validation_status = 'EXPERIMENT_FAILED'` and `lifecycle_status = 'PARKED'`.
3. **Query the Single-Pane Decision View**:
   ```bash
   python3 scripts/discovery_db.py --db "discovery.sqlite" --dashboard
   ```
   Filters candidates ready to build:
   ```sql
   SELECT candidate_id, title, solution_class, research_score 
   FROM v_discovery_dashboard 
   WHERE validation_status = 'VALIDATED' AND lifecycle_status = 'READY_TO_BUILD';
   ```

---

## Gotchas

| Naive / Speculative Approach | Principal Architect Production Reality |
|---|---|
| "Pass raw SQLite CREATE TABLE and SQL queries into agent prompts so the LLM can query the database directly." | **SQL Token Bloat & Syntax Failure**: Reasoning agents waste thousands of tokens parsing schema definitions and frequently generate invalid SQL dialect syntax. The Context Builder provides bounded, pre-queried JSON packs. |
| "Ask the LLM to count how many signals were collected from Reddit vs GitHub." | **LLM Counting Hallucination**: LLMs are notoriously unreliable at counting items in large context windows. Python computes deterministic counts and distributions with 100% mathematical certainty. |
| "Hard delete failed experiments or disqualified candidates to keep the database tidy." | **Destruction of Negative Knowledge**: Knowing what *failed* is as valuable as knowing what succeeded. Failed experiments prevent future teams from repeating the same flawed assumptions. |
| "Rely on long conversational chat histories between agents." | **Context Drift & Degradation**: Chat histories become noisy and exceed context limits. Dynamic Context Packs enable each agent to execute in an isolated, fresh turn. |
| "Use unindexed JSON queries across large datasets." | **Hybrid Claim-Check Pattern**: High-frequency filtering uses indexed relational columns (`research_score`, `lifecycle_status`), while deep nested maps live in validated JSON document columns. |
