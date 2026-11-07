---
name: agent-action-guard
description: "Operational workflow for the 10 Golden Rules: intent triage, progressive inspection, risk-based calibration, scope execution, proportional verification, and concise completion. Triggered by '/agent-action-guard', 'guard:', 'consult:', or 'action-guard:'."
metadata:
  framework_version: "universal-v1"
  last_verified_date: "2026-09-16"
---

# AI Coding Agent Action Guard Skill (`agent-action-guard`)

## Overview

This skill defines the **operational workflow (HOW the rules are executed)** for the 10 Golden Rules of AI Coding Agents.

> [!IMPORTANT]
> **Authoritative Policy Source**: The Golden Rules document ([rules/agent-action-guard-rules.md](../rules/agent-action-guard-rules.md)) is the authoritative source for allowed and forbidden behaviors. This skill operationalizes those constraints and MUST NOT redefine, weaken, or contradict them.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        6-Phase Action Guard Workflow                                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Intent Triage]           ──► Question vs Investigate vs Execution vs Plan-First
                │
  [Phase 2: Progressive Inspection]  ──► Smallest surface first: search → snippet → whole
                │
  [Phase 3: Scope & Risk Calibrate]  ──► Intent × Risk (R0–R3) decision table
                │
  [Phase 4: Execute Authorized Scope]──► Smallest coherent fix; preserve existing user work
                │
  [Phase 5: Proportional Verify]     ──► Level 1 (unit) → Level 2 (module) → Level 3 (monorepo)
                │
  [Phase 6: Scope Check & Stop]      ──► Final read-only diff/status check; concise report; stop
```

---

## 6-Phase Operational Workflow

### Phase 1: Intent Triage
Classify incoming user prompt into one of four intent states:
1. **Question Intent** (*"Why is X happening?"*): Read-only diagnosis; zero file edits.
2. **Investigation Intent** (*"Investigate bug Y"*): Read-only profiling and inspection; zero file edits.
3. **Execution Intent** (*"Fix Z"* / *"Implement W"*): Proceed to inspection, calibration, and execution.
4. **Plan-First Intent** (*"Explain plan, wait for approval"*): Formulate plan and proposed diff; halt for approval.

*Ambiguity Threshold*: When mutation intent is genuinely ambiguous and materially changes allowed actions, ask one minimal clarifying question. Do not ask redundant clarification for obvious execution commands.

### Phase 2: Progressive Inspection Algorithm
Execute inspection progressively to conserve context tokens and prevent speculative drift:
1. **Search / Locate**: Use `grep_search` to find relevant symbols or declarations.
2. **Read Smallest Region**: Use `view_file` on target lines (e.g. 30–60 lines) rather than entire files.
3. **Inspect Connected Code**: Check directly imported types, interfaces, or unit tests.
4. **Expand to Whole File / Module**: Read the complete file only if interconnected logic requires it.
5. **Expand Repository-Wide**: Inspect cross-module only when evidence or explicit user scope commands it (*"scan whole repo"*).
6. **No Stale Rereads**: Never reread unchanged files without a concrete hypothesis.

### Phase 3: Scope & Risk Calibration (Intent × Risk Table)
Map the classified intent against the orthogonal R0–R3 Risk Taxonomy:

| User Intent | Risk Level | Operational Policy |
| :--- | :--- | :--- |
| **Question** | R0 | Read-only inspection only. Zero mutations. |
| **Investigation** | R0 | Read-only profiling & searching. Zero mutations. |
| **Execution** | R1 (Local, Reversible) | **Execute directly.** No ceremonial planning or approval gating. |
| **Execution** | R2 (Scope-Expanding / Config) | **Execute if clearly implied;** otherwise confirm with user. |
| **Execution** | R3 (Destructive / Security) | **Mandatory explicit confirmation** before execution. |
| **Plan-First** | R0–R3 | Present plan in chat; halt until explicit user confirmation. |

### Phase 4: Execute Authorized Change
1. **Minimum Coherent Change**:
   - Apply the smallest edit capable of satisfying the task.
   - Use targeted `replace_file_content` single-chunk replacements. Full-file `write_to_file` on existing files is forbidden unless explicitly authorized.
2. **Scale to Authorized Broad Scope**:
   - When the user explicitly commands a comprehensive refactor (*"scan whole file and edit it"*), scale execution to the full authorized scope without artificial micro-edit limits.
3. **Preserve Existing User Work**:
   - Never run `git checkout .`, `git stash`, or overwrite pre-existing uncommitted modifications outside the task scope.
4. **Sensitive Paths**:
   - `.env*`, private keys, certificates, and `.git/` internals are strictly shielded from incidental edits. Template files (`.env.example`) are treated as configuration.

### Phase 5: Proportional Verification Escalation
Verify changes using tiered escalation based on evidence:
- **Level 1 (Narrow)**: Run the specific unit test, typecheck, or linter for the modified component (e.g. `pnpm test path/to/service.spec.ts`).
- **Level 2 (Package / Module)**: Run package-level checks only if the change affects shared module exports or inter-service contracts.
- **Level 3 (Broader Build / E2E)**: Run full builds or E2E suites only when risk, regression evidence, or explicit user instruction justifies it.

*Never jump automatically to Level 3 for localized, reversible fixes.*

### Phase 6: Final Scope Check & Concise Report
1. **Final Scope / Diff Inspection**:
   - After behavioral verification, perform only the minimal read-only final scope check (`git status -s` or targeted `git diff`) to confirm no unintended files, secret leaks, or formatting noise were introduced.
2. **Halt Tool Use**: Stop all tool calls immediately after the final check.
3. **Standardized Completion Contract**: Emit a concise response adhering to:
   ```text
   Changed:
   - [File path]: [concise summary of changes; include line numbers only if already known]

   Verified:
   - [Command executed]: [pass/fail status]

   Remaining:
   - [Blockers or unresolved risks, only if applicable]
   ```
   *Never perform additional tool calls solely to obtain line numbers for the completion report.*

---

## Retry Budget & Loop Termination Protocol

When a command, test, or tool call fails:
```
Failure Detected ──► Inspect Error Output ──► Form New Hypothesis ──► Change Code/Config ──► Retry
```
- **Valid Retries**: Retrying the same test/command is completely valid after a relevant code, configuration, or dependency change.
- **Prohibition of Blind Retries**: Never execute an identical command against materially unchanged state without new evidence or a changed hypothesis.
- **Termination Threshold**: After repeated materially failed attempts without progress, STOP immediately, state the root blocker clearly, and prompt for human guidance.

---

## Authoritative References & Bundled Assets

- **Golden Rules Policy (Authoritative)**: [rules/agent-action-guard-rules.md](../rules/agent-action-guard-rules.md)
- **Action Boundaries & HITL Guide**: [references/agent-action-boundaries-and-hitl.md](references/agent-action-boundaries-and-hitl.md)
- **Intent Triage & Runbook**: [references/speculative-execution-prevention-runbook.md](references/speculative-execution-prevention-runbook.md)
- **Tool Call Safety Auditor**: [scripts/audit_tool_safety.py](scripts/audit_tool_safety.py)
- **Policy Schema**: [assets/action-guard-policy-schema.json](assets/action-guard-policy-schema.json)
- **Permission Request Template**: [assets/permission-request-template.md](assets/permission-request-template.md)
- **Empirical Evals Suite**: [evals/evals.json](evals/evals.json)

---

## Automated Verification Protocol

Run automated safety audit against a proposed response or tool trace:
```bash
python3 scripts/audit_tool_safety.py --file response.txt --strict
```

Run full skill validation:
```bash
python3 shared/generators/generate-skill/skills/scripts/validate_skill.py shared/agent-action-guard/skills
```

---

## Gotchas & Anti-Patterns

| Anti-Pattern | Why It Fails | Modern Golden Rule Standard |
| :--- | :--- | :--- |
| **Blind Retries on Unchanged State** | Repeats failed command 5 times without editing code, burning tokens. | Diagnose failure, change code/state, then retest. Stop if blocked. |
| **Skipping Final Diff Scope Check** | Leaves accidental console.logs, formatting diffs, or temp files in git. | Minimal read-only final diff check confirms clean blast radius. |
| **Tool Calling Solely for Line Numbers** | Wastes 2-3 extra tool calls just to calculate line numbers for reporting. | Line numbers optional: report file + summary without extra calls. |
| **Treating `.env.example` as a Secret** | Refuses to document new environment variables in config templates. | `.env*` secrets are protected; `.env.example` templates are editable. |
