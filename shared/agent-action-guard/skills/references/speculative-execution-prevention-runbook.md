# Speculative Execution Prevention & Operational Runbook

## 1. The Intent × Risk Decision Table

Combine the 4-Way Intent classification with the R0–R3 Risk Taxonomy to determine the exact tool permission:

| User Intent | Risk Tier | Authorized Action |
| :--- | :--- | :--- |
| **Question** (*"Why is this slow?"*) | R0 | Inspect & diagnose in chat. **Zero file mutations.** |
| **Investigation** (*"Investigate bug"*) | R0 | Read-only profiling & searching. **Zero file mutations.** |
| **Execution** (*"Fix the bug"*) | R1 | **Execute directly.** Minimum necessary change. No ceremonial plan. |
| **Execution** (*"Upgrade NestJS dependencies"*) | R2 | **Execute if clearly implied;** confirm if scope expands unexpectedly. |
| **Execution** (*"Reset DB & clean repository"*) | R3 | **Mandatory confirmation pause.** State risks, get green-light. |
| **Plan-First** (*"Explain first, wait for me"*) | R0–R3 | Present plan & proposed diff preview in chat. **Wait for approval.** |

---

## 2. The 6-Step Progressive Inspection Algorithm

Never jump directly to whole-file or repository-wide dumps. Execute progressive inspection:

```
[Step 1: Search & Locate]   ──► grep_search to find exact symbol or function name
           │
[Step 2: Read Smallest Region] ──► view_file targeting specific 30–60 lines
           │
[Step 3: Inspect Connected Code] ──► Read imported interfaces, schemas, or tests
           │
[Step 4: Expand to Whole File]  ──► Read full file ONLY if complex intra-file coupling exists
           │
[Step 5: Expand Repository-Wide]──► Search cross-module ONLY if commanded ("scan repo")
           │
[Step 6: No Stale Rereads]      ──► Never reread unchanged files without a new hypothesis
```

---

## 3. Retry Budget & Loop Termination Protocol

When a command, test, or tool call fails:
1. **Analyze Diagnostic Output**: Inspect the stderr or stack trace thoroughly.
2. **Formulate New Hypothesis**: Identify the underlying mechanism of the failure.
3. **Change Parameters or Approach**: Modify the code or command based on the hypothesis.
4. **Halt on Repeated Failures**: If multiple successive attempts fail without progress, STOP calling tools immediately. Report the blocker clearly to the user with evidence and options.

---

## 4. The Standardized Completion Contract

Upon completing any task, emit a concise response adhering to this exact format:

```text
Changed:
- src/path/to/file.ts (lines 40–45): Fixed tax rounding calculation

Verified:
- pnpm test src/path/to/file.spec.ts: 8 tests passed, 0 failures

Remaining:
- None (or state any unresolved risks / follow-up recommendations)
```
