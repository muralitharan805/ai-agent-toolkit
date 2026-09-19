# Audit Criteria & Token Budget Specifications

## 1. Overview
The `audit-agent-toolkit` skill acts as the Quality Assurance Inspector for the entire `ai-agent-toolkit` ecosystem. It continuously enforces token budgets, file length limits, frontmatter syntax, global synchronization parity, and open-source security isolation.

---

## 2. Hard Limits & Token Budgets

| Component | Target Budget | Hard IDE Limit | Action on Violation |
| :--- | :--- | :--- | :--- |
| **Agent Skill (`SKILL.md`)** | 100–250 lines | **500 lines** | Split reference patterns into `references/` or `examples/`. |
| **Antigravity Rule (`.md`)** | 6,000–8,000 chars | **12,000 chars** | Split into modular sub-rules (`model_decision` or `glob`). |
| **Global Rules (`GEMINI.md`)** | 6,000–8,000 chars | **12,000 chars** | Prune non-essential rules; keep only universal invariants. |
| **Skill Name** | Lowercase kebab-case | Matches directory | Rename frontmatter or directory to achieve 1:1 parity. |
| **Frontmatter Description** | 100–300 chars | **1,024 chars** | Rephrase into clear third-person imperative summary. |

---

## 3. The 4 Audit Dimensions

### Dimension 1: File Length & Character Ceilings
- **Skills**: Every `SKILL.md` must be $\le 500$ lines. Auxiliary files must live in subdirectories (`references/`, `scripts/`, `assets/`, `evals/`).
- **Rules**: Every `.md` rule file must be $\le 12,000$ characters. A warning is emitted if a rule exceeds 8,000 characters.
- **Global Context**: Total character length of `~/.gemini/GEMINI.md` must not exceed 12,000 characters to prevent system prompt truncation.

### Dimension 2: YAML Frontmatter & GUI Compatibility
- **Skills**: Must include `name:` (matching directory) and `description:` (third-person imperative phrasing).
- **Rules**: Must include `description:` and valid `trigger:` (`model_decision`, `glob`, `always_on`, or `manual`). If `trigger: glob`, the `globs: [...]` array is mandatory.
- **Workflows Sunset**: Any standalone `.agents/workflows/*.md` file or `workflows/` directory must be flagged as DEPRECATED (retirement on Nov 1, 2026).

### Dimension 3: Global Parity & Synchronization Health
- **Orphan Detection**: Detects skills in `~/.gemini/antigravity/skills/` or `~/.gemini/config/skills/` that no longer exist in the toolkit source.
- **Outdated Sync**: Flags skills or rules whose source file modification timestamp is newer than the deployed copy in `.agents/` or `~/.gemini/`.
- **Framework Bleed**: Ensures no framework-specific rules (`angular-*`, `nestjs-*`, `docker-*`) are leaked into universal global `GEMINI.md`.

### Dimension 4: Open-Source Security & Domain Leak Isolation
- **Gitignore Protection**: Verifies that `.gitignore` contains `domains/*` (and `!domains/README.md`).
- **Proprietary Token Leak Check**: Open-source public folders (`frameworks/`, `infra/`, `shared/`) must have ZERO references to proprietary project domain names:
  - `nidhiflow`
  - `civicpath`
  - `seyalicraft`
  - `docker-dev-infra`
- Any detected proprietary token in a public file constitutes an immediate audit **CRITICAL FAIL**.
