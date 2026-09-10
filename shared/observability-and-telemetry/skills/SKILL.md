---
name: observability-and-telemetry
description: "Implements and audits the 3 pillars of enterprise observability: structured JSON logging, Prometheus RED metrics at /metrics, and OpenTelemetry distributed tracing with W3C traceparent headers. Triggered by 'observability:', 'telemetry:', 'metrics:', 'tracing:', or '/observability-and-telemetry'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Observability & Distributed Telemetry Skill

## Overview

This skill establishes the production engineering protocol for implementing the **Three Pillars of Observability**—**Structured JSON Logging**, **Prometheus RED Metrics**, and **OpenTelemetry Distributed Tracing**—across language-agnostic backend architectures. It ensures zero production blind spots by combining discrete event records with quantitative time-series metrics and end-to-end distributed execution traces.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Telemetry Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Structured JSON Logging] ──► Single-line JSON logger + PII redaction
                │
  [Phase 2: Correlation Propagation] ──► Inject & carry correlationId / traceId
                │
  [Phase 3: Prometheus RED Metrics]  ──► Instrument Rate, Errors, Duration at /metrics
                │
  [Phase 4: OpenTelemetry Tracing]   ──► Traceparent header & child span tracing
                │
  [Phase 5: Conformance Audit]       ──► Run audit_observability_pipeline.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Structured JSON Logging & PII Redaction
1. **Eliminate Raw Console Calls**:
   - Forbid `console.log()`, `console.error()`, and `print()` in production runtime code.
   - Deploy high-performance structured loggers (Pino for Node.js, structlog for Python, zerolog for Go).
2. **Mandate Baseline Log Schema**:
   - Every log entry emitted to `stdout` must be a single-line JSON string containing:
     - `timestamp`: ISO-8601 UTC string (`new Date().toISOString()`).
     - `level`: Normalized severity (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`).
     - `service`: Microservice identifier.
     - `correlationId`: Active request tracking UUID.
     - `message`: Clear human-readable description.
3. **Recursive Credential Masking**:
   - Run payloads through recursive sanitization before stringification.
   - Mask `password`, `token`, `authorization`, `creditcard`, `cvv`, `ssn`, and `secret` with `"[REDACTED]"`.

### Phase 2: Correlation Context Propagation
1. **Ingest / Generate Trace Identifier**:
   - Read `x-correlation-id` from inbound request headers; generate a fresh UUID v4 if missing.
   - Echo `X-Correlation-ID` on all HTTP responses.
2. **Bind Context Across Asynchronous Operations**:
   - Utilize Node.js `AsyncLocalStorage`, Python `contextvars`, or Go `context.Context` to implicitly pass the correlation identifier across async boundaries without manual parameter threading.

### Phase 3: Prometheus RED Metrics Instrumentation
1. **Instrument Core RED Metrics**:
   - **Rate (R)**: Counter `http_requests_total{method, route, status}` tracking request throughput.
   - **Errors (E)**: Counter `errors_total{type, code}` tracking application failures.
   - **Duration (D)**: Histogram `http_request_duration_seconds{method, route}` with standard exponential buckets (`[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]`) to compute p50, p90, and p99 percentiles.
2. **Cardinality Protection Guard**:
   - Strictly parameterize route labels (`/api/v1/users/:id`).
   - NEVER inject raw URLs, user IDs, or query strings into metric labels.
3. **Expose Metrics Endpoint**:
   - Serve Prometheus metrics at `GET /metrics`. Restrict access to internal networks or protect via reverse proxy basic auth.

### Phase 4: OpenTelemetry Distributed Tracing
1. **W3C Trace Context Propagation**:
   - Parse and propagate W3C standard `traceparent` headers across inter-service HTTP requests and message brokers:
     `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
2. **Instrument Critical Spans**:
   - Wrap outbound database queries, cache operations, and external payment calls in dedicated child spans via `tracer.startActiveSpan()`.
   - Record unhandled exceptions on the active span and set span status to `ERROR`.

### Phase 5: Conformance Audit
1. Run the telemetry audit tool against the codebase:
   ```bash
   python3 shared/observability-and-telemetry/skills/scripts/audit_observability_pipeline.py ./src --strict
   ```
2. Verify zero raw `console.log` violations, presence of RED metrics, and valid cardinality protection.

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [Three Pillars of Observability](references/three-pillars-of-observability.md) for Prometheus percentile formulas, W3C specification details, and log aggregation topologies.
- **Production Template**: Review [prometheus-red-metrics.template.ts](assets/prometheus-red-metrics.template.ts) for production-grade TypeScript logger, RED middleware, and OTel helper implementations.
- **CLI Auditor**: Execute [audit_observability_pipeline.py](scripts/audit_observability_pipeline.py) to automatically detect compliance regressions.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Raw `console.log()` statements scattered in source code | Structured JSON logger (e.g. Pino) writing serialized single-line JSON to `stdout` | Blocks event loop, breaks log aggregation pipelines, leaks secrets. |
| High-cardinality metric labels (`route: req.originalUrl`) | Parameterized route templates (`route: req.route?.path || ':id'`) | Multiplies time-series in Prometheus memory exponentially, leading to OOM crash. |
| Average latency calculations (`sum(duration) / count`) | Prometheus Histograms calculating p50, p90, and p99 percentiles | Averages hide tail latency spikes experienced by 1-5% of real users. |
| Missing W3C `traceparent` propagation across microservices | OpenTelemetry standard W3C header propagation across HTTP & message queues | Breaks distributed trace graphs; makes cross-service latency debugging impossible. |
| Plaintext password/token logging in payload dumps | Recursive PII sanitization utility (`sanitizeLogPayload()`) | Direct violation of PCI-DSS, GDPR, and security compliance standards. |
| Scraping `/metrics` without rate limiting or IP whitelist | Restrict `/metrics` route to internal VPC / Prometheus scraper subnet | Exposes internal architecture details and creates a DoS vector. |
