---
name: caching-strategies
description: "Enterprise guidelines for production-grade Redis caching, visual console logging for cache hits (cached) vs misses (database query), fault-tolerant DB fallbacks, TTL management, and mutation cache invalidation."
---

# Enterprise Redis Caching & Visual Logging Interceptor Architecture

## Goal
Guide developers and AI coding agents in implementing production-grade Redis caching in backend applications (NestJS / Node.js). Enforces fault-tolerant fallback, key namespacing, cache invalidation on data mutations, and **visual console logging that explicitly differentiates Cache HITs `(cached - 2ms)` from Cache MISSES `(database query - 85ms)`**.

---

# Core Redis Caching Principles

1. **Cache Key Namespacing**: Use colon-delimited key namespacing: `<app>:cache:<domain>:<endpoint>:<query_md5>` (e.g. `nidhiflow:cache:users:list:a8f9b2`).
2. **Explicit TTL Expiration**: All cached keys MUST have an explicit TTL (default: 300 seconds / 5 minutes) to prevent stale memory bloat.
3. **Fault-Tolerant Fallback**: If Redis connection is down, log a warning and transparently execute the database query without throwing HTTP 500 errors.
4. **Visual Console Logging**: Every request intercepted by the caching layer MUST produce a clear console log entry explicitly displaying `(cached)` vs `(database query)` with execution duration.
5. **Mutation Cache Invalidation**: Data mutation endpoints (`POST`, `PATCH`, `DELETE`) MUST invalidate related cache keys (e.g. `nidhiflow:cache:users:*`).

---

# Production NestJS Redis Implementation

### 1. Redis Cache Service (`redis-cache.service.ts`)

```typescript
import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Redis from 'ioredis';

@Injectable()
export class RedisCacheService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(RedisCacheService.name);
  private client: Redis;
  private isConnected = false;

  constructor(private readonly configService: ConfigService) {}

  onModuleInit() {
    const host = this.configService.get<string>('REDIS_HOST', 'localhost');
    const port = this.configService.get<number>('REDIS_PORT', 6379);
    const password = this.configService.get<string>('REDIS_PASSWORD', '');

    this.client = new Redis({
      host,
      port,
      password: password || undefined,
      retryStrategy: (times) => Math.min(times * 100, 3000), // Max 3s retry interval
      maxRetriesPerRequest: 2,
    });

    this.client.on('connect', () => {
      this.isConnected = true;
      this.logger.log(`✅ Connected to Redis Server at ${host}:${port}`);
    });

    this.client.on('error', (err) => {
      this.isConnected = false;
      this.logger.warn(`⚠️ Redis Connection Error: ${err.message}. Falling back to DB queries.`);
    });
  }

  onModuleDestroy() {
    this.client.disconnect();
  }

  async get<T>(key: string): Promise<T | null> {
    if (!this.isConnected) return null;
    try {
      const data = await this.client.get(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      this.logger.warn(`Failed to read key ${key} from Redis: ${error.message}`);
      return null;
    }
  }

  async set(key: string, value: any, ttlSeconds = 300): Promise<void> {
    if (!this.isConnected) return;
    try {
      await this.client.set(key, JSON.stringify(value), 'EX', ttlSeconds);
    } catch (error) {
      this.logger.warn(`Failed to write key ${key} to Redis: ${error.message}`);
    }
  }

  async delByPattern(pattern: string): Promise<void> {
    if (!this.isConnected) return;
    try {
      const stream = this.client.scanStream({ match: pattern, count: 100 });
      stream.on('data', (keys: string[]) => {
        if (keys.length > 0) {
          const pipeline = this.client.pipeline();
          keys.forEach((k) => pipeline.del(k));
          pipeline.exec();
        }
      });
    } catch (error) {
      this.logger.warn(`Failed to clear cache pattern ${pattern}: ${error.message}`);
    }
  }
}
```

---

### 2. HTTP Cache Interceptor with Visual Logger (`http-cache.interceptor.ts`)

```typescript
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';
import { RedisCacheService } from './redis-cache.service';
import * as crypto from 'crypto';

@Injectable()
export class HttpCacheInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HttpCache');

  constructor(private readonly redisCacheService: RedisCacheService) {}

  async intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const ctx = context.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    // Cache ONLY GET requests
    if (request.method !== 'GET') {
      return next.handle();
    }

    const startTime = Date.now();
    
    // Generate deterministic cache key from URL & query string
    const urlHash = crypto.createHash('md5').update(request.originalUrl).digest('hex').substring(0, 8);
    const cacheKey = `nidhiflow:cache:${request.path.replace(/\//g, ':')}:${urlHash}`;

    // Try reading from Redis Cache
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

        // Store result in Redis asynchronously (5 minutes TTL)
        await this.redisCacheService.set(cacheKey, data, 300);
      }),
    );
  }
}
```

---

### 3. Console Output Specification

When routes are accessed, NestJS console logs MUST clearly highlight cache hits vs database queries:

```text
# First Request (Cache Miss - Fetches from PostgreSQL):
[Nest] 18400  - 07/24/2026, 8:12:00 AM     LOG [HttpCache] 🔍 [CACHE MISS] GET /api/v1/users?page=1 (database query - 85ms)

# Second Request (Cache Hit - Served directly from Redis):
[Nest] 18400  - 07/24/2026, 8:12:05 AM     LOG [HttpCache] ⚡ [CACHE HIT] GET /api/v1/users?page=1 (cached - 2ms)
```

---

# Verification Protocols

1. **Visual Log Test**: Execute `curl http://localhost:3000/api/v1/users` twice; verify the second call prints `⚡ [CACHE HIT] ... (cached - Xms)` in NestJS logger console.
2. **HTTP Header Test**: Verify second HTTP response contains header `X-Cache: HIT`.
3. **Failover Test**: Stop Redis container (`docker compose stop redis`); verify backend logs warning and serves response from database without throwing errors.
