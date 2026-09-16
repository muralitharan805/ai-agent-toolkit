# Agent Action Boundaries & Golden Rules Implementation Guide

## 1. The Authoritative vs Operational Decoupling

To eliminate policy drift over time, the Agent Action Guard architecture strictly bifurcates responsibilities:

- **Golden Rules ([rules/agent-action-guard-rules.md](../../rules/agent-action-guard-rules.md))**: Authoritative policy source (**WHAT** is allowed and forbidden).
- **Skill Core ([SKILL.md](../SKILL.md))**: Operational workflow (**HOW** the policy is executed).
- **Auditor & Evals**: Automated verification (**PROOF** that the policy is upheld).

---

## 2. The Orthogonal R0–R3 Risk Taxonomy

Risk evaluation is independent of user intent. Regardless of how the user phrases a request, the underlying action carries an inherent operational risk:

| Risk Tier | Definition | Examples | Gating Standard |
| :--- | :--- | :--- | :--- |
| **R0** | **Read-Only Inspection** | `view_file`, `grep_search`, `list_dir`, `git status` | Autonomous execution; zero approval needed. |
| **R1** | **Local, Reversible Mutation** | Bug fixes, single-component refactors | Direct execution when execution intent is clear. |
| **R2** | **Scope-Expanding / Shared Config** | Updating `package.json`, shared API interfaces | Execute if clearly implied; otherwise confirm. |
| **R3** | **Destructive, Security, or Production** | Deletions, `git reset --hard`, schema drops | Mandatory explicit confirmation before running. |

---

## 3. Preserving Existing User Work

A critical failure mode of automated coding assistants is clobbering uncommitted developer changes. The assistant must enforce:
1. **Never Discard User Working Tree State**:
   - `git checkout .`, `git reset --hard`, and `git clean -fd` are strictly prohibited.
2. **Preserve Unrelated Modifications**:
   - When editing a dirty file containing pre-existing user changes, target ONLY the lines relevant to the assigned task. Never revert surrounding modifications.
3. **Check Status Before Major Operations**:
   - Run `git status -s` to recognize active user modifications before applying changes.

---

## 4. Proportional Verification Escalation (Levels 1–3)

Rather than running monolithic test suites for localized edits, verification follows tiered evidence-based escalation:

```
[Level 1: Component Check]  ──► Run targeted test/linter for the modified file
           │ (Does it pass? Yes ──► Stop)
           │ (Does it break inter-service contracts?)
           ▼
[Level 2: Module Check]     ──► Run package/module-level test suite
           │ (Does it pass? Yes ──► Stop)
           │ (Does it modify core schemas or global configs?)
           ▼
[Level 3: Global Check]     ──► Run full monorepo build or E2E suite
```

*Always start at Level 1; escalate to higher levels ONLY when dependency impact, risk, or regression evidence requires it.*
