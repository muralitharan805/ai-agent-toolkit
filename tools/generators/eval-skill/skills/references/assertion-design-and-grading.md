# Assertion Design & Quality Grading Guide

## 1. Overview
In the Agent Skills Open Standard (`agentskills.io`), **Evals** are the empirical verification mechanism that proves an agent skill actually improves AI performance. The core unit of evaluation is the **Objective Assertion**.

Subjective grading ("code looks neat", "well designed") is strictly prohibited. Every assertion must be binary, verifiable, and backed by concrete evidence from the generated output.

---

## 2. Objective vs Subjective Assertions

| Anti-Pattern (Subjective / Vague) | Production-Grade (Objective & Verifiable) |
| :--- | :--- |
| ❌ "Output uses good TypeScript code" | ✅ "All exported functions have explicit return type annotations with zero `any` types" |
| ❌ "Form handles errors nicely" | ✅ "Uses centralized `<app-form-error [control]='...' />` presenter rather than inline `@if` checks" |
| ❌ "Database is secured" | ✅ "Queries use parameterized Prisma client calls; zero raw string concatenation in SQL" |
| ❌ "Includes deployment instructions" | ✅ "Provides exact `./bin/sync-context.sh --global [path]` command in the output" |
| ❌ "Component is reactive" | ✅ "Uses `signal()` and `computed()` primitives instead of RxJS `BehaviorSubject` for local component state" |

---

## 3. The 4 Assertion Archetypes

When designing assertions for `evals/evals.json`, combine these 4 archetypes:

### 1. Structural / File Assertions
Verifies that expected files, directories, or schemas exist:
- `"Scaffolds modular bundle with references/, scripts/, assets/, and evals/ directories"`
- `"YAML frontmatter contains name matching parent directory and valid description"`

### 2. Syntax & Invariant Prohibitions (Negative Checks)
Verifies that forbidden patterns are absent:
- `"Zero 'any' types present across all generated source files"`
- `"Does not generate deprecated standalone .agents/workflows/*.md files"`
- `"No raw unparameterized SQL queries in repository services"`

### 3. API & Framework Correctness (Positive Checks)
Verifies that modern framework idioms are used:
- `"Uses inject(FormBuilder).nonNullable to guarantee non-nullable default form semantics"`
- `"Applies takeUntilDestroyed() to all observable subscriptions"`
- `"Configures changeDetection: ChangeDetectionStrategy.OnPush"`

### 4. Protocol & Lifecycle Adherence
Verifies that operational sequences are satisfied:
- `"Executes form.markAllAsTouched() prior to checking validity"`
- `"Extracts submission payload using form.getRawValue() instead of form.value"`

---

## 4. Benchmark Delta: Baseline vs Equipped

The true value of a skill is measured by comparing:
1. **Baseline Agent (Without Skill)**:
   - What the base foundation model outputs using generic weights.
   - Typically scores 40%–60% due to common traps (legacy syntax, unmanaged memory leaks, missing flags).
2. **Equipped Agent (With Skill)**:
   - What the agent outputs when steered by `SKILL.md`, `references/`, and `## Gotchas`.
   - Target benchmark: **100% Assertion Pass Rate**.

The formula for skill effectiveness:
$$\Delta_{\text{skill}} = \text{Pass Rate}_{\text{equipped}} - \text{Pass Rate}_{\text{baseline}}$$

---

## 5. Grading Remediation Protocol
When an assertion fails during evaluation:
1. **Never ignore the failure**.
2. Identify the root cause:
   - Was the instruction missing from `SKILL.md`? ➡️ Add a clear protocol step.
   - Was the failure due to an obscure edge case? ➡️ Add an explicit entry under `## Gotchas`.
   - Was the assertion ambiguous? ➡️ Refine the assertion text.
3. Re-run `run_evals.py` until all assertions pass.
