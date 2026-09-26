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

## 💻 CLI Commands & Usage Reference

The Problem Discovery Agent CLI (`python -m agents.problem_discovery.cli`) supports single-stage execution, continuous multi-stage execution (`--until-blocked`), file-based prompts, SQLite state inspection, SeyaliCraft Build Verdict generation, and interactive REPL sessions.

### 🚀 Quick Cheat Sheet

```bash
# 1. Run detailed research from a file until paused at an experiment gate
python -m agents.problem_discovery.cli --file geo_research.txt --db-path discovery.sqlite --until-blocked

# 2. View SeyaliCraft Build Verdict (Go / No-Go decision) for all candidates
python -m agents.problem_discovery.cli --db-path discovery.sqlite --verdict

# 3. View Build Verdict for a specific candidate
python -m agents.problem_discovery.cli --db-path discovery.sqlite --verdict CAND-001

# 4. Zero-token read-only query (inspects SQLite without calling LLM)
python -m agents.problem_discovery.cli --db-path discovery.sqlite "CAND-001 status enna?"

# 5. Resume a paused research run or candidate
python -m agents.problem_discovery.cli --db-path discovery.sqlite "Continue RUN-2026-001" --until-blocked

# 6. Launch an interactive REPL shell
python -m agents.problem_discovery.cli --db-path discovery.sqlite --interactive
```

---

### 📋 CLI Options & Flags

| Flag | Shorthand | Description |
| :--- | :--- | :--- |
| `prompt` | *(positional)* | Research request string, resume instruction, experiment submission, or `@path/to/prompt.txt`. |
| `--file PATH` | `-f PATH` | Path to a UTF-8 text file containing the research prompt (avoids shell escaping). |
| `--until-blocked` | `-e`, `--end-to-end` | Runs justified stages continuously until paused at a real-world gate or completed. |
| `--verdict [ID]` | — | Prints the **SeyaliCraft Build Verdict Card** (Go / Hold / No-Go) for `ALL` or a specific candidate. |
| `--db-path PATH` | — | Overrides the discovery SQLite database (default is canonical `discovery-state/data/discovery.sqlite`). |
| `--json` | — | Emits machine-readable JSON output (includes token usage and build verdicts). |
| `--interactive` | `-i` | Launches an interactive REPL terminal session. |

---

### 📖 Workflow Examples

#### 1. Starting New Research

##### A. From a detailed text file (Recommended for complex domains):
```bash
python -m agents.problem_discovery.cli --file geo_research.txt --db-path discovery.sqlite --until-blocked
```
*Alternatively, use the `@` shorthand:*
```bash
python -m agents.problem_discovery.cli @geo_research.txt --db-path discovery.sqlite --until-blocked
```

##### B. Inline prompt string:
```bash
python -m agents.problem_discovery.cli \
  --db-path discovery.sqlite \
  --until-blocked \
  "Research whether private dental clinics face recurring inventory backorders from distributors."
```

##### C. Single-turn execution (runs only the immediate next stage, e.g. planning only):
```bash
python -m agents.problem_discovery.cli \
  --db-path discovery.sqlite \
  "Research whether freight brokers experience invoice discrepancy friction."
```

---

#### 2. Evaluating Build Decisions (SeyaliCraft Build Verdict)

The verdict engine evaluates persisted evidence against SeyaliCraft portfolio criteria (`CLIENT_SIDE_UTILITY`, `BROWSER_EXTENSION`, `STANDALONE_SAAS`, `EDUCATIONAL_GUIDE`, or `NON_SOFTWARE`):

```bash
# View Build Verdicts for all candidates in the database
python -m agents.problem_discovery.cli --db-path discovery.sqlite --verdict

# Inspect a specific candidate (e.g. CAND-001)
python -m agents.problem_discovery.cli --db-path discovery.sqlite --verdict CAND-001

# Inspect candidates in the canonical discovery-state database
python -m agents.problem_discovery.cli --verdict
```

**Example Verdict Output Card:**
```text
================================================================
 SEYALICRAFT BUILD VERDICT: CAND-001
================================================================
Title:             Dental Consumable Replenishment Stockouts
Domain:            dental_practice_supply_chain
Target Audience:   dental office manager / clinical procurement staff
Evidence Strength: Score: 24/35 | Level: L2 (6 signals)
Validation Status: IN_PROGRESS (Lifecycle: VALIDATING)
----------------------------------------------------------------
DECISION:          HOLD (VALIDATE FIRST BEFORE BUILDING)
Confidence:        MODERATE
Recommended Shape: STANDALONE_SAAS
Reversibility:     Type 1 (One-Way Door - High Resource Commitment)
----------------------------------------------------------------
Justification:
  Problem is real (Score: 24/35), but SaaS requires ongoing database and auth infra.
  Validate with a manual concierge/spreadsheet trial before scaffolding full stack.

SeyaliCraft Portfolio Fit:
  - Target Placement: app.seyalicraft.com or standalone domain
  - Tech Architecture: NestJS API + Next.js + PostgreSQL + Stripe billing
  - Monthly Infra Cost: $15 - $40 / month (VPS compute + Managed database)
  - Monetization Strategy: Recurring monthly/annual subscription ($19 - $49 / month)

Next Concrete Steps:
  1. Do NOT write backend SaaS code or provision servers yet.
  2. Run a 7-day manual concierge experiment (e.g. Google Sheets / WhatsApp template).
  3. Verify if at least 2 operators commit to paying before architecting multi-tenant database.
================================================================
```

---

#### 3. Read-Only Status & FTS Search (Zero LLM Tokens / Free)

Read-only queries use SQLite full-text search (`discovery_fts`) directly. They incur **0 API cost**:

```bash
# Check current candidate status (English or Thanglish)
python -m agents.problem_discovery.cli --db-path discovery.sqlite "CAND-001 status enna?"
python -m agents.problem_discovery.cli --db-path discovery.sqlite "What is the status of RUN-2026-001?"

# Search existing findings
python -m agents.problem_discovery.cli --db-path discovery.sqlite "ecommerce inventory sync"

# Output as JSON
python -m agents.problem_discovery.cli --db-path discovery.sqlite "CAND-001" --json
```

---

#### 4. Resuming Paused Workflows

When new signals or research data are available, resume the workflow:

```bash
# Resume an entire research run
python -m agents.problem_discovery.cli --db-path discovery.sqlite "Continue RUN-2026-001" --until-blocked

# Resume a specific candidate (e.g. advance to experiment design)
python -m agents.problem_discovery.cli --db-path discovery.sqlite "Continue CAND-001" --until-blocked
```

---

#### 5. Submitting Real-World Experiment Results

When empirical observations from a preregistered experiment trial are collected, submit them for immutable contract evaluation:

```bash
python -m agents.problem_discovery.cli --db-path discovery.sqlite \
  "EXP-001 results are ready. sample_achieved=5, observed mean=4.2, \
   artifact sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855, \
   audited_by=Murali, audit_date=2026-09-26."
```

*(If mandatory verification artifacts or sample thresholds are unmet, the experiment remains `PREREGISTERED` / `INCOMPLETE`).*

---

#### 6. Interactive REPL Mode

Launch a stateful terminal session to execute multiple queries or research commands:

```bash
python -m agents.problem_discovery.cli --db-path discovery.sqlite --interactive
```
```text
discovery> CAND-001 status enna?
discovery> Continue RUN-2026-001
discovery> exit
```

---

### ⚙️ Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(None)* | Google AI Studio / Gemini API authentication key. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Reasoning model (`gemini-3.8-flash` recommended for speed & cost). |
| `DISCOVERY_DB_PATH` | `.../discovery-state/data/discovery.sqlite` | Global fallback path for discovery database. |

---

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
