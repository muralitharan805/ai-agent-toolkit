# Problem Discovery Suites

## Overview
This directory houses the modular, decoupled capabilities forming the **Problem Discovery Lifecycle Ecosystem**. Unlike monolithic discovery scripts, each capability represents an independent reasoning or infrastructure suite adhering strictly to the `agentskills.io` 5-pillar modular architecture.

---

## Suite Topology

| Stage | Suite Name | Type | Directory | Core Responsibility |
|:---:|:---|:---:|:---|:---|
| **01** | `research-planning` | Reasoning | `shared/problem-discovery-suites/research-planning/` | Slot filling, domain decomposition, precision search dorks & MECE streams. |
| **02** | `evidence-research` | Reasoning | `shared/problem-discovery-suites/evidence-research/` | Search execution, primary source inspection, verbatim quotes & L1–L5 tagging. |
| **03** | `problem-evaluation` | Reasoning | `shared/problem-discovery-suites/problem-evaluation/` | Forensic 14-node workflow mapping, root-cause isolation & 35-point scoring. |
| **04** | `experiment-validation` | Reasoning | `shared/problem-discovery-suites/experiment-validation/` | Preregistered experiment contracts (DESIGN) & empirical trial audits (ASSESS). |
| **05** | `solution-strategy` | Reasoning | `shared/problem-discovery-suites/solution-strategy/` | Non-software sufficiency, 15-flag constraints, SaaS gating & 14-day STS design. |
| **06** | `discovery-state` | Infrastructure | `shared/problem-discovery-suites/discovery-state/` | SQLite persistence, deterministic math, dynamic context packs & `v_discovery_dashboard`. |

---

## 5-Pillar Architecture Inside Every Suite

Every suite implements the standard directory bundle:
- `rules/`: Strict execution and validation invariants (`model_decision` trigger, 6k–8k chars).
- `skills/SKILL.md`: Core multi-phase procedure (< 500 lines) with persona and gotchas.
- `skills/references/`: Granular technical runbooks and architecture guidelines.
- `skills/scripts/`: Standalone, idempotent CLI automation tools (PEP 723 metadata).
- `skills/assets/`: JSON schemas (Draft 2020-12), DDLs, and template output packs.
- `skills/evals/`: Verifiable test cases (`evals.json`) and grading scorecards (`grading.json`).

---

## Synchronization & Tooling

To synchronize all 6 suites into your active workspace (`.agents/`):
```bash
./bin/context.sh -w shared/problem-discovery-suites
```

To sync an individual suite:
```bash
./bin/context.sh -w shared/problem-discovery-suites/research-planning
```

To verify all suites:
```bash
for dir in shared/problem-discovery-suites/*; do
  [[ -d "$dir" ]] && python3 tools/generators/generate-agent-suite/skills/scripts/verify_suite.py "$dir"
done
```
