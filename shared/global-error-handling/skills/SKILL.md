---
name: global-error-handling
description: "Implements and audits domain error class hierarchies, operational vs programmer error classification, global catch-all exception filters, and on-call alerting hooks. Triggered by 'error-handling:', 'global-filter:', or '/global-error-handling'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Global Error Handling & Domain Error Standards Skill

## Overview

This skill establishes the production engineering protocol for **domain error class hierarchies**, **operational versus programmer error classification**, **global catch-all exception filters**, and **automated on-call alerting hooks** across language-agnostic backend systems. It eliminates untyped generic exceptions, prevents silent error swallowing, guarantees clean mapping between domain exceptions and HTTP status codes, and ensures 500-level crashes notify on-call engineers without exposing stack traces to public clients.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Domain Hierarchy]       ──► Define BaseAppError & domain subclasses
               │
  [Phase 2: Error Classification]   ──► Classify into Operational vs Programmer
               │
  [Phase 3: Global Exception Filter]──► Mount catch-all filter as final pipeline hook
               │
  [Phase 4: On-Call Alert Hook]     ──► Dispatch incident webhook on 500 crashes
               │
  [Phase 5: Conformance Audit]      ──► Run audit_error_handling.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Domain Error Class Hierarchy Definition
1. **Extend BaseAppError**:
   Create a dedicated error class hierarchy representing business domain failures:
   ```typescript
   export abstract class BaseAppError extends Error {
     public readonly isOperational = true;
     constructor(
       public readonly code: ErrorCode,
       public readonly message: string,
       public readonly httpStatus: number,
       public readonly details?: ReadonlyArray<{ field: string; message: string }>
     ) {
       super(message);
     }
   }
   ```
2. **Implement Typed Subclasses**:
   - `NotFoundError` (404)
   - `ValidationError` (400)
   - `UnauthorizedError` (401)
   - `ForbiddenError` (403)
   - `ConflictError` (409)
   - `UnprocessableEntityError` (422)

### Phase 2: Operational vs. Programmer Error Classification
1. **Operational Errors** (`isOperational: true`):
   - Known, expected failure conditions (e.g. invalid password, entity not found).
   - Log at `WARN` severity with correlation ID.
   - Return formatted 4xx client response without alerting on-call engineers.
2. **Programmer Errors** (`isOperational: false` or unhandled exceptions):
   - Unexpected bugs, syntax errors, null dereferences, or database outages.
   - Log at `ERROR` or `FATAL` severity with full stack trace.
   - Dispatch an on-call alert to PagerDuty or Slack.
   - Return a sanitized 500 error envelope.

### Phase 3: Global Catch-All Exception Filter Implementation
1. **Mount as the Terminal Middleware**:
   - Ensure the error filter is the absolute last middleware in the server pipeline.
   - Format all responses using the standard `{ success: false, error, meta }` contract.
   - Always echo the `X-Correlation-ID` header.

### Phase 4: Automated On-Call Alert Hook Integration
1. **Trigger Incident Dispatcher**:
   - Hook the error handler into your incident management service (PagerDuty Events API, Sentry, or Slack webhook):
   ```typescript
   if (!err.isOperational || err.httpStatus >= 500) {
     await onCallNotifier.sendAlert({
       correlationId,
       errorName: err.name,
       message: err.message,
       stack: err.stack,
       path: req.originalUrl,
     });
   }
   ```

### Phase 5: Conformance Audit & Quality Verification
1. **Run Error Handling Auditor CLI**:
   - Execute the bundled audit tool to detect empty catch blocks and generic untyped errors:
   ```bash
   python3 scripts/audit_error_handling.py src/ --strict
   ```

---

## Working Checklist

- [ ] **Domain Error Hierarchy**: All business exceptions extend `BaseAppError` with status code mapping.
- [ ] **Typed Throws**: Services throw explicit subclasses (`NotFoundError`, `ConflictError`), never raw `new Error()`.
- [ ] **Error Classification**: Operational errors logged as `WARN`; unexpected bugs logged as `ERROR`.
- [ ] **On-Call Alerting**: 500-level programmer errors trigger automated incident dispatch hooks.
- [ ] **Zero Stack Traces to Client**: Production clients receive sanitized error messages; stack traces stay in server logs.
- [ ] **Zero Swallowed Errors**: No empty `catch (e) {}` blocks in the codebase.
- [ ] **Correlation ID Tracked**: Every error log and error response contains the active `correlationId`.

---

## Authoritative References & Bundled Assets

- **Domain Error Hierarchy Guide**: [references/domain-error-hierarchy-and-triage.md](references/domain-error-hierarchy-and-triage.md)
- **Error Handling Auditor CLI Tool**: [scripts/audit_error_handling.py](scripts/audit_error_handling.py)
- **Domain Error Hierarchy Template**: [assets/domain-error-hierarchy.template.ts](assets/domain-error-hierarchy.template.ts)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Error Handling)

| Legacy Antipattern | Modern Error Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Generic Errors Everywhere** (`throw new Error("not found")`) | **Domain Error Hierarchy (`throw new NotFoundError(...)`)** | Enables global filter to automatically infer HTTP status codes without brittle string matching. |
| **Swallowing Exceptions** (`try { ... } catch (e) {}`) | **Explicit Logging or Rethrowing** | Prevents silent data corruption and un-debuggable ghost failures in production. |
| **Alerting on Every Error** (Alerting on 400s or 404s) | **Operational vs. Programmer Triage** | Eliminates on-call alert fatigue by paging engineers only for real 500-level system outages. |
| **Leaking Stack Traces to Clients** (`res.json({ stack: err.stack })`) | **Sanitized Generic 500 Message** | Blocks attackers from learning internal library versions, file system paths, and source code line numbers. |
| **Missing Correlation ID in Error Logs** | **Correlation Context Propagation** | Allows engineers to instantly correlate a user-reported error with the exact server-side stack trace. |
