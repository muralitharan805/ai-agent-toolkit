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
tools/generators/eval-skill/skills/
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
    └── grading.json                                # Optional local deterministic report; not shipped in public source
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

### Phase 2: Collect Real Evaluation Evidence (Baseline vs Equipped)
For each test case entry in `evals/evals.json`:
1. Extract the `id`, `name`, `prompt`, `expected_output`, `assertions` list, and `files` paths.
2. **Baseline (Without Skill)**:
   - Record measured artifacts from a real agent run without the skill. If that run is unavailable, mark baseline **NOT_MEASURED**. Do not invent likely model failures as evidence.
3. **Equipped Execution (With Skill)**:
   - Inspect artifacts from an actual agent run using this skill. If no run exists, mark semantic assertions **NOT_EVALUATED** rather than passing them.
4. Capture or locate the resulting code artifacts or CLI outputs.

---

### Phase 3: Objective Assertion Grading
For each assertion in the test case:
1. Objectively evaluate whether the generated output satisfies the assertion statement.
2. Assign evidence-based status:
   - **`PASS`**: A real grader confirms the requirement with concrete code/diagnostic evidence.
   - **`FAIL`**: Evidence disproves the requirement.
   - **`NOT_EVALUATED`**: No reliable evidence or deterministic checker exists. Never call this PASS.
3. Report a pass rate only for assertions actually graded. Show unverified count separately; do not turn missing evidence into an implied pass.

---

### Phase 4: Automated Verification via Runner Script
Run the deterministic evaluation runner to check suite schema and basic file presence; it **does not execute a model or measure skill lift**. Missing semantic evidence remains `NOT_EVALUATED`. Do not present its output as a completed baseline-vs-equipped benchmark.

Execute the bundled evaluation runner to validate and persist grading:
```bash
python3 tools/generators/eval-skill/skills/scripts/run_evals.py <target-skill-path> --save-grading
```

Optional CLI flags:
- `--json`: Emits raw machine-readable JSON output to stdout.
- `--dry-run`: Validates test case schema and assertions without checking filesystem artifacts.
- `--strict`: Treats warnings as execution failures.
- `--output <path>`: Writes grading report to custom location.
- Deterministic assertion: write the literal `files_exist` with a `files` array under the test case. Natural-language assertions remain `NOT_EVALUATED`.
- Exit status: `0` verified or successful `--dry-run`; `1` failure; `2` unverified semantic assertions. This CLI does not execute an agent.

---

### Phase 5: Scorecard Presentation & Remediation
1. Output the structured visual evaluation scorecard:

```text
=== 🧪 AGENT SKILL EVALUATION REPORT: [skill-name] ===
Skill Directory : [path-to-skill]
Total Test Cases: [count]
Total Assertions: [count]

Comparative Benchmark:
  - Baseline (Without Skill): [Measured Pass % or NOT_MEASURED]
  - Equipped (With Skill)   : [Measured Pass % or NOT_MEASURED]
  - Net Skill Lift (Delta)  : [Measured Delta or NOT_MEASURED]

Test Case #1: "[test name / prompt summary]"
  ✅ PASS - [assertion 1] (Evidence: [brief code snippet or proof])
  ✅ PASS - [assertion 2] (Evidence: [proof])
  Result: [X]/[Y] Assertions Passed 🟢

Final Quality Score : [Score / 100]% [🟢 / 🔴]
Overall Verdict     : [VERIFIED | FAILED | NOT_EVALUATED]
======================================================
```

2. **Remediation Rule**: If any assertion fails:
   - Cite the exact failure cause.
   - Provide a concise 1-sentence instruction or Gotcha to add to the target skill's `SKILL.md` to prevent future failures.

---

## Gotchas
- **No Subjective Praise**: Never grade an assertion as PASS based on vague impressions like "looks clean". Concrete filepaths, line references, or command outputs MUST be cited.
- **No fabricated grades**: A checked assertion is binary verified/failed; an unchecked semantic assertion is `NOT_EVALUATED`. Missing evidence is not a pass or a failure.
- **Directory Path Precision**: When executing `run_evals.py`, always provide a valid relative or absolute directory path containing `SKILL.md` and `evals/evals.json`.
- **Zero any Types**: In any TypeScript evaluation, the presence of an explicit `any` type constitutes an immediate failure of type-safety assertions.
