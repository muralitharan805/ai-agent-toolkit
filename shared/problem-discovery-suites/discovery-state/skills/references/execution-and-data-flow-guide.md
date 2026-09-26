# Problem Discovery: End-to-End Execution & Data Flow Guide

> **Purpose:** Master visual reference guide explaining how each slash command interacts with SQLite tables, what context the agent reads, and what data gets written back at every stage.  
> **Source Database:** `discovery.sqlite` (Hybrid 4-Table Relational + JSON Store)  
> **Updated:** 2026-09-26  

---

## 🏛️ Problem Discovery Suite Topology

| Stage | Suite Name | Type | Directory | Core Responsibility |
|:---:|:---|:---:|:---|:---|
| **01** | `research-planning` | Reasoning | `shared/problem-discovery-suites/research-planning/` | Slot filling, domain decomposition, precision search dorks & MECE streams. |
| **02** | `evidence-research` | Reasoning | `shared/problem-discovery-suites/evidence-research/` | Search execution, source inspection, raw `UNASSESSED` capture, and evidence qualification. |
| **03** | `problem-evaluation` | Reasoning | `shared/problem-discovery-suites/problem-evaluation/` | Forensic 14-node workflow mapping, root-cause isolation & 35-point scoring. |
| **04** | `experiment-validation` | Reasoning | `shared/problem-discovery-suites/experiment-validation/` | Preregistered experiment contracts (DESIGN) & empirical trial audits (ASSESS). |
| **05** | `solution-strategy` | Reasoning | `shared/problem-discovery-suites/solution-strategy/` | Non-software sufficiency, 15-flag constraints, SaaS gating & 14-day STS design. |
| **06** | `discovery-state` | Infrastructure | `shared/problem-discovery-suites/discovery-state/` | SQLite persistence, deterministic math, dynamic context packs & `v_discovery_dashboard`. |

---

## 🧭 1. High-Level Lifecycle & Data Flow Topology

```text
User Question / Domain Prompt
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: /research-planning "<domain idea>"                                 │
│  - Reads Context  : None (Fresh Idea)                                       │
│  - Agent Task     : Slot extraction (Domain, Operator), 5-stream dorks      │
│  - Writes State   : ───► DiscoveryDB.create_research_run(plan_dict)         │
│                          Table: research_runs (RUN-YYYY-NNN)                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: /evidence-research <RUN-ID>                                        │
│  - Reads Context  : SELECT plan_json FROM research_runs                     │
│  - Agent Task     : Live search + source inspection; raw hits stay UNASSESSED │
│  - Writes State   : ───► DiscoveryDB.save_evidence_signals(signals_list)    │
│                          Table: evidence_signals (candidate_id = NULL)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔄 DISCOVERY-STATE INPUT: Context Pack Compiler                             │
│  - CLI Input      : build_agent_context.py --task problem-evaluation        │
│                                           --research-id RUN-YYYY-NNN        │
│  - Action         : Fetches unlinked signals + run plan + calculates math   │
│  - Emits          : JSON Context Pack (Zero LLM counting hallucination)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: /problem-evaluation <RUN-ID>                                       │
│  - Reads Context  : JSON Context Pack (from build_agent_context.py)         │
│  - Agent Task     : 14-node workflow, root causes, 35-pt evidence gate      │
│  - Writes State   : ───► DiscoveryDB.upsert_candidate(evaluation_dict)      │
│                          Table: candidates (CAND-NNN) & links signals       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔄 DISCOVERY-STATE INPUT: Experiment Context Compiler                       │
│  - CLI Input      : build_agent_context.py --task experiment-validation     │
│                                           --candidate-id CAND-NNN           │
│  - Action         : Fetches candidate evaluation + historical trial counts  │
│  - Emits          : JSON Context Pack for experiment designer/auditor       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: /experiment-validation <CAND-ID>                                   │
│  - Reads Context  : JSON Context Pack (from build_agent_context.py)         │
│  - Agent Task     : [DESIGN] 14-day falsifiable contract & thresholds       │
│                     [ASSESS] Audit trial logs & SHA-256 artifact hash        │
│  - Writes State   : ───► DiscoveryDB.preregister_experiment(contract_dict)  │
│                          Table: experiments (EXP-YYYY-NNN) & updates status │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔄 DISCOVERY-STATE INPUT: Solution Strategy Compiler                        │
│  - CLI Input      : build_agent_context.py --task solution-strategy         │
│                                           --candidate-id CAND-NNN           │
│  - Action         : Fetches candidate + validated experiment outcomes       │
│  - Emits          : JSON Context Pack for architecture sizing & gating      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: /solution-strategy <CAND-ID>                                       │
│  - Reads Context  : JSON Context Pack (from build_agent_context.py)         │
│  - Agent Task     : 15-point constraints, Non-software gate, SaaS rejection,│
│                     Select Solution Class, Design 14-day STS                 │
│  - Writes State   : ───► DiscoveryDB.finalize_solution(solution_dict)       │
│                          Table: candidates (solution_class, PILOT_READY)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏁 MASTER SINGLE-PANE DECISION VIEW & SEARCH (discovery-state)              │
│  - Dashboard CLI  : discovery_db.py --dashboard [--filter-status <STATUS>]  │
│  - FTS5 Search    : search_discovery.py "<query>"                           │
│  - SQL View       : SELECT * FROM v_discovery_dashboard;                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 📥 How Input is Provided to Discovery State (3 Modalities)

`discovery-state` operates as the central blackboard. Input is provided to it through three distinct modalities:

#### 1. Direct CLI Input (User & Developer Controls):
| Command | What Input You Provide | What Discovery-State Does |
| :--- | :--- | :--- |
| `init_db.py [--db <path>]` | Target `.sqlite` path (optional) | Creates 4 relational tables, FTS5 virtual table, triggers, and sets `PRAGMA journal_mode=WAL;`. |
| `build_agent_context.py` | `--task <stage>` and `--research-id <ID>` or `--candidate-id <ID>` | Extracts normalized records from SQLite, deterministically computes counts, and emits a clean JSON Context Pack to `stdout`. |
| `discovery_db.py --dashboard` | Optional `--filter-status <STATUS>` | Reads flattened metrics from `v_discovery_dashboard` view and prints a formatted terminal table. |
| `discovery_db.py --search "<term>"` | Natural language query string | Runs instant BM25 full-text search across `discovery_fts` index. |
| `search_discovery.py "<term>"` | Query string with optional `--type SIGNAL\|RUN\|CANDIDATE` | Executes typed BM25 ranking across all discovery tables with snippet highlighting. |

#### 2. Dynamic Context Pack Input (Bridge to Reasoning Agents):
When invoking any reasoning agent turn, the agent receives its input by reading the output of `build_agent_context.py`:
- **For Stage 3 (`problem-evaluation`):**
  - **Input Provided:** `build_agent_context.py --task problem-evaluation --research-id RUN-2026-001`
  - **What Discovery-State Compiles:** Ingests unlinked `evidence_signals` (`candidate_id IS NULL`), counts signals by platform/level, and bundles them with the original `ResearchPlan`.
- **For Stage 4 (`experiment-validation`):**
  - **Input Provided:** `build_agent_context.py --task experiment-validation --candidate-id CAND-001 [--mode DESIGN|ASSESS]`
  - **What Discovery-State Compiles:** Ingests candidate profile, 14-node friction summary, and prior experiment history.
- **For Stage 5 (`solution-strategy`):**
  - **Input Provided:** `build_agent_context.py --task solution-strategy --candidate-id CAND-001`
  - **What Discovery-State Compiles:** Ingests candidate profile, 14-node workflow, experiment validation verdicts (`PASSED`), and operational metrics.

#### 3. Automated Script & API Input (`DiscoveryDB` Python Client):
All pipeline reasoning tools feed structured payloads into `discovery-state` via the canonical `DiscoveryDB` interface:
```python
from discovery_db import DiscoveryDB
db = DiscoveryDB()  # Automatically resolves DISCOVERY_DB_PATH or ./discovery.sqlite

# Stage 1 input -> db.create_research_run(...)
# Stage 2 input -> db.save_evidence_signals(...)
# Stage 3 input -> db.upsert_candidate(...)
# Stage 4 input -> db.preregister_experiment(...) / db.record_experiment_assessment(...)
# Stage 5 input -> db.finalize_solution(...)
```

#### 4. Environment Configuration Input:
- **`DISCOVERY_DB_PATH`**: Set this environment variable (e.g. `export DISCOVERY_DB_PATH="/custom/path/discovery.sqlite"`) to redirect all CLI tools, scripts, and views to a specific database location without modifying code.

---

## 🔍 2. Detailed Stage-by-Stage Data Flow Matrix

### Stage 1: Scope & Research Planning
*When you start a fresh problem exploration or brain-dump.*

- **Trigger Command:**  
  ```bash
  /research-planning "Small ecommerce sellers who sell across multiple marketplaces have trouble keeping inventory quantities synchronized..."
  ```
- **What Input You Provide:**  
  Raw, unstructured user prompt, business problem observation, or domain idea.
- **Context Agent Ingests:**  
  - No database context required (unless repeat-domain search check is performed).
  - Agent loads `shared/problem-discovery-suites/research-planning/skills/SKILL.md`.
- **What Agent Does (Cognitive Reasoning):**  
  - Strips conversational noise and extracts slots: `Domain`, `Geography`, `Operator`, `Task`, `Friction`.
  - Generates 5 precision search streams (Atomic Search Units: Community, Filetypes, Jobs, Software Gaps, Regional).
  - Emits the structured `ResearchPlan` contract.
- **Database Mutation (Where Data is Written):**
  - **Table:** `research_runs`
  - **Action:** `INSERT`
  - **Key Fields Written:**
    - `research_id`: Generated identifier (e.g. `'RUN-2026-001'`).
    - `original_request`: Verbatim prompt text.
    - `domain`: Normalized domain slug (e.g. `'multi_marketplace_inventory_sync'`).
    - `current_stage`: `'EVIDENCE_RESEARCH'`.
    - `status`: `'ACTIVE'`.
    - `plan_json`: Complete `ResearchPlan` document with queries and streams.

---

### Stage 2: Evidence & Live Signal Research
*When you have a planned research run and need real-world practitioner evidence.*

- **Trigger Command:**  
  ```bash
  /evidence-research RUN-2026-001
  ```
- **What Input You Provide:**  
  The `research_id` output by Stage 1.
- **Context Agent Ingests:**  
  - Reads `plan_json` from table `research_runs` where `research_id = 'RUN-2026-001'`.
- **What Agent Does (Cognitive Reasoning):**  
  - Runs search queries across GitHub Issues, Reddit, and Hacker News via `collect_research_signals.py`.
  - Inspects primary source URLs, extracts verbatim quotes, timestamps, and classifications.
  - Assigns Evidence Levels (`L1` to `L5`). **Hard boundary: Agent never scores or clusters problems here.**
- **Database Mutation (Where Data is Written):**
  - **Table 1:** `evidence_signals`
    - **Action:** `INSERT` (typically 10–50 rows).
    - **Key Fields Written:**
      - `signal_id`: `'SIG-RUN-2026-001-001'`, `'SIG-RUN-2026-001-002'`, etc.
      - `research_id`: `'RUN-2026-001'`.
      - `candidate_id`: `NULL` *(Intentionally NULL! Candidates do not exist yet).*
      - `platform`: `'GITHUB'`, `'REDDIT'`, `'HACKERNEWS'`.
      - `source_url`: Verbatim URL.
      - `reported_issue`: Direct complaint statement.
      - `evidence_level`: Raw/snippet hits are `'UNASSESSED'`; inspected evidence may later qualify as `L1`–`L5`.
      - `payload_json`: Raw API metadata.
  - **Table 2:** `research_runs`
    - **Action:** `UPDATE`
    - `current_stage`: `'PROBLEM_EVALUATION'`.

---

### Stage 3: Problem Evaluation & 14-Node Mapping
*When evidence signals are collected and need forensic analysis, clustering, and scoring.*

- **Trigger Command:**  
  ```bash
  /problem-evaluation RUN-2026-001
  ```
- **What Input You Provide:**  
  The `research_id` containing collected signals.
- **Context Agent Ingests:**  
  - Assembled automatically via `build_agent_context.py --task problem-evaluation --research-id RUN-2026-001`.
  - Dynamic Context Pack containing:
    - `research_run` metadata & plan unknowns.
    - All unlinked rows from `evidence_signals` (`candidate_id IS NULL`).
    - Deterministic signal counts & platform distributions computed in Python.
- **What Agent Does (Cognitive Reasoning):**  
  - Clusters signals into a discrete problem candidate.
  - Maps the **14-node forensic workflow** (Trigger $\to$ Glue Work $\to$ Errors $\to$ Cost $\to$ Risk).
  - Evaluates root causes and audits alternatives (competitors, spreadsheets, SOPs).
  - Applies 35-point evidence-gated scoring (caps scores based on evidence level).
- **Database Mutation (Where Data is Written):**
  - **Table 1:** `candidates`
    - **Action:** `INSERT` (or upsert via `score_problem_candidate.py --save-db`).
    - **Key Fields Written:**
      - `candidate_id`: `'CAND-001'`.
      - `origin_research_id`: `'RUN-2026-001'`.
      - `title`: Problem title.
      - `domain`: Domain classification.
      - `target_operator`: Human experiencing the pain (e.g. `'small ecommerce merchant'`).
      - `track`: `'COMMERCIAL'` or `'FREE_UTILITY'`.
      - `research_score`: `0` to `35` (e.g. `30`).
      - `evidence_level`: Deterministically derived usable level from the linked supporting signals; caller/model labels cannot upgrade it.
      - `validation_status`: `'UNVERIFIED'` (or `'IN_PROGRESS'`).
      - `lifecycle_status`: `'RESEARCH_PRIORITY'` or `'EXPERIMENT_DESIGNED'`.
      - `evaluation_json`: 14-node map, root causes, 35-pt subscores.
  - **Table 2:** `evidence_signals`
    - **Action:** `UPDATE`
    - `UPDATE evidence_signals SET candidate_id = 'CAND-001' WHERE signal_id IN (...)` *(Permanently links supporting signals to this candidate)*.
  - **Table 3:** `research_runs`
    - **Action:** `UPDATE`
    - `current_stage`: `'EXPERIMENT_VALIDATION'`.

---

### Stage 4: Experiment Validation & Falsifiable Contracts
*When a scored candidate needs empirical field verification.*

- **Trigger Command:**  
  ```bash
  /experiment-validation CAND-001
  ```
- **What Input You Provide:**  
  The `candidate_id` output by Stage 3.
- **Context Agent Ingests:**  
  - Assembled via `build_agent_context.py --task experiment-validation --candidate-id CAND-001`.
  - Ingests candidate title, operator, friction metrics, and evaluation summary.
- **What Agent Does (Cognitive Reasoning):**  
  - Operates in one of two strict modes:
    - **`DESIGN` Mode** *(Default when real trials haven't occurred)*:
      - Defines a 14-day empirical experiment with strict numeric thresholds (e.g. "$\ge 4$ of 10 merchants complete 14 days and confirm sync lag $< 2$ mins").
      - Establishes unambiguous failure rules; database verdicts are `PASSED`, `FAILED`, `INCOMPLETE`, or `INVALID`.
    - **`ASSESS` Mode** *(When user provides real participant logs)*:
      - Audits observed data against the locked thresholds.
      - Computes local artifact SHA-256 digest and records human auditor name.
- **Database Mutation (Where Data is Written):**
  - **Table 1:** `experiments`
    - **Action:** `INSERT` or `UPDATE`
    - **Key Fields Written:**
      - `experiment_id`: `'EXP-2026-001'`.
      - `candidate_id`: `'CAND-001'`.
      - `hypothesis`: Falsifiable test statement.
      - `metric_name`: Primary KPI measured.
      - `target_threshold`: Numeric bar (e.g. `4.0`).
      - `outcome_verdict`: `'PREREGISTERED'` (in DESIGN mode) OR `'PASSED'` / `'FAILED'` (in ASSESS mode).
      - `contract_json`: Locked experiment contract.
      - `artifact_hash`: SHA-256 checksum of evidence file.
  - **Table 2:** `candidates`
    - **Action:** `UPDATE`
    - `validation_status`: A passed claim normally becomes `PARTIALLY_VALIDATED`; a failed individual experiment keeps the candidate under `IN_PROGRESS` research/validation review.
    - `lifecycle_status`: Updates to `'EXPERIMENT_DESIGNED'` or `'PARKED'`.

---

### Stage 5: Solution Strategy & Architecture Gating
*When a validated problem is ready for architecture sizing and the smallest testable solution.*

- **Trigger Command:**  
  ```bash
  /solution-strategy CAND-001
  ```
- **What Input You Provide:**  
  The `candidate_id`.
- **Context Agent Ingests:**  
  - Assembled via `build_agent_context.py --task solution-strategy --candidate-id CAND-001`.
  - Ingests candidate evaluation, experiment trial counts, and outcome verdicts.
- **What Agent Does (Cognitive Reasoning):**  
  - Audits **15 operational constraints** (single-user vs multi-user, cloud sync, background execution, latency).
  - **Non-Software Sufficiency Gate:** Tests whether a Notion template, checklist, or spreadsheet solves the problem.
  - **SaaS Justification Gate:** Strictly rejects SaaS unless multi-user shared state and centralized synchronization are mandatory.
  - Selects smallest justified Solution Class (e.g. `INTEGRATION_SERVICE`, `CLI_UTILITY`, `BROWSER_EXTENSION`, `MICRO_SAAS`).
  - Designs a **14-day Smallest Testable Solution (STS)**.
- **Database Mutation (Where Data is Written):**
  - **Table:** `candidates`
    - **Action:** `UPDATE` (via `evaluate_solution_strategy.py`)
    - **Key Fields Written:**
      - `solution_class`: Selected architecture class (e.g. `'INTEGRATION_SERVICE'`).
      - `lifecycle_status`: Validated candidates may transition to `'PILOT_READY'`; otherwise a draft assessment remains `'SOLUTION_PROPOSED'`.
      - `solution_json`: 15-flag constraints audit, SaaS justification verdict, and 14-day STS design.
  - **Table:** `research_runs`
    - **Action:** `UPDATE`
    - `current_stage`: `'COMPLETED'`.
    - `status`: `'COMPLETED'`.

---

### Component 06: Discovery State & Dynamic Context Engine
*The central infrastructure backbone managing SQLite persistence, schema migrations, and deterministic context assembly.*

- **Role:** Dedicated infrastructure capability (NOT an AI reasoning agent). It executes zero prompts and holds zero opinions. It enforces 100% deterministic schema contracts, mathematical aggregations, and context assembly.
- **Why It Exists (The Blackboard Architecture):**
  1. **Zero SQL in Prompts:** Upstream and downstream reasoning agents never see raw SQL DDL (`CREATE TABLE`, `ALTER TABLE`) or write complex JOIN queries. This saves context tokens and prevents LLM SQL syntax errors.
  2. **Zero LLM Counting Hallucinations:** LLMs frequently hallucinate counts (e.g. claiming 18 signals exist when 14 were retrieved). `discovery-state` deterministically calculates signal counts, platform distributions, and trial pass rates in Python.
  3. **Conversational Independence:** You can invoke any stage in a completely fresh conversation turn. You do not need a long, degraded chat history because `build_agent_context.py` compiles the exact state required from SQLite.

#### The 4 Command-Line Tools in `discovery-state`:

1. **`init_db.py` (Database Bootstrapper):**
   - **Command:**  
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/init_db.py [--db discovery.sqlite]
     ```
   - **Action:** Creates tables (`research_runs`, `evidence_signals`, `candidates`, `experiments`), provisions FTS5 virtual table (`discovery_fts`), creates indexes, configures `PRAGMA journal_mode = WAL;` and `PRAGMA foreign_keys = ON;`, and builds the `v_discovery_dashboard` view.

2. **`build_agent_context.py` (Dynamic Context Pack Compiler):**
   - **Command for Stage 3 (Problem Evaluation):**
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/build_agent_context.py \
       --task problem-evaluation --research-id RUN-2026-001
     ```
     - **What it reads from SQLite:** Parent row from `research_runs` + all unlinked rows from `evidence_signals` where `candidate_id IS NULL`.
     - **What it compiles (JSON Output):** Injects `total_signals`, `platforms_summary`, `evidence_levels_summary`, and all raw signal observations into a single clean JSON pack for the evaluation agent.
   - **Command for Stage 4 (Experiment Validation):**
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/build_agent_context.py \
       --task experiment-validation --candidate-id CAND-001 --mode DESIGN
     ```
     - **What it reads from SQLite:** `candidates` record, its 14-node evaluation summary, and prior experiment history.
     - **What it compiles (JSON Output):** Injects candidate title, target operator, friction metrics, and trial counts for the experiment designer.
   - **Command for Stage 5 (Solution Strategy):**
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/build_agent_context.py \
       --task solution-strategy --candidate-id CAND-001
     ```
     - **What it reads from SQLite:** `candidates` row + all associated rows in `experiments`.
     - **What it compiles (JSON Output):** Injects candidate evaluation, 14-node workflow, experiment outcome verdicts (`PASSED`/`FAILED`), and known constraints.

3. **`discovery_db.py` (Canonical State Manager & Dashboard):**
   - **View Dashboard:**
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/discovery_db.py --dashboard
     ```
   - **Filter Dashboard by Status:**
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/discovery_db.py --dashboard --filter-status PILOT_READY
     ```
   - **FTS5 Keyword Search:**
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/discovery_db.py --search "inventory desync"
     ```

4. **`search_discovery.py` (Full-Text Search Dispatcher):**
   - **Command:**  
     ```bash
     python3 shared/problem-discovery-suites/discovery-state/skills/scripts/search_discovery.py "overselling AND cancellation" [--type SIGNAL]
     ```
   - **Action:** Queries the FTS5 full-text index across runs, candidates, and collected signals with sub-millisecond BM25 ranking.

---

#### The 4-Table Relational + JSON Schema Blueprint:

```text
┌───────────────────────────────┐
│         research_runs         │
├───────────────────────────────┤
│ research_id (PK)              │◄───────┐
│ original_request (TEXT)       │        │ (1:N)
│ domain (TEXT)                 │        │
│ current_stage (TEXT)          │        │
│ plan_json (JSON)              │        │
└───────────────┬───────────────┘        │
                │ (1:N)                  │
                ▼                        │
┌───────────────────────────────┐        │
│       evidence_signals        │        │
├───────────────────────────────┤        │
│ signal_id (PK)                │        │
│ research_id (FK) ─────────────┼────────┘
│ candidate_id (FK, NULLABLE) ──┼────────┐
│ platform (TEXT)               │        │
│ source_url (TEXT)             │        │
│ reported_issue (TEXT)         │        │ (N:1, linked at Stage 3)
│ evidence_level (L1-L5)        │        │
│ payload_json (JSON)           │        │
└───────────────────────────────┘        │
                                         ▼
                        ┌───────────────────────────────┐
                        │          candidates           │
                        ├───────────────────────────────┤
                        │ candidate_id (PK)             │◄───────┐
                        │ origin_research_id (FK)       │        │
                        │ title (TEXT)                  │        │ (1:N)
                        │ research_score (INTEGER, 0-35)│        │
                        │ validation_status (TEXT)      │        │
                        │ lifecycle_status (TEXT)       │        │
                        │ solution_class (TEXT)         │        │
                        │ evaluation_json (JSON)        │        │
                        │ solution_json (JSON)          │        │
                        └───────────────┬───────────────┘        │
                                        │ (1:N)                  │
                                        ▼                        │
                        ┌───────────────────────────────┐        │
                        │          experiments          │        │
                        ├───────────────────────────────┤        │
                        │ experiment_id (PK)            │        │
                        │ candidate_id (FK) ────────────┼────────┘
                        │ hypothesis (TEXT)             │
                        │ metric_name (TEXT)            │
                        │ target_threshold (REAL)       │
                        │ outcome_verdict (TEXT)        │
                        │ contract_json (JSON)          │
                        │ assessment_json (JSON)        │
                        │ artifact_hash (SHA-256)       │
                        └───────────────────────────────┘
```

---

### Guardrail Invariants

- Search result or snippet is not verified evidence; raw collection defaults to `UNASSESSED`.
- Planned operator is research context, not observed actor identity.
- Candidate evidence level and 35-point score are recomputed from persisted supporting signals.
- Official policy evidence can prove policy/consequence but does not by itself establish behavioral L1.
- An experiment must have one atomic primary metric and a preregistered aggregation rule.
- One passed experiment does not imply market demand, willingness-to-pay, adoption, or retention validation.
- A single finalized candidate cannot complete a research run while another attached candidate is still active.

---

#### Canonical `DiscoveryDB` Client Methods (Python Interface):

Every reasoning script interacts with SQLite exclusively through these 7 methods:
- `create_research_run(research_id, request, domain, scope_type, geography, plan_dict)` $\to$ Inserts run, sets `stage='EVIDENCE_RESEARCH'`.
- `save_evidence_signals(research_id, signals_list)` $\to$ Bulk inserts normalized signals with `candidate_id=NULL`, updates run to `stage='PROBLEM_EVALUATION'`.
- `upsert_candidate(candidate_id, research_id, title, ..., evaluation_dict, supporting_signal_ids)` $\to$ Upserts candidate, atomically links supporting signal rows, advances run to `stage='EXPERIMENT_VALIDATION'`.
- `preregister_experiment(experiment_id, candidate_id, contract_dict)` $\to$ Inserts an immutable contract with `verdict='PREREGISTERED'` and updates the candidate to `validation_status='IN_PROGRESS'`, `lifecycle='VALIDATING'`.
- `record_experiment_assessment(experiment_id, assessment_dict, artifact_hash, ...)` $\to$ Verifies the locked threshold, sample, artifact, and human review; stores `PASSED` / `FAILED` / `INCOMPLETE` / `INVALID` and updates claim-scoped candidate validation.
- `finalize_solution(candidate_id, solution_class, solution_dict)` $\to$ Rejects unfinished experiments, stores the smallest justified solution, and uses `PILOT_READY` only when validation supports it. The run completes only when every attached candidate is terminal.
- `get_discovery_dashboard(status_filter=None)` $\to$ Returns flattened single-pane rows directly from `v_discovery_dashboard`.

---

## 📊 3. How to Check Your Decision Dashboard

At any stage of research, you never need to join multiple tables manually. The single-pane view `v_discovery_dashboard` flattens all metrics into one clean table.

### CLI Command:
```bash
python3 shared/problem-discovery-suites/discovery-state/skills/scripts/discovery_db.py --dashboard
```

### Direct SQLite SQL:
```sql
SELECT 
    candidate_id, 
    title, 
    research_score, 
    evidence_level, 
    validation_status, 
    solution_class, 
    lifecycle_status, 
    total_evidence_count,
    latest_experiment_verdict
FROM v_discovery_dashboard;
```

### Example Real-World Output:
| candidate_id | title | score | evidence | validation | solution_class | lifecycle | total_evidence | latest_experiment |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :---: | :--- |
| `CAND-001` | Multi-Marketplace Inventory Desynchronization | 30/35 | L3 | `PARTIALLY_VALIDATED` | `INTEGRATION_SERVICE` | `PILOT_READY` | 6 | `PASSED` |

---

## 💡 Quick Rules of Thumb

1. **Where does the database live?**
   - Default: `./discovery.sqlite` (workspace root).
   - Override anytime via `export DISCOVERY_DB_PATH="/path/to/custom.sqlite"`.
2. **Do I need `pip install`?**
   - **No.** All 9 Python scripts rely exclusively on the built-in Python standard library (`sqlite3`, `json`, `urllib`).
3. **What if an experiment fails?**
   - The record is **NEVER deleted**. The experiment remains `FAILED` as negative knowledge; the candidate can remain `IN_PROGRESS` / `RESEARCH_PRIORITY` while the orchestrator decides whether to retry, gather evidence, park, or archive it.
