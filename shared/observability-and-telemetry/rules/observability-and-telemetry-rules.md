---
trigger: model_decision
description: "Enforces the 3 pillars of observability (structured JSON logging, Prometheus RED metrics at /metrics, and OpenTelemetry distributed tracing with W3C traceparent headers)."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Observability & Telemetry Standards (The Three Pillars)

## Description
Enforces enterprise-grade observability and telemetry across all backend services by mandating the three complementary pillars: Structured JSON Logging, Prometheus RED Metrics, and OpenTelemetry Distributed Tracing. Prohibits raw `console.log` statements in production, enforces strict recursive PII/secret masking, requires RED metrics (Rate, Errors, Duration) exposed at a dedicated `/metrics` scrape route, prevents metric label cardinality explosion, and ensures end-to-end request tracing via W3C `traceparent` header context propagation.

## Constraints

### 1. Mandatory Three Pillars Architecture (Zero Blind Spots)
- Every production backend service MUST implement all three pillars of telemetry:
  1. **Logs** (What happened): Discrete timestamped JSON events recording state changes, business transactions, and handled exceptions.
  2. **Metrics** (How much / How fast): Aggregated numeric time-series tracking throughput, latency distributions, and system saturation.
  3. **Traces** (Where time was spent): Distributed execution spans tracking a single request across multiple services, databases, caches, and queues.
- Relying solely on logs without metrics and tracing leaves critical production blind spots and is STRICTLY FORBIDDEN.

### 2. Single-Line Structured JSON Logging (Zero `console.log`)
- Production applications MUST NOT use raw `console.log()`, `console.error()`, or `print()` statements.
- All log events MUST be emitted through a dedicated structured logger (e.g. Pino, Winston, structlog, zerolog) as single-line serialized JSON strings.
- Every emitted log object MUST contain the mandatory baseline fields:
  - `timestamp`: ISO-8601 UTC string.
  - `level`: Log level string (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`).
  - `service`: Microservice name.
  - `correlationId`: Active request tracking UUID.
  - `message`: Clear human-readable description.

### 3. Mandatory Recursive PII & Secret Redaction
- Log payloads MUST pass through an automated sanitization utility before serialization.
- The following sensitive keys and patterns MUST be replaced with `"[REDACTED]"`:
  - Passwords, passcodes, PINs.
  - JWT tokens, refresh tokens, bearer authorization headers.
  - Credit card PANs, CVVs, expiration dates.
  - National ID / SSN numbers, bank account numbers.
  - Private cryptographic keys and API secrets.

### 4. Prometheus RED Metrics Specification
- Every service MUST expose a Prometheus-formatted text endpoint at `/metrics` (scraped every 15s by Prometheus/VictoriaMetrics).
- Every service MUST instrument the core RED metrics:
  - **Rate (R)**: Counter `http_requests_total{method, route, status}` tracking request volume.
  - **Errors (E)**: Counter `errors_total{type, code}` tracking failures.
  - **Duration (D)**: Histogram `http_request_duration_seconds{method, route}` with standard latency buckets (0.01s, 0.05s, 0.1s, 0.25s, 0.5s, 1s, 2.5s, 5s, 10s) to calculate p50, p90, and p99 percentiles.
- System metrics tracking memory RSS, CPU percentage, and active database connection pool count MUST be collected.

### 5. Metric Label Cardinality Explosion Guard
- Metric labels MUST be strictly restricted to low-cardinality values (HTTP method, parameterized route template `/api/v1/users/:id`, HTTP status code).
- Placing high-cardinality values (e.g. user IDs, order UUIDs, email addresses, timestamps, raw query strings) into Prometheus metric labels is a CRITICAL RISK that causes metric server memory exhaustion and is STRICTLY FORBIDDEN.

### 6. OpenTelemetry Distributed Tracing & W3C Propagation
- Distributed requests MUST propagate W3C Trace Context headers (`traceparent: 00-{traceId}-{spanId}-{flags}`) across all inter-service HTTP calls and message queues.
- Asynchronous database queries, Redis calls, and third-party API invocations MUST create dedicated child spans linked to the root trace ID.

## Examples

### 1. Structured JSON Log with Mandatory Fields & Redaction

```typescript
// ❌ FORBIDDEN: Raw console.log leaking plaintext password
console.log('Login attempt for ' + user.email + ' with password ' + req.body.password);

// ✅ CORRECT: Dedicated structured logger with automated redaction & correlation ID
logger.info({
  event: 'auth.login_attempt',
  correlationId: req.headers['x-correlation-id'],
  service: 'identity-service',
  email: sanitizeEmail(user.email),
  payload: sanitizeLogPayload(req.body), // Replaces 'password' with '[REDACTED]'
  message: 'User credential authentication initiated',
});
```

### 2. Prometheus RED Metrics Instrumentation

```typescript
// ✅ CORRECT: Standard RED metric instrumentation in Express / Fastify
import client from 'prom-client';

export const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests processed',
  labelNames: ['method', 'route', 'status'] as const,
});

export const httpRequestDurationSeconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration distribution in seconds',
  labelNames: ['method', 'route'] as const,
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10], // For p50, p95, p99
});

// Middleware recording metrics with LOW cardinality route template
export function metricsMiddleware(req: Request, res: Response, next: NextFunction): void {
  const start = process.hrtime();
  res.on('finish', () => {
    const [seconds, nanoseconds] = process.hrtime(start);
    const durationInSeconds = seconds + nanoseconds / 1e9;
    const route = req.route?.path || req.baseUrl || 'unmatched'; // Low cardinality!

    httpRequestsTotal.inc({ method: req.method, route, status: res.statusCode });
    httpRequestDurationSeconds.observe({ method: req.method, route }, durationInSeconds);
  });
  next();
}
```

### 3. OpenTelemetry Child Span Creation

```typescript
// ✅ CORRECT: Tracing database query with OpenTelemetry span
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('order-service');

export async function findOrderById(orderId: string): Promise<Order | null> {
  return tracer.startActiveSpan('db.query.findOrderById', async (span) => {
    try {
      span.setAttribute('db.system', 'postgresql');
      span.setAttribute('db.operation', 'SELECT');
      const order = await dbPool.query('SELECT * FROM orders WHERE id = $1', [orderId]);
      return order;
    } finally {
      span.end();
    }
  });
}
```
