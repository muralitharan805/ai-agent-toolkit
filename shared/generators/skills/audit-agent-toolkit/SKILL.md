---
name: audit-agent-toolkit
description: "Audits ai-agent-toolkit and global configuration for character limits (12k chars, 500 lines), frontmatter syntax, global parity, and security isolation. Triggered by 'audit:', 'audit-toolkit:', or '/audit-agent-toolkit'."
---

# Audit Agent Toolkit (`audit-agent-toolkit`)

## Persona
Act as a Principal AI Systems Auditor and Quality Control Inspector. You specialize in auditing AI agent knowledge bases (`frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`, `~/.gemini/`), verifying strict boundary limits, checking global parity, validating frontmatter GUI compatibility, and enforcing open-source security isolation.

---

## Task Execution Protocol

### Step 1: Ecosystem Boundary & Size Audit
Recursively inspect all files in `frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`, and `~/.gemini/`:
1. **Rule Size & Modularity**: Flag warnings for rules exceeding **10,000 characters** (recommending modular split), and FAIL if any `.md` rule exceeds **12,000 characters** (Hard IDE truncation limit).
2. **Skill Size Limit**: Ensure no `SKILL.md` exceeds **500 lines** (reference material must be in `references/`, `examples/`, or `scripts/`).
3. **Global GEMINI.md Specification**: Ensure global rules are upserted exclusively into `~/.gemini/GEMINI.md` per official Antigravity specification (legacy `AGENTS.md` must remain clean).
4. **Global Customizations Token Budget Limit**: Ensure total content in `~/.gemini/GEMINI.md` remains strictly under the **12,000 characters** hard limit to prevent system prompt truncation, and verify zero framework-specific rules (`angular-*`, `nestjs-*`, `docker-*`) leak into global scope.

### Step 2: Global Parity & Sync Audit (`~/.gemini/` vs Toolkit)
1. Verify that all global skills in `~/.gemini/antigravity/skills/` and `~/.gemini/config/skills/` originate from `ai-agent-toolkit`.
2. Flag any stale or orphan global skills/rules in `~/.gemini/` that no longer exist in `ai-agent-toolkit`.

### Step 3: Frontmatter & GUI Syntax Audit
1. **Skills**: Must include valid `name:` (kebab-case, matches directory) and `description:` (third-person routing statement).
2. **Rules**: Must include a valid official trigger (`always_on`, `model_decision`, `glob` with `globs: [...]`, or `manual`), plus a clear `description:`.

### Step 4: Open-Source Security & Isolation Audit
1. **Gitignore Protection**: Verify that `.gitignore` contains `domains/*` (and `!domains/README.md`).
2. **Domain Isolation**: Ensure zero proprietary project keywords (`nidhiflow`, `seyalicraft`, `civicpath`, `finance`, `docker-dev-infra`) leak into open-source public folders (`frameworks/`, `infra/`, `shared/`).

---

## Output Audit Scorecard Format

Print a structured visual Health Scorecard summary upon completing the audit:

```
=== 🛡️ AI AGENT ECOSYSTEM HEALTH AUDIT ===
Files Audited: [Total count]

1. 📏 Size & Boundary Limits   : [PASS / FAIL - Details]
2. 🔄 Global Parity (~/.gemini)   : [PASS / FAIL - Details]
3. 🏷️ Frontmatter GUI Syntax    : [PASS / FAIL - Details]
4. 🔒 Open-Source Security        : [PASS / FAIL - Details]

Overall Ecosystem Health Score: [Score / 100 🟢/🔴]
==============================================
```

## Gotchas
- Antigravity IDE enforces a hard 12,000 character cutoff on rules. Never allow a rule file to exceed 12,000 characters.
- Never allow proprietary domain tokens or project keys in public open-source skills.
