# Memory Leaks & Lifecycle Cleanup in NestJS

## Overview

Long-running Node.js processes in containers (Kubernetes, AWS ECS, Docker Compose) often suffer from silent memory exhaustion, dangling TCP connections, and ungraceful pod termination. In NestJS applications, memory leaks and connection hanging are typically caused by missing shutdown hooks, unmanaged database connection pools, dangling event listeners, unclosed Redis clients, and unbounded memory caches.

---

## 1. NestJS Lifecycle Hooks Overview

NestJS provides structured application lifecycle events for resource initialization and teardown:

```text
Bootstrapping:
onModuleInit() ────────► onApplicationBootstrap() ────────► Application Listening

Termination (Requires app.enableShutdownHooks()):
onModuleDestroy() ─────► beforeApplicationShutdown() ────► onApplicationShutdown()
```

> [!IMPORTANT]
> By default, NestJS **does NOT** listen to system shutdown signals (`SIGTERM`, `SIGINT`). You MUST explicitly call `app.enableShutdownHooks()` in `main.ts`!

---

## 2. Mandatory Shutdown Configuration (`main.ts`)

```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);

  // Mandatory: Enable graceful shutdown signal handling
  app.enableShutdownHooks();

  await app.listen(process.env.PORT ?? 3000);
}
void bootstrap();
```

---

## 3. Database Connection Pool Cleanup

### Prisma ORM Lifecycle Management:
```typescript
// src/prisma/prisma.service.ts
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  async onModuleInit(): Promise<void> {
    await this.$connect();
  }

  async onModuleDestroy(): Promise<void> {
    // Closes connection pool cleanly upon SIGTERM
    await this.$disconnect();
  }
}
```

### TypeORM Data Source Management:
```typescript
@Injectable()
export class DatabaseLifecycleService implements OnModuleDestroy {
  constructor(private readonly dataSource: DataSource) {}

  async onModuleDestroy(): Promise<void> {
    if (this.dataSource.isInitialized) {
      await this.dataSource.destroy();
    }
  }
}
```

---

## 4. Redis Client & Background Queue Teardown

### Redis Client (`ioredis`):
```typescript
import { Injectable, OnModuleDestroy } from '@nestjs/common';
import Redis from 'ioredis';

@Injectable()
export class RedisService implements OnModuleDestroy {
  private readonly client: Redis;

  constructor() {
    this.client = new Redis(process.env.REDIS_URL ?? 'redis://localhost:6379');
  }

  async onModuleDestroy(): Promise<void> {
    // Quits cleanly, allowing pending commands to complete
    await this.client.quit();
  }
}
```

### BullMQ Queue Management:
```typescript
@Injectable()
export class QueueLifecycleService implements OnModuleDestroy {
  constructor(
    @InjectQueue('email') private readonly emailQueue: Queue,
  ) {}

  async onModuleDestroy(): Promise<void> {
    await this.emailQueue.pause();
    await this.emailQueue.close();
  }
}
```

---

## 5. RxJS & Event Listener Leaks

### Problem: Unsubscribed Observables in Long-Lived Services
In NestJS backend services, long-lived Observables (e.g. WebSocket streams, Kafka listeners, polling timers) will retain memory references indefinitely if not unsubscribed.

### Solution: Lifecycle Subject Teardown
```typescript
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Injectable()
export class MetricsPollerService implements OnModuleInit, OnModuleDestroy {
  private readonly destroy$ = new Subject<void>();

  onModuleInit(): void {
    interval(5000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.pollHealthMetrics();
      });
  }

  onModuleDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private pollHealthMetrics(): void {
    // Polling logic
  }
}
```

---

## 6. Memory Leak Diagnostic Commands

```bash
# 1. Profile Node.js heap in dev mode
NODE_OPTIONS="--max-old-space-size=512 --expose-gc" pnpm start:dev

# 2. Inspect active handles before shutdown
node -e 'console.log(process._getActiveHandles())'

# 3. Check for dangling database connections in Postgres
SELECT pid, query, state, age(clock_timestamp(), query_start)
FROM pg_stat_activity
WHERE state != 'idle';
```
