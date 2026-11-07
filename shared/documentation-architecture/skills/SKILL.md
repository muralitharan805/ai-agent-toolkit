---
name: documentation-architecture
description: "Enforces 5-minute developer onboarding README standards, 6-pillar docs/ architecture runbooks, version-controlled Mermaid diagrams, Keep a Changelog governance, and production troubleshooting playbooks. Triggered by 'docs:', 'readme:', 'architecture-doc:', 'runbook:', or '/documentation-architecture'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Documentation Architecture & System Runbook Skill

## Overview

This skill establishes the production engineering standards for **< 5-Minute Developer Onboarding READMEs**, the **Six-Pillar `docs/` Technical Runbook Suite**, **Declarative Mermaid.js Diagramming**, **Architectural Decision Records (ADRs)**, **Production Incident Troubleshooting Playbooks**, and **Keep a Changelog Governance**. It eradicates tribal knowledge, guarantees rapid developer onboarding, and arms on-call engineers with clear, structured incident runbooks.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                   5-Phase Documentation Architecture Pipeline                  │
│                                                                                │
│   [Phase 1: 5-Min README Onboarding] ──► Prerequisites & docker compose up -d │
│                 │                                                              │
│   [Phase 2: 6-Pillar docs/ Runbooks] ──► Architecture, Dev, Test, Deploy, DB   │
│                 │                                                              │
│   [Phase 3: Declarative Diagrams]    ──► Version-controlled Mermaid.js graphs  │
│                 │                                                              │
│   [Phase 4: Architectural Decisions] ──► Structured ADR records in docs/       │
│                 │                                                              │
│   [Phase 5: Playbooks & CHANGELOG]   ──► On-call incident runbooks & releases  │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Phase Execution Guide

### Phase 1: 5-Minute Developer Onboarding README Scaffolding
1. **Document Single-Sentence Scope**:
   - Clearly state the business problem and domain ownership of the service.
2. **Deterministic Quick Start**:
   - Provide exact copy-paste CLI commands: clone, copy `.env.example`, `docker compose up -d`, install, migrate, and start.
3. **Automated Verification Step**:
   - Include a curl check against `/api/v1/health/ready` to verify correct local startup.

### Phase 2: Six-Pillar `docs/` Technical Runbook Hierarchy
1. **Scaffold the Six Core Documents**:
   - `docs/architecture.md`: Clean architecture layers, data flow, and external system boundaries.
   - `docs/development.md`: Local environment configurations, debugging runbooks, and useful CLI scripts.
   - `docs/testing.md`: Testing pyramid execution (unit, integration, smoke, performance) and data fixtures.
   - `docs/deployment.md`: CI/CD pipelines, staging/production topology, and rollback runbooks.
   - `docs/database.md`: ER diagrams, migration conventions, and connection pool sizing.
   - `docs/troubleshooting.md`: Common production error codes, FAQ, and incident remediation steps.

### Phase 3: Declarative Mermaid.js System & ER Diagramming
1. **Embed Diagrams Declaratively**:
   - Use fenced code blocks with language `mermaid` directly inside markdown files.
2. **Version Control Integration**:
   - Never use static binary image files (`.png`, `.jpg`) for core architecture or entity relationship diagrams.
   - Mermaid diagrams can be reviewed and diffed directly within git pull requests.

### Phase 4: Architectural Decision Records (ADRs)
1. **Record Critical Decisions**:
   - Document non-trivial technical trade-offs (e.g. database selection, caching strategies, queue brokers).
2. **Standard ADR Format**:
   - Include: `Status`, `Context`, `Decision`, and `Consequences`.

### Phase 5: Incident Playbooks & Release Changelogs
1. **Author High-Stress On-Call Playbooks**:
   - In `docs/troubleshooting.md`, pair each critical alert with root cause diagnostics and immediate mitigation commands.
2. **Maintain Release History**:
   - Update `CHANGELOG.md` following the Keep a Changelog standard (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`).

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/system-documentation-and-runbooks.md](references/system-documentation-and-runbooks.md) for six-pillar breakdowns, Mermaid templates, and incident response structures.
- **Production Asset**: Inspect [assets/readme-and-docs-bootstrap.template.ts](assets/readme-and-docs-bootstrap.template.ts) for README, architecture, and troubleshooting Markdown templates.
- **CLI Auditor Tool**: Run [scripts/audit_documentation_architecture.py](scripts/audit_documentation_architecture.py) to audit README quick start, docs/ pillars, and Mermaid diagrams.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Architectural Risk |
| :--- | :--- | :--- | :--- |
| **Developer Onboarding** | Multi-page wiki guide with tribal knowledge steps | **< 5-minute setup** via `docker compose up -d` in README | 2–3 days wasted per developer onboarding, high friction. |
| **Architecture Diagrams** | Unversioned PNG images or dead links to external tools | **Declarative Mermaid.js** diagrams embedded in markdown | Documentation instantly becomes stale and cannot be git-diffed. |
| **Incident Response** | Searching Slack history at 2 AM during an outage | **`docs/troubleshooting.md`** with alert playbooks | Prolonged MTTR (mean time to resolution) and customer downtime. |
| **Changelog Hygiene** | Unstructured commit logs dumped as release notes | Structured **`CHANGELOG.md` (Keep a Changelog)** | Consumers unaware of breaking changes, API regressions. |
| **Pre-Deployment Gate** | Launching service with empty or outdated docs | **Mandatory documentation review gate** in PR | Unmaintainable services when the original author leaves the team. |
