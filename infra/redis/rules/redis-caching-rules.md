---
description: "Strict Redis caching rules, global cache toggle (REDIS_CACHE_GLOBAL_ENABLED), blacklist exclusions (@NoCache() / CACHE_DISABLED_ROUTES), custom TTL decorators (@UseCache(600)), mandatory TTL expiration, fault-tolerant DB fallback, and visual log formatting."
trigger: model_decision
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

### 3. Visual Console Log Differentiation Rule
- HTTP caching interceptors MUST format logger output to explicitly differentiate cache hits from database queries:
  - Cache HIT: `⚡ [CACHE HIT] GET /route (cached - Xms)`
  - Cache MISS: `🔍 [CACHE MISS] GET /route (database query - Xms)`
- Responses MUST inject custom `X-Cache: HIT` or `X-Cache: MISS` headers.

### 4. Mandatory TTL Expiration Rule
- Every cached Redis key MUST be configured with an explicit Time-To-Live (TTL) expiration (default: 300 seconds). Indefinite caching without TTL is strictly forbidden.

### 5. Fault-Tolerant Fallback Rule
- If the Redis server is unavailable or throws a connection error, application request handlers MUST NOT fail with HTTP 500 errors.
- The caching layer MUST log a warning and transparently execute the underlying primary database query.

### 6. Cache Invalidation on Data Mutation
- Data mutation endpoints (`POST`, `PATCH`, `PUT`, `DELETE`) MUST invalidate relevant cached key patterns (e.g. `example-app:cache:users:*`) to prevent serving stale data to clients.

## Examples

### 1. Fault-Tolerant Cache Service with Transparent DB Fallback
```typescript
// ❌ FORBIDDEN: Crashing the HTTP request when Redis connection drops
async function getCachedUser(userId: string): Promise<User> {
  const cached = await redisClient.get(`user:${userId}`); // Throws unhandled error if Redis is down!
  return JSON.parse(cached);
}

// ✅ CORRECT: Graceful fallback to primary database when Redis fails
async function getCachedUser(userId: string): Promise<User> {
  try {
    if (this.isRedisConnected) {
      const cached = await this.redisClient.get(`app:cache:users:${userId}`);
      if (cached) {
        return JSON.parse(cached);
      }
    }
  } catch (error) {
    this.logger.warn(`Redis get failed for user ${userId}, falling back to database: ${error}`);
  }
  return this.database.users.findUnique({ where: { id: userId } });
}
```

### 2. Visual Log Formatting & X-Cache Headers
```typescript
// ✅ CORRECT: Explicit visual emoji tags and sub-second latency reporting
if (cacheHit) {
  this.logger.log(`⚡ [CACHE HIT] GET ${request.url} (cached - ${durationMs}ms)`);
  response.setHeader('X-Cache', 'HIT');
  return of(cachedPayload);
} else {
  this.logger.log(`🔍 [CACHE MISS] GET ${request.url} (database query - ${durationMs}ms)`);
  response.setHeader('X-Cache', 'MISS');
  // Pass through to controller handler...
}
```

### 3. Mutation Invalidation Pattern Purging
```typescript
// ✅ CORRECT: Automatic pattern purge following successful mutation
@Patch(':id')
async updateUser(@Param('id') id: string, @Body() dto: UpdateUserDto): Promise<User> {
  const updated = await this.userService.update(id, dto);
  // Purge all list and detail caches for users
  await this.cacheService.delByPattern('app:cache:users:*');
  return updated;
}
```
