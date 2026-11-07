---
trigger: model_decision
description: "Enforces production caching architecture, L1/L2 tiered caching, standardized key namespacing, cache stampede mitigation (mutex locking, early expiration), mandatory TTLs, and graceful DB fallback."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Caching & In-Memory Store Architecture Standards

## Description
Enforces resilient, high-throughput in-memory and distributed caching standards across all backend services. Establishes the architectural guidelines for multi-tiered L1 (in-process LRU) and L2 (distributed Redis) caching, mandates standardized hierarchical key namespacing, requires explicit Time-To-Live (TTL) on all cached entries to eliminate zombie keys, enforces cache stampede (thundering herd) prevention via distributed mutex locks or probabilistic early expiration, guarantees graceful degradation to primary databases during cache outages, and prohibits caching raw authentication tokens or unencrypted sensitive PII.

## Constraints

### 1. Multi-Tiered Caching & In-Memory Leak Prevention
- Applications implementing caching MUST clearly distinguish between caching tiers:
  - **Tier 1 (L1 In-Process Cache)**: Process-local memory (e.g. Node.js `lru-cache`, Go `sync.Map`, Python `cachetools`). Must be strictly bounded with `max` item counts and aggressive TTLs (10s–300s). Unbounded in-memory maps (`const cache = {}`) are STRICTLY FORBIDDEN due to inevitable process Out-Of-Memory (OOM) crashes.
  - **Tier 2 (L2 Distributed Cache)**: Shared distributed store (Redis / Memcached / Dragonfly). Survives application pod restarts and serves horizontally scaled replicas with sub-millisecond latencies.
- Local L1 caches MUST NOT store dynamic multi-tenant write data that requires immediate cluster-wide consistency.

### 2. Standardized Hierarchical Cache Key Convention
- Every cache key MUST follow the standardized four-part hierarchical namespacing pattern:
  `{service}:{entity}:{identifier}:{version}`
- **Examples**:
  - `user-service:profile:usr_abc123:v1`
  - `order-service:list:usr_abc123:page:2:size:20:v1`
  - `rate-limit:ip:192.168.1.1:v1`
- Un-namespaced, flat keys (e.g. `12345`, `profile`, `userData`) are STRICTLY FORBIDDEN to prevent collision between distinct microservices and schemas sharing the same Redis instance.

### 3. Mandatory TTL & Prohibition of Zombie Keys
- Every cached entry written to L1 or L2 stores MUST include an explicit Time-To-Live (TTL) expiration value.
- Invoking indefinite storage commands (e.g. Redis `SET key value` without `EX`, `PX`, or `EXAT`) on application entities is STRICTLY FORBIDDEN.
- Un-expiring "zombie keys" accumulate indefinitely, leading to memory saturation, stale state, and forced Redis LRU evictions that degrade production performance.

### 4. Cache Stampede (Thundering Herd) Mitigation
- High-traffic hot keys subject to concurrent reads MUST implement cache stampede protection. When a hot key expires:
  - **Strategy A (Distributed Mutex / Lock)**: The first incoming request acquires a distributed lock (`SET lock:{resource} {token} NX EX 10`), loads the missing record from the primary database, populates the cache, and releases the lock. Concurrent requests wait or yield and retrieve the populated cache value.
  - **Strategy B (Probabilistic Early Expiration / XFetch)**: Requests probabilistically recompute and refresh the cached entry slightly before actual TTL expiration based on read frequency and computation cost:
    $-\beta \cdot \delta \cdot \ln(\text{random}()) > \text{remainingTTL}$.
- Allowing 1,000+ concurrent requests to hit the primary database simultaneously on cache miss is a CRITICAL RISK and is STRICTLY FORBIDDEN.

### 5. Graceful Degradation & Primary DB Fallback
- The application runtime MUST remain operational if the cache cluster becomes unavailable, partitioned, or suffers downtime.
- Cache clients (e.g. `ioredis`, `redis-py`, `go-redis`) MUST configure:
  - Reconnect retry strategies with exponential backoff and jitter.
  - Command timeouts ($\le 2000\text{ms}$).
- If a cache read fails or times out, the application MUST log a `WARN` event, degrade gracefully, and fetch data directly from the primary database without throwing unhandled 500 errors to users.

### 6. Cache Telemetry & Security Protection
- **Telemetry**: Caching layers MUST track and expose Prometheus counters for `cache_hits_total{tier, entity}` and `cache_misses_total{tier, entity}` to monitor cache efficiency.
- **Credential Protection**: Raw passwords, JWT signing keys, authorization bearer tokens, and unencrypted credit card numbers MUST NEVER be stored in cache keys or values.

## Examples

### 1. Unbounded In-Memory Cache Leak vs. Bounded L1 LRU

```typescript
// ❌ FORBIDDEN: Unbounded in-memory map leaks memory and crashes Node.js with OOM
const userCache = new Map<string, UserProfile>();
export function getUser(id: string): UserProfile {
  if (!userCache.has(id)) {
    userCache.set(id, fetchUser(id)); // Never evicted, indefinite growth!
  }
  return userCache.get(id)!;
}

// ✅ CORRECT: Bounded LRU cache with max items and TTL
import { LRUCache } from 'lru-cache';

export const boundedUserCache = new LRUCache<string, UserProfile>({
  max: 5000,              // Hard ceiling on items
  ttl: 1000 * 60 * 5,     // 5 minutes max lifespan
  updateAgeOnGet: false,  // Prevents stale data retention
});
```

### 2. Cache-Aside Pattern with Mutex Stampede Guard

```typescript
// ✅ CORRECT: Cache-Aside with distributed lock to prevent thundering herd
export async function getCachedOrder(orderId: string): Promise<OrderRecord> {
  const cacheKey = `order-service:orders:${orderId}:v1`;
  const cached = await redisClient.get(cacheKey);
  if (cached) {
    metrics.cacheHits.inc({ entity: 'orders' });
    return JSON.parse(cached);
  }

  metrics.cacheMisses.inc({ entity: 'orders' });
  const lockKey = `lock:orders:${orderId}`;
  const acquired = await redisClient.set(lockKey, 'locked', 'NX', 'EX', 5);

  if (!acquired) {
    // Another worker is populating the cache; wait and retry cache lookup
    await sleep(50);
    return getCachedOrder(orderId);
  }

  try {
    const freshOrder = await db.orders.findUnique({ where: { id: orderId } });
    if (freshOrder) {
      await redisClient.set(cacheKey, JSON.stringify(freshOrder), 'EX', 300); // 5 min TTL
    }
    return freshOrder;
  } finally {
    await redisClient.del(lockKey);
  }
}
```

### 3. Graceful Cache Failure Fallback

```typescript
// ✅ CORRECT: Resilient cache fetch with fallback to primary DB on Redis failure
export async function resilientCacheGet<T>(
  key: string,
  fetchFromDb: () => Promise<T>,
  ttlSeconds = 300
): Promise<T> {
  try {
    const cached = await redisClient.get(key);
    if (cached) return JSON.parse(cached);
  } catch (err) {
    logger.warn({
      event: 'cache.unavailable',
      key,
      error: (err as Error).message,
      message: 'Redis cache unavailable. Falling back directly to database.',
    });
  }

  // Gracefully fallback to primary database
  const result = await fetchFromDb();

  try {
    if (result) {
      await redisClient.set(key, JSON.stringify(result), 'EX', ttlSeconds);
    }
  } catch {
    // Non-blocking: fail silently if write fails during Redis partition
  }

  return result;
}
```
