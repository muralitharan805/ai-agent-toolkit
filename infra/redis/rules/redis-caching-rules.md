---
trigger: always_on
description: "Strict Redis caching rules, mandatory TTL expiration, fault-tolerant DB fallback, visual (cached) vs (database query) log formatting, and mutation cache invalidation."
---

# Enterprise Redis Caching & Visual Logging Rules

## Description
Enforces mandatory standards for Redis caching, cache key namespacing, fault-tolerant database fallback, and visual logger formatting in backend applications.

## Constraints

### 1. Visual Console Log Differentiate Rule
- HTTP caching interceptors MUST format logger output to explicitly differentiate cache hits from database queries:
  - Cache HIT: `⚡ [CACHE HIT] GET /route (cached - Xms)`
  - Cache MISS: `🔍 [CACHE MISS] GET /route (database query - Xms)`
- Responses MUST inject custom `X-Cache: HIT` or `X-Cache: MISS` headers.

### 2. Mandatory TTL Expiration Rule
- Every cached Redis key MUST be configured with an explicit Time-To-Live (TTL) expiration (default: 300 seconds).
- Writing un-expiring keys without explicit architectural justification is strictly forbidden.

### 3. Fault-Tolerant Fallback Rule
- If the Redis server is unavailable or throws a connection error, application request handlers MUST NOT fail with HTTP 500 errors.
- The caching layer MUST log a warning and transparently execute the underlying primary database query.

### 4. Cache Invalidation on Data Mutation
- Data mutation endpoints (`POST`, `PATCH`, `DELETE`) MUST invalidate relevant cached keys (e.g. `nidhiflow:cache:users:*`) to prevent serving stale data to clients.

### 5. Colon-Delimited Key Namespacing Rule
- Cache keys MUST follow the colon-delimited namespace convention: `<app>:cache:<domain>:<endpoint>:<query_hash>`.
