---
name: github-issue-pr-automation
description: "Automates the GitHub feature lifecycle: issue creation, normalized branch management, conventional commits, pull requests with auto-closing, and branch pruning."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# GitHub Issue & PR Automation Architecture

Provides structured standards and procedural automation for managing the feature development lifecycle on GitHub. Enforces the Issue-First rule, normalized branch naming (`feat/<id>-<slug>`), Conventional Commits, Pull Request auto-closing directives, and post-merge branch pruning.

---

## 5-Pillar Architecture Directory Layout

```text
shared/github-issue-pr-automation/
├── rules/
│   └── github-pr-issue-workflow.md
└── skills/
    ├── SKILL.md                                           # Core procedural lifecycle guidance (< 500 lines)
    ├── references/                                        # Authoritative deep-dive runbooks
    │   ├── branching-and-pr-automation-guide.md          # Branch patterns, PR directives, and cleanup
    │   └── conventional-commits-specification.md         # Conventional Commits format specification
    ├── scripts/                                           # Standalone automation tools
    │   ├── manage_git_feature_lifecycle.py               # CLI lifecycle validation & hygiene checker
    │   └── validate_commit_message.py                    # Commit message syntax validator
    ├── assets/                                            # Reusable templates and starters
    │   ├── issue-template.json                           # Structured junior-friendly issue template
    │   ├── pr-template.md                                # Pull request template with Closes directive
    │   └── commit-template.txt                           # Conventional commit text template
    └── evals/                                             # Verifiable test cases and grading
        ├── evals.json
        └── grading.json
```

---

## Authoritative References & Assets

- **Branching & PR Automation**: Read [branching-and-pr-automation-guide.md](references/branching-and-pr-automation-guide.md) for branch patterns, PR directives, and cleanup runbooks.
- **Conventional Commits**: Consult [conventional-commits-specification.md](references/conventional-commits-specification.md) for commit type definitions and semantic release formats.
- **CLI Automation Tools**:
  - Run [manage_git_feature_lifecycle.py](scripts/manage_git_feature_lifecycle.py) for branch hygiene and issue linking verification.
  - Run [validate_commit_message.py](scripts/validate_commit_message.py) to validate commit message format.
- **Assets & Templates**: Review [issue-template.json](assets/issue-template.json), [pr-template.md](assets/pr-template.md), and [commit-template.txt](assets/commit-template.txt).
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## 6-Step Procedural Execution Protocol

Follow this 6-step lifecycle sequence for any feature development or bug fix:

### Step 1: Junior-Friendly Issue Creation
- **Rule**: Direct commits to `main` without an issue are STRICTLY FORBIDDEN.
- Check active repository and default branch (`main` or `master`).
- Create an issue via GitHub MCP `issue_write` (see `assets/issue-template.json`):
  - **Title**: `feat(<scope>): <summary>` or `fix(<scope>): <summary>`
  - **Body**: Structured into Overview, Technical Context, and Acceptance Criteria.

### Step 2: Main Sync & Feature Branch Initialization
1. Switch to default branch and pull latest changes:
   ```bash
   git checkout main && git pull origin main
   ```
2. Create and checkout normalized feature branch using the issue number:
   ```bash
   git checkout -b feat/<id>-<slug>
   ```
3. Validate branch name format using the CLI script:
   ```bash
   python3 scripts/manage_git_feature_lifecycle.py --branch feat/<id>-<slug> --strict
   ```

### Step 3: Implementation & Conventional Commit
1. Implement the requested feature or fix adhering to Clean Code and TSDoc standards.
2. Run local unit tests and build commands to guarantee zero regressions:
   ```bash
   pnpm test && pnpm build
   ```
3. Commit staged changes using Conventional Commits:
   ```bash
   git commit -m "feat(<scope>): <summary>"
   ```

### Step 4: Push & Pull Request Drafting
1. Push local branch to remote origin:
   ```bash
   git push -u origin feat/<id>-<slug>
   ```
2. Draft Pull Request using GitHub MCP `create_pull_request` (or web UI):
   - **Title**: `feat(<scope>): <summary>`
   - **Body**: Fill out `assets/pr-template.md`.
   - **Mandatory Directive**: MUST include `Closes #<id>` or `Fixes #<id>` to auto-close the issue on merge.
   - **Base Branch**: `main`.

### Step 5: Pull Request Merge Execution
1. Review automated CI/CD checks and test results.
2. Execute PR merge into `main` using GitHub MCP `merge_pull_request` (or user approval).

### Step 6: Post-Merge Main Sync & Branch Pruning
Once the PR is merged, execute immediate local and remote branch pruning:
```bash
# 1. Return to main and pull latest merged code
git checkout main && git pull origin main

# 2. Delete local feature branch
git branch -d feat/<id>-<slug>

# 3. Delete remote tracking branch
git push origin --delete feat/<id>-<slug>

# 4. Prune stale tracking refs
git remote prune origin
```

---

## Gotchas & Git Lifecycle Pitfalls

| Insecure Shortcut / Anti-Pattern | Standard Enterprise Protocol | Why It Matters |
|---|---|---|
| Committing directly to `main` branch | Checkout normalized branch `feat/<id>-<slug>` | Bypasses code review, automated CI tests, and breaks branch protection rules. |
| Non-standard branch names (`temp`, `test1`) | Normalized `feat/<id>-<slug>` pattern | Makes tracking which branch addresses which GitHub Issue impossible across teams. |
| Using `"Related to #42"` in PR body | Explicit `Closes #42` or `Fixes #42` | GitHub will NOT auto-close the issue without an explicit recognized closing keyword. |
| Leaving merged branches hanging forever | Pruning local (`git branch -d`) & remote branches | Stale branch accumulation creates clutter and confusion in repository graphs. |
| Creating feature branches off dirty state | Checking out and pulling `main` before branching | Leads to unexpected merge conflicts and accidental inclusion of unrelated edits. |
| Pushing without running unit tests | Running `pnpm test` and `pnpm build` before pushing | Pushing broken code breaks the team's shared CI build pipeline. |
