# Redis Reconnection & Fault-Tolerant Circuit Breaking Architecture

## Overview
In production distributed architectures, in-memory caches like Redis are optimization layers, not single points of failure. If the Redis server restarts, encounters network partition, or runs out of memory, application HTTP request lifecycles MUST NOT fail with 500 Internal Server Errors.

---

## 1. Non-Blocking Connection & Reconnection Strategy
Using `ioredis` in Node.js / NestJS, configure resilient retry strategies with exponential backoff and maximum retry thresholds:

```typescript
import Redis, { RedisOptions } from 'ioredis';

export function createResilientRedisClient(options: {
  host: string;
  port: number;
  password?: string;
}): Redis {
  const redisOptions: RedisOptions = {
    host: options.host,
    port: options.port,
    password: options.password,
    retryStrategy(times: number): number | null {
      // Exponential backoff capped at 2000ms
      const delay = Math.min(times * 100, 2000);
      return delay;
    },
    maxRetriesPerRequest: 1, // Fail fast on individual commands to prevent thread stalling
    enableReadyCheck: true,
    lazyConnect: true // Prevent blocking application startup if Redis is temporarily offline
  };

  return new Redis(redisOptions);
}
```

---

## 2. Transparent Database Fallback Protocol
Wrap all cache reads in `try/catch` guard blocks:
- On Cache Miss OR Connection Error: Log a warning and seamlessly execute the primary database query.
- Never throw an unhandled exception up the NestJS filter pipeline due to Redis connectivity faults.

```typescript
async getOrSet<T>(
  cacheKey: string,
  fetchFn: () => Promise<T>,
  ttlSeconds: number = 300
): Promise<T> {
  try {
    if (this.isConnected) {
      const cached = await this.client.get(cacheKey);
      if (cached) {
        return JSON.parse(cached) as T;
      }
    }
  } catch (err) {
    this.logger.warn(`Redis get failed for '${cacheKey}', falling back to DB: ${err}`);
  }

  // Transparent database retrieval
  const freshData = await fetchFn();

  // Async non-blocking cache population
  if (freshData !== null && freshData !== undefined) {
    this.safeSet(cacheKey, freshData, ttlSeconds).catch((err) => {
      this.logger.warn(`Background Redis set failed for '${cacheKey}': ${err}`);
    });
  }

  return freshData;
}
```
