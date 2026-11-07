# Problem Discovery Orchestration Flow & State Machine Lifecycle

## 1. Architectural Philosophy

The Problem Discovery Orchestrator adheres strictly to the **Separation of Architectural Concerns**:

```text
Skill owns capability.
Orchestrator owns workflow.
Runtime owns execution.
Discovery-state owns persistence.
```

The orchestrator never contains synthetic fallbacks for research evidence or experiment execution. It operates as a deterministic finite-state machine over durable SQLite records, eliminating model hallucinations regarding lifecycle progression.

---

## 2. Complete Lifecycle State Topology

```mermaid
graph TD
    Start["User Prompt: /problem-discovery"] --> S0["Stage 0: Intent & State Inspection<br/>(determine_next_stage.py)"]
    
    S0 -->|New Research Query| S1["Stage 1: Research Planning<br/>(research-planning)"]
    S0 -->|Read-only Query / Status| SQ["Stage Q: Discovery Query<br/>(discovery-state FTS5 / Dashboard)"]
    S0 -->|Continue Run / Candidate| S0_Eval["Inspect Run/Candidate Record"]
    
    S1 -->|plan_json persisted, status=ACTIVE| S2["Stage 2: Evidence Research<br/>(evidence-research)"]
    S2 -->|signals saved in evidence_signals| S3["Stage 3: Problem Evaluation<br/>(problem-evaluation)"]
    
    S3 -->|candidate evaluated, validation=UNVERIFIED| S4["Stage 4: Experiment Validation [DESIGN]<br/>(experiment-validation)"]
    
    S4 --> Gate{"Experiment Preregistered?"}
    Gate -->|EXP-xxx PREREGISTERED| Pause["🛑 WORKFLOW PAUSE<br/>(WAITING_FOR_REAL_WORLD_EXPERIMENT)<br/>Stop turn & emit user trial instructions"]
    
    Pause -.->|User submits observed trial CSV/data| S5["Stage 5: Experiment Validation [ASSESS]<br/>(experiment-validation)"]
    
    S5 --> ExpVerdict{"Experiment Verdict"}
    ExpVerdict -->|PASSED| S6["Stage 6: Solution Strategy<br/>(solution-strategy)"]
    ExpVerdict -->|FAILED / INVALID| Park["Candidate Parked / Pivot<br/>(Update lifecycle in SQLite)"]
    
    S6 --> Done["Lifecycle Finalized<br/>(Single-pane dashboard updated)"]
```

---

## 3. State Machine Transitions Matrix

| Current SQLite State | Subordinate Evidence / Condition | Action Taken | Target Capability |
| :--- | :--- | :--- | :--- |
| **Uninitialized / Empty** | Fresh user topic prompt | `INVOKE_SKILL` | `research-planning` |
| `RESEARCH_PLANNING` | `plan_json` is NULL | `INVOKE_SKILL` | `research-planning` |
| `RESEARCH_PLANNING` | `plan_json` populated, signals == 0 | `INVOKE_SKILL` | `evidence-research` |
| `RESEARCHED` | Signals > 0, candidates == 0 | `INVOKE_SKILL` | `problem-evaluation` |
| `EVALUATED` | Candidate `UNVERIFIED`, experiments == 0 | `INVOKE_SKILL` (Mode: `DESIGN`) | `experiment-validation` |
| `VALIDATING` | Experiment `PREREGISTERED`, no trial data | `PAUSE_FOR_HUMAN` | *None (Wait for User)* |
| `VALIDATING` | Experiment `PREREGISTERED`, trial data supplied | `INVOKE_SKILL` (Mode: `ASSESS`) | `experiment-validation` |
| `PARTIALLY_VALIDATED` / `VALIDATED` | Candidate `solution_json` is NULL | `INVOKE_SKILL` | `solution-strategy` |
| Finalized | All candidates scored & solutions gated | `COMPLETE` | `discovery-state` |

---

## 4. The Human-in-the-Loop Pause Invariant

Real-world commercial and behavioral validation cannot be executed in-silico by an LLM.

When `experiment-validation` outputs an immutable `ExperimentContract`:
1. The experiment record is inserted into SQLite with `outcome_verdict = 'PREREGISTERED'`.
2. The orchestrator encounters the preregistration gate and **MUST immediately pause**.
3. It emits a clear summary to the user:
   - Target Candidate ID and Title
   - Pre-registered Experiment ID (`EXP-xxx`)
   - Exact primary metric, threshold, and sample size target
   - Guidance on conducting the trial and required artifact format (CSV, SHA-256 hash, auditor name)
4. It instructs the user on how to resume later:
   ```text
   /problem-discovery continue CAND-001
   ```
