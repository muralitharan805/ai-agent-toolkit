# Evals and Grading Schemas (Toolkit Convention)

This document describes **this toolkit's** `evals/evals.json` format and the actual output from `scripts/run_evals.py`. The Agent Skills format does not require these particular JSON files. Do not present these local schemas as mandatory upstream Agent Skills standards.

## 1. Input: `evals/evals.json`

The runner reads `<skill-dir>/evals/evals.json` with a non-empty `evals` array. Example:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "name": "Creates the expected file",
      "prompt": "Create the requested artifact",
      "expected_output": "A validated implementation",
      "files": ["src/example.ts"],
      "assertions": [
        "files_exist",
        "Generated code follows the domain constraints"
      ]
    }
  ]
}
```

- `id`: unique integer or string per test case.
- `prompt`: non-empty task string.
- `expected_output`: non-empty description.
- `assertions`: non-empty array of assertion strings.
- `files`: optional list of expected output files, resolved under the **current working directory** from which the runner is launched. The validator rejects file paths escaping that directory.
- `files_exist`: **only supported deterministic assertion**, spelled exactly. It checks that every declared `files` path refers to an existing file. If no `files` array is supplied, it remains `NOT_EVALUATED`.
- All other assertions, including natural-language claims mentioning “file” or “scaffold”, are `NOT_EVALUATED` unless an independent agent run and an assertion-specific grader supply evidence. They are **never automatically passed** by keyword matching.

The runner does **not** generate files, execute the prompt, run unit tests, inspect source semantics, or measure model quality.

## 2. Output: `evals/grading.json`

The deterministic runner emits a grading report matching `../assets/grading-schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "skill_name": "example-skill",
  "evaluated_at": "2026-11-07T00:00:00+00:00",
  "evaluator": "eval-suite-validator v1.1.0",
  "verdict": "not_evaluated",
  "deterministic_coverage_percent": 50,
  "benchmark": null,
  "summary": {
    "total_test_cases": 1,
    "verified_test_cases": 0,
    "failed_test_cases": 0,
    "not_evaluated_test_cases": 1,
    "total_assertions": 2,
    "verified_assertions": 1,
    "failed_assertions": 0,
    "not_evaluated_assertions": 1
  },
  "test_cases": [
    {
      "id": 1,
      "name": "Creates the expected file",
      "status": "not_evaluated",
      "assertions_total": 2,
      "assertions_verified": 1,
      "assertions_failed": 0,
      "assertions_not_evaluated": 1,
      "details": [
        {
          "assertion": "files_exist",
          "status": "verified",
          "evidence": "Every file declared in the test case's files list exists inside the workspace.",
          "remediation": null
        },
        {
          "assertion": "Generated code follows the domain constraints",
          "status": "not_evaluated",
          "evidence": "Requires an actual agent run and grader.",
          "remediation": "Run an assertion-specific grader."
        }
      ]
    }
  ]
}
```

The sample assumes `src/example.ts` exists; its timestamp is illustrative, not a claimed live evaluation.

### Reporting contract

- Assertion and case `status`: `verified`, `failed`, or `not_evaluated`.
- `verdict`: `failed` if a deterministic assertion fails; otherwise `not_evaluated` if any remain unverified; otherwise `verified`.
- `deterministic_coverage_percent`: percentage of assertions the runner could definitively check (verified **or failed**), **not a model quality score**.
- `benchmark: null` means no baseline/equipped agent comparison was performed. Never invent pass rates or skill lift.

### CLI exit codes

- `0`: verified deterministic assertions, or successful `--dry-run` suite validation.
- `1`: invalid input/schema, failed deterministic assertion, or strict-mode warnings.
- `2`: assertions remain `not_evaluated` in a real (non-dry-run) execution.

Use `--save-grading` only when you want to overwrite the skill's grading report with the current **deterministic** results. A proper semantic evaluation requires a separate, evidenced agent run; preserve that evidence outside this runner.
