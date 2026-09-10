# Circuit Breakers, Timeouts & Resilience Patterns

## Overview

Distributed systems are inherently subject to partial failures. Network partitions, downstream API degradation, and database deadlocks will occur. Resilience engineering ensures that when a dependency degrades or fails, the host application degrades gracefully rather than suffering a cascading failure.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    The 4 Core Pillars of Service Resilience                  │
└──────────────────────────────────────────────────────────────────────────────┘
  1. TIMEOUTS        ──► Bound every network call (DB, Redis, HTTP, MQ)
  2. JITTERED RETRY  ──► Exponential backoff with jitter for transient errors ONLY
  3. CIRCUIT BREAKER ──► Fail fast when downstream fails; prevent thread lockup
  4. IDEMPOTENCY KEY ──► Prevent duplicate transactions on client retry
```

---

## 1. Timeout Budgeting Across Distributed Hops

In a microservice call chain, timeouts must decrement sequentially at each downstream hop to prevent orphaned processing:

```
[Ingress Gateway]   Timeout: 10,000ms
       │
       ▼
[Order Service]     Timeout: 6,000ms
       │
       ▼
[Payment Partner]   Timeout: 3,000ms
```

If the Payment Partner timeout is set higher than the Gateway timeout, the client will time out and disconnect while the Order Service and Payment Partner continue executing, wasting compute and risking inconsistent state.

### Mandatory Production Timeouts

| Dependency Type | Recommended Timeout | Failure Consequence Without Timeout |
| :--- | :--- | :--- |
| **Database Queries** | `5000ms` (statement_timeout) | Connection pool saturated by slow queries; crashes all pods. |
| **Redis Cache** | `1000ms` | Slow cache lookup blocks request thread; defeats caching purpose. |
| **External HTTP APIs** | Connect: `2000ms`, Read: `5000ms` | Socket pool exhaustion; inability to make new outbound connections. |
| **Message Broker** | `10000ms` (Ack timeout) | Unacknowledged messages pile up; consumer thread deadlocks. |

---

## 2. Circuit Breaker State Machine

The Circuit Breaker pattern prevents an application from repeatedly attempting an operation that is guaranteed to fail.

```
       ┌─────────────────────────┐
       │         CLOSED          │ ◄─────────────────────────┐
       │ (Normal Operation)      │                           │
       └────────────┬────────────┘                           │
                    │                                        │
           Failure rate > Threshold                          │ Canary
           (e.g., 5 failures in 10s)                         │ probe succeeds
                    │                                        │
                    ▼                                        │
       ┌─────────────────────────┐                  ┌────────┴────────┐
       │          OPEN           │ ──Cooldown (30s)►│    HALF-OPEN    │
       │ (Fail Fast Immediately) │                  │ (1 Canary Test) │
       └─────────────────────────┘                  └────────┬────────┘
                    ▲                                        │
                    │         Canary probe fails             │
                    └────────────────────────────────────────┘
```

- **CLOSED**: Requests flow normally. Failures increment an error counter.
- **OPEN**: All calls fail fast immediately with a local fallback or `503 Service Unavailable` error without executing any network calls.
- **HALF-OPEN**: After a cooldown timer, one probe request tests the downstream system. If it succeeds, the circuit closes. If it fails, the circuit returns to the OPEN state for another cooldown period.

---

## 3. Transient vs. Terminal Error Classification

Never retry terminal errors. Doing so produces identical failures, amplifies load, and violates business logic:

| Error Category | HTTP Status / Codes | Action |
| :--- | :--- | :--- |
| **Transient Errors** | `429`, `502`, `503`, `504`, `ETIMEDOUT`, `ECONNRESET` | **RETRY** with exponential backoff + jitter. |
| **Terminal Client Errors** | `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable` | **DO NOT RETRY**. Fail immediately. |
| **Terminal Business Errors**| `INSUFFICIENT_FUNDS`, `DUPLICATE_ORDER`, `INVALID_SCHEMA` | **DO NOT RETRY**. Record domain error. |

---

## 4. HTTP Idempotency-Key Protocol

When clients experience network timeouts on mutating endpoints (`POST /payments`, `POST /orders`), they inevitably retry. Without idempotency protection, this results in double charging or duplicate orders.

### The Idempotency Lifecycle

1. **Client Submits Request**: Includes `Idempotency-Key: <UUIDv4>` header.
2. **Server Checks Store (Redis)**:
   - **Case A (Key Completed)**: Returns cached status code and response payload immediately. Zero business logic re-execution.
   - **Case B (Key In-Progress)**: Returns HTTP `409 Conflict` (`"Request currently processing"`).
   - **Case C (Key Missing)**:
     - Sets key with status `IN_PROGRESS` and a short acquisition lock (e.g. 60s).
     - Executes business transaction.
     - Updates key with status `COMPLETED`, status code, and response body with a 24-hour TTL (`EX 86400`).
