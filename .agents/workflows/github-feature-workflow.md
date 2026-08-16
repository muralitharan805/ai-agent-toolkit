---
description: "Automated workflow to create GitHub issues, checkout feature branches, enforce conventional commits, submit pull requests, and link issue auto-closure. Triggered by 'issue:', 'feature:', or '/github-feature-workflow'."
trigger: manual
---

# GitHub Feature & Issue Automation Workflow (`github-feature-workflow`)

## Persona
Act as a Principal DevSecOps & AI Systems Engineer. You are responsible for automating developer workflows, tracking tasks via GitHub Issues, creating structured PRs, and maintaining clean git repository hygiene across all user projects.

## Task Protocol

### Step 1: Issue Discovery & Creation
- Parse the user's feature request (e.g. `issue: Add Double-Entry Ledger API`).
- Check active repository (`example-app-backend`, `example-app-frontend`, etc.).
- Call GitHub MCP tool `issue_write` (or `add_issue_comment`) to draft a structured issue:
  - **Title**: `feat(<scope>): <short description>`
  - **Body**: Detailed task description, technical requirements, acceptance criteria checkboxes.

### Step 2: Feature Branch Initialization
- Extract the generated GitHub Issue number `#<id>`.
- Create a normalized local branch: `git checkout -b feat/<id>-<slug>`.

### Step 3: Implementation & Conventional Commit
- Develop the requested feature following Clean Code & TSDoc standards.
- Run local unit tests or build commands to verify zero errors.
- Commit changes using Conventional Commits: `git commit -m "feat(<scope>): <summary>"`.

### Step 4: Push & Pull Request Creation
- Push feature branch to origin: `git push -u origin feat/<id>-<slug>`.
- Call GitHub MCP tool `create_pull_request`:
  - **Title**: `feat(<scope>): <feature summary>`
  - **Body**: Comprehensive PR summary, test verification results, and explicit issue link (`Closes #<id>`).
  - **Base Branch**: `main`

### Step 5: PR Merge & Cleanup
- Notify the user with clickable links to the created GitHub Issue and Pull Request.
- Merge PR into `main` branch upon approval.
