---
trigger: model_decision
description: "Enforces deterministic 13-step backend application bootstrap sequence, infrastructure-only wiring, process-level crash handlers (unhandledRejection/uncaughtException), and pre-flight dependency health gates."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Application Bootstrap & Server Lifecycle Standards

## Description
Enforces a deterministic, language-agnostic startup sequence and server lifecycle architecture across all backend services. Eliminates startup race conditions, guarantees process-level crash interception (`unhandledRejection`, `uncaughtException`, and panics), mandates pre-flight infrastructure connectivity checks with exponential backoff retries before accepting HTTP traffic, restricts bootstrap logic strictly to infrastructure wiring, and requires graceful shutdown hooks to be registered prior to network binding.

## Constraints

### 1. Mandatory 13-Step Boot Sequence Order
The application bootstrap entry point (`main` / `server`) MUST execute the startup sequence in a strict, non-negotiable order:
1. **Load & Validate Configuration**: Execute schema validation gate; crash immediately with exit code `1` if invalid.
2. **Initialize Structured Logger**: Bootstrap the singleton JSON logger before any operational step to ensure failures are captured.
3. **Register Process-Level Crash Handlers**: Bind listeners for `unhandledRejection`, `uncaughtException`, and runtime panics.
4. **Connect to Database Store**: Initialize connection pool with retry backoff and verify health via ping.
5. **Connect to In-Memory Cache / Redis**: Establish and verify cache connectivity.
6. **Connect to Message Broker**: Initialize AMQP/Kafka consumers/publishers (if applicable).
7. **Wire Dependency Injection Container**: Resolve services, repositories, and use case singletons.
8. **Register Middleware Pipeline**: Mount security headers, correlation IDs, request loggers, and parsers in correct order.
9. **Register Routes & Adapters**: Mount controllers and HTTP route handlers.
10. **Register Global Error Filter**: Mount the catch-all RFC-7807 exception filter as the final middleware.
11. **Register Graceful Shutdown Hooks**: Bind OS termination signals (`SIGTERM`, `SIGINT`) BEFORE starting network listeners.
12. **Start Network Listener**: Bind the HTTP/gRPC server to host and port.
13. **Emit Ready Log Event**: Emit a single structured JSON log confirming `Server ready at {host}:{port}`.

### 2. Infrastructure-Only Wiring Invariant (Zero Business Logic in Main)
- The application entry point (`main.ts`, `main.go`, `app.py`) is restricted EXCLUSIVELY to infrastructure composition, dependency injection wiring, and lifecycle registration.
- Executing domain business logic, processing seed data, or running long-running synchronous calculations directly inside `main()` is STRICTLY FORBIDDEN.

### 3. Mandatory Process-Level Crash Interception
- The application MUST register global crash handlers to catch unhandled asynchronous rejections and unhandled synchronous exceptions.
- Handlers MUST log the complete error stack trace, error name, and context using structured `FATAL` level logging, flush log buffers, and execute a controlled process termination (`process.exit(1)`).
- Swallowing unhandled rejections with empty catch blocks or allowing silent crashes without structured logging is STRICTLY FORBIDDEN.

### 4. Pre-Flight Infrastructure Connectivity Gate
- The HTTP/gRPC server MUST NOT begin listening on its network port until all critical downstream dependencies (database connection pool, mandatory Redis cache) have successfully established connectivity and verified health.
- Serving HTTP traffic while database pools are in an uninitialized or broken state is STRICTLY FORBIDDEN.

### 5. Resilient Connection Retry with Exponential Backoff
- Database and broker connection attempts during bootstrap MUST implement retry logic with exponential backoff and jitter (minimum 3 retry attempts) before terminating the process.
- Transient network blips during orchestrator (Kubernetes / Docker Compose) container startup must not trigger immediate container crash loops.

### 6. Pre-Listen Termination Hook Registration
- OS signal listeners (`SIGTERM`, `SIGINT`) MUST be registered before calling `server.listen()`.
- If an orchestrator sends a `SIGTERM` while the application is still initializing, the bootstrap process must cleanly abort without hanging.

## Examples

### 1. Deterministic 13-Step Bootstrap vs. Race-Condition Prone Startup

```typescript
// ❌ FORBIDDEN: Starting server before DB is connected and missing crash handlers
export async function startApp(): Promise<void> {
  const app = express();
  app.listen(3000); // Bad! Accepts traffic before DB is connected or config is validated
  connectDatabase(); // Floating promise! Crashes requests with unhandled rejection
}

// ✅ CORRECT: Deterministic sequential bootstrap with pre-flight gates
export async function bootstrapApplication(): Promise<void> {
  // Step 1: Config
  const config = ConfigService.initialize();
  // Step 2: Logger
  const logger = LoggerService.initialize(config.LOG_LEVEL);
  // Step 3: Crash handlers
  registerProcessCrashHandlers(logger);
  // Step 4 & 5: Infrastructure connectivity with retries
  const dbPool = await DatabaseConnection.connectWithRetry(config.DATABASE_URL, logger);
  const redisClient = await CacheConnection.connect(config.REDIS_URL, logger);
  // Step 6 & 7: DI wiring
  const container = wireDependencies({ config, dbPool, redisClient, logger });
  // Step 8, 9, 10: Middlewares, routes, error handlers
  const app = createAppServer(container);
  // Step 11: Shutdown hooks registered BEFORE listening
  const server = http.createServer(app);
  registerShutdownHooks({ server, dbPool, redisClient, logger });
  // Step 12 & 13: Listen & Log
  server.listen(config.PORT, () => {
    logger.info({ event: 'server_ready', port: config.PORT, env: config.APP_ENV });
  });
}
```

### 2. Process-Level Crash Handlers

```typescript
// ✅ CORRECT: Mandatory process-level error interception
export function registerProcessCrashHandlers(logger: LoggerService): void {
  process.on('unhandledRejection', (reason: unknown) => {
    logger.fatal({
      event: 'process_unhandled_rejection',
      error: reason instanceof Error ? reason.stack : String(reason),
    });
    process.exit(1);
  });

  process.on('uncaughtException', (error: Error) => {
    logger.fatal({
      event: 'process_uncaught_exception',
      error: error.stack,
    });
    process.exit(1);
  });
}
```

### 3. Resilient Database Connection with Exponential Backoff

```typescript
// ✅ CORRECT: Retry loop with exponential backoff before fatal abort
export async function connectWithRetry(
  dbUrl: string,
  logger: LoggerService,
  maxRetries: number = 3
): Promise<DatabasePool> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const pool = new DatabasePool(dbUrl);
      await pool.query('SELECT 1'); // Health ping
      logger.info({ event: 'database_connected', attempt });
      return pool;
    } catch (error) {
      const delayMs = Math.pow(2, attempt) * 500;
      logger.warn({ event: 'database_connect_retry', attempt, nextRetryMs: delayMs, error });
      if (attempt === maxRetries) {
        logger.fatal({ event: 'database_connect_failed_fatal', maxRetries });
        process.exit(1);
      }
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
  throw new Error('Unreachable');
}
```
