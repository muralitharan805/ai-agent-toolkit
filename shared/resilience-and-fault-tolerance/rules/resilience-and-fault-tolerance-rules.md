---
trigger: model_decision
description: "Enforces resilience patterns across all external I/O: strict timeouts, exponential backoff with jitter for transient errors, circuit breakers (Closed/Open/Half-Open), and HTTP Idempotency-Key handling."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Resilience & Fault Tolerance Engineering Standards

## Description
Enforces system resilience, fault tolerance, and graceful degradation standards across all backend services and microservices. Mandates that every outbound network and I/O call enforces strict bounded timeouts, requires exponential backoff retries with randomized jitter strictly limited to transient errors, enforces Circuit Breaker protection (Closed, Open, Half-Open) on external dependencies to stop cascading failure propagation, mandates HTTP `Idempotency-Key` header handling on all mutating endpoints to prevent duplicate operations, and requires explicit fallback definitions for degraded operating modes.

## Constraints

### 1. Mandatory Bounded Timeouts on All I/O Operations
- Unbounded network requests, database queries, and message broker calls are STRICTLY FORBIDDEN.
- Every external I/O operation MUST configure explicit timeout ceilings:
  - **Database Queries**: Maximum `5000ms` (statement_timeout).
  - **Cache (Redis / Memcached)**: Maximum `1000ms`.
  - **Downstream HTTP APIs**: `connectTimeout: 2000ms`, `readTimeout: 5000ms`.
  - **Message Broker Acknowledgment**: Maximum `10000ms`.
- **Rationale**: In the absence of strict timeouts, a single degraded downstream service holding connections open causes thread/socket pool exhaustion that crashes the entire host application.

### 2. Transient-Only Retries with Exponential Backoff and Jitter
- Retrying non-transient client errors (HTTP `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`) is STRICTLY FORBIDDEN. Retrying client bugs produces identical failures while wasting CPU and network bandwidth.
- Retries MUST be strictly isolated to transient network anomalies:
  - HTTP `429 Too Many Requests`, HTTP `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout`, and TCP socket timeouts (`ETIMEDOUT`, `ECONNRESET`).
- Retry attempts MUST enforce exponential backoff with randomized jitter ($\pm 10\%\text{--}20\%$):
  $$\text{delay} = \min(\text{baseDelay} \times 2^{\text{attempt}}, \text{maxDelay}) + \text{jitter}$$

### 3. Circuit Breaker Protection on External Services
- Outbound client calls to third-party APIs or decoupled downstream microservices MUST be wrapped in a Circuit Breaker state machine:
  1. **CLOSED (Normal)**: Requests pass through. Successes reset error counters.
  2. **OPEN (Tripped)**: When the failure rate exceeds the threshold (e.g. 5 consecutive failures or $> 50\%$ failures over a 10s rolling window), the circuit trips to OPEN. All subsequent requests fail fast immediately without making network calls.
  3. **HALF-OPEN (Probe)**: After a cooldown reset timeout (e.g. 15s–30s), a single probe request is permitted through. If successful, the circuit resets to CLOSED. If it fails, it trips back to OPEN.
- Failing fast in the OPEN state protects downstream systems from being hammered during outages and prevents upstream application thread exhaustion.

### 4. HTTP Idempotency-Key Specification for Mutating Endpoints
- Mutating HTTP endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) subject to client retries (e.g. payment processing, order placement, funds transfer) MUST enforce the `Idempotency-Key` header:
  `Idempotency-Key: <UUIDv4>`
- **Server Lifecycle**:
  1. **Check Existing Key**: If the key exists in the idempotency store (Redis) with status `COMPLETED`, return the stored HTTP status code and response payload immediately without re-executing business logic.
  2. **In-Flight Lock**: If the key status is `IN_PROGRESS`, return HTTP `409 Conflict` or queue the concurrent request with a short lock timeout to prevent race conditions.
  3. **Execution & Caching**: If the key is new, store status `IN_PROGRESS` with an acquisition lock, execute the handler, store the final response with a 24-hour TTL (`EX 86400`), and return the result.

### 5. Graceful Degradation & Fallback Strategy
- Every critical dependency failure MUST have a documented fallback strategy:
  - Return cached data (even if slightly stale) during read path degradation.
  - Queue operations asynchronously when synchronous partner systems are offline.
  - Return a degraded response contract (`status: "degraded"`) rather than throwing an unhandled HTTP 500 error.

## Examples

### 1. HTTP Client with Strict Timeouts & Transient-Only Retry

```typescript
// ✅ CORRECT: Strict timeouts, transient filtering, and jittered backoff
import axios from 'axios';

const httpClient = axios.create({
  timeout: 5000, // 5s read timeout
  // Node.js http/https agent socket connection timeout
});

export async function callExternalPartner(url: string, payload: unknown, maxAttempts = 3): Promise<unknown> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const response = await httpClient.post(url, payload);
      return response.data;
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } }).response?.status;
      const isTransient = !status || status >= 500 || status === 429;

      // Never retry client validation errors!
      if (!isTransient || attempt === maxAttempts - 1) {
        throw error;
      }

      const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
      const jitter = (Math.random() - 0.5) * (delay * 0.2);
      await new Promise((resolve) => setTimeout(resolve, delay + jitter));
    }
  }
}
```

### 2. Idempotency Middleware with Redis Lock

```typescript
// ✅ CORRECT: Idempotency middleware preventing duplicate payment execution
export function idempotencyMiddleware(req: Request, res: Response, next: NextFunction): void {
  const idempotencyKey = req.headers['idempotency-key'] as string;
  if (!idempotencyKey) {
    return next(); // Key optional for non-financial routes, or reject if strictly required
  }

  const cacheKey = `idempotency:${idempotencyKey}`;
  redisClient.get(cacheKey).then((cached) => {
    if (cached) {
      const record = JSON.parse(cached);
      if (record.status === 'IN_PROGRESS') {
        return res.status(409).json({ message: 'A request with this idempotency key is already in progress' });
      }
      return res.status(record.statusCode).json(record.body);
    }

    // Set lock
    redisClient.set(cacheKey, JSON.stringify({ status: 'IN_PROGRESS' }), 'EX', 60);

    // Intercept response send to store result
    const originalJson = res.json.bind(res);
    res.json = (body: unknown) => {
      redisClient.set(cacheKey, JSON.stringify({ status: 'COMPLETED', statusCode: res.statusCode, body }), 'EX', 86400);
      return originalJson(body);
    };

    next();
  }).catch(() => next());
}
```
