# Audit Criteria & Token Budget Specifications

> Antigravity rule format/limits verified 2026-11-07: https://antigravity.google/docs/rules ; workflow status: https://antigravity.google/docs/migration/workflows-to-skills. Numeric authoring targets below are toolkit policy unless explicitly marked as a platform limit.

## 1. Overview
The `audit-agent-toolkit` skill acts as the Quality Assurance Inspector for the entire `ai-agent-toolkit` ecosystem. It continuously enforces token budgets, file length limits, frontmatter syntax, global synchronization parity, and open-source security isolation.

---

## 2. Hard Limits & Token Budgets

| Component | Target Budget | Hard IDE Limit | Action on Violation |
| :--- | :--- | :--- | :--- |
| **Agent Skill (`SKILL.md`)** | 100–250 lines | No verified platform 500-line hard limit (toolkit policy: 500 lines) | Split reference patterns into `references/` or `examples/`. |
| **Antigravity Rule (`.md`)** | 6,000–8,000 chars | **24,000 UTF-8 bytes** after `@[...]` expansion | Split into modular sub-rules (`model_decision` or `glob`). |
| **Global Rules (`GEMINI.md`)** | 6,000–8,000 chars | **24,000 UTF-8 bytes per rule**; 20,000 aggregate active-rule tokens | Prune non-essential rules; keep only universal invariants. |
| **Skill Name** | Lowercase kebab-case | Matches directory | Rename frontmatter or directory to achieve 1:1 parity. |
| **Frontmatter Description** | 100–300 chars | **1,024 chars** | Rephrase into clear third-person imperative summary. |

---

## 3. The 4 Audit Dimensions

**Scope note:** The bundled `audit_toolkit.py` performs static size, frontmatter, rule-trigger, deprecated-workflow and keyword-isolation checks. `--check-global` currently checks the global `GEMINI.md` size only; full orphan/hash parity and aggregate prompt-token inspection are **not implemented** and must not be represented as verified.

### Dimension 1: File Length & Character Ceilings
- **Skills**: Every `SKILL.md` must be $\le 500$ lines. Auxiliary files must live in subdirectories (`references/`, `scripts/`, `assets/`, `evals/`).
- **Rules**: Every `.md` rule file must be within 24,000 UTF-8 bytes after inline expansion (platform limit). The toolkit warns above 8,000 characters.
- **Global Context**: The audit can check the source file's 24,000-byte rule limit but **cannot compute** the 20,000-token aggregate budget or expanded includes without additional context.

### Dimension 2: YAML Frontmatter & GUI Compatibility
- **Skills**: Must include `name:` (matching directory) and `description:` (third-person imperative phrasing).
- **Rules**: Must include `description:` and valid `trigger:` (`model_decision`, `glob`, `always_on`, or `manual`). If `trigger: glob`, a comma-separated string under `globs:` (or `glob:`) is required.
- **Workflows Sunset**: Any standalone `.agents/workflows/*.md` file or `workflows/` directory must be flagged as DEPRECATED (no confirmed retirement date; legacy workflows still work for now).

### Dimension 3: Global Parity & Synchronization Health
- **Orphan Detection (not implemented)**: Manually compare installed global skill directories against toolkit sources when needed.
- **Outdated Sync (not implemented)**: Check installed manifests/hashes or re-sync explicitly; the bundled audit does not compare timestamps.
- **Framework Bleed (not implemented)**: Review global `GEMINI.md` content manually; the bundled audit only checks its source-file size.

### Dimension 4: Open-Source Security & Domain Leak Isolation
- **Gitignore Protection**: Verifies that `.gitignore` contains `domains/*` (and `!domains/README.md`).
- **Configurable private-name screening (opt-in)**: Set `AI_AGENT_TOOLKIT_PRIVATE_TOKENS` to a comma-separated list of names **in your local environment**, not in public Git-tracked files. The audit checks `frameworks/`, `infra/`, and `shared/` for those names.
- If the variable is unset, the result is **NOT CONFIGURED**, not a completed privacy review. Independently review tracked source, Git history, third-party licensing, and run Gitleaks. A configured match is a blocking signal requiring investigation; the keyword scanner alone cannot prove that a snapshot is safe.
