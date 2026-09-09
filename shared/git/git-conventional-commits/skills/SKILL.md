---
name: git-conventional-commits
description: "Formats and validates Git commit messages using the Conventional Commits specification, semantic types, and scope boundaries."
---

# Git Conventional Commits Architecture

Enforces the official Conventional Commits specification (v1.0.0) across all repository commits. Guarantees deterministic semantic versioning, automated changelog generation, clear history audits, and automated validation gates.

---

## 5-Pillar Architecture Directory Layout

```text
shared/git/skills/git-conventional-commits/
├── SKILL.md                                           # Core procedural commit guidance (< 500 lines)
├── references/                                        # Authoritative deep-dive runbooks
│   └── conventional-commits-specification.md         # Types, scopes, and breaking change rules
├── scripts/                                           # Standalone automation tools
│   └── validate_commit_message.py                    # CLI commit message linter
├── assets/                                            # Reusable templates and starters
│   └── commit-template.txt                           # Git commit message template
└── evals/                                             # Verifiable test cases and grading
    ├── evals.json
    └── grading.json
```

---

## 4-Step Execution Protocol

Follow this 4-step sequence to format, verify, and apply Conventional Commits:

### Step 1: Change Intent & Scope Analysis
1. Inspect staged changes via `git diff --staged` or `git status`.
2. Identify the primary intent and target scope:
   - `feat(<scope>)`: New functionality or user-facing feature.
   - `fix(<scope>)`: Bug patch or error resolution.
   - `docs(<scope>)`: Documentation, comments, or README updates.
   - `refactor(<scope>)`: Structural cleanup with zero behavior change.
   - `test(<scope>)`: Unit, integration, or E2E test modifications.
   - `chore(<scope>)`: Dependencies, tooling, or build configuration.

### Step 2: Header Formatting & Validation
1. Construct the header line: `<type>(<scope>): <short description>`.
2. Enforce strict invariants:
   - **Length**: Maximum 72 characters.
   - **Mood**: Imperative, present tense (`add`, `fix`, `refactor` — NEVER `added`, `fixes`).
   - **Casing**: Lowercase first letter of description.
   - **Punctuation**: NO trailing period (`.`).

### Step 3: Breaking Change & Footer Declaration
1. If a breaking API or schema change is introduced:
   - Add an exclamation mark before the colon: `feat(api)!: migrate payload structure`.
   - Add a footer: `BREAKING CHANGE: <explanation and migration steps>`.
2. Link associated issues in the footer: `Closes #<id>` or `Fixes #<id>`.

### Step 4: Automated CLI Linting
Validate the constructed message before committing:
```bash
python3 scripts/validate_commit_message.py "feat(auth): implement refresh token rotation" --strict
```
Apply the validated commit:
```bash
git commit -m "feat(auth): implement refresh token rotation"
```

---

## Gotchas & Commit Pitfalls

| Naive / Prohibited Pattern | Conventional Commit Replacement | Why It Matters |
|---|---|---|
| Vague messages (`git commit -m "fixed bug"`) | `git commit -m "fix(ledger): correct debit sum calculation"` | Vague messages make git bisect and changelog generation impossible. |
| Past-tense verbs (`added tests and fixed bug`) | `git commit -m "fix(auth): handle expired tokens"` | Imperative mood aligns with git's native commit format ("apply this commit to..."). |
| Trailing periods (`feat(user): add profile endpoint.`) | `feat(user): add profile endpoint` | Commits act as titles/headers in git logs, where trailing punctuation creates visual noise. |
| Capitalizing the description (`feat(api): Add Login`) | `feat(api): add login endpoint` | Lowercase descriptions ensure consistent standard formatting across all contributors. |
| Hiding breaking changes inside commit bodies | Using `!` in header and `BREAKING CHANGE:` footer | Automated semantic-release tools will fail to bump the MAJOR version number. |
| Exceeding 72 characters on the summary line | Truncating summary and putting details in commit body | Long headers wrap and render poorly in GitHub UI and terminal `git log --oneline`. |
