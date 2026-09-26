# Problem Discovery Orchestrator Agent (`ProblemDiscoveryAgent`)

The **Problem Discovery Orchestrator Agent** is an autonomous, production-quality AI agent built with the official **Google Antigravity Python SDK** (`google-antigravity`). It transforms unstructured, natural-language problem exploration requests into an evidence-backed, persisted discovery lifecycle across five modular reasoning capabilities without requiring the user to manually sequence individual skills.

---

## Architecture

```
User (Natural Language / CLI / API)
                │
                ▼
      ProblemDiscoveryAgent
                │
                ├── IntentRouter (5 intents: NEW_RESEARCH, RESUME_RUN, RESUME_CANDIDATE, DISCOVERY_QUERY, EXPERIMENT_RESULT)
                │
                ├── DiscoveryStateMachine (Deterministic gates, lifecycle transitions, pause/resume)
                │
                ├── Modular Capability Skills (Loaded dynamically via SDK skills_paths)
                │     ├── research-planning
                │     ├── evidence-research
                │     ├── problem-evaluation
                │     ├── experiment-validation
                │     └── solution-strategy
                │
                └── DiscoveryStateTools (15 narrow tools wrapping canonical DiscoveryDB)
                                │
                                ▼
                       discovery-state (SQLite)
                     [data/discovery.sqlite]
```

### Separation of Responsibilities
* **Skill owns a capability**: The 5 reasoning skills (`research-planning`, `evidence-research`, etc.) remain modular, reference-backed, and independently reusable.
* **Orchestrator owns a workflow**: `ProblemDiscoveryAgent` coordinates the end-to-end lifecycle, determines stage transitions, and enforces stage gates.
* **Runtime owns execution**: Google Antigravity SDK manages execution, safety policies, and tool invocation.
* **Discovery-state owns persistence**: SQLite schema ownership and mutations are strictly isolated to `discovery-state`. No raw SQL is written by reasoning modules or prompts.

---

## Key Features

1. **Natural Language Routing**: Handles prompts in English or Thanglish (e.g. *"Research whether multi-channel inventory sync is a problem"*, *"Continue CAND-001"*, *"CAND-001 status enna?"*).
2. **Durable SQLite State**: Workflow resumption relies 100% on persistent SQLite state, not ephemeral chat transcripts or context memory.
3. **Deterministic Pause/Resume**: Preregistered experiments (`EXP-xxx`) cleanly pause the workflow and return precise real-world trial requirements (sample size, atomic metric, aggregation rule, artifact format, reviewer).
4. **Evidence & Scoring Invariants**: Model proposals cannot artificially elevate uninspected snippets (`SNIPPET_ONLY` stays `UNASSESSED`). High research scores (e.g. 28/35) never bypass validation gates.
5. **Principle of Least Complexity**: The agent tests non-software solutions first, strictly gates speculative SaaS proposals, and avoids unnecessary architectural complexity.
6. **Multi-Candidate Safety**: A research run remains `ACTIVE` until all linked candidates reach terminal states (`PILOT_READY`, `PARKED`, `ARCHIVED`, `BUILT`).

---

## Installation & Setup

### 1. Prerequisites
- Python >= 3.11
- Google Antigravity Python SDK (`google-antigravity`)
- Pydantic >= 2.0

### 2. Install Dependencies
```bash
pip install google-antigravity pydantic
```

### 3. Environment Configuration
```bash
# Set Gemini API Key (optional for offline state machine runs; required for live model chats)
export GEMINI_API_KEY="your-gemini-api-key"

# Optional: Override SQLite database location (default: shared/problem-discovery-suites/discovery-state/data/discovery.sqlite)
export DISCOVERY_DB_PATH="/path/to/custom/discovery.sqlite"
```

---

## Usage

### 1. Command-Line Interface (CLI)

#### Start New Research
```bash
python -m agents.problem_discovery.cli \
  "Research whether multi-channel ecommerce sellers have recurring inventory sync problems"
```

#### Resume Run or Candidate
```bash
# Resume an existing research run
python -m agents.problem_discovery.cli "Continue RUN-2026-001"

# Resume an existing candidate problem
python -m agents.problem_discovery.cli "Continue CAND-001"
```

#### Read-Only Discovery Queries
Read-only queries use `DISCOVERY_QUERY` and never advance or mutate workflow state:
```bash
# Check status in English or Thanglish
python -m agents.problem_discovery.cli "CAND-001 status enna?"
python -m agents.problem_discovery.cli "Inventory sync problem-ku namma enna evidence collect pannirukkom?"
python -m agents.problem_discovery.cli "Failed experiments irukka?"
```

#### Record Experiment Results
```bash
python -m agents.problem_discovery.cli \
  "EXP-001 results are ready. 5 participants, observed mean 4.2. Here is the artifact."
```

#### Interactive Terminal Mode
```bash
python -m agents.problem_discovery.cli --interactive
```

#### Output Machine-Readable JSON
```bash
python -m agents.problem_discovery.cli "CAND-001 status enna?" --json
```

---

### 2. Python API

```python
import asyncio
from agents.problem_discovery import ProblemDiscoveryAgent, ProblemDiscoveryConfig

async def main():
    config = ProblemDiscoveryConfig()
    agent = ProblemDiscoveryAgent(config=config)

    # Execute workflow request
    result = await agent.run("Research whether accountants have recurring reconciliation issues.")
    print("Intent:", result.intent.value)
    print("Stage:", result.current_stage.value)
    print("Status:", result.workflow_status.value)
    print("Message:\n", result.message)

    # Conversational chat
    async with ProblemDiscoveryAgent(config=config) as live_agent:
        response = await live_agent.chat("CAND-001 current status enna?")
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Experiment Pause & Resume Protocol

When an experiment is designed and preregistered, the orchestrator refuses to fabricate real-world observations and halts execution:

```text
============================================================
INTENT:    RESUME_CANDIDATE
STAGE:     EXPERIMENT_VALIDATION
STATUS:    PAUSED
CAND ID:   CAND-001
EXP ID:    EXP-001
PAUSED:    WAITING_FOR_REAL_WORLD_EXPERIMENT
============================================================

Workflow paused.

research_id: RUN-2026-001
candidate_id: CAND-001
experiment_id: EXP-001
reason: WAITING_FOR_REAL_WORLD_EXPERIMENT

Required result:
- minimum usable sample: 5
- metric: manual_sync_events_per_seller_per_week
- aggregation rule: MEAN_PER_PARTICIPANT
- artifact: CSV observation log
- named human reviewer
- review date
- SHA-256 integrity hash

Please conduct the trial and provide observed participant data to proceed.
```

When trial data is provided in a future session (`"Continue CAND-001"` or `"EXP-001 results are ready"`), the agent loads the locked contract from SQLite and audits the outcome against preregistered thresholds.

---

## Inspecting Database with DBeaver / GUI

1. Open DBeaver or your preferred SQLite viewer.
2. Connect to the SQLite file:
   `shared/problem-discovery-suites/discovery-state/data/discovery.sqlite`
3. Primary tables and views:
   - `research_runs`: High-level run records and research plans.
   - `candidates`: Evaluated problem candidates, scores, and lifecycle status.
   - `evidence_signals`: Qualified L1–L5 research signals and sources.
   - `experiments`: Immutable experiment contracts and trial assessments.
   - `discovery_fts`: Full-text search index across all entities.
   - `v_discovery_dashboard`: Real-time aggregated candidate health view.

---

## Running Automated Tests

Deterministic unit and integration tests run offline without external API dependencies:

```bash
# Run all Problem Discovery Agent tests
python -m unittest tests/test_problem_discovery_agent_router.py
python -m unittest tests/test_problem_discovery_agent_state_machine.py
python -m unittest tests/test_problem_discovery_agent_tools.py
python -m unittest tests/test_problem_discovery_agent_sdk.py

# Run entire repository test suite
python -m unittest discover tests
```
