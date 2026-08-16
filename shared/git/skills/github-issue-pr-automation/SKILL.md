---
name: github-issue-pr-automation
description: Guidelines and protocols for automating GitHub Issue creation, feature branch management, conventional commits, pull requests, automated issue closing, and post-merge branch cleanup using GitHub MCP tools.
---

# GitHub Issue & PR Automation Skill

## Overview
Provides strict operational standards and step-by-step procedures for AI Agents to manage feature development cycles via GitHub. Ensures all code changes are backed by a junior-friendly GitHub Issue, built on a normalized feature branch, formatted with Conventional Commits, merged through a structured Pull Request, and cleaned up locally and remotely.

## Operational Standards & Protocols

### 1. Junior-Friendly Issue Creation Protocol
- **NEVER** write code or push directly to `main` without an associated GitHub Issue.
- When the user requests a feature (e.g., `issue: Add Double-Entry Ledger API`), inspect the active repository and invoke the `github-mcp-server` tool `issue_write` to create a structured GitHub Issue.
- Structure the body so any junior developer can understand the context, objective, and acceptance criteria.

```json
{
  "title": "feat(ledger): add trial balance report endpoint",
  "body": "## Overview\nImplement double-entry trial balance calculation endpoint for financial reporting.\n\n## Technical Context\nThis endpoint computes total debits and credits across all account heads and ensures balanced books.\n\n## Acceptance Criteria\n- [ ] Calculate debit/credit sums per account head\n- [ ] Validate sum(debits) - sum(credits) == 0\n- [ ] Return structured JSON DTO",
  "labels": ["enhancement", "backend"]
}
```

### 2. Base Branch Sync & Normalized Naming
- Always checkout and pull `main` (or `master`) before branching.
- Name feature branches using the format: `feat/<issue-id>-<slug>` or `fix/<issue-id>-<slug>`.
- Examples:
  - `feat/12-trial-balance-endpoint`
  - `fix/18-emi-rounding-error`

### 3. Conventional Commit Enforcement
- Every git commit MUST follow Conventional Commits specification:
  - `feat(<scope>): description`
  - `fix(<scope>): description`
  - `docs(<scope>): description`
  - `refactor(<scope>): description`
  - `test(<scope>): description`

### 4. Automated PR & Issue Auto-Close Linking
- Upon feature completion, push the branch to remote origin.
- Use `create_pull_request` MCP tool to draft a PR.
- **CRITICAL**: Include `Closes #<issue-id>` or `Fixes #<issue-id>` in the PR body so GitHub automatically closes the issue upon merge.

### 5. PR Merge Execution & Branch Cleanup Protocol
- Merge PR into `main`.
- Switch local workspace back to `main` and pull updated commits:
  ```bash
  git checkout main && git pull origin main
  ```
- Delete local feature branch:
  ```bash
  git branch -d feat/<issue-id>-<slug>
  ```
- Delete remote origin branch:
  ```bash
  git push origin --delete feat/<issue-id>-<slug>
  ```
