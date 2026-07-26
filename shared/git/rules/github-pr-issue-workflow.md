# GitHub Issue & PR Development Workflow Rule

## Description
Enforces mandatory GitHub Issue creation, normalized feature branch naming, Conventional Commits, and Pull Request issue-linking across all core projects (`nidhiflow`, `seyalicraft`, `civicpath`, `ai-agent-toolkit`).

## Constraints

### 1. Mandatory Issue First Requirement
- Direct commits to `main` branch are STRICTLY FORBIDDEN.
- All code modifications MUST be tracked under an explicit GitHub Issue.
- If no issue exists, the agent MUST automatically create one via GitHub MCP before writing code.

### 2. Standardized Branch Naming
- Feature branches MUST follow `feat/<issue-id>-<slug>` or `fix/<issue-id>-<slug>`.
- Unformatted branch names (e.g. `temp`, `my-branch`, `test1`) are forbidden.

### 3. PR Auto-Closing Syntax
- Every Pull Request body MUST include explicit issue closing keywords (`Closes #<issue-id>` or `Fixes #<issue-id>`).
- Direct merging without issue linking is forbidden.

### 4. Conventional Commit Standards
- All commit messages MUST adhere to Conventional Commits standard (`feat(...)`, `fix(...)`, `docs(...)`, `refactor(...)`).

## Examples

- **Correct Workflow Execution:**
```bash
# 1. GitHub Issue #14 created: "Add EMI Amortization Schedule Endpoint"
# 2. Checkout feature branch:
git checkout -b feat/14-emi-amortization-schedule

# 3. Commit with Conventional Commits:
git commit -m "feat(emi): implement amortization calculation service"

# 4. Open PR with issue link:
# PR Title: feat(emi): add EMI amortization schedule endpoint
# PR Body: Implements monthly EMI breakdown. Closes #14
```

- **Incorrect Workflow (FORBIDDEN):**
```bash
# Direct push to main without Issue or PR (FORBIDDEN)
git checkout main
git commit -m "added emi code"
git push origin main
```
