---
trigger: always_on
description: "Strict Redis caching rules, global cache toggle (REDIS_CACHE_GLOBAL_ENABLED), blacklist exclusions (@NoCache() / CACHE_DISABLED_ROUTES), custom TTL decorators (@UseCache(600)), mandatory TTL expiration, fault-tolerant DB fallback, and visual log formatting."
---

# Enterprise Redis Caching Rules

## Description
Enforces mandatory standards for Redis caching, global cache configuration, blacklist route exclusions, custom TTL overrides, fault-tolerant database fallback, and visual logger formatting in backend applications.

## Constraints

### 1. Global Cache Enablement & Exclusions Rule
- When `REDIS_CACHE_GLOBAL_ENABLED=true` in `.env`, GET routes are cached automatically by default.
- Routes MUST be excluded from caching via:
  - `@NoCache()` decorator on the controller method/class.
  - OR route prefix listed in `CACHE_DISABLED_ROUTES` environment variable.

### 2. Custom TTL Decorator Rule (`@UseCache(ttlSeconds)`)
- Endpoints requiring non-default cache duration MUST use the `@UseCache(ttlSeconds)` decorator (e.g. `@UseCache(600)` for 10 minutes TTL).

### 3. Visual Console Log Differentiate Rule
- HTTP caching interceptors MUST format logger output to explicitly differentiate cache hits from database queries:
  - Cache HIT: `⚡ [CACHE HIT] GET /route (cached - Xms)`
  - Cache MISS: `🔍 [CACHE MISS] GET /route (database query - Xms)`
- Responses MUST inject custom `X-Cache: HIT` or `X-Cache: MISS` headers.

### 4. Mandatory TTL Expiration Rule
- Every cached Redis key MUST be configured with an explicit Time-To-Live (TTL) expiration (default: 300 seconds).

### 5. Fault-Tolerant Fallback Rule
- If the Redis server is unavailable or throws a connection error, application request handlers MUST NOT fail with HTTP 500 errors.
- The caching layer MUST log a warning and transparently execute the underlying primary database query.

### 6. Cache Invalidation on Data Mutation
- Data mutation endpoints (`POST`, `PATCH`, `DELETE`) MUST invalidate relevant cached keys (e.g. `nidhiflow:cache:users:*`) to prevent serving stale data to clients.
