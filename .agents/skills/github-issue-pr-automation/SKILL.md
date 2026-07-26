---
name: github-issue-pr-automation
description: Guidelines and protocols for automating GitHub Issue creation, feature branch management, conventional commits, pull requests, and automated issue closing using GitHub MCP tools.
---

# GitHub Issue & PR Automation Skill

## Overview
Provides strict operational standards and step-by-step procedures for AI Agents to manage feature development cycles via GitHub. Ensures all code changes are backed by a formal GitHub Issue, built on a normalized feature branch, formatted with Conventional Commits, and merged through a structured Pull Request.

## Operational Standards & Protocols

### 1. Mandatory Issue First Protocol
- **NEVER** write code or push directly to `main` without an associated GitHub Issue.
- When the user requests a feature (e.g., `issue: Add Double-Entry Ledger API`), inspect the active repository and invoke the `github-mcp-server` tool `issue_write` to create a structured GitHub Issue.
- Include clear acceptance criteria, technical requirements, and task checkboxes in the issue body.

```json
{
  "title": "feat(ledger): add trial balance report endpoint",
  "body": "## Description\nImplement double-entry trial balance calculation endpoint.\n\n## Acceptance Criteria\n- [ ] Calculate debit/credit sums per account head\n- [ ] Validate sum(debits) - sum(credits) == 0\n- [ ] Return structured JSON DTO",
  "labels": ["enhancement", "backend"]
}
```

### 2. Normalized Feature Branch Naming
- Always branch off `main`.
- Name feature branches using the format: `feat/<issue-id>-<short-description-slug>` or `fix/<issue-id>-<short-description-slug>`.
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

### 4. Automated Pull Request (PR) Creation
- Upon feature completion and verification, push the branch to remote origin.
- Use `create_pull_request` MCP tool to draft a PR.
- **CRITICAL**: Include `Closes #<issue-id>` or `Fixes #<issue-id>` in the PR body so GitHub automatically closes the issue upon merge.

```json
{
  "title": "feat(ledger): implement trial balance calculation service",
  "body": "## Summary of Changes\n- Created TrialBalanceService with double-entry validation\n- Added GET /reports/trial-balance REST controller\n\nCloses #12",
  "head": "feat/12-trial-balance-endpoint",
  "base": "main"
}
```
