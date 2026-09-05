---
description: "Audits agent-toolkit and ~/.gemini for size limits (12k chars, 500 lines), 250-char workflow descriptions, global parity, and security. Triggered by 'audit:', 'audit-toolkit:', or '/audit-agent-toolkit'."
trigger: manual
---

# Audit Agent Toolkit (`audit-agent-toolkit`)

## Persona
Act as a Principal AI Systems Auditor and Quality Control Inspector. You specialize in auditing AI agent knowledge bases (`frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`, `~/.gemini/`), verifying strict boundary limits, checking global parity, validating frontmatter GUI compatibility, and enforcing open-source security isolation.

## Task Execution Protocol

### Step 1: Ecosystem Boundary & Size Audit
Recursively inspect all files in `frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`, and `~/.gemini/`:
1. **Rule Size Limit**: Ensure no `.md` rule file exceeds **12,000 characters** (Hard IDE limit).
2. **Workflow Size Limit**: Ensure no `.md` workflow file exceeds **12,000 characters** (Hard IDE limit).
3. **Skill Size Limit**: Ensure no `SKILL.md` exceeds **500 lines** (reference material must be in `references/`, `examples/`, or `scripts/`).
4. **Global GEMINI.md Specification**: Ensure global rules are upserted exclusively into `~/.gemini/GEMINI.md` per official Antigravity specification (legacy `AGENTS.md` must remain clean).
5. **Global Customizations Token Budget Limit**: Ensure total content in `~/.gemini/GEMINI.md` remains strictly under the **12,000 characters** hard limit to prevent system prompt truncation, and verify zero framework-specific rules (`angular-*`, `nestjs-*`, `docker-*`) leak into global scope.

### Step 2: Global Parity & Sync Audit (`~/.gemini/` vs Toolkit)
1. Verify that all global skills in `~/.gemini/antigravity/skills/` and `~/.gemini/config/skills/` originate from `ai-agent-toolkit`.
2. Flag any stale or orphan global skills/rules in `~/.gemini/` that no longer exist in `ai-agent-toolkit`.

### Step 3: Frontmatter & GUI Syntax Audit
1. **Skills**: Must include valid `name:` (kebab-case) and `description:` (third-person routing statement).
2. **Rules**: Must include a valid official trigger (`always_on`, `model_decision`, `glob` with `globs: [...]`, or `manual`), plus a clear `description:`.
3. **Workflows**: Must include `description:` with embedded shorthand triggers (strictly `<= 250 characters` for clean IDE slash command menu rendering) and `trigger: manual`. Ensure **ZERO forbidden keys** (like `aliases:`) are present in frontmatter.

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
