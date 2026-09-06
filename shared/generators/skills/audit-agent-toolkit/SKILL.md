---
name: audit-agent-toolkit
description: "Audits ai-agent-toolkit and global configuration for character limits (12k chars, 500 lines), frontmatter syntax, global parity, and security isolation. Triggered by 'audit:', 'audit-toolkit:', or '/audit-agent-toolkit'."
---

# Audit Agent Toolkit (`audit-agent-toolkit`)

## Persona
Act as a Principal AI Systems Auditor and Ecosystem Quality Inspector. You specialize in auditing AI agent knowledge bases (`frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`, `~/.gemini/`), verifying strict token budgets, validating frontmatter GUI compatibility, detecting deprecated workflows, checking global parity, and enforcing open-source security isolation.

---

## 5-Pillar Directory Map

```text
shared/generators/skills/audit-agent-toolkit/
├── SKILL.md                                        # Tier 2 Core Audit Protocol (< 500 lines)
├── references/
│   └── audit-criteria-and-token-budgets.md         # Detailed token ceilings and isolation criteria
├── scripts/
│   └── audit_toolkit.py                            # Standalone whole-repo CLI audit utility (PEP 723)
└── evals/
    ├── evals.json                                  # Objective test cases for ecosystem audit
    └── grading.json                                # Automated verification scorecard
```

---

## Authoritative Reference Grounding
Consult the bundled reference guides and tools:
- [Audit Criteria & Token Budgets](references/audit-criteria-and-token-budgets.md): Exact character ceilings, line limits, and domain isolation criteria.
- [AI Toolkit Authoring Standards Rule](../../../ai-agent-toolkit/rules/ai-toolkit-authoring-rules.md): Supreme governing authoring rule for the repository.
- [Audit CLI Script](scripts/audit_toolkit.py): Automated tool executing comprehensive whole-repo inspection.

---

## Task Protocol

### Phase 1: Preparation & Target Identification
1. Identify whether the audit is targeting the **local repository**, a **specific module**, or includes **global context** (`~/.gemini/`).
2. Read [references/audit-criteria-and-token-budgets.md](references/audit-criteria-and-token-budgets.md) to review the 4 audit dimensions.

---

### Phase 2: Automated CLI Ecosystem Audit
Execute the bundled audit utility directly via terminal:

```bash
# Standard whole-repo audit:
python3 shared/generators/skills/audit-agent-toolkit/scripts/audit_toolkit.py

# Machine-readable JSON output:
python3 shared/generators/skills/audit-agent-toolkit/scripts/audit_toolkit.py --json

# Strict mode (warnings treated as failures):
python3 shared/generators/skills/audit-agent-toolkit/scripts/audit_toolkit.py --strict

# Include global ~/.gemini/ parity check:
python3 shared/generators/skills/audit-agent-toolkit/scripts/audit_toolkit.py --check-global
```

---

### Phase 3: Evaluating the 4 Audit Dimensions

The audit script inspects:
1. **📏 Size & Boundary Limits**:
   - Every `SKILL.md` MUST be $\le 500$ lines.
   - Every `.md` rule file MUST be $\le 12,000$ characters (warns if $> 8,000$ chars).
2. **🏷️ YAML Frontmatter & GUI Syntax**:
   - Skills must have valid `name:` matching directory and imperative `description:`.
   - Rules must have valid `trigger:` (`model_decision`, `glob`, `always_on`, `manual`).
3. **⚠️ Deprecated Workflows**:
   - Flags any legacy standalone `.agents/workflows/*.md` or `workflows/` files slated for retirement on November 1, 2026.
4. **🔒 Open-Source Security & Domain Isolation**:
   - Ensures zero proprietary domain tokens (`nidhiflow`, `civicpath`, `seyalicraft`, `docker-dev-infra`) leak into open-source public folders (`frameworks/`, `infra/`, `shared/`).
5. **🌐 Global Parity (`~/.gemini/`)**:
   - Checks `~/.gemini/GEMINI.md` total characters ($\le 12,000$).
   - Flags orphan skills in `~/.gemini/` that no longer exist in `ai-agent-toolkit`.

---

### Phase 4: Scorecard Presentation & Remediation Protocol

1. Present the visual Health Scorecard to the user:

```text
========================================================
🛡️  AI AGENT TOOLKIT ECOSYSTEM HEALTH AUDIT
========================================================
Repository Root    : [path]
Overall Health     : [Score]% [🟢/🟡/🔴]
Status             : [PASS 🟢 | NEEDS ATTENTION 🔴]
--------------------------------------------------------
📦 Skills Audited  : [Passed]/[Total] Passed
📜 Rules Audited   : [Passed]/[Total] Passed
⚠️  Deprecated WFs : [Count] Found
🔒 Domain Security : [CLEAN 🟢 | LEAK DETECTED 🔴]
========================================================
```

2. **Remediation Action Plan**:
   - If a rule exceeds 12,000 characters: Recommend splitting into focused sub-rules using `model_decision` or `glob`.
   - If a skill exceeds 500 lines: Move reference manuals to `references/` or code to `scripts/`.
   - If deprecated workflows exist: Propose migrating them to 5-pillar **Procedural Skills**.

---

## Gotchas
- **Hard Truncation Ceiling**: Antigravity IDE enforces a hard 12,000-character cutoff on rules. Never allow a rule file to approach 12,000 characters.
- **Factory Protection**: Never alter or delete generator skills under `shared/generators/`.
- **Zero Proprietary Leaks**: Public open-source commits must never leak private company domain keys or names.
