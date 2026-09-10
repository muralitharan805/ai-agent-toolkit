---
trigger: model_decision
description: "Enforces deterministic 11-step graceful shutdown sequence, SIGTERM/SIGINT signal handling, readiness probe invalidation (503), in-flight request draining (<30s), telemetry/log flushing, and connection teardown."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Graceful Shutdown & Process Termination Standards

## Description
Enforces a deterministic 11-step graceful shutdown protocol across all backend applications, HTTP services, and worker processes. Mandates proper handling of POSIX operating system termination signals (`SIGTERM`, `SIGINT`), immediate invalidation of the readiness health probe (`GET /health/ready` $\rightarrow$ 503) to prevent load balancer traffic blackholing, in-flight request draining within a strict grace timeout budgeted below Kubernetes `terminationGracePeriodSeconds`, graceful consumer pause on message queues, comprehensive flushing of telemetry and log buffers, clean closure of database and cache pools, and deterministic process exit codes (0 for clean termination, 1 for timed-out force kill).

## Constraints

### 1. Dual POSIX Termination Signal Handling
- Backend applications MUST bind explicit event listeners for both `SIGTERM` (emitted by Kubernetes, Docker, and systemd) and `SIGINT` (emitted by interactive terminal `Ctrl+C`).
- Unhandled termination signals resulting in abrupt default process death are STRICTLY FORBIDDEN.
- Signal listener binding MUST occur during process initialization prior to opening network ports.
- Once a shutdown sequence has initiated, subsequent incoming signals MUST be ignored or handled with a forced fast-exit fallback.

### 2. Readiness Probe Invalidation & Traffic Draining
- Upon receiving a termination signal, the service MUST immediately mark its internal readiness state as `UNHEALTHY` so that `GET /health/ready` returns HTTP 503 Service Unavailable.
- **Load Balancer Propagation Delay**:
  - The service MUST pause for 2 to 5 seconds (sleep) before closing the HTTP server socket.
  - **Reason**: Kubernetes kube-proxy and cloud load balancers (AWS ALB, GCP Cloud Load Balancing) require several seconds to detect the failing readiness probe and remove the pod IP from active routing tables. Closing the server listener immediately causes in-flight network requests to receive connection refused (HTTP 502 Bad Gateway) errors.

### 3. In-Flight Request Draining & Kubernetes Grace Budgeting
- The application MUST allow existing in-flight HTTP requests to complete cleanly before terminating.
- **Timeout Budget Constraint**:
  - The internal application shutdown timeout MUST be strictly shorter than the orchestrator timeout (e.g. set internal timeout to 25 seconds when Kubernetes `terminationGracePeriodSeconds` is set to 30 seconds).
  - Exceeding the orchestrator timeout causes the kernel to send an uncatchable `SIGKILL` (exit 137), corrupting state and dropping telemetry.
- If in-flight requests do not finish within the budgeted grace period, the shutdown orchestrator MUST abort active connections, log an error diagnostic, and exit with code 1.

### 4. Queue Consumer Pause & Message Broker Decoupling
- Background worker processes and message queue consumers (Kafka, RabbitMQ, BullMQ, SQS) MUST immediately stop pulling new messages from queues upon receiving `SIGTERM`.
- Currently active message consumer jobs MUST be allowed to finish their execution or be cleanly re-queued / negative-acknowledged (`NACK`) before closing message broker client connections.
- Terminating workers mid-job without proper acknowledgement or state checkpointing is STRICTLY FORBIDDEN.

### 5. Mandatory Telemetry, Metrics & Log Buffer Flushing
- Before closing database connections or terminating the process, the service MUST flush all in-memory telemetry buffers:
  1. OpenTelemetry distributed tracing spans exporter (`tracerProvider.shutdown()`).
  2. Prometheus / OpenTelemetry metrics push/aggregation buffers.
  3. Structured logging streams (Pino `destination.flushSync()`, Winston `flush`, Winston file streams).
- Failing to flush log buffers prior to process exit causes the final 5–15 seconds of error logs and shutdown traces to be permanently lost.

### 6. Resource Teardown Order & Exit Codes
- Database pools and cache connections MUST NOT be closed while in-flight requests or consumer workers are still processing.
- Teardown MUST follow a strict sequential order:
  1. Stop accepting new traffic (readiness probe $\rightarrow$ 503, wait 2-5s).
  2. Stop queue consumers.
  3. Close HTTP listener and drain in-flight requests.
  4. Flush metrics, traces, and log buffers.
  5. Close database connection pools (PostgreSQL, MySQL).
  6. Close cache connections (Redis).
  7. Emit structured termination completion log containing process uptime.
  8. Call `process.exit(0)` on clean completion, or `process.exit(1)` on grace period timeout.

## Examples

### 1. Complete Production Graceful Shutdown Orchestrator (TypeScript)
```typescript
// ✅ CORRECT: Deterministic 11-step graceful shutdown with Kubernetes grace budgeting
export class ShutdownCoordinator {
  private isShuttingDown = false;
  private readonly GRACE_TIMEOUT_MS = 25000; // Strictly < K8s 30s terminationGracePeriod

  constructor(
    private readonly server: Server,
    private readonly dbPool: Pool,
    private readonly redisClient: Redis,
    private readonly messageConsumer: MessageQueueConsumer,
    private readonly logger: StructuredLogger
  ) {}

  public registerSignalHandlers(): void {
    const handleSignal = (signal: NodeJS.Signals): void => {
      if (this.isShuttingDown) return;
      this.isShuttingDown = true;
      this.executeShutdown(signal).catch((err) => {
        this.logger.error({ msg: 'Fatal error during shutdown', error: err });
        process.exit(1);
      });
    };

    process.on('SIGTERM', () => handleSignal('SIGTERM'));
    process.on('SIGINT', () => handleSignal('SIGINT'));
  }

  public isReady(): boolean {
    return !this.isShuttingDown;
  }

  private async executeShutdown(signal: string): Promise<void> {
    const startTime = Date.now();
    this.logger.info({ msg: `Received ${signal}, initiating graceful shutdown` });

    const timeoutTimer = setTimeout(() => {
      this.logger.error({ msg: 'Shutdown grace timeout expired, forcing exit' });
      process.exit(1);
    }, this.GRACE_TIMEOUT_MS);

    try {
      // Step 1 & 2: Mark /ready 503 and allow LB propagation delay
      await new Promise((resolve) => setTimeout(resolve, 3000));

      // Step 3: Stop queue consumers
      await this.messageConsumer.stopConsuming();

      // Step 4: Close HTTP server listener & drain in-flight requests
      await new Promise<void>((resolve, reject) => {
        this.server.close((err) => (err ? reject(err) : resolve()));
      });

      // Step 5: Flush telemetry and logging buffers
      await telemetryProvider.shutdown();
      await this.logger.flush();

      // Step 6: Close DB pool and Redis connections
      await this.dbPool.end();
      await this.redisClient.quit();

      clearTimeout(timeoutTimer);
      const uptimeSec = Math.floor(process.uptime());
      this.logger.info({ msg: `Shutdown complete. Uptime: ${uptimeSec}s`, durationMs: Date.now() - startTime });
      process.exit(0);
    } catch (error) {
      clearTimeout(timeoutTimer);
      this.logger.error({ msg: 'Error during graceful shutdown sequence', error });
      process.exit(1);
    }
  }
}
```

### 2. Readiness Probe Route Binding
```typescript
// ✅ CORRECT: Readiness endpoint returns 503 immediately upon shutdown initiation
app.get('/api/v1/health/ready', (req: Request, res: Response) => {
  if (!shutdownCoordinator.isReady()) {
    return res.status(503).json({
      status: 'UNHEALTHY',
      reason: 'Server is terminating and draining traffic',
    });
  }
  return res.status(200).json({ status: 'READY' });
});
```
