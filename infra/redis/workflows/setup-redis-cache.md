---
description: "Workflow to scaffold enterprise Redis caching modules, visual (cached) logging interceptors, and mutation cache invalidators in NestJS/Node.js apps. Triggered by 'redis:', 'cache:', or '/setup-redis-cache'."
trigger: manual
---

# Setup Enterprise Redis Caching & Visual Logging Workflow

Follow this step-by-step workflow to scaffold enterprise-grade Redis caching into a backend application.

## Steps

### Step 1: Install Redis Dependencies via `pnpm`
```bash
pnpm add ioredis @nestjs/config
pnpm add -D @types/ioredis
```

### Step 2: Implement Redis Cache Service (`redis-cache.service.ts`)
1. Create `src/core/cache/redis-cache.service.ts` implementing `OnModuleInit` and `OnModuleDestroy`.
2. Configure automatic reconnection strategy and connection error handlers.
3. Implement `get<T>()`, `set()`, and pattern-based cache purging `delByPattern()`.

### Step 3: Implement Visual Logging Cache Interceptor (`http-cache.interceptor.ts`)
1. Create `src/core/cache/http-cache.interceptor.ts`.
2. Intercept GET requests and compute deterministic MD5 cache key (`app:cache:<endpoint>:<md5>`).
3. On Cache HIT: Log `⚡ [CACHE HIT] GET /route (cached - 2ms)` and set `X-Cache: HIT` header.
4. On Cache MISS: Execute DB query, log `🔍 [CACHE MISS] GET /route (database query - 85ms)`, set `X-Cache: MISS` header, and cache result in Redis for 300 seconds.

### Step 4: Register Cache Module & Global Interceptor
Register `RedisCacheModule` in `app.module.ts` or `core.module.ts`.

### Step 5: Verification & Console Log Test
1. Make a GET request to `/api/v1/users`; verify console output displays `🔍 [CACHE MISS] ... (database query - Xms)`.
2. Make the same GET request immediately; verify console output displays `⚡ [CACHE HIT] ... (cached - Xms)`.
