# Asynchronous Job Queues, Workers & Event-Driven Patterns

## Overview

Modern scalable backend systems decouple synchronous user interactions from long-running, compute-intensive, or unreliable operations. Performing heavy operations inside the HTTP request-response cycle leads to thread starvation, request timeouts, and poor user experience.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Asynchronous Queue & Worker Architecture                  │
└──────────────────────────────────────────────────────────────────────────────┘
  HTTP Client
       │ (1) POST /invoices/export
       ▼
  [API Gateway / Web Pod]  ──► Validate & Enqueue Job
       │ (2) Returns 202 Accepted { jobId: "job_9981" }
       │
       ▼ (Job Message)
  [Reliable Message Broker] (RabbitMQ / SQS / Redis Streams / Kafka)
       │
       │ (3) Pull / Push
       ▼
  [Dedicated Worker Pod]   ──► (4) Idempotency Check (processed_jobs)
       │                       ├── Process heavy workload (PDF, Email)
       │                       ├── Succeeded? Ack message & notify user
       │                       └── Transient Failure? Retry with Backoff + Jitter
       ▼ (All retries exhausted)
  [Dead Letter Queue (DLQ)] ──► Emits Alert to On-Call Engineer (PagerDuty)
```

---

## 1. The Synchronous HTTP Trap

| Workload | Synchronous Risk | Asynchronous Solution |
| :--- | :--- | :--- |
| **Email / SMS Dispatch** | SMTP handshake can take 3–8s; provider blip hangs HTTP request. | Enqueue message, return 202 Accepted. Worker retries on provider failure. |
| **PDF / Report Rendering** | CPU-bound rendering blocks Node.js event loop / saturates CPU cores. | Dedicated worker executes rendering in isolated worker container. |
| **Third-Party Webhooks** | Partner API latency directly degrades your application SLA. | Outbound queue with exponential backoff and rate-limiting. |
| **Batch DB Import / Export** | Long-running transactions hold database table and row locks. | Chunked worker processing with progress tracking. |

---

## 2. Message Broker Comparison

| Feature | AWS SQS | RabbitMQ | BullMQ (Redis) | Apache Kafka |
| :--- | :--- | :--- | :--- | :--- |
| **Model** | Managed Cloud Queue | AMQP Broker | Redis In-Memory Queue | Distributed Event Log |
| **Best For** | Serverless / AWS native | Complex routing, RPC | Fast Node.js background jobs | High-throughput event streaming |
| **DLQ Support** | Native Redrive Policy | Dead-Letter Exchange | Built-in failed job set | Dead-letter topic pattern |
| **Ordering** | FIFO queues available | Per-channel FIFO | Delayed & FIFO jobs | Partition-level ordering |

---

## 3. Exponential Backoff with Jitter Mathematics

When a downstream dependency (e.g. email API) fails, retrying immediately exacerbates the outage. Retrying with deterministic delays causes synchronized spikes.

### Full Jitter Formula

$$\text{exponentialDelay} = \min(\text{baseDelay} \times 2^{\text{attempt}}, \text{maxDelay})$$

$$\text{actualDelay} = \text{random}(0, \text{exponentialDelay})$$

```
Attempt 1: delay = 1000ms  ──► with jitter: 250ms - 1000ms
Attempt 2: delay = 2000ms  ──► with jitter: 500ms - 2000ms
Attempt 3: delay = 4000ms  ──► with jitter: 1000ms - 4000ms
Attempt 4: delay = 8000ms  ──► with jitter: 2000ms - 8000ms
Attempt 5: Exhausted      ──► Move to Dead Letter Queue (DLQ)
```

Adding randomness breaks the synchronization among concurrent workers, smoothing out traffic load against the recovering service.

---

## 4. Dead Letter Queue (DLQ) Governance

1. **Never Silently Drop Jobs**: If a job cannot succeed after maximum attempts, discarding it loses critical business state (e.g. unbilled orders).
2. **Never Infinite Retry**: A "poison pill" message with invalid data will loop forever, consuming 100% of worker CPU and stalling valid jobs behind it.
3. **DLQ Redrive**: Once the bug is fixed or downstream provider recovers, operational tooling must allow redriving DLQ messages back into the active queue.
4. **Monitoring Alert**: An alert must fire immediately if DLQ size $> 0$:
   `sum(queue_depth{queue="orders-dlq"}) > 0`

---

## 5. Idempotent Consumer Patterns

Message brokers guarantee **at-least-once** delivery. Network acknowledgments can drop even if a worker successfully completed its task.

### The Deduplication Table Pattern

```sql
CREATE TABLE IF NOT EXISTS processed_jobs (
  idempotency_key VARCHAR(128) PRIMARY KEY,
  job_type VARCHAR(64) NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```typescript
export async function executeWithIdempotency(
  key: string,
  handler: () => Promise<void>
): Promise<void> {
  const existing = await db.processedJobs.findUnique({ where: { idempotency_key: key } });
  if (existing) {
    logger.info({ message: 'Skipping duplicate message', key });
    return;
  }

  await db.$transaction(async (tx) => {
    await tx.processedJobs.create({ data: { idempotency_key: key, job_type: 'ORDER_FULFILLMENT' } });
    await handler();
  });
}
```
