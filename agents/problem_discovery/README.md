# Problem Discovery Orchestrator Agent

`ProblemDiscoveryAgent` is the single user-facing orchestrator for the five reusable
Problem Discovery reasoning capabilities.

It uses the official Google Antigravity Python SDK for reasoning/tool execution and
uses `discovery-state` + SQLite as the durable source of truth.

## Architecture

```text
User
  ↓
ProblemDiscoveryAgent
  ↓
IntentRouter + deterministic DiscoveryStateMachine
  ↓
exactly one justified reasoning stage
  ↓
Google Antigravity Agent
  ├─ research-planning skill
  ├─ evidence-research skill
  ├─ problem-evaluation skill
  ├─ experiment-validation skill
  └─ solution-strategy skill
  ↓
narrow DiscoveryStateTools
  ↓
canonical DiscoveryDB
  ↓
SQLite
```

The key rule is:

```text
Skill owns capability.
Orchestrator owns workflow.
Runtime owns execution.
Discovery-state owns persistence.
```

The orchestrator never contains a synthetic fallback for research evidence or
experiment execution.

## Real execution behavior

For a new research request the orchestrator:

1. reserves a stable `RUN-...` identifier without writing fake state;
2. runs only `RESEARCH_PLANNING` through Antigravity and the loaded planning skill;
3. re-reads SQLite;
4. runs `EVIDENCE_RESEARCH` using real source/web access;
5. re-reads SQLite;
6. runs `PROBLEM_EVALUATION` only from persisted evidence;
7. designs and preregisters an experiment when justified;
8. **stops at `PREREGISTERED`**.

A real-world experiment is never auto-completed.

The expected normal endpoint of an initial workflow is therefore often:

```text
workflow_status = PAUSED
pause_reason = WAITING_FOR_REAL_WORLD_EXPERIMENT
```

Only a later user submission containing the real observed result and all required
artifact/reviewer metadata can be assessed against the immutable contract.

## What is explicitly forbidden

The runtime must never create synthetic:

- Reddit/GitHub/forum evidence;
- practitioner interviews;
- source URLs;
- participant counts;
- observed experiment values;
- artifact hashes;
- reviewer names;
- audit dates;
- passing experiment outcomes.

If Antigravity/source access fails, the workflow returns an error/blocker and leaves
SQLite unadvanced.

## SDK integration

The agent uses:

```python
from google.antigravity import Agent, LocalAgentConfig
```

with:

- `skills_paths` for the six Problem Discovery suite directories;
- narrow custom Python tools from `DiscoveryStateTools`;
- read-only built-in web/file capabilities;
- policies that deny shell execution and direct file writes.

Every reasoning stage is sent through `Agent.chat(...)`; after the turn completes,
the orchestrator ignores model claims about lifecycle state and re-reads SQLite to
determine the next action.

## Database

Default:

```text
shared/problem-discovery-suites/discovery-state/data/discovery.sqlite
```

Override only when required:

```bash
export DISCOVERY_DB_PATH=/absolute/path/to/discovery.sqlite
```

The default no longer depends on the current working directory.

SQLite runtime files are ignored by Git through the repository's `*.sqlite*` /
`*.db*` rules.

## Setup

```bash
pip install google-antigravity pydantic
export GEMINI_API_KEY="..."
```

Read-only status queries can operate from SQLite without running a model. Reasoning
stages require a working Antigravity runtime/authentication configuration.

## Usage

Start research:

```bash
python -m agents.problem_discovery.cli \
  "Research whether multi-channel ecommerce sellers have recurring inventory sync problems"
```

Run with stage progress until a real gate blocks execution:

```bash
python -m agents.problem_discovery.cli --until-blocked \
  "Research whether multi-channel ecommerce sellers have recurring inventory sync problems"
```

`--end-to-end` remains a compatibility alias for `--until-blocked`. It does **not**
mean "fabricate enough data to complete every stage."

Resume:

```bash
python -m agents.problem_discovery.cli "Continue RUN-2026-001"
python -m agents.problem_discovery.cli "Continue CAND-001"
```

Read-only query:

```bash
python -m agents.problem_discovery.cli "CAND-001 current status enna?"
```

Submit a real experiment result only after the requested evidence exists:

```bash
python -m agents.problem_discovery.cli \
  "EXP-001 results are ready. sample_achieved=5, observed mean=4.2, \
   artifact sha256=<real hash>, audited_by=<reviewer>, audit_date=2026-09-26."
```

If required contract fields/artifact/reviewer evidence are missing, the agent must
leave the experiment `PREREGISTERED`.

## Python API

```python
import asyncio
from agents.problem_discovery import ProblemDiscoveryAgent, ProblemDiscoveryConfig

async def main():
    config = ProblemDiscoveryConfig()

    async with ProblemDiscoveryAgent(config=config) as agent:
        result = await agent.run(
            "Research whether accountants have recurring reconciliation problems."
        )
        print(result.workflow_status)
        print(result.message)

asyncio.run(main())
```

## Tests

```bash
python -m unittest discover tests
```

Important regression coverage includes:

- no synthetic fallback when the SDK cannot execute;
- real stage progression is driven by persisted state;
- initial research pauses at a preregistered experiment;
- no assessment row/hash/reviewer is fabricated;
- missing assessment evidence cannot default to PASS;
- read-only discovery queries do not require a live model;
- raw unassessed evidence cannot be promoted by model proposal;
- solution finalization is blocked by unfinished experiments;
- multi-candidate runs cannot complete prematurely.

A live SDK smoke test runs only when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set.
