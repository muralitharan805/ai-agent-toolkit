---
name: async-jobs-and-event-processing
description: "Implements and audits asynchronous background job processing, queue-worker decoupling, exponential backoff with jitter, Dead Letter Queue (DLQ) routing, and consumer idempotency. Triggered by 'async-jobs:', 'message-queue:', 'worker:', 'dlq:', or '/async-jobs-and-event-processing'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Asynchronous Jobs & Event Processing Skill

## Overview

This skill establishes the production engineering protocol for **Asynchronous Job Queues**, **Decoupled Worker Processes**, **Exponential Backoff Retries with Jitter**, and **Dead Letter Queue (DLQ) Governance** across backend architectures. It guarantees that heavy or non-deterministic operations (emails, PDFs, notifications, third-party webhooks) never block synchronous HTTP request cycles, prevents thundering herd retries, and enforces consumer idempotency to eliminate duplicate processing.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Async Processing Pipeline                    │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: HTTP Decoupling]        ──► Enqueue job & return 202 Accepted
                │
  [Phase 2: Worker Isolation]       ──► Run consumers in dedicated worker process
                │
  [Phase 3: Backoff with Jitter]    ──► Retry transient errors exponentially + jitter
                │
  [Phase 4: Dead Letter Queue]      ──► Route exhausted failures to DLQ & alert
                │
  [Phase 5: Consumer Idempotency]   ──► Guard against duplicate processing
```

---

## 5-Phase Execution Guide

### Phase 1: HTTP Controller Decoupling (Return 202 Accepted)
1. **Identify Heavy Operations**:
   - Extract email sending, PDF generation, push notifications, and partner API sync from HTTP controllers.
2. **Enqueue and Respond Fast**:
   - Enqueue a versioned message envelope to the message broker (RabbitMQ, SQS, Redis Streams/BullMQ).
   - Return HTTP `202 Accepted` immediately with a tracking job ID:
     ```typescript
     res.status(202).json({ status: 'accepted', jobId, pollUrl: `/api/v1/jobs/${jobId}` });
     ```

### Phase 2: Dedicated Worker Process Isolation
1. **Separate Process Boundary**:
   - Execute job consumers in dedicated container pods or distinct OS processes. Never run heavy worker loops inside the API web server process.
2. **Independent Autoscaling**:
   - Configure worker autoscaling based on queue depth metrics (`queue_depth` or `ApproximateNumberOfMessagesVisible`), independent of HTTP request rate.

### Phase 3: Exponential Backoff Retries with Full Jitter
1. **Prevent Thundering Herd Retries**:
   - Configure transient failure retry delays using exponential backoff with randomized jitter:
     $$\text{delay} = \min(\text{baseDelay} \times 2^{\text{attempt}}, \text{maxDelay}) + \text{jitter}$$
   - Random jitter ($\pm 10\%\text{--}20\%$) prevents synchronized concurrent retries against recovering downstream APIs.

### Phase 4: Dead Letter Queue (DLQ) & Backlog Telemetry
1. **Eliminate Poison Pills**:
   - Configure a Dead Letter Queue (DLQ) for every primary queue.
   - When max attempts (e.g. 3–5) are exhausted, transfer the failed message to the DLQ along with error details and stack trace.
2. **Alert on DLQ Growth**:
   - Configure alerts to trigger immediately if `dlq_depth > 0`.

### Phase 5: Consumer Idempotency Guard & Conformance Audit
1. **Handle At-Least-Once Delivery**:
   - Message brokers guarantee at-least-once delivery. Verify `idempotencyKey` in an atomic deduplication store (`processed_jobs` table) before executing non-reversible side effects.
2. **Run Conformance Audit**:
   ```bash
   python3 shared/async-jobs-and-event-processing/skills/scripts/audit_async_jobs.py ./src --strict
   ```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [Async Job Queues & Worker Patterns](references/async-job-queues-and-worker-patterns.md) for full jitter formulas, message broker comparison (SQS vs RabbitMQ vs BullMQ), and deduplication schema designs.
- **Production Template**: Review [async-queue-orchestrator.template.ts](assets/async-queue-orchestrator.template.ts) for production TypeScript base worker consumer, backoff calculator, and DLQ dispatcher.
- **CLI Auditor**: Execute [audit_async_jobs.py](scripts/audit_async_jobs.py) to detect synchronous blocking calls in HTTP routes.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Sending emails or PDFs synchronously in HTTP routes | Enqueue job to background queue; return HTTP 202 Accepted | Slow external SMTP or rendering engine causes client HTTP timeout and blocks server event loop. |
| Running worker consumers inside web server process | Separate worker container/process scaled on queue depth | Heavy jobs monopolize CPU/RAM, degrading web API latency and causing server crashes. |
| Consumer lacking idempotency checks | Atomic deduplication check via `idempotencyKey` or DB table | At-least-once delivery causes duplicate charges, double emails, or corrupted database records. |
| Immediate or deterministic retry without jitter | Exponential backoff with randomized jitter | Synchronized worker retries overwhelm recovering downstream services (thundering herd). |
| Silently discarding failed jobs without DLQ | Route exhausted failed jobs to DLQ and alert on-call team | Critical business state is lost without notification, causing silent customer-facing failures. |
| Unversioned job payload schemas | Explicit schema versioning (`version: 1`) on all envelopes | Rolling deployments crash older worker pods when new payload shapes arrive. |
