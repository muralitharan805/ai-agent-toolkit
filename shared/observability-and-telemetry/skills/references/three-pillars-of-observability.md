# The Three Pillars of Observability & Distributed Telemetry

## Overview

Modern cloud-native systems require unified observability across three complementary pillars to prevent production blind spots:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    The 3 Pillars of Distributed Telemetry                   │
└──────────────────────────────────────────────────────────────────────────────┘
  1. LOGS        ──► WHAT happened (discrete events, exceptions, state changes)
  2. METRICS     ──► HOW MUCH / HOW FAST (rates, percentiles, system saturation)
  3. TRACES      ──► WHERE time was spent (distributed end-to-end request journey)
```

Relying on any single pillar in isolation produces operational blind spots. High error rates detected by metrics require traces to pinpoint the failing microservice, and structured logs to inspect the localized exception payload.

---

## Pillar 1: Structured JSON Logging

### 1. Mandatory Schema & Baseline Fields

All production logs MUST be formatted as single-line serialized JSON strings. Multiline or unstructured human-readable logs break ingestion pipelines (e.g., Vector, Fluentbit, Loki, Elasticsearch).

```json
{
  "timestamp": "2026-09-10T08:30:00.000Z",
  "level": "INFO",
  "service": "order-service",
  "version": "1.4.2",
  "environment": "production",
  "correlationId": "c8d3e2a1-4567-489a-bcde-0123456789ab",
  "event": "order.created",
  "userId": "usr_99812",
  "orderId": "ord_55412",
  "durationMs": 34,
  "message": "Order successfully created and queued for fulfillment"
}
```

### 2. Log Levels & Usage Invariants

| Level | Purpose | Invariant |
| :--- | :--- | :--- |
| `TRACE` | Extremely fine-grained execution flow, loop iterations, raw byte counters. | Local development only. Must never emit in production. |
| `DEBUG` | Internal state transitions, external HTTP payload diagnostics. | Staging / diagnostic dev environments. |
| `INFO` | Significant business events (`user.registered`, `payment.received`). | Production baseline. Low noise, high signal. |
| `WARN` | Recoverable or unexpected occurrences (retries, rate limit throttles, degraded fallback). | Production monitored. |
| `ERROR` | Operation failure affecting a user request or background task. | Emits alert. Includes stack trace and error codes. |
| `FATAL` | Process-level crash, unhandled panic, database connection failure at startup. | Process immediately terminates after flush. |

### 3. Recursive PII & Secret Redaction

Log serialization must recursively sanitize object trees before JSON stringification:

```typescript
export const REDACTED_KEYS = new Set([
  'password',
  'token',
  'refreshtoken',
  'accesstoken',
  'authorization',
  'creditcard',
  'cardnumber',
  'cvv',
  'ssn',
  'secret',
  'apikey',
  'privatekey',
]);

export function sanitizeLogPayload(payload: unknown, depth = 0): unknown {
  if (depth > 5 || payload === null || typeof payload !== 'object') {
    return payload;
  }

  if (Array.isArray(payload)) {
    return payload.map((item) => sanitizeLogPayload(item, depth + 1));
  }

  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload as Record<string, unknown>)) {
    const normalizedKey = key.toLowerCase().replace(/[-_]/g, '');
    if (REDACTED_KEYS.has(normalizedKey)) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeLogPayload(value, depth + 1);
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
}
```

---

## Pillar 2: Prometheus RED Metrics

### 1. The RED Method (Rate, Errors, Duration)

Every HTTP and RPC service MUST instrument the core RED metrics using standard Prometheus types:

```typescript
import client from 'prom-client';

// 1. Rate (R): Monotonically increasing request counter
export const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of inbound HTTP requests',
  labelNames: ['method', 'route', 'status'] as const,
});

// 2. Errors (E): Error counter partitioned by error category
export const errorsTotal = new client.Counter({
  name: 'errors_total',
  help: 'Total count of operational and internal application errors',
  labelNames: ['type', 'code'] as const,
});

// 3. Duration (D): Latency distribution histogram (seconds)
export const httpRequestDurationSeconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request latency distribution in seconds',
  labelNames: ['method', 'route'] as const,
  // Standard latency buckets (10ms to 10s) to calculate p50, p90, p99
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});
```

### 2. Guarding Against Metric Cardinality Explosion

> [!CAUTION]
> Placing unbounded strings (UUIDs, user IDs, query parameters, raw timestamps) into Prometheus metric labels multiplies the total time-series count exponentially. This exhausts Prometheus memory, slows scrapers, and causes outages.

- **DO NOT USE**: `route: "/api/v1/orders/550e8400-e29b-41d4-a716-446655440000"` (Unbounded cardinality)
- **DO USE**: `route: "/api/v1/orders/:id"` (Parameterized template: bounded cardinality)

### 3. Extended Metric Set & Scraping

In addition to RED metrics, export:
- System saturation: `process_cpu_seconds_total`, `process_resident_memory_bytes`.
- Database connection pool: `db_pool_active_connections`, `db_pool_waiting_requests`.
- Cache efficiency: `cache_hits_total`, `cache_misses_total`.
- Expose `/metrics` on an internal port or protect via IP whitelist / reverse-proxy basic authentication.

---

## Pillar 3: Distributed Tracing & OpenTelemetry

### 1. Trace Context & W3C Propagation

In a distributed microservice topology, a single user transaction spans multiple services. Distributed tracing tracks this path via context propagation headers:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │  └──────────────┬───────────────┘ └───────┬────────┘ └─┬─┘
           Version          Trace ID                  Parent Span ID Flags
```

- **Trace ID** (`32 hex`): Unique identifier for the entire transaction lifecycle.
- **Span ID** (`16 hex`): Identifier for a single unit of contiguous work (e.g., HTTP handler, DB query, external RPC).
- **Trace Flags** (`2 hex`): E.g., `01` indicating recorded/sampled trace.

### 2. OpenTelemetry Node.js / TypeScript SDK Setup

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';

const sdk = new NodeSDK({
  serviceName: process.env.SERVICE_NAME || 'api-gateway',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4317',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown().finally(() => process.exit(0));
});
```

### 3. Custom Span Instrumentation

Wrap high-latency critical sections (DB queries, Redis access, external API calls) in custom spans:

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('order-service');

export async function processOrderPayment(orderId: string, amountInCents: number): Promise<PaymentReceipt> {
  return tracer.startActiveSpan('payment_gateway.charge', async (span) => {
    try {
      span.setAttribute('order.id', orderId);
      span.setAttribute('payment.amount_cents', amountInCents);

      const receipt = await paymentClient.charge({ orderId, amountInCents });
      span.setStatus({ code: SpanStatusCode.OK });
      return receipt;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: (error as Error).message,
      });
      throw error;
    } finally {
      span.end();
    }
  });
}
```
