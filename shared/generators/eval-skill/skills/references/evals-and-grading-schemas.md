# Evals & Grading JSON Schemas Specification

## 1. Overview
The Agent Skills Open Standard (`agentskills.io`) mandates empirical verification through structured evaluation suites. This document defines the exact JSON schema specifications for:
1. **Input Test Suite**: `<skill-dir>/evals/evals.json`
2. **Output Evaluation Report**: `<skill-dir>/evals/grading.json`

Both files must adhere to strict typing, deterministic structure, and reproducible grading semantics.

---

## 2. Test Suite Schema (`evals.json`)

The `evals.json` file resides in `<skill-dir>/evals/evals.json` and contains an array of discrete test cases designed to evaluate agent proficiency with and without the skill.

### Structure & Fields

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "skill_name": "angular-signal-state-management",
  "evals": [
    {
      "id": 1,
      "name": "Cart Signal Store Implementation",
      "prompt": "Create a shopping cart store in Angular 19 using Signals and signalStore from @ngrx/signals with addItem and removeItem methods.",
      "expected_output": "A production-ready cart.store.ts using signalStore, withState, withMethods, and computed selectors with zero any types.",
      "assertions": [
        "Uses signalStore from @ngrx/signals or native signal() state",
        "Includes computed signals for derived state like cartItemCount and totalPrice",
        "Provides strongly typed state model interface without any types",
        "State updates use immutable patterns (no direct mutations)"
      ],
      "files": [
        "src/app/cart/data-access/cart.store.ts"
      ]
    }
  ]
}
```

### Field Definitions

| Field | Type | Mandatory | Description |
| :--- | :--- | :--- | :--- |
| `skill_name` | `string` | Recommended | Name of the skill matching the directory name. |
| `evals` | `array` | **Yes** | Non-empty list of test cases (minimum 2 recommended). |
| `evals[].id` | `integer` \| `string` | **Yes** | Unique identifier for the test case within the suite. |
| `evals[].name` | `string` | Optional | Human-readable title summarizing the evaluation objective. |
| `evals[].prompt` | `string` | **Yes** | Realistic user prompt simulating actual developer interaction. |
| `evals[].expected_output` | `string` | **Yes** | Architectural description of expected solution characteristics. |
| `evals[].assertions` | `string[]` | **Yes** | List of objective, binary verifiable criteria (minimum 2 per test). |
| `evals[].files` | `string[]` | Optional | Filepaths expected to be created or inspected during execution. |

---

## 3. Evaluation Grading Schema (`grading.json`)

When `eval-skill` executes or when `scripts/run_evals.py` runs, it generates or updates `<skill-dir>/evals/grading.json` with deterministic results.

### Structure & Fields

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "skill_name": "angular-signal-state-management",
  "evaluated_at": "2026-09-06T15:45:00.000Z",
  "evaluator": "eval-skill-runner v1.0.0",
  "quality_score_percent": 100,
  "verdict": "passed",
  "benchmark": {
    "baseline_pass_rate_percent": 50,
    "equipped_pass_rate_percent": 100,
    "delta_improvement_percent": 50
  },
  "summary": {
    "total_test_cases": 2,
    "passed_test_cases": 2,
    "total_assertions": 8,
    "passed_assertions": 8
  },
  "test_cases": [
    {
      "id": 1,
      "name": "Cart Signal Store Implementation",
      "passed": true,
      "assertions_total": 4,
      "assertions_passed": 4,
      "details": [
        {
          "assertion": "Uses signalStore from @ngrx/signals or native signal() state",
          "passed": true,
          "evidence": "src/app/cart/data-access/cart.store.ts:L14 uses signalStore()",
          "remediation": null
        },
        {
          "assertion": "Provides strongly typed state model interface without any types",
          "passed": true,
          "evidence": "CartState interface defined with strict readonly primitives",
          "remediation": null
        }
      ]
    }
  ]
}
```

### Field Definitions

| Field | Type | Mandatory | Description |
| :--- | :--- | :--- | :--- |
| `skill_name` | `string` | **Yes** | Name of the evaluated skill. |
| `evaluated_at` | `string` (ISO-8601) | **Yes** | UTC timestamp of the evaluation execution. |
| `quality_score_percent` | `integer` (0–100) | **Yes** | Percentage of passed assertions: `(passed / total) * 100`. |
| `verdict` | `string` | **Yes** | Enum: `"passed"` (100%), `"needs_revision"` (80–99%), `"failed"` (< 80%). |
| `benchmark` | `object` | Optional | Baseline vs Equipped performance metrics. |
| `summary` | `object` | **Yes** | High-level count of test cases and assertions. |
| `test_cases` | `array` | **Yes** | Itemized results per test case with assertion evidence. |
| `test_cases[].details` | `array` | **Yes** | Each assertion with boolean `passed`, cited `evidence`, and optional `remediation`. |

---

## 4. Schema Integrity Constraints

1. **Deterministic Scoring**:
   $$\text{quality\_score\_percent} = \text{round}\left(\frac{\sum \text{assertions\_passed}}{\sum \text{assertions\_total}} \times 100\right)$$
2. **Evidence Requirement**:
   For every passed or failed assertion, the `evidence` field MUST cite a concrete code fragment, line number, or specific diagnostic string. Empty or generic evidence strings (`"looks good"`) are strictly invalid.
3. **Remediation Prescription**:
   If `passed: false`, the `remediation` field MUST specify the exact instruction or Gotcha to add to the target skill's `SKILL.md` to prevent recurrence.
