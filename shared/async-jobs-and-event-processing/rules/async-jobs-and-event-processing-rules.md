---
trigger: model_decision
description: "Enforces asynchronous background job processing standards, decoupled worker processes, exponential backoff with jitter, Dead Letter Queues (DLQ), and consumer idempotency."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Asynchronous Jobs & Event Processing Standards

## Description
Enforces resilient, decoupled background job processing and asynchronous event architectures across all backend services. Mandates that heavy, high-latency, or non-deterministic workloads (email dispatch, PDF rendering, external API synchronization, batch processing) are strictly decoupled from the synchronous HTTP request-response lifecycle. Enforces dedicated worker process isolation, exponential backoff retries with randomized jitter, Dead Letter Queue (DLQ) routing for unrecoverable failures, strict consumer idempotency to prevent duplicate side effects, and job schema versioning across rolling deployments.

## Constraints

### 1. Mandatory HTTP Decoupling (Return 202 Accepted)
- The synchronous HTTP request-response lifecycle MUST NOT perform heavy or unpredictable operations:
  - Sending transactional emails, SMS, or mobile push notifications.
  - Generating PDFs, spreadsheets, or image thumbnails.
  - Making synchronous network calls to third-party webhooks or external partner APIs.
  - Running batch database writes or full-text indexing.
- When an HTTP client requests a heavy task, the HTTP route handler MUST:
  1. Validate the inbound request payload.
  2. Enqueue a job to a reliable message broker (RabbitMQ, AWS SQS, Apache Kafka, Redis Streams / BullMQ).
  3. Respond immediately with HTTP `202 Accepted` including a tracking job ID and status poll URL.

### 2. Dedicated Worker Process Isolation
- Job consumer workers MUST execute in dedicated, separate operating system processes or container pods.
- Running heavy worker background queues inside the active HTTP server process is STRICTLY FORBIDDEN:
  - Heavy CPU or I/O workloads monopolize the HTTP event loop, spiking API latency for all concurrent users.
  - Worker crashes or memory leaks will terminate the HTTP server and drop active client TCP connections.
- Worker pods MUST scale independently from HTTP gateway pods based on queue backlog metrics (Queue Depth / Lag).

### 3. Exponential Backoff with Randomized Jitter
- Retries on transient failure MUST implement exponential backoff with randomized jitter:
  $$\text{delay} = \min(\text{baseDelay} \times 2^{\text{attempt}}, \text{maxDelay}) + \text{jitter}$$
- **Jitter Requirement**: The jitter component ($\pm 10\%\text{--}20\%$ of current delay) is MANDATORY. Without jitter, hundreds of failed jobs retry simultaneously in lockstep, generating a synchronized thundering herd that repeatedly crashes recovering downstream services.

### 4. Dead Letter Queue (DLQ) & Alerting Invariant
- Every production queue MUST have a paired Dead Letter Queue (DLQ) or dead-letter topic.
- When a job exceeds its maximum configured retry threshold (e.g. 3 to 5 attempts):
  - It MUST NOT be silently discarded or dropped.
  - It MUST NOT remain in an infinite retry loop that blocks downstream jobs.
  - It MUST be transferred to the DLQ along with error diagnostics, stack traces, and attempt metadata.
- DLQ depth MUST be tracked as a primary Prometheus/CloudWatch metric, with automated PagerDuty/Slack alerts firing when the DLQ depth exceeds 0.

### 5. Mandatory Consumer Idempotency
- Distributed message brokers guarantee **at-least-once delivery**, not exactly-once delivery. Network partitions and worker timeouts inevitably cause duplicate message delivery.
- All consumer handlers MUST be idempotent:
  - Every job MUST carry a unique identifier (`jobId` or business idempotency key).
  - Consumers MUST verify whether the `jobId` has already been processed (e.g. via atomic `processed_jobs` database table check or Redis key with TTL) before executing irreversible side effects.
  - Duplicate message delivery MUST NEVER cause duplicate billing charges, duplicate emails, or corrupted database records.

### 6. Job Payload Schema Versioning
- Job payloads MUST declare an explicit version field (`version: 1`, `version: 2`).
- Consumers MUST be engineered to handle both legacy and current schema versions during rolling zero-downtime container deployments.

## Examples

### 1. HTTP Route Enqueuing Job vs. Blocking Execution

```typescript
// ❌ FORBIDDEN: Generating PDF and sending email inside HTTP request lifecycle
app.post('/api/v1/invoices/:id/send', async (req, res) => {
  const pdfBytes = await generateHeavyInvoicePdf(req.params.id); // 8s blocking!
  await emailService.sendWithAttachment(req.body.email, pdfBytes); // 2s network call!
  res.status(200).json({ success: true }); // Total latency: 10s. Client timeout risk!
});

// ✅ CORRECT: Fast enqueue and immediate 202 Accepted response
app.post('/api/v1/invoices/:id/send', async (req, res) => {
  const jobId = await invoiceQueue.add('send_invoice_email', {
    version: 1,
    invoiceId: req.params.id,
    recipientEmail: req.body.email,
  });

  res.status(202).json({
    status: 'accepted',
    message: 'Invoice dispatch queued for asynchronous processing',
    jobId,
    trackingUrl: `/api/v1/jobs/${jobId}`,
  });
});
```

### 2. Idempotent Consumer with Deduplication Guard

```typescript
// ✅ CORRECT: Idempotent worker processing with atomic deduplication
export async function processPaymentJob(job: Job<PaymentPayload>): Promise<void> {
  const { idempotencyKey, customerId, amountInCents } = job.data;

  // 1. Atomic database deduplication check
  const alreadyProcessed = await db.processedJobs.findUnique({
    where: { idempotencyKey },
  });

  if (alreadyProcessed) {
    logger.info({ message: 'Duplicate job detected; skipping execution', idempotencyKey });
    return; // Safely acknowledge and exit
  }

  // 2. Execute business transaction atomically
  await db.$transaction(async (tx) => {
    await tx.processedJobs.create({ data: { idempotencyKey, processedAt: new Date() } });
    await tx.ledger.create({ data: { customerId, amountInCents } });
    await paymentGateway.charge({ customerId, amountInCents, idempotencyKey });
  });
}
```

### 3. Exponential Backoff with Jitter Calculation

```typescript
// ✅ CORRECT: Calculating exponential backoff with randomized jitter
export function calculateBackoffWithJitter(
  attempt: number,
  baseDelayMs = 1000,
  maxDelayMs = 30000
): number {
  const exponentialDelay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
  const jitterRange = exponentialDelay * 0.2; // 20% jitter window
  const randomizedJitter = (Math.random() - 0.5) * jitterRange;
  return Math.round(exponentialDelay + randomizedJitter);
}
```
