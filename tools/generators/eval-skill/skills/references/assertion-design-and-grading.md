# Assertion Design & Quality Grading Guide

## 1. Overview
Within this toolkit, evals are an optional authoring and quality practice; the Agent Skills open format does not mandate this exact JSON schema. A meaningful agent-performance claim requires real runs and evidence, not a schema-only check.

Subjective grading ("code looks neat", "well designed") is strictly prohibited. Every assertion must be binary, verifiable, and backed by concrete evidence from the generated output.

---

## 2. Objective vs Subjective Assertions

| Anti-Pattern (Subjective / Vague) | Production-Grade (Objective & Verifiable) |
| :--- | :--- |
| ❌ "Output uses good TypeScript code" | ✅ "All exported functions have explicit return type annotations with zero `any` types" |
| ❌ "Form handles errors nicely" | ✅ "Uses centralized `<app-form-error [control]='...' />` presenter rather than inline `@if` checks" |
| ❌ "Database is secured" | ✅ "Queries use parameterized Prisma client calls; zero raw string concatenation in SQL" |
| ❌ "Includes deployment instructions" | ✅ "Provides exact `./bin/context.sh -g [path]` command in the output" |
| ❌ "Component is reactive" | ✅ "Uses `signal()` and `computed()` primitives instead of RxJS `BehaviorSubject` for local component state" |

---

## 3. The 4 Assertion Archetypes

When designing assertions for `evals/evals.json`, combine these 4 archetypes:

### 1. Structural / File Assertions
Check outputs and structural constraints. The bundled runner can deterministically check **existing file paths only** via an exact `files_exist` assertion and the test case's `files` array; all other assertions below need a dedicated grader:
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
   - Do not infer a baseline score. Run the same evaluation prompt without the skill and capture its artifacts.
2. **Equipped Agent (With Skill)**:
   - What the agent outputs when steered by `SKILL.md`, `references/`, and `## Gotchas`.
   - Measure the actual pass rate from a separately graded, evidenced run; never assume 100%.

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
3. Re-run real agent evaluation and grade the actual outputs. `run_evals.py` alone checks only declared file presence and leaves semantic assertions `NOT_EVALUATED`.
