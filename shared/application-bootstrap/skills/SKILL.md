---
name: application-bootstrap
description: "Orchestrates deterministic 13-step backend application bootstrap, universal startup sequencing, process-level crash handling, and pre-flight infrastructure readiness gates. Triggered by 'bootstrap:', 'server-lifecycle:', or '/application-bootstrap'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Application Bootstrap & Server Lifecycle Skill

## Overview

This skill establishes the production engineering protocol for **deterministic backend application startup** and **process lifecycle orchestration** across language-agnostic services. It eliminates startup race conditions, prevents premature traffic acceptance before infrastructure connections are healthy, mandates process-level crash interception (`unhandledRejection` and `uncaughtException`), guarantees resilient exponential backoff connection retries, and enforces pre-listen graceful termination hook registration.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Config & Logger]        ──► Validate schema & boot JSON logger singleton
               │
  [Phase 2: Crash Interception]     ──► Register unhandledRejection & uncaughtException
               │
  [Phase 3: Resilient Connect]      ──► Connect DB & cache with exponential retries
               │
  [Phase 4: DI & Middleware]        ──► Wire containers, security headers, & error filter
               │
  [Phase 5: Pre-Listen & Bind]      ──► Register SIGTERM hooks & bind HTTP listener
```

---

## 5-Phase Execution Guide

### Phase 1: Environment & Logger Initialization
1. **Execute Schema Validation Gate**:
   - Validate environment variables before any other action. Crash immediately (`process.exit(1)`) if configuration is invalid.
2. **Bootstrap Structured Logger**:
   - Initialize the singleton JSON logger using validated configuration (`LOG_LEVEL`). All subsequent failures must be captured in structured format.

### Phase 2: Process-Level Crash Handler Registration
1. **Capture Asynchronous & Synchronous Failures**:
   - Register process-level handlers for unhandled promise rejections and uncaught exceptions:
   ```typescript
   process.on('unhandledRejection', (reason: unknown) => {
     logger.fatal({ event: 'unhandled_rejection', error: reason instanceof Error ? reason.stack : reason });
     process.exit(1);
   });

   process.on('uncaughtException', (error: Error) => {
     logger.fatal({ event: 'uncaught_exception', error: error.stack });
     process.exit(1);
   });
   ```

### Phase 3: Resilient Infrastructure Connection with Exponential Retries
1. **Connect with Exponential Backoff**:
   - Connect to database pools (PostgreSQL) and in-memory caches (Redis) with a retry loop (minimum 3 attempts) and jitter:
   $$\text{Delay} = \min(5000, 500 \times 2^{\text{attempt}}) + \text{RandomJitter}$$
2. **Execute Health Ping**:
   - Execute an active verification query (`SELECT 1`) to confirm connectivity before declaring infrastructure ready.

### Phase 4: Dependency Injection & Middleware Pipeline Wiring
1. **Wire Technical Dependencies**:
   - Resolve dependency injection containers, repositories, and use case singletons.
   - Strictly prohibit executing business logic, data seeding, or complex computations in `main()`.
2. **Mount Ordered Middlewares**:
   - Mount security headers, correlation ID injectors, body parsers, and request loggers in deterministic sequence.
   - Mount the global RFC-7807 error filter as the final middleware.

### Phase 5: Pre-Listen Shutdown Hooks & Network Binding
1. **Register Termination Hooks Before Listen**:
   - Attach `SIGTERM` and `SIGINT` signal handlers before calling `server.listen()`.
2. **Bind Network Listener**:
   - Bind to config-driven `PORT` and host (`0.0.0.0`).
   - Emit a single structured JSON log confirming: `Server ready at 0.0.0.0:{PORT}`.

---

## Working Checklist

- [ ] **Deterministic Sequence**: Follows the universal 13-step startup pipeline from config gate to network listen.
- [ ] **Infrastructure-Only Main**: Application entry point contains zero business logic or domain calculations.
- [ ] **Crash Interception**: `unhandledRejection` and `uncaughtException` logged with fatal severity and stack trace.
- [ ] **Connection Retries**: Database connects with 3-stage exponential backoff and jitter before fatal exit.
- [ ] **Pre-Flight Health Gate**: HTTP port opened only after DB pool and cache verify healthy connectivity.
- [ ] **Pre-Listen Hooks**: `SIGTERM` and `SIGINT` listeners registered prior to `server.listen()`.
- [ ] **Config-Driven Port**: Zero hardcoded ports or connection strings in bootstrap code.

---

## Authoritative References & Bundled Assets

- **Universal Startup Architecture Guide**: [references/universal-bootstrap-sequence.md](references/universal-bootstrap-sequence.md)
- **Bootstrap Auditor CLI Tool**: [scripts/audit_bootstrap_sequence.py](scripts/audit_bootstrap_sequence.py)
- **Production Lifecycle Orchestrator Template**: [assets/bootstrap-lifecycle-orchestrator.ts](assets/bootstrap-lifecycle-orchestrator.ts)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Bootstrap)

| Legacy Antipattern | Modern Bootstrap Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Premature Port Listening** (`app.listen(3000)` before DB connects) | **Pre-Flight Connectivity Gate** | Prevents incoming HTTP requests from failing with 500 errors during cold boot. |
| **Floating Promise DB Connect** (`connectDb()` without `await`) | **Sequential Awaited Connection** | Eliminates unhandled promise rejections and race conditions during bootstrap. |
| **Silent Process Crashes** (Missing crash listeners) | **Structured Fatal Logging (`unhandledRejection`)** | Guarantees error stack traces appear in observability dashboards (Datadog/ELK). |
| **Brittle Single-Attempt DB Connect** | **Exponential Backoff with Jitter** | Prevents container crash loops during transient DB restarts and network blips. |
| **Late Shutdown Hook Registration** (Registering hooks after `listen()`) | **Pre-Listen Registration** | Prevents container hanging if orchestrator aborts deployment during startup. |
| **Business Logic in Main** (Seeding users or computing reports in boot) | **Infrastructure-Only Bootstrap** | Keeps application startup sub-second and cleanly decouples domain from server runtime. |
