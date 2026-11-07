# Caching Architecture, Invalidation & Stampede Prevention

## Overview

Caching reduces primary database load and delivers sub-millisecond query responses. However, naive caching implementations create severe production risks: memory leaks from unbounded in-process maps, stale data anomalies, cache stampedes (thundering herds) crashing databases during peak traffic, and cascading outages when the cache layer becomes unreachable.

---

## 1. Multi-Tiered Caching Hierarchy (L1 vs L2)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Multi-Tiered Caching Architecture                    │
└──────────────────────────────────────────────────────────────────────────────┘
  Client Request
       │
       ▼
  [Tier 1: L1 In-Process Cache]   ──► Memory RAM (< 100 nanoseconds)
       │ (Miss)                       • Max size: 5,000 items
       ▼                              • TTL: 10s–300s (volatile)
  [Tier 2: L2 Distributed Cache]  ──► Redis Cluster (< 1 millisecond)
       │ (Miss)                       • Shared across all pod replicas
       ▼                              • Survives app restarts
  [Primary Persistence Database]  ──► PostgreSQL / MySQL (5ms–50ms)
```

### Key Differences

| Feature | L1 In-Process Cache | L2 Distributed Cache (Redis) |
| :--- | :--- | :--- |
| **Location** | Application RAM | Dedicated cluster node |
| **Access Latency** | Nanoseconds | Sub-millisecond (TCP round-trip) |
| **Consistency** | Pod-local (drifts across replicas) | Strong / Eventual cluster consistency |
| **Best Used For** | Static reference data, read-heavy config | User profiles, sessions, rate limits |
| **Primary Risk** | Memory leaks if unbounded | Network partitioning, cache stampedes |

---

## 2. Standardized Cache Key Namespacing

Cache keys share a flat keyspace in Redis. Collisions between microservices or different schema versions corrupt data. All keys MUST follow the four-tier schema:

```
{service}:{entity}:{identifier}:{version}
```

- **service**: Originating microservice (e.g., `user-service`, `billing-service`).
- **entity**: Business domain noun (e.g., `profile`, `orders`, `permissions`).
- **identifier**: Unique primary key or parameterized filter (e.g., `usr_123`, `page:2:size:20`).
- **version**: Schema format identifier (e.g., `v1`, `v2`). Incrementing this version instantly purges stale cache schemas without running costly scan/flush operations.

---

## 3. Cache Invalidation Strategies

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Invalidation Strategy Comparison                     │
└──────────────────────────────────────────────────────────────────────────────┘
  Pattern           How it Works                       Trade-off
  ───────           ────────────                       ─────────
  TTL Expiration    Keys expire automatically          Data stale for TTL duration
  Cache-Aside       Read misses trigger DB loads       Simple; vulnerable to stampedes
  Write-Through     Writes update Cache & DB together  Always fresh; slower writes
  Event-Driven      Events (Kafka) trigger deletions   Zero stale data; complex event bus
```

---

## 4. Cache Stampede (Thundering Herd) Mitigation

### The Problem
When a hot key (e.g., product catalog for a flash sale) expires, hundreds or thousands of concurrent user requests experience a cache miss simultaneously. Every request attempts to load the same record from the database at the exact same moment, overwhelming the connection pool and crashing the database.

### Mitigation Strategy 1: Distributed Mutex (Locking)
Only the first request is permitted to fetch from the database:

```typescript
export async function fetchWithMutex<T>(
  key: string,
  fetchFn: () => Promise<T>,
  ttlSeconds = 300
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const lockKey = `lock:${key}`;
  const acquired = await redis.set(lockKey, 'locked', 'NX', 'EX', 10);

  if (!acquired) {
    // Wait for other worker to populate cache, then retry
    await new Promise((resolve) => setTimeout(resolve, 50));
    return fetchWithMutex(key, fetchFn, ttlSeconds);
  }

  try {
    const data = await fetchFn();
    await redis.set(key, JSON.stringify(data), 'EX', ttlSeconds);
    return data;
  } finally {
    await redis.del(lockKey);
  }
}
```

### Mitigation Strategy 2: Probabilistic Early Expiration (XFetch)
Recomputes the cache proactively before actual expiration based on computational delta $\delta$ and random logarithm:

$$\text{currentTime} - (\beta \times \delta \times \ln(\text{random}())) > \text{expiryTime}$$

---

## 5. Graceful Degradation & Resilience

Redis must never become a Single Point of Failure (SPOF) for read paths:
1. **Network Retries**: Configure `retryStrategy` with exponential backoff and max retry count.
2. **Command Timeouts**: Cap Redis command latency ($\le 1000\text{ms}$).
3. **Safe Fallback**: Catch Redis connection exceptions and transparently route reads to the primary database.
4. **Metrics**: Instrument Prometheus counters for `cache_hits_total` and `cache_misses_total` to track hit ratios.
