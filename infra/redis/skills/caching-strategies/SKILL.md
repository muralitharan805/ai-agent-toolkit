---
name: caching-strategies
description: "Enterprise guidelines for production-grade Redis caching, global cache enablement (REDIS_CACHE_GLOBAL_ENABLED), blacklist exclusions (@NoCache() / CACHE_DISABLED_ROUTES), custom TTL decorators (@UseCache(600)), visual console logging for cache hits vs misses, fault-tolerant DB fallbacks, and mutation cache invalidation."
---

# Enterprise Redis Caching & Visual Logging Interceptor Architecture

## Goal
Guide developers and AI coding agents in implementing production-grade Redis caching in backend applications (NestJS / Node.js). Supports **Global Cache Enablement (`REDIS_CACHE_GLOBAL_ENABLED=true`)**, **Blacklist Exclusions (`@NoCache()` / `CACHE_DISABLED_ROUTES`)**, and **Custom Route TTL Overrides (`@UseCache(600)`)**. Features fault-tolerant fallback, key namespacing, cache invalidation on data mutations, and **visual console logging that explicitly differentiates Cache HITs `(cached - 2ms)` from Cache MISSES `(database query - 85ms)` and Cache BYPASSES**.

---

# Core Redis Caching Principles

1. **Global Cache Enablement (`REDIS_CACHE_GLOBAL_ENABLED=true`)**: When enabled in `.env`, all GET routes are cached automatically by default.
2. **Dual Exclusion Mechanisms**:
   - **Decorator Exclusion (`@NoCache()`)**: Explicitly bypasses caching for specific controller endpoints.
   - **Config Blacklist (`CACHE_DISABLED_ROUTES=/api/v1/users/me,/api/v1/health`)**: Comma-separated list of route prefixes excluded from caching.
3. **Custom TTL Decorator (`@UseCache(ttlSeconds)`)**: Allows setting custom cache duration (e.g. `@UseCache(600)` for 10 minutes) or forcing cache enablement when global mode is OFF.
4. **Cache Key Namespacing**: Use colon-delimited key namespacing: `<app>:cache:<domain>:<endpoint>:<query_md5>` (e.g. `nidhiflow:cache:users:list:a8f9b2`).
5. **Fault-Tolerant Fallback**: If Redis connection is down, log a warning and transparently execute the database query without throwing HTTP 500 errors.
6. **Visual Console Logging**: Every request intercepted by the caching layer MUST produce a clear console log entry explicitly displaying `(cached)` vs `(database query)`.

---

# Production NestJS Redis Implementation

### 1. Cache Custom Decorators (`cache.decorators.ts`)

```typescript
import { SetMetadata } from '@nestjs/common';

export const IS_CACHE_ENABLED_KEY = 'isCacheEnabled';
export const IS_CACHE_DISABLED_KEY = 'isCacheDisabled';
export const CACHE_TTL_KEY = 'cacheTTL';

/**
 * Opt-In / Custom TTL Decorator: Enables Redis caching & sets custom duration for a GET endpoint.
 * @param ttlSeconds Custom TTL in seconds (e.g. 600 for 10 minutes)
 * 
 * @example
 * @Get()
 * @UseCache(600)
 * findAll() { ... }
 */
export const UseCache = (ttlSeconds = 300) => (target: any, key?: any, descriptor?: any) => {
  SetMetadata(IS_CACHE_ENABLED_KEY, true)(target, key, descriptor);
  SetMetadata(CACHE_TTL_KEY, ttlSeconds)(target, key, descriptor);
};

/**
 * Explicit Bypass Decorator: Forcefully disables caching for a specific endpoint.
 * 
 * @example
 * @Get('me')
 * @NoCache()
 * getProfile() { ... }
 */
export const NoCache = () => SetMetadata(IS_CACHE_DISABLED_KEY, true);
```

---

### 2. Config-Driven & Flexible HTTP Cache Interceptor (`http-cache.interceptor.ts`)

```typescript
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ConfigService } from '@nestjs/config';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';
import { RedisCacheService } from './redis-cache.service';
import { IS_CACHE_ENABLED_KEY, IS_CACHE_DISABLED_KEY, CACHE_TTL_KEY } from './cache.decorators';
import * as crypto from 'crypto';

@Injectable()
export class HttpCacheInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HttpCache');

  constructor(
    private readonly redisCacheService: RedisCacheService,
    private readonly reflector: Reflector,
    private readonly configService: ConfigService,
  ) {}

  async intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const ctx = context.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    // Rule 1: Cache ONLY GET requests
    if (request.method !== 'GET') {
      return next.handle();
    }

    // Rule 2: Check explicit @NoCache() decorator exclusion
    const isExplicitlyDisabledByDecorator = this.reflector.getAllAndOverride<boolean>(
      IS_CACHE_DISABLED_KEY,
      [context.getHandler(), context.getClass()],
    );
    if (isExplicitlyDisabledByDecorator) {
      return next.handle();
    }

    // Rule 3: Check Config Blacklist (CACHE_DISABLED_ROUTES)
    const blacklistConfig = this.configService.get<string>('CACHE_DISABLED_ROUTES', '');
    const blacklistedRoutes = blacklistConfig ? blacklistConfig.split(',').map((r) => r.trim()) : [];
    if (blacklistedRoutes.some((route) => request.path.startsWith(route))) {
      return next.handle();
    }

    // Rule 4: Evaluate Caching Decision (Global Flag OR Decorator @UseCache OR Config Whitelist)
    const isGlobalCacheEnabled = this.configService.get<boolean>('REDIS_CACHE_GLOBAL_ENABLED', true);

    const isDecoratorEnabled = this.reflector.getAllAndOverride<boolean>(
      IS_CACHE_ENABLED_KEY,
      [context.getHandler(), context.getClass()],
    );

    const whitelistConfig = this.configService.get<string>('CACHE_ENABLED_ROUTES', '');
    const whitelistedRoutes = whitelistConfig ? whitelistConfig.split(',').map((r) => r.trim()) : [];
    const isWhitelistedInConfig = whitelistedRoutes.some((route) => request.path.startsWith(route));

    const shouldCache = isGlobalCacheEnabled || isDecoratorEnabled || isWhitelistedInConfig;

    if (!shouldCache) {
      return next.handle();
    }

    // Determine custom TTL (from @UseCache(ttl) or default 300s)
    const customTTL =
      this.reflector.getAllAndOverride<number>(CACHE_TTL_KEY, [
        context.getHandler(),
        context.getClass(),
      ]) || 300;

    const startTime = Date.now();
    const urlHash = crypto.createHash('md5').update(request.originalUrl).digest('hex').substring(0, 8);
    const cacheKey = `nidhiflow:cache:${request.path.replace(/\//g, ':')}:${urlHash}`;

    // Read from Redis Cache
    const cachedData = await this.redisCacheService.get(cacheKey);

    if (cachedData) {
      const duration = Date.now() - startTime;
      
      // VISUAL LOGGER OUTPUT FOR CACHE HIT
      this.logger.log(
        `⚡ [CACHE HIT] ${request.method} ${request.originalUrl} (cached - ${duration}ms)`
      );

      response.setHeader('X-Cache', 'HIT');
      response.setHeader('X-Response-Time', `${duration}ms`);
      return of(cachedData);
    }

    // CACHE MISS: Execute Database Query Handler
    response.setHeader('X-Cache', 'MISS');

    return next.handle().pipe(
      tap(async (data) => {
        const duration = Date.now() - startTime;

        // VISUAL LOGGER OUTPUT FOR CACHE MISS
        this.logger.log(
          `🔍 [CACHE MISS] ${request.method} ${request.originalUrl} (database query - ${duration}ms)`
        );

        // Store result in Redis asynchronously with configured TTL
        await this.redisCacheService.set(cacheKey, data, customTTL);
      }),
    );
  }
}
```

---

### 3. Environment Configuration Template (`.env.example`)

```env
# Master Redis Cache Toggle (true = All GET routes cached by default)
REDIS_CACHE_GLOBAL_ENABLED=true

# Blacklist Routes (Excluded from caching even if global mode is true)
CACHE_DISABLED_ROUTES=/api/v1/users/me,/api/v1/health,/api/v1/auth

# Whitelist Routes (Only used if REDIS_CACHE_GLOBAL_ENABLED=false)
CACHE_ENABLED_ROUTES=/api/v1/reports
```

---

# Verification Protocols

1. **Global Cache Test**: Set `REDIS_CACHE_GLOBAL_ENABLED=true`; verify GET `/api/v1/users` is cached on 2nd request.
2. **Decorator Exclusion Test**: Add `@NoCache()` to `GET /api/v1/users/me`; verify it is NEVER cached.
3. **Config Blacklist Test**: Add `/api/v1/health` to `CACHE_DISABLED_ROUTES`; verify requests to `/api/v1/health` bypass cache completely.
4. **Custom TTL Test**: Add `@UseCache(600)` to `GET /api/v1/reports`; verify key is written to Redis with 600s TTL.
