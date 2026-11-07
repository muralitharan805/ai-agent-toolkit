# Branching & Pull Request Automation Architecture

## Overview

Modern software engineering teams rely on structured issue tracking, normalized git branches, and automated PR lifecycles to maintain repository health, eliminate phantom branches, and prevent accidental direct commits to `main`.

---

## 1. Junior-Friendly GitHub Issue Standard

Every code change begins with an explicit GitHub Issue. If no issue exists, agents must scaffold one prior to branching.

### Issue Quality Anatomy:
1. **Title**: Follows Conventional Commits (`feat(<scope>): <summary>` or `fix(<scope>): <summary>`).
2. **Overview**: Clear plain-language explanation of what problem needs solving.
3. **Technical Context**: Key modules, database tables, or endpoints affected.
4. **Acceptance Criteria**: Verifiable markdown checklist (`- [ ] ...`) defining the definition of done.

```json
{
  "title": "feat(orders): add order status webhook notification",
  "body": "## Overview\nNotify external merchants when order status changes to COMPLETED or REFUNDED.\n\n## Technical Context\nTriggered from `OrdersService.updateStatus()`, emitting a webhook payload to the merchant's configured callback URL.\n\n## Acceptance Criteria\n- [ ] Emit HMAC-SHA256 signature in X-Signature header\n- [ ] Retry with exponential backoff on 5xx failures\n- [ ] Unit tests for webhook dispatch service",
  "labels": ["enhancement", "backend"]
}
```

---

## 2. Normalized Branch Naming Convention

Always branch off a fresh, updated `main` (or `master`):

```bash
git checkout main && git pull origin main
```

### Branch Pattern:
```text
<type>/<issue-id>-<slug>
```

| Type | Pattern | Valid Example |
|---|---|---|
| **Feature** | `feat/<id>-<slug>` | `feat/42-order-status-webhook` |
| **Bug Fix** | `fix/<id>-<slug>` | `fix/19-emi-rounding-error` |
| **Docs** | `docs/<id>-<slug>` | `docs/8-update-api-spec` |
| **Refactor**| `refactor/<id>-<slug>` | `refactor/105-decouple-auth-service` |

---

## 3. Pull Request Auto-Closing Linking Syntax

GitHub automatically closes referenced issues when a Pull Request is merged into the default branch, provided that one of the recognized closing keywords is included:

### Recognized Auto-Closing Directives:
- `Closes #<id>` (or `closes #<id>`, `closed #<id>`)
- `Fixes #<id>` (or `fixes #<id>`, `fixed #<id>`)
- `Resolves #<id>` (or `resolves #<id>`, `resolved #<id>`)

> [!IMPORTANT]
> The keyword must precede the issue number directly (e.g. `Closes #42`). Phrases like `"Related to #42"` or `"See #42"` will **NOT** auto-close the issue upon merge!

---

## 4. Post-Merge Branch Pruning Protocol

Once a Pull Request has been merged into `main`, clean up both local and remote branches immediately to prevent repository bloat:

```bash
# 1. Return to default branch and pull merged code
git checkout main && git pull origin main

# 2. Delete local branch (safe delete)
git branch -d feat/42-order-status-webhook

# 3. Delete remote origin branch
git push origin --delete feat/42-order-status-webhook

# 4. Prune stale tracking references
git remote prune origin
```
