---
name: caching-strategies
description: "Universal architecture for Redis caching, resilient reconnection, transparent database fallbacks, visual hit/miss logging, and mutation invalidation."
---

# Enterprise Redis Caching & Visual Logging Skill

## Purpose
Establishes production-grade Redis caching architectures, resilient client reconnection strategies, transparent primary database fallbacks, visual HTTP interceptor logging (`⚡ [CACHE HIT]`, `🔍 [CACHE MISS]`), custom TTL overrides, and automatic mutation pattern invalidation.

## Architecture & Tooling Matrix
- **Reconnection & Fault Tolerance**: [references/redis-reconnection-and-fault-tolerance.md](references/redis-reconnection-and-fault-tolerance.md)
- **NestJS Interceptors & Invalidation**: [references/nest-cache-interceptors-and-invalidation.md](references/nest-cache-interceptors-and-invalidation.md)
- **Automated CLI Validator**: [scripts/audit_redis_cache_hygiene.py](scripts/audit_redis_cache_hygiene.py)
- **Starter Templates**:
  - Redis Service: [assets/redis-cache-service-template.ts](assets/redis-cache-service-template.ts)
  - HTTP Interceptor: [assets/http-cache-interceptor-template.ts](assets/http-cache-interceptor-template.ts)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Environment Configuration & Client Setup
1. Validate required environment variables (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_CACHE_GLOBAL_ENABLED`) using Zod or `@nestjs/config`.
2. Configure `ioredis` with exponential backoff (`retryStrategy: (times) => Math.min(times * 100, 2000)`).
3. Set `lazyConnect: true` and `maxRetriesPerRequest: 1` to prevent startup stalls during temporary Redis outages.

### Phase 2: Fault-Tolerant Cache Service Implementation
1. Encapsulate client operations within `RedisCacheService`.
2. Wrap `get`, `set`, and `del` in defensive `try/catch` guard blocks.
3. If Redis fails, log a diagnostic warning and return `null` to trigger seamless fallback to primary database queries.
4. Enforce mandatory Time-To-Live (TTL) expiration on all cache operations (default: 300 seconds).

### Phase 3: Visual Logging HTTP Cache Interceptor
1. Implement a global `HttpCacheInterceptor` targeting idempotent `GET` requests.
2. Generate deterministic MD5 cache keys combining route paths and query parameters.
3. On Cache HIT:
   - Emit visual console log: `⚡ [CACHE HIT] GET /route (cached - Xms)`.
   - Set HTTP response header: `X-Cache: HIT`.
4. On Cache MISS:
   - Emit visual console log: `🔍 [CACHE MISS] GET /route (database query - Xms)`.
   - Set HTTP response header: `X-Cache: MISS`.
   - Asynchronously populate the Redis cache with the response payload.

### Phase 4: Automatic Mutation Pattern Invalidation
1. Implement a `CacheInvalidationInterceptor` observing data mutation verbs (`POST`, `PATCH`, `PUT`, `DELETE`).
2. Construct resource-targeted pattern keys (e.g., `app:cache:users:*`).
3. Upon successful write completion, asynchronously purge matching keys via `delByPattern()`.
4. Emit confirmation log: `🧹 [CACHE INVALIDATION] Purged pattern: app:cache:users:*`.

### Phase 5: Automated CLI Hygiene & Verification
1. Execute the automated CLI audit tool to verify resilience and log formatting:
   ```bash
   python3 infra/redis/skills/caching-strategies/scripts/audit_redis_cache_hygiene.py --path ./src --strict
   ```
2. Test request latency and visual log output across sequential GET requests.

---

## Gotchas & Common Pitfalls

| Faulty / Anti-Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Crashing on Redis Outage** (Unhandled error) | Transparent DB query fallback | Makes Redis a single point of failure; cache outages cause complete application downtime. |
| **Missing Expiration TTL** (Indefinite caching) | Mandatory TTL (e.g., 300s) on all `set()` calls | Unexpired keys accumulate indefinitely, leading to Redis Out-Of-Memory (OOM) eviction errors. |
| **Hardcoded Redis Passwords** | Environment variables (`process.env.REDIS_PASSWORD`) | Leaks infrastructure credentials into source code and version control history. |
| **Missing Cache Invalidation on Mutations** | Automatic `delByPattern` on POST/PATCH/DELETE | Users see stale or outdated records after updating resources, leading to data consistency bugs. |
| **Caching Non-Idempotent Verbs** (Caching POST) | Cache exclusively idempotent `GET` routes | Caches mutate state unexpectedly and return identical responses for distinct creation requests. |
| **Un-hashed Query Param Keys** | Deterministic MD5 hash of query parameters | Inconsistent query parameter orders generate distinct cache entries, fragmenting cache memory. |
