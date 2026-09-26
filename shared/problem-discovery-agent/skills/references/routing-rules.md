# Command Routing & Intent Classification Rules

## 1. Multi-Intent Routing Hierarchy

The orchestrator classifies incoming user prompts into five unambiguous operational intents:

```text
User Request
    │
    ├── 1. Read-Only Query (status, details, explain, evidence, questions)
    │      └── Action: QUERY_DATABASE -> discovery-state (FTS5 / Dashboard View)
    │
    ├── 2. Resume / Continue (continue CAND-xxx, resume RUN-xxx, continue pannu)
    │      └── Action: Determine Next Stage from SQLite -> Resume exact lifecycle point
    │
    ├── 3. Experiment Outcome Submission (observed values, artifact hashes, audit dates)
    │      └── Action: Ingest Trial Artifact -> experiment-validation [ASSESS Mode]
    │
    ├── 4. Fresh Research Topic (exploratory domain prompt)
    │      └── Action: Initialize Run -> research-planning
    │
    └── 5. Malformed or Unknown Identifier
           └── Action: Report validation error without mutating database
```

---

## 2. Intent Pattern Matching Matrix

| Intent Type | Trigger Regex / Keywords | Entity Extracted | Next Action |
| :--- | :--- | :--- | :--- |
| `READ_ONLY_QUERY` | `status`, `enna`, `irukku`, `details`, `show me`, `explain`, `\?$`, `what is` | `CAND-xxx` or `RUN-xxx` or query text | Execute `build_agent_context.py --task discovery-query` or `discovery_db.py --dashboard` |
| `CONTINUE_WORKFLOW` | `continue`, `resume`, `proceed`, `advance`, `continue pannu`, `next step` | `CAND-xxx` or `RUN-xxx` | Run `determine_next_stage.py` to route to correct next uncompleted stage |
| `SUBMIT_EXPERIMENT` | `results? ready`, `observed mean`, `artifact sha256`, `trial result`, `participants` | `EXP-xxx` or `CAND-xxx` + payload | Run `build_agent_context.py --task experiment-validation --mode ASSESS` |
| `NEW_RESEARCH` | Domain phrase (e.g. *"inventory sync in ecommerce"*, *"accountant tax reconciliation"*) | None | Initialize `research-planning` |

---

## 3. Post-Turn SQLite Re-reading Invariant

The orchestrator **MUST NEVER** trust conversational model claims regarding state advancement (e.g., *"I have completed problem evaluation and validated the candidate"*).

After any sub-skill tool invocation finishes:
1. Re-read the database via `determine_next_stage.py`.
2. Inspect the persistent row columns: `current_stage`, `validation_status`, `outcome_verdict`, `solution_class`.
3. Base subsequent routing decisions solely on the returned database state.
