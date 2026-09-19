# Evaluating & Testing Agent Skills

> Principles for designing evaluation suites (`evals/evals.json`) and testing skill triggering accuracy.

## 1. Why Evals Matter: Eval-Driven Development
Writing a skill is only the first step. To ensure the skill reliably triggers on appropriate user requests and produces high-quality output without regressions, skills should include structured test cases.

### Progressive Disclosure Guarantee
The `evals/` directory is **never loaded into the agent's context during active user conversations**. It is invoked only during testing and evaluation passes, resulting in **zero token cost** during production usage.

---

## 2. Test Cases Specification (`evals/evals.json`)

Test cases live under `<skill-name>/evals/evals.json`. Each test case defines a realistic user request, human-readable expected output, and objective assertions:

```json
{
  "skill_name": "sample-domain-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Refactor UserProfileComponent to use Angular 19 signals with zoneless change detection.",
      "expected_output": "The component is refactored to use signal() and computed() with zero any types and proper TSDoc comments.",
      "assertions": [
        "Component defines readonly state using signal<T>()",
        "No explicit 'any' types present in code",
        "All public methods contain TSDoc block comments",
        "Includes ChangeDetectionStrategy.OnPush"
      ],
      "files": []
    },
    {
      "id": 2,
      "prompt": "Create an automated migration for a legacy database table with soft delete columns.",
      "expected_output": "A migration file generating indexed deleted_at column and composite index.",
      "assertions": [
        "Includes deleted_at TIMESTAMP NULL",
        "Creates partial index on (id) WHERE deleted_at IS NULL"
      ]
    }
  ]
}
```

### Tips for Authoring Good Test Prompts
1. **Vary Formality and Detail**: Include casual prompts (`"hey clean up this query"`) alongside explicit, context-heavy prompts with paths and column names.
2. **Cover Boundary Edge Cases**: Include at least one edge case (e.g. malformed input, missing foreign key, empty payload).
3. **Write Verifiable Assertions**:
   - Good: `"The output file is valid JSON"`, `"Imports are strictly standalone"`.
   - Weak: `"The output is good"` (too vague), `"Output contains exact string XYZ"` (too brittle).

---

## 3. Trigger Evaluation Queries (`eval_queries.json`)

To verify that the skill's `description` field triggers reliably, author a set of 15–20 queries split into positive and negative test cases:

```json
[
  {
    "query": "Can you analyze our customer churn data in data/churn.csv and plot a distribution chart?",
    "should_trigger": true
  },
  {
    "query": "I need to update formulas in an Excel budget workbook",
    "should_trigger": false
  }
]
```

### The Near-Miss Principle
The most valuable negative test cases are **near-misses** — queries that share domain keywords (e.g., "data", "spreadsheet") but require a different tool or general reasoning. This prevents false-positive skill activations.

### Train/Validation Splits
When optimizing descriptions, use a 60/40 train/validation split:
- **Train (60%)**: Used to identify trigger failures and iterate on keywords.
- **Validation (40%)**: Held out to confirm that changes generalize rather than overfit.
