---
name: code-quality-and-devex
description: "Focuses strictly on tooling and automation (ESLint, Prettier, Husky pre-commit hooks, commitlint, GitLeaks). Not for software design patterns. Triggered by 'devex:', 'lint:', 'prettier:', 'commitlint:', 'pre-commit:', or '/code-quality-and-devex'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Code Quality, DevEx & Tooling Skill

## Overview

This skill establishes the production engineering protocol for **Automated Linting & Zero-Debate Formatting**, **Strict Type Safety (zero `any`)**, **Staged Pre-Commit Hooks (Husky + lint-staged)**, **Conventional Commits Governance (commitlint)**, **Pre-Commit Secret Scanning (GitLeaks)**, and **One-Command Local Environment Orchestration (Compose v2)**. It accelerates developer velocity, eliminates style debates in pull request reviews, and blocks defect leakage before code reaches the git history.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                     5-Phase DevEx & Quality Gate Pipeline                      │
│                                                                                │
│   [Phase 1: Lint & Format Config]   ──► ESLint strict + Prettier auto-format   │
│                 │                                                              │
│   [Phase 2: Strict Type Safety]     ──► tsconfig strict: true; zero any        │
│                 │                                                              │
│   [Phase 3: Staged Pre-Commit Gate] ──► Husky + lint-staged (<1s feedback)    │
│                 │                                                              │
│   [Phase 4: Conventional Commits]   ──► @commitlint/cli commit-msg hook        │
│                 │                                                              │
│   [Phase 5: Secrets & Local DevEx]  ──► GitLeaks staged scan + compose.yaml    │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Phase Execution Guide

### Phase 1: Linters & Zero-Debate Formatters Configuration
1. **Automate Formatting & Remove Bikeshedding**:
   - Install and configure Prettier alongside ESLint.
   - Use `eslint-config-prettier` to disable formatting rules in ESLint, delegating pure formatting to Prettier.
2. **Strict Linter Rules**:
   - Enable `@typescript-eslint/recommended-type-checked` to detect unhandled promises, floating promises, and unsafe type coercions.

### Phase 2: Strict Type Safety & TypeScript Hardening
1. **Enable Strict Compiler Flags**:
   - In `tsconfig.json`, set `"strict": true`, `"noImplicitAny": true`, `"strictNullChecks": true`, and `"noUncheckedIndexedAccess": true`.
2. **Enforce Zero `any`**:
   - Replace explicit `any` with `unknown` paired with type guards or schemas.
   - For unknown payload maps, use `Record<string, unknown>`.

### Phase 3: Staged Pre-Commit Quality Gates (Husky + lint-staged)
1. **Initialize Husky**:
   - Initialize hooks via `pnpm exec husky init`.
2. **Execute Strictly Against Staged Files**:
   - In `package.json`, configure `lint-staged` using [assets/devex-tooling-bootstrap.template.ts](assets/devex-tooling-bootstrap.template.ts).
   - Only staged files (`*.ts`, `*.json`) are linted and formatted, guaranteeing sub-second commit execution.

### Phase 4: Conventional Commits Governance (commitlint)
1. **Standardize Header Syntax**:
   - Install `@commitlint/cli` and `@commitlint/config-conventional`.
   - Configure `.husky/commit-msg` to validate headers: `<type>(<scope>): <description>`.
2. **Allowed Semantic Types**:
   - `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`.
   - Reject uninformative messages (e.g. `wip`, `update`, `fixed bug`).

### Phase 5: Pre-Commit Secret Scanning & Local Docker DevEx
1. **Pre-Commit Secret Scanning**:
   - Integrate `gitleaks protect --staged` into `.husky/pre-commit`.
   - Block commits containing raw API keys, private certificates, or JWT secrets before git commits are written.
2. **One-Command Local Environment**:
   - Provide a root `compose.yaml` spinning up PostgreSQL, Redis, and queues with automated health checks via `docker compose up -d`.

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/code-quality-devex-and-tooling.md](references/code-quality-devex-and-tooling.md) for ecosystem tooling tables, tsconfig flags, and secret scanner configs.
- **Production Asset**: Inspect [assets/devex-tooling-bootstrap.template.ts](assets/devex-tooling-bootstrap.template.ts) for lint-staged, commitlint, GitLeaks, and Docker Compose configurations.
- **CLI Auditor Tool**: Run [scripts/audit_code_quality_devex.py](scripts/audit_code_quality_devex.py) to audit linter, formatter, pre-commit hook, and secret scanner presence.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Architectural Risk |
| :--- | :--- | :--- | :--- |
| **Pre-Commit Scope** | Running full `pnpm test` or full lint on every commit | **`lint-staged` on staged files only** (< 1s feedback) | Slow commits (15–60s) prompt developers to bypass hooks with `--no-verify`. |
| **Formatting Debates** | Debating tabs vs spaces and line lengths in PR reviews | Automated **Prettier with CI failure gates** | Wasted engineering hours and friction during code reviews. |
| **Type Discipline** | Sprinkling `any` to silence compiler errors | Strict **`unknown` + runtime type guards** | Runtime `TypeError: Cannot read properties of undefined` in production. |
| **Secret Scanning** | Scanning for leaked secrets only after push to remote CI | **Pre-commit GitLeaks staged scan** before commit creation | Leaked credentials become immortalized in public git history commits. |
| **Commit Messages** | Arbitrary messages like `fix bug`, `temp`, `wip` | **Conventional Commits** validated via `commit-msg` hook | Impossible automated changelog generation and broken semantic release pipelines. |
| **Local Setup** | Multi-page manual markdown setup guide for DB & Redis | **`docker compose up -d`** with automated health checks | "Works on my machine" issues and multi-day developer onboarding friction. |
