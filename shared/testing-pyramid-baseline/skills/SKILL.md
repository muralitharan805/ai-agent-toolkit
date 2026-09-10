---
name: testing-pyramid-baseline
description: "Enforces testing pyramid ratio (60% unit, 30% integration, 10% E2E/smoke), Testcontainers isolation with transaction rollback, deterministic seeding, CI coverage thresholds (80% line, 75% branch), and k6 performance SLA baselines. Triggered by 'testing-pyramid:', 'testcontainers:', 'smoke-test:', 'k6-test:', or '/testing-pyramid-baseline'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Testing Pyramid Baseline Skill

## Overview

This skill establishes the production engineering standards for the **Testing Pyramid (60% Unit, 30% Integration, 10% E2E/Smoke)**, **Sub-millisecond Unit Test Isolation**, **Testcontainers Production-Parity Integration Testing with Transaction Rollback**, **Post-Deployment Smoke Verification**, and **k6 Performance SLA Baselines**. It eliminates flaky tests, prevents in-memory mock drift, and guarantees high CI confidence with sub-second feedback loops.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                       5-Phase Testing Pipeline & Quality Gate                  │
│                                                                                │
│   [Phase 1: Pyramid Topology & Coverage] ──► Configure 80% line / 75% branch  │
│                     │                                                          │
│   [Phase 2: Unit Test Mock Isolation]    ──► Mock I/O, <1ms execution, seeds   │
│                     │                                                          │
│   [Phase 3: Testcontainers Harness]      ──► Real Postgres/Redis + Rollback    │
│                     │                                                          │
│   [Phase 4: Post-Deploy Smoke Gate]      ──► Verify /health/ready & Auth 401   │
│                     │                                                          │
│   [Phase 5: k6 Performance SLA Baseline] ──► Validate p95 <200ms & error <0.1%│
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Phase Execution Guide

### Phase 1: Pyramid Topology & Coverage Configuration
1. **Enforce Coverage Thresholds**:
   - In `jest.config.ts` or `vitest.config.ts`, mandate coverage thresholds:
     ```typescript
     thresholds: {
       lines: 80,
       branches: 75,
       functions: 80,
       statements: 80,
     }
     ```
2. **Maintain 60/30/10 Ratio**:
   - Target 60% unit tests, 30% integration tests, and 10% smoke/E2E tests.
   - Reject inverted "ice cream cone" test suites that rely heavily on slow, brittle E2E tests.

### Phase 2: Unit Test Mock Isolation & Determinism
1. **Isolate All External I/O**:
   - Mock all databases, external HTTP clients, caches, and queues.
   - Target execution time of < 1ms per test.
2. **Deterministic Inputs & Timers**:
   - Use fixed seeds for data generators (no unseeded `Math.random()`).
   - Mock system timers via `jest.useFakeTimers()` or `vi.useFakeTimers()` instead of `setTimeout`.

### Phase 3: Testcontainers Integration Testing & Transaction Rollback
1. **Ephemeral Real Infrastructure**:
   - Use Testcontainers for real PostgreSQL and Redis containers; NEVER mock database engines with in-memory SQLite.
2. **Run Migrations Pre-Suite**:
   - Execute database schema migrations against the container before starting tests.
3. **Rollback Every Test**:
   - Wrap each integration test in an explicit transaction (`BEGIN ... ROLLBACK`) using `withRollbackTransaction()` from [assets/testcontainers-integration-bootstrap.template.ts](assets/testcontainers-integration-bootstrap.template.ts).
   - Never use slow `TRUNCATE TABLE` operations between individual tests.

### Phase 4: Post-Deployment Smoke Testing Gate
1. **Automate Smoke Tests in CI/CD**:
   - Execute immediately post-deployment before routing live customer traffic.
2. **Mandatory Verifications**:
   - `GET /health/ready` returns HTTP 200 with all dependencies healthy.
   - Critical user journey (login $\rightarrow$ fetch authenticated resource $\rightarrow$ logout).
   - Security error contracts return HTTP 401 with standard error envelope.

### Phase 5: k6 Performance SLA Verification
1. **Load Test Core Endpoints**:
   - Execute k6 load tests across normal, stress, spike, and soak profiles.
2. **Enforce Concrete SLA Thresholds**:
   - **p50 Latency**: < 50ms
   - **p95 Latency**: < 200ms
   - **p99 Latency**: < 500ms
   - **Error Rate**: < 0.1%

---

## Authoritative References & Assets

- **Deep Architectural Reference**: Read [references/testing-pyramid-and-testcontainers.md](references/testing-pyramid-and-testcontainers.md) for Testcontainers lifecycle, transaction rollback mechanics, smoke test scripts, and k6 SLA definitions.
- **Production Asset**: Inspect [assets/testcontainers-integration-bootstrap.template.ts](assets/testcontainers-integration-bootstrap.template.ts) for container management and rollback wrappers.
- **CLI Auditor Tool**: Run [scripts/audit_testing_pyramid.py](scripts/audit_testing_pyramid.py) to audit coverage gates, test distribution, and non-deterministic patterns.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Architectural Risk |
| :--- | :--- | :--- | :--- |
| **Database Mocking** | Mocking PostgreSQL with SQLite in-memory | Real PostgreSQL container via **Testcontainers** | Dialect drift, missing JSONB/UUID operators, unverified constraints. |
| **Test State Isolation** | Running `TRUNCATE TABLE` after every test | Wrapping each test in **transaction with `ROLLBACK`** | Severe CI slowdowns (10x–50x slower test runs) and table lock contention. |
| **Test Execution Order** | Tests depending on insertion order or prior state | Self-contained tests supporting **randomized order** | Silent test failures in parallel runners and impossible test debugging. |
| **System Time Flakiness** | Using real `setTimeout(500)` in tests | **Fake system timers** advancing clock deterministically | Flaky builds, false CI red flags, and wasted developer time. |
| **Deployment Gate** | Manual "QA sanity click around" post-rollout | **Automated smoke test suite** in CI/CD pipeline | Human error, uncaught runtime configuration crashes in production. |
| **Performance Testing** | Deploying without load testing baselines | **k6 performance suites** enforcing SLA latency gates | Catastrophic outages and latency degradation during initial traffic surges. |
