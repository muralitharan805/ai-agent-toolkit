# Universal Application Bootstrap & Lifecycle Architecture Reference

## 1. Architectural Philosophy

> **App Boot = Infrastructure Wiring Only**: The bootstrap phase of a service is responsible solely for plumbing technical infrastructure (configuration, logging, process signals, database pools, caches, dependency containers, and middlewares). Any business logic executed during boot represents an architectural smell that degrades cold-start latency and couples business state to process lifecycles.

---

## 2. The 13-Step Boot Sequence Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        13-Step Startup Pipeline                        │
└────────────────────────────────────────────────────────────────────────┘
  [Step 1: Config Validation]       ──► Fail-fast schema check (Exit 1 on failure)
               │
  [Step 2: Logger Initialization]   ──► Bootstrap structured JSON logger singleton
               │
  [Step 3: Process Crash Handlers]  ──► Bind unhandledRejection & uncaughtException
               │
  [Step 4: Database Connection]     ──► Pool creation with retry backoff + SELECT 1
               │
  [Step 5: Cache / Redis Connect]   ──► Establish and ping in-memory store
               │
  [Step 6: Message Broker Connect]  ──► Establish AMQP/Kafka consumers/publishers
               │
  [Step 7: DI Container Wiring]     ──► Register singletons, repos, and use cases
               │
  [Step 8: Middleware Pipeline]     ──► Headers, correlation ID, body parsers, logging
               │
  [Step 9: Controller & Routes]     ──► Mount HTTP/gRPC route handlers
               │
  [Step 10: Global Error Filter]    ──► Mount RFC-7807 exception filter as final hook
               │
  [Step 11: Shutdown Hooks]         ──► Attach SIGTERM & SIGINT listeners BEFORE listen
               │
  [Step 12: Network Listener]       ──► Bind HTTP server to 0.0.0.0:{PORT}
               │
  [Step 13: Ready Log Event]        ──► Emit JSON log: "Server ready at 0.0.0.0:{PORT}"
```

---

## 3. Multi-Language Bootstrap Implementations

### TypeScript / Node.js
```typescript
import http from 'node:http';
import { ConfigService } from './config/config.service';
import { LoggerService } from './observability/logger.service';
import { DatabaseConnection } from './database/connection';
import { CacheConnection } from './database/cache';
import { wireDependencies } from './container';
import { createServerApp } from './app';
import { registerShutdownHooks } from './lifecycle/shutdown';

export async function bootstrap(): Promise<void> {
  // 1. Config
  const config = ConfigService.initialize();

  // 2. Logger
  const logger = LoggerService.initialize(config.LOG_LEVEL);

  // 3. Process Crash Handlers
  process.on('unhandledRejection', (reason) => {
    logger.fatal({ event: 'unhandled_rejection', error: reason instanceof Error ? reason.stack : reason });
    process.exit(1);
  });

  process.on('uncaughtException', (err) => {
    logger.fatal({ event: 'uncaught_exception', error: err.stack });
    process.exit(1);
  });

  // 4 & 5. Database & Cache with retries
  const dbPool = await DatabaseConnection.connectWithRetry(config.DATABASE_URL, logger);
  const cache = await CacheConnection.connect(config.REDIS_URL, logger);

  // 7. DI Container
  const container = wireDependencies({ config, logger, dbPool, cache });

  // 8, 9, 10. Express / Fastify / Koa App
  const app = createServerApp(container);
  const server = http.createServer(app);

  // 11. Graceful Shutdown Hooks (Pre-Listen)
  registerShutdownHooks({ server, dbPool, cache, logger });

  // 12 & 13. Listen & Announce
  server.listen(config.PORT, '0.0.0.0', () => {
    logger.info({ event: 'server_ready', port: config.PORT, env: config.APP_ENV });
  });
}

bootstrap().catch((err) => {
  console.error('Fatal bootstrap failure:', err);
  process.exit(1);
});
```

### Python / FastAPI (`lifespan` Context Manager)
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import sys
import logging
from .config import AppConfig
from .database import DatabasePool
from .cache import RedisClient

config = AppConfig()
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Sequence (Steps 4 - 11)
    logger.info("Initializing infrastructure connections...")
    db_pool = await DatabasePool.create_with_retry(config.database_url)
    redis = await RedisClient.create(config.redis_url)

    app.state.db = db_pool
    app.state.redis = redis
    logger.info(f"Server ready at port {config.port}")

    yield  # Application serves traffic here

    # Shutdown Sequence (Teardown)
    logger.info("Draining connections on shutdown...")
    await redis.close()
    await db_pool.close()
    logger.info("Graceful shutdown complete.")

app = FastAPI(lifespan=lifespan)
```

### Go (Standard Library & Chi / Gin)
```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	// 1. Config & 2. Logger
	cfg := config.LoadConfig()
	log := logger.NewLogger(cfg.LogLevel)

	// 4. DB Connection with ping check
	db, err := database.ConnectWithRetry(cfg.DatabaseURL, 3, time.Second*2)
	if err != nil {
		log.Fatal("Database connection failed", "error", err)
		os.Exit(1)
	}
	defer db.Close()

	// 7, 8, 9, 10. Router & Middleware
	router := server.NewRouter(db, cfg, log)

	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      router,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	// 11. Shutdown Hook Channel
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM, syscall.SIGINT)

	go func() {
		log.Info("Server ready", "port", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("Server error", "error", err)
		}
	}()

	<-stop
	log.Info("Shutting down gracefully...")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Error("Server forced to shutdown", "error", err)
	}
}
```

---

## 4. Connection Retry & Jitter Algorithm

When multiple backend containers start simultaneously (e.g. after a deployment), connecting immediately to the database can create a "thundering herd" problem.

$$\text{Delay} = \min(\text{MaxDelay}, \text{InitialDelay} \times 2^{\text{attempt}}) + \text{UniformRandom}(0, \text{Jitter})$$

Using exponential backoff with randomized jitter ensures that retry attempts distribute evenly, preventing database CPU saturation during cluster recoveries.
