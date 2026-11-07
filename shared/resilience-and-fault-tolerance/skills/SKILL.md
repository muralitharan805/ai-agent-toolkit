---
name: resilience-and-fault-tolerance
description: "Implements and audits enterprise resilience patterns across backend systems: strict I/O timeouts, circuit breakers, exponential backoff with jitter for transient errors, and HTTP Idempotency-Key handling. Triggered by 'resilience:', 'circuit-breaker:', 'idempotency-key:', 'fault-tolerance:', or '/resilience-and-fault-tolerance'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Resilience & Fault Tolerance Architecture Skill

## Overview

This skill establishes the production engineering protocol for **Service Resilience**, **Fault Tolerance**, **Cascading Failure Mitigation**, and **Graceful Degradation** across language-agnostic backend architectures. It enforces bounded timeouts on every I/O call, isolates retries to transient errors using randomized jitter, implements Circuit Breaker state machines to protect degrading dependencies, and enforces the HTTP `Idempotency-Key` protocol to eliminate duplicate operations on client retries.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         5-Phase Resilience Architecture                        │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Bounded Timeouts]       ──► Enforce timeouts on DB, Redis, HTTP, MQ
                │
  [Phase 2: Transient Retries]      ──► Retry 5xx/429 with jitter (Never retry 4xx)
                │
  [Phase 3: Circuit Breaker]        ──► Closed -> Open -> Half-Open state machine
                │
  [Phase 4: Idempotency-Key]        ──► Mutating routes with 24h cached response
                │
  [Phase 5: Conformance Audit]      ──► Run audit_resilience_patterns.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Hard I/O Timeout Enforcement
1. **Eliminate Unbounded Network Calls**:
   - Every network client MUST define explicit connect and read timeouts:
     - Database: `statement_timeout = 5000ms`.
     - Redis: `connectTimeout = 1000ms`, `commandTimeout = 1000ms`.
     - Outbound HTTP: `connectTimeout = 2000ms`, `readTimeout = 5000ms`.
     - Message broker: `ackTimeout = 10000ms`.

### Phase 2: Transient-Only Retries with Jittered Backoff
1. **Filter Non-Transient Errors**:
   - NEVER retry client errors (`400`, `401`, `403`, `404`, `422`).
   - Only retry transient network anomalies (`502`, `503`, `504`, `429`, `ETIMEDOUT`, `ECONNRESET`).
2. **Apply Jittered Backoff**:
   - Compute retry delays using exponential backoff combined with randomized jitter:
     $$\text{delay} = \min(\text{baseDelay} \times 2^{\text{attempt}}, \text{maxDelay}) \pm \text{jitter}$$

### Phase 3: Circuit Breaker State Machine Setup
1. **Wrap Downstream Services**:
   - Wrap all external network calls in a Circuit Breaker:
     - **CLOSED**: Requests proceed normally.
     - **OPEN**: When consecutive failures exceed the threshold (e.g. 5 failures), trip to OPEN. Fail fast immediately with a local fallback or 503 without hitting downstream.
     - **HALF-OPEN**: After a 30s cooldown, allow one test probe. If successful, reset to CLOSED.

### Phase 4: HTTP Idempotency-Key Middleware
1. **Protect Mutating Endpoints**:
   - Apply idempotency middleware to `POST /payments`, `POST /orders`, and balance transfers:
     - Read `Idempotency-Key: <UUID>` header.
     - If key is `COMPLETED`, return the cached response payload immediately.
     - If key is `IN_PROGRESS`, return HTTP `409 Conflict` to prevent concurrent race conditions.
     - If key is new, acquire lock, execute handler, and cache the response with a 24-hour TTL (`EX 86400`).

### Phase 5: Conformance Audit
1. Run the resilience auditor across the codebase:
   ```bash
   python3 shared/resilience-and-fault-tolerance/skills/scripts/audit_resilience_patterns.py ./src --strict
   ```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [Circuit Breakers, Timeouts & Resilience Patterns](references/circuit-breakers-and-resilience-patterns.md) for distributed timeout budgeting, error taxonomy, and state machine transitions.
- **Production Template**: Review [resilience-orchestrator.template.ts](assets/resilience-orchestrator.template.ts) for production TypeScript Circuit Breaker class, backoff retry helper, and idempotency middleware.
- **CLI Auditor**: Execute [audit_resilience_patterns.py](scripts/audit_resilience_patterns.py) to detect unbounded HTTP calls and missing resilience configurations.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Unbounded HTTP/DB calls without timeout | Explicit bounded connect and read timeouts on every call | A slow downstream dependency causes connection thread starvation, taking down the entire app. |
| Retrying HTTP 400 or 404 client errors | Only retry transient 5xx, 429, and socket timeouts | Client bugs produce identical errors; wastes server CPU and network bandwidth. |
| Deterministic retry without randomized jitter | Full jitter ($\pm 10\text{--}20\%$) added to exponential delay | Hundreds of failed requests retry at the exact same second, repeatedly crashing recovering services. |
| Hammering failing downstream services | Circuit Breaker failing fast in OPEN state | Delays cascade upstream; exhausts client connection pools and prolongs downstream outage. |
| Mutating financial endpoints without Idempotency-Key | Mandatory `Idempotency-Key` header with 24h cached response | Client network drop on response triggers retry, causing double charging or duplicate orders. |
