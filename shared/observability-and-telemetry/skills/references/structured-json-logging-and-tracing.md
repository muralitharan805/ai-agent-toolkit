# Structured JSON Logging & Request Tracing Reference

## 1. Core Principles of Production Observability

Modern distributed backend applications (NestJS, Express, microservices) cannot rely on multi-line human-readable console prints. Production log collectors (Datadog Agent, Grafana Promtail / Loki, AWS CloudWatch Logs, ELK Filebeat) require deterministic, single-line structured JSON records.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                       HTTP Request Tracing Lifecycle                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Client HTTP Request]
          │ (Optional incoming `X-Correlation-ID`)
          ▼
  [CorrelationIdMiddleware] ──► Extracts or generates RFC 4122 UUID
          │                     Attaches to AsyncLocalStorage / Request context
          ▼
  [LoggingInterceptor]      ──► Records `startTime = Date.now()`
          │
  [Controller & Service]    ──► Business logic emits structured logs with correlationId
          │
  [Response Stream Pipe]    ──► Sets outgoing `X-Correlation-ID` response header
          │                     Calculates latency: `durationMs = Date.now() - startTime`
          ▼
  [Structured Log Output]   ──► Emits single-line JSON log record to stdout
```

---

## 2. Standard Structured Log Payload Schema

Every log event emitted by services or interceptors should conform to the OpenTelemetry / Elastic Common Schema (ECS) standard:

```json
{
  "timestamp": "2026-09-06T17:05:00.123Z",
  "level": "INFO",
  "correlationId": "c8b8f88c-d6b3-4f93-b4d2-8924b1c1e7a5",
  "service": "billing-service",
  "environment": "production",
  "message": "Processed EMI repayment installment successfully",
  "context": "PaymentProcessingService",
  "http": {
    "method": "POST",
    "route": "/api/v1/payments/repay",
    "statusCode": 200,
    "durationMs": 34
  },
  "metadata": {
    "loanId": "LOAN-98421",
    "amountPaid": 24500
  }
}
```

### Log Levels & Hierarchy
- **FATAL (60)**: Catastrophic failures causing process crash or unrecoverable system state.
- **ERROR (50)**: Unhandled exceptions or business failures requiring immediate on-call attention.
- **WARN (40)**: Degraded operations, retried network timeouts, or deprecated API consumption.
- **INFO (30)**: Key business milestones (user logged in, payment authorized, job scheduled).
- **DEBUG (20)**: Granular diagnostics for staging environments (database query timings, cache hits/misses).
- **TRACE (10)**: Low-level network I/O or full AST traversals (never enabled in production).

---

## 3. Asynchronous Context Tracing (`AsyncLocalStorage`)

Rather than manually threading `correlationId` through every service method and repository parameter, modern Node.js and NestJS applications utilize `AsyncLocalStorage` to maintain request-scoped context across asynchronous boundaries:

```typescript
import { AsyncLocalStorage } from 'node:async_hooks';

export interface RequestContextStore {
  readonly correlationId: string;
  readonly userId?: string;
  readonly tenantId?: string;
}

export const requestContextStorage = new AsyncLocalStorage<RequestContextStore>();

/**
 * Retrieves the active correlation ID for the current execution context.
 */
export function getActiveCorrelationId(): string {
  const store = requestContextStorage.getStore();
  return store ? store.correlationId : 'system-background-context';
}
```

---

## 4. HTTP Execution Latency Logging Invariants

### Response Time Calculation
- Latency MUST be recorded in whole milliseconds (`durationMs`).
- Latency logs MUST capture HTTP method, route template, HTTP status code, and correlation ID:
  `[c8b8f88c-d6b3] POST /api/v1/loans 201 Created - 42ms`

### Outgoing Header Guarantee
- All HTTP responses (2xx, 4xx, 5xx, and unhandled exceptions) MUST propagate the `X-Correlation-ID` header so that clients and external integrators can cross-reference errors with backend log streams.
