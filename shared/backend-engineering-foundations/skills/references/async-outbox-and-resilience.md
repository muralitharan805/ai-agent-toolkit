# Asynchronous Processing, The Outbox Pattern & Resilience

## 1. The Dual-Write Hazard & Transactional Outbox

When a service updates a database and publishes an event to a message broker, process crashes between the two steps cause state corruption:
- Case A: DB commits, but queue publish fails $\rightarrow$ Event lost forever.
- Case B: Queue publishes, but DB transaction rolls back $\rightarrow$ Phantom state processed.

### The Solution
Atomically persist state and event in the same local ACID transaction:

```sql
BEGIN TRANSACTION;
  INSERT INTO orders (id, customer_id, total, status)
  VALUES ('018e3f2a-bc91-7890-a123-456789abcdef', 'cust_123', 9950, 'CREATED');

  INSERT INTO transactional_outbox (id, aggregate_type, aggregate_id, event_type, payload, status, created_at)
  VALUES (
    '018e3f2a-bc92-7890-a123-456789abcdef',
    'ORDER',
    '018e3f2a-bc91-7890-a123-456789abcdef',
    'ORDER_CREATED',
    '{"orderId":"018e3f2a-bc91-7890-a123-456789abcdef","total":9950}',
    'PENDING',
    CURRENT_TIMESTAMP_UTC
  );
COMMIT;
-- Background CDC poller reads PENDING rows and publishes to message queue.
```

---

## 2. Idempotent Queue Consumers

Consumers must defend against at-least-once message duplication:

```text
FUNCTION ProcessMessage(Message):
    DedupKey = "consumer:dedup:" + Message.eventId
    
    // Attempt to set key for 7 days
    IsNew = Redis.SET(DedupKey, "PROCESSED", NX=TRUE, EX=604800)
    IF NOT IsNew:
        LOG_WARN("Duplicate message received. Skipping.", {"eventId": Message.eventId})
        RETURN ACK // Acknowledge to remove from queue
        
    ExecuteBusinessProcessing(Message.payload)
    RETURN ACK
```

---

## 3. Resilience: Timeouts, Exponential Backoff & Circuit Breakers

### Explicit Network Timeouts
- Connect Timeout: $\le 2\text{s}$
- Read/Response Timeout: $\le 10\text{s}$

### Exponential Backoff with Full Jitter
To prevent thundering herds hitting a recovering downstream dependency:

$$\text{SleepTime} = \text{random}(0, \min(\text{MaxBackoff}, \text{BaseDelay} \times 2^{\text{attempt}}))$$

### Circuit Breaker States
- **Closed**: All requests pass through. If error rate exceeds 50% over a 10s window, transition to **Open**.
- **Open**: Fail fast immediately with a fallback response. Do not execute network calls. Wait 30s.
- **Half-Open**: Send 3 canary test requests. If all succeed, transition to **Closed**. If any fail, return to **Open**.
