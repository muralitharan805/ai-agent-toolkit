# NestJS Cache Interceptors & Automatic Mutation Invalidation

## Overview
High-performance REST APIs implement caching at the HTTP gateway layer using NestJS Interceptors. This eliminates database query execution for repeated idempotent `GET` requests while ensuring immediate cache purging when data mutations occur.

---

## 1. Deterministic Cache Key Generation
To prevent cache key collisions across tenants, environments, and route parameters:
```text
<app_name>:cache:<controller_resource>:<action>:<md5_hash_of_query_and_params>
```
Example:
```text
example-app:cache:users:list:e3b0c44298fc1c149afbf4c8996fb92427ae41e4
```

---

## 2. Visual Log Formatting & X-Cache Response Headers
Every intercepted HTTP request MUST emit structured visual console logs differentiating cache hits from primary database executions:

- **Cache HIT**:
  ```text
  ⚡ [CACHE HIT] GET /api/v1/users (cached - 2ms)
  Header: X-Cache: HIT
  ```
- **Cache MISS**:
  ```text
  🔍 [CACHE MISS] GET /api/v1/users (database query - 85ms)
  Header: X-Cache: MISS
  ```

---

## 3. Pattern-Based Mutation Invalidation
When data modification endpoints (`POST`, `PATCH`, `PUT`, `DELETE`) succeed, the application MUST purge all related cached keys:

```typescript
import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { Observable, tap } from 'rxjs';
import { RedisCacheService } from './redis-cache.service';

@Injectable()
export class CacheInvalidationInterceptor implements NestInterceptor {
  constructor(private readonly cacheService: RedisCacheService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const http = context.switchToHttp();
    const req = http.getRequest();
    const method = req.method.toUpperCase();

    return next.handle().pipe(
      tap(async () => {
        if (['POST', 'PATCH', 'PUT', 'DELETE'].includes(method)) {
          const resource = req.route?.path?.split('/')[1] || 'global';
          const pattern = `app:cache:${resource}:*`;
          await this.cacheService.delByPattern(pattern);
          console.log(`🧹 [CACHE INVALIDATION] Purged pattern: ${pattern}`);
        }
      })
    );
  }
}
```
