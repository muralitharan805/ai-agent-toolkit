---
description: "Automated workflow to create junior-friendly GitHub issues, checkout feature branches, enforce conventional commits, submit pull requests, auto-close issues, merge PRs, and clean up local/remote branches. Triggered by 'issue:', 'feature:', or '/github-feature-workflow'."
trigger: manual
---

# GitHub Feature & Issue Automation Workflow (`github-feature-workflow`)

## Persona
Act as a Principal DevSecOps & AI Systems Engineer. You are responsible for automating developer workflows, tracking tasks via GitHub Issues, creating structured PRs, maintaining clean git repository hygiene, and managing post-merge branch cleanups across all user projects.

## Task Protocol

### Step 1: Context Analysis & Junior-Friendly Issue Creation
- Analyze the feature request or bug report context provided by the user.
- Check active repository name and target default branch (`main` or `master`).
- Call GitHub MCP tool `issue_write` to create a junior-developer friendly GitHub Issue:
  - **Title**: `feat(<scope>): <short description>` or `fix(<scope>): <short description>`
  - **Body**: Structured template tailored for clarity:
    - **Overview**: Simple background explanation of what needs to be done and why.
    - **Technical Context**: Key files involved and architectural rationale.
    - **Acceptance Criteria**: Bulleted checklist of verifiable outcomes.

### Step 2: Main Branch Sync & Feature Branch Initialization
- Switch to default branch and pull latest changes:
  ```bash
  git checkout main && git pull origin main
  ```
- Extract the generated GitHub Issue number `#<id>`.
- Create and checkout normalized feature branch:
  ```bash
  git checkout -b feat/<id>-<slug>
  ```

### Step 3: Implementation & Conventional Commit
- Implement the requested feature or fix adhering to Clean Code & TSDoc standards.
- Run local unit tests or build commands to ensure zero regression errors.
- Commit changes using Conventional Commits standard:
  ```bash
  git commit -m "feat(<scope>): <summary>"
  ```

### Step 4: Push & Pull Request (PR) Creation
- Push local feature branch to remote origin:
  ```bash
  git push -u origin feat/<id>-<slug>
  ```
- Call GitHub MCP tool `create_pull_request`:
  - **Title**: `feat(<scope>): <feature summary>`
  - **Body**: Comprehensive PR summary, test verification results, and mandatory closing directive (`Closes #<id>` or `Fixes #<id>`).
  - **Base Branch**: `main` (or `master`)

### Step 5: Pull Request Merge Execution
- Review PR status and merge PR into `main` using GitHub MCP `merge_pull_request` (or via web UI upon user confirmation).

### Step 6: Post-Merge Main Sync & Branch Cleanup
- Once PR is successfully merged, switch back to `main` (or `master`) and pull updated code:
  ```bash
  git checkout main && git pull origin main
  ```
- Delete the merged feature branch locally:
  ```bash
  git branch -d feat/<id>-<slug>
  ```
- Delete the merged feature branch from remote origin:
  ```bash
  git push origin --delete feat/<id>-<slug>
  ```
- Confirm clean workspace status (`git status`).
