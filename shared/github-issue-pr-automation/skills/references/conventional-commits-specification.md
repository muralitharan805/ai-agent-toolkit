# Conventional Commits Specification Guide

## Overview

The Conventional Commits specification is a lightweight convention on top of commit messages. It provides an easy set of rules for creating an explicit commit history, which makes it easier to write automated tools (such as semantic versioning, changelog generation, and automated release tagging).

---

## 1. Commit Message Structure

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Key Formatting Invariants:
1. **Header Line**:
   - Format: `<type>(<scope>): <description>`
   - Max length: **72 characters**.
   - Imperative, present tense ("add" not "added", "fix" not "fixed").
   - Lowercase first letter of description.
   - **No trailing period (`.`)**.
2. **Body (Optional)**:
   - Separated from header by a blank line.
   - Explains the *what* and *why*, not the how.
3. **Footers (Optional)**:
   - One or more footers, each on a new line:
   - `BREAKING CHANGE: <description of change and migration instructions>`
   - `Closes #<id>` or `Fixes #<id>`

---

## 2. Standard Commit Types

| Type | Purpose | SemVer Bump | Example |
|---|---|---|---|
| **`feat`** | A new feature for the user or system | **MINOR** | `feat(auth): implement refresh token rotation` |
| **`fix`** | A bug fix for the user or system | **PATCH** | `fix(ledger): correct rounding discrepancy in debit totals` |
| **`docs`** | Documentation changes only | None | `docs(readme): add docker compose development setup instructions` |
| **`refactor`** | Code refactoring without changing functionality or fixing bugs | None | `refactor(users): extract user credential lookup into shared module` |
| **`test`** | Adding missing tests or correcting existing tests | None | `test(order): add unit test spec for negative payment validation` |
| **`perf`** | Code change that improves performance | **PATCH** | `perf(query): add database index on tenant_id and created_at` |
| **`ci`** | Changes to CI/CD configuration files and scripts | None | `ci(github): add pnpm frozen lockfile audit build step` |
| **`chore`** | Maintenance tasks, dependencies, tooling | None | `chore(deps): bump prisma engine to version 6.2.0` |

---

## 3. Breaking Changes

A breaking change can be represented in two ways:
1. Append an exclamation mark (`!`) immediately before the colon in the header:
   ```text
   feat(auth)!: replace cookie sessions with bearer jwt tokens
   ```
2. Include a `BREAKING CHANGE:` footer:
   ```text
   feat(api): migrate user endpoint to v2 payload

   BREAKING CHANGE: The 'username' property has been renamed to 'handle'.
   ```

---

## 4. Good vs. Bad Commit Examples

```bash
# ✅ Good: Specific, scoped, imperative, under 72 chars
feat(emi): implement monthly amortization breakdown calculation
fix(redis): resolve memory leak during client reconnection retry
docs(api): document correlation ID header requirements in swagger
refactor(auth): decouple user service using symbol injection token

# ❌ Forbidden: Vague, past tense, capitalized, trailing period, no type
added new emi stuff.
Fixed Bug In Controller
wip
update files
changes
```
