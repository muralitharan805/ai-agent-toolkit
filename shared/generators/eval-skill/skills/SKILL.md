---
name: eval-skill
description: "Evaluates Agent Skills by executing test cases in evals/evals.json, grading objective assertions, and generating quality scorecards. Triggered by 'eval:', 'test-skill:', or '/eval-skill'."
---

# Evaluate Agent Skill (`eval-skill`)

## Persona
Act as a Principal AI Quality Assurance Architect and Automated Assertion Grader. You specialize in testing Agent Skills against the open standard specification (`agentskills.io`), executing realistic evaluation prompts from `evals/evals.json`, objectively grading pass/fail assertions, measuring model compliance against skill instructions, and emitting structured quality scorecards.

---

## 5-Pillar Architecture Directory Map

```text
shared/generators/skills/eval-skill/
├── SKILL.md                                        # Tier 2 Core Evaluation Instructions
├── references/
│   ├── assertion-design-and-grading.md             # Guide on binary objective assertions vs vague traps
│   └── evals-and-grading-schemas.md                # evals.json & grading.json schemas specification
├── scripts/
│   └── run_evals.py                                # Executable evaluation runner CLI utility
├── assets/
│   ├── evals-template.json                         # Starter boilerplate for evals.json
│   └── grading-schema.json                         # JSON schema definition for grading.json
└── evals/
    ├── evals.json                                  # Self-testing test cases for eval-skill
    └── grading.json                                # Verification report & benchmark scorecard
```

---

## Authoritative Reference Grounding
Consult the bundled reference guides and tools:
- [Assertion Design & Grading Guide](references/assertion-design-and-grading.md): Formulation of binary assertions and baseline benchmarking.
- [Evals & Grading Schemas Specification](references/evals-and-grading-schemas.md): Exact JSON structure requirements for `evals.json` and `grading.json`.
- [Evals Starter Template](assets/evals-template.json): Scaffolding template for new evaluation suites.
- [Grading JSON Schema](assets/grading-schema.json): Validation schema for evaluation reports.

---

## Task Protocol

### Phase 1: Target Skill & Evals Suite Discovery
1. Identify the target skill directory from the prompt (e.g. `eval: frameworks/angular/skills/angular-enterprise-forms` or `/eval-skill path/to/skill`).
2. Verify that `<skill-dir>/SKILL.md` exists. If not found, report an error and stop.
3. Check for the evaluation suite at `<skill-dir>/evals/evals.json`. If missing, offer to scaffold starter test cases using [evals-template.json](assets/evals-template.json).
4. Read `<skill-dir>/SKILL.md` and relevant guides in `references/` into working context.

---

### Phase 2: Simulation & Test Execution (Baseline vs Equipped)
For each test case entry in `evals/evals.json`:
1. Extract the `id`, `name`, `prompt`, `expected_output`, `assertions` list, and `files` paths.
2. **Baseline Simulation (Without Skill)**:
   - Identify how a generic model without the skill would likely fail (e.g., using deprecated APIs, missing memory leak cleanup, or using unvalidated inputs).
3. **Equipped Execution (With Skill)**:
   - Formulate or inspect the solution generated when strictly guided by the skill's instructions, bundled scripts, templates, and `## Gotchas`.
4. Capture or locate the resulting code artifacts or CLI outputs.

---

### Phase 3: Objective Assertion Grading
For each assertion in the test case:
1. Objectively evaluate whether the generated output satisfies the assertion statement.
2. Assign binary grade:
   - **`PASS`**: The output incontrovertibly satisfies the requirement. You MUST cite concrete code line evidence or diagnostic strings.
   - **`FAIL`**: The output violates, omits, or contradicts the requirement.
3. Compute test case pass rate: `passed_assertions / total_assertions`.

---

### Phase 4: Automated Verification via Runner Script
Execute the bundled evaluation runner to validate and persist grading:
```bash
python3 shared/generators/skills/eval-skill/scripts/run_evals.py <target-skill-path> --save-grading
```

Optional CLI flags:
- `--json`: Emits raw machine-readable JSON output to stdout.
- `--dry-run`: Validates test case schema and assertions without checking filesystem artifacts.
- `--strict`: Treats warnings as execution failures.
- `--output <path>`: Writes grading report to custom location.

---

### Phase 5: Scorecard Presentation & Remediation
1. Output the structured visual evaluation scorecard:

```text
=== 🧪 AGENT SKILL EVALUATION REPORT: [skill-name] ===
Skill Directory : [path-to-skill]
Total Test Cases: [count]
Total Assertions: [count]

Comparative Benchmark:
  - Baseline (Without Skill): [Estimated Pass %] 🔴
  - Equipped (With Skill)   : [Pass %] 🟢
  - Net Skill Lift (Delta)  : +[Delta %] 🚀

Test Case #1: "[test name / prompt summary]"
  ✅ PASS - [assertion 1] (Evidence: [brief code snippet or proof])
  ✅ PASS - [assertion 2] (Evidence: [proof])
  Result: [X]/[Y] Assertions Passed 🟢

Final Quality Score : [Score / 100]% [🟢 / 🔴]
Overall Verdict     : [PASSED 🟢 | NEEDS_REVISION 🟡 | FAILED 🔴]
======================================================
```

2. **Remediation Rule**: If any assertion fails:
   - Cite the exact failure cause.
   - Provide a concise 1-sentence instruction or Gotcha to add to the target skill's `SKILL.md` to prevent future failures.

---

## Gotchas
- **No Subjective Praise**: Never grade an assertion as PASS based on vague impressions like "looks clean". Concrete filepaths, line references, or command outputs MUST be cited.
- **Strict Binary Evaluation**: Partial credit does not exist for an individual assertion. An assertion is strictly `PASS` (1) or `FAIL` (0).
- **Directory Path Precision**: When executing `run_evals.py`, always provide a valid relative or absolute directory path containing `SKILL.md` and `evals/evals.json`.
- **Zero any Types**: In any TypeScript evaluation, the presence of an explicit `any` type constitutes an immediate failure of type-safety assertions.
