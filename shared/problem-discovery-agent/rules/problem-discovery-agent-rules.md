---
description: "Enforces single-orchestrator problem discovery workflow, deterministic state machine stage routing, pause on preregistered experiments, and zero synthetic evidence generation."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Problem Discovery Orchestrator & Workflow Standards

## Description
This rule governs the central orchestration of the Problem Discovery lifecycle across its five reasoning capabilities (`research-planning`, `evidence-research`, `problem-evaluation`, `experiment-validation`, `solution-strategy`) and the durable persistence layer (`discovery-state`). It mandates that any agent operating as the Problem Discovery Orchestrator adhere strictly to deterministic SQLite state-machine routing, enforce the human-in-the-loop pause upon experiment preregistration, unconditionally reject the generation of synthetic evidence or simulated participant trials, and uphold the Principle of Least Complexity before recommending software builds.

## Constraints

### 1. Architectural Boundary & Concern Separation
- The orchestrator owns **workflow orchestration, state machine transitions, and user interaction**.
- Subordinate skills own **domain reasoning capabilities**:
  - `research-planning`: Decomposes raw intent into structured search contracts.
  - `evidence-research`: Inspects primary web sources and qualifies observational signals.
  - `problem-evaluation`: Clusters signals, reconstructs 14-node workflows, and scores problems.
  - `experiment-validation`: Designs immutable experiment contracts and audits trial results.
  - `solution-strategy`: Evaluates non-software sufficiency and gates SaaS proposals.
- `discovery-state` owns **relational persistence, SQLite schema integrity, and dynamic context pack assembly**.
- The orchestrator MUST NEVER merge subordinate skills into an unmaintainable monolith, bypass sub-skill validation gates, or perform ad-hoc SQL schema mutations.

### 2. Deterministic State Machine & SQLite Grounding
- The agent MUST NOT infer or hallucinate workflow stage progression based on conversational memory or language model confidence.
- Every state advancement MUST be grounded in persistent SQLite table state (`research_runs`, `candidates`, `evidence_signals`, `experiments`).
- After every stage execution or sub-skill turn, the orchestrator MUST re-inspect the database using `scripts/determine_next_stage.py` before determining the subsequent action.
- Permitted stage transitions are strictly monotonic:
  `START` $\rightarrow$ `RESEARCH_PLANNING` $\rightarrow$ `RESEARCHED` $\rightarrow$ `EVALUATED` $\rightarrow$ `VALIDATING` $\rightarrow$ `COMPLETED` (or `PARKED`).

### 3. The Preregistration Pause Invariant (Human-in-the-Loop Gate)
- When `experiment-validation` completes in `DESIGN` mode and writes an experiment record with `outcome_verdict = 'PREREGISTERED'`, the orchestrator **MUST IMMEDIATELY PAUSE EXECUTION**.
- The agent is STRICTLY FORBIDDEN from automatically proceeding to `solution-strategy` or simulating real-world participant trials within the same turn.
- Upon pause, the orchestrator MUST report:
  1. The target candidate reference (`CAND-xxx`) and operational problem statement.
  2. The preregistered experiment reference (`EXP-xxx`), primary metric, directional operator, and target sample size.
  3. Clear instructions on conducting the trial, compiling observed results into a CSV/log, computing the SHA-256 artifact digest, and recording the human auditor name.
  4. The exact continuation command for the next session:
     `/problem-discovery continue CAND-xxx` (or with trial results payload).

### 4. Zero Synthetic Evidence & Anti-Fabrication Rule
- The orchestrator and subordinate tools MUST NEVER generate synthetic:
  - Reddit, GitHub, forum, or portal links, quotes, or timestamps.
  - Participant counts, interview transcripts, or survey samples.
  - Measured quantitative metrics, error reduction rates, or test values.
  - SHA-256 cryptographic hashes or auditor signatures.
- If primary sources cannot be accessed or live web search adapters return insufficient signals, the workflow MUST report an evidence blocker and leave the database unadvanced. Fabricating data to pass validation gates is treated as a critical integrity violation.

### 5. Multi-Intent Routing Protocol
The orchestrator must classify user prompts into explicit operational intents before executing actions:
- **`READ_ONLY_QUERY`** (e.g. *"What is the status of CAND-001?"*, *"Show me evidence signals"*, *"CAND-001 status enna bro?"*):
  Execute `discovery-state` context generation or dashboard queries without creating runs or altering stages.
- **`NEW_RESEARCH`** (e.g. *"Research inventory sync in multi-channel ecommerce"*):
  Reserve a stable `RUN-YYYY-NNN` token and trigger `research-planning`.
- **`CONTINUE_WORKFLOW`** (e.g. *"continue CAND-001"*, *"resume RUN-2026-004"*):
  Inspect existing entity state via `determine_next_stage.py` and resume from the first incomplete lifecycle stage.
- **`SUBMIT_EXPERIMENT`** (observed trial metrics, sample size, SHA-256 artifact digest):
  Trigger `experiment-validation` in `ASSESS` mode. Reject assessment if required audit fields or artifact digests are missing.

### 6. Principle of Least Complexity & SaaS Gating
- Evidence of recurring operational friction does not automatically justify software. Need for software does not automatically justify a SaaS platform.
- The orchestrator MUST enforce that `solution-strategy` evaluates non-software solutions (SOPs, checklists, spreadsheets) before approving technical architecture.
- Full SaaS architecture is gated behind multi-tenancy, cross-system sync, or complex backend requirements.

## Examples

### 1. New Research Initiation & Automatic Pause at Experiment
```text
User: "/problem-discovery Research inventory sync friction among SMB multi-channel sellers"

Orchestrator Execution:
1. Calls scripts/determine_next_stage.py -> Action: INVOKE_SKILL (research-planning).
2. Generates ResearchPlan JSON and reserves RUN-2026-005 in SQLite.
3. Calls determine_next_stage.py -> Action: INVOKE_SKILL (evidence-research).
4. Inspects sources, extracts 8 qualified signals, batch inserts into evidence_signals.
5. Calls determine_next_stage.py -> Action: INVOKE_SKILL (problem-evaluation).
6. Reconstructs 14-node workflow, scores candidate (26/35), creates CAND-003.
7. Calls determine_next_stage.py -> Action: INVOKE_SKILL (experiment-validation, mode: DESIGN).
8. Preregisters EXP-007 (threshold: mismatch_rate <= 0.02, sample_target: 15).
9. Encountering outcome_verdict = 'PREREGISTERED', orchestrator PAUSES:
   "Research completed through candidate evaluation. EXP-007 is PREREGISTERED.
    Target: 15 sellers over 7 days.
    Resume later: /problem-discovery continue CAND-003 <trial_results_data>"
```

### 2. Forbidden Synthetic Trial Advancement
```text
// ❌ FORBIDDEN: Fabricating participant results in-silico to complete workflow
"Experiment EXP-007 succeeded! We simulated 15 sellers and observed a 0.01 mismatch rate.
 Moving forward to solution-strategy and designing a multi-tenant SaaS."

// ✅ CORRECT: Enforcing physical pause and requiring real-world evidence
"EXP-007 is PREREGISTERED in SQLite. The agent cannot simulate or fabricate participant
 trials. Please execute the empirical trial and submit real data to resume assessment."
```
