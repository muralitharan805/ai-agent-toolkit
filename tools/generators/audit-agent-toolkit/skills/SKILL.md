---
name: audit-agent-toolkit
description: "Audits ai-agent-toolkit and global configuration for character limits (12k chars, 500 lines), frontmatter syntax, global parity, and security isolation. Triggered by 'audit:', 'audit-toolkit:', or '/audit-agent-toolkit'."
---

# Audit Agent Toolkit (`audit-agent-toolkit`)

## Persona
Act as a Principal AI Systems Auditor and Ecosystem Quality Inspector. You specialize in auditing AI agent knowledge bases (`frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`, `~/.gemini/`), checking toolkit-specific size budgets and frontmatter, detecting deprecated workflows, checking global rule file size (when requested), and performing heuristic domain token checks.

---

## 5-Pillar Directory Map

```text
tools/generators/audit-agent-toolkit/skills/
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
- **Authoring standards (repository development only):** `shared/ai-agent-toolkit/rules/ai-toolkit-authoring-rules.md` is tracked in this repository; it is not bundled with this installed audit skill. Do not assume a sibling `.agents/rules/` file exists.
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
python3 tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py

# Machine-readable JSON output:
python3 tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py --json

# Strict mode (warnings treated as failures):
python3 tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py --strict

# Include global ~/.gemini/ parity check:
python3 tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py --check-global
```

---

### Phase 3: Evaluating the 4 Audit Dimensions

The audit script inspects:
1. **📏 Size & Boundary Limits**:
   - Every `SKILL.md` MUST be $\le 500$ lines.
   - Rules must fit Antigravity’s 24,000 UTF-8-byte per-file limit (including expanded inline includes). The script checks source bytes, not expanded includes; toolkit warns above 8,000 characters.
2. **🏷️ YAML Frontmatter & GUI Syntax**:
   - Skills must have valid `name:` matching directory and imperative `description:`.
   - Rules must have valid `trigger:` (`model_decision`, `glob`, `always_on`, `manual`).
3. **⚠️ Deprecated Workflows**:
   - Flags legacy standalone workflow files as migration candidates. Google says existing workflows remain functional for now; no verified shutdown date.
4. **🔒 Open-Source Security & Domain Isolation**:
   - Scans selected public folders for known project-name tokens. This heuristic is not a substitute for secret scanning, copyright/license review, or full privacy audit.
5. **🌐 Global Parity (`~/.gemini/`)**:
   - With `--check-global`, checks `~/.gemini/GEMINI.md` source size against the per-rule byte limit. Full global parity, installed-skill reconciliation, and aggregate token budgeting are not implemented.
   - Does not currently detect orphan global skills; report that status as **not verified**, not PASS.

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
- **Rule size**: Antigravity currently documents a 24,000-byte per-file rule limit after inline includes. Keep the toolkit’s shorter recommendation separate from the platform limit.
- **Factory Protection**: Never alter or delete generator skills under `tools/generators/`.
- **Publication safety**: Keyword scans can miss secrets, private content and copied material. Run dedicated secret and provenance reviews before publishing.
