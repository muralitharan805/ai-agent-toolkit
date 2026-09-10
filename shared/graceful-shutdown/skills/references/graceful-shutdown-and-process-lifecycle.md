# Graceful Shutdown & Process Lifecycle Architecture Reference

## Overview
This reference establishes the engineering principles and architectural runbook for implementing a **deterministic 11-step graceful shutdown protocol** across distributed backend microservices, API servers, and asynchronous worker processes. It details **POSIX Signal Trapping**, **Readiness Probe Invalidation**, **Kubernetes Pod Lifecycle Synchronization**, **Connection Draining**, and **Telemetry Buffer Flushing**.

---

## 1. The Deterministic 11-Step Ordered Shutdown Sequence

When a termination signal (`SIGTERM` or `SIGINT`) is trapped by the operating system, the application must execute the following 11 steps strictly in sequence:

```
[OS Signal: SIGTERM / SIGINT]
        │
        ▼
  1. Mark /ready → 503 (Set internal readiness flag to false)
        │
  2. Sleep 2–5s (Wait for Load Balancer / Kube-Proxy IP table propagation)
        │
  3. Stop accepting new HTTP connections (server.close() initiated)
        │
  4. Wait for in-flight requests to complete (Grace timeout budget: 25s < K8s 30s)
        │
  5. Stop consuming from message queues (Kafka, RabbitMQ, BullMQ paused)
        │
  6. Wait for active worker jobs to checkpoint or finish
        │
  7. Flush telemetry spans & metric buffers (OpenTelemetry tracerProvider.shutdown())
        │
  8. Flush log buffers (Pino flushSync() / Winston stream drain)
        │
  9. Close Database connection pools (PostgreSQL, MySQL pool.end())
        │
  10. Close Cache connections (Redis client.quit())
        │
  11. Emit final completion log with process uptime and exit (process.exit(0))
```

---

## 2. Kubernetes Pod Deletion Lifecycle & Grace Budgeting

In Kubernetes, pod termination follows an asynchronous two-pronged lifecycle:

```
                      [API Server initiates Pod Deletion]
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
  [Endpoint Controller]                             [Kubelet on Node]
  Remove Pod IP from EndpointSlice                   Send SIGTERM to Pod container
  Kube-proxy updates iptables on nodes                             │
  Ingress / Cloud LB removes target IP                             ▼
               │                                      Container begins shutdown
               │ ◄────────── 2 to 5 seconds ────────► Wait for LB removal
               │             propagation delay                     │
               ▼                                                   ▼
  [No new traffic routed to Pod]                       Drain active requests
                                                                   │
                                                                   ▼
                                                       Container exits cleanly
                                                       (Exit Code 0)
```

### Why Grace Period Budgeting Matters
- Default Kubernetes `terminationGracePeriodSeconds` is **30 seconds**.
- If the application sets an internal grace timeout of 30 seconds or higher, Kubernetes will forcibly issue `SIGKILL` (Exit Code 137) before the application finishes closing DB connections or flushing logs.
- **Production Standard**: Budget internal shutdown timeout to **25 seconds** (or 80% of `terminationGracePeriodSeconds`).

| Parameter | Kubernetes Config | Application Budget | Rationale |
| :--- | :--- | :--- | :--- |
| `terminationGracePeriodSeconds` | 30s | N/A | Kubelet hard ceiling before issuing uncatchable `SIGKILL`. |
| Load Balancer Propagation Sleep | N/A | 2s–5s | Prevents HTTP 502 Bad Gateway during iptables propagation. |
| In-Flight Request Drain Timeout | N/A | 15s–18s | Allows in-progress HTTP operations to finalize responses. |
| Infrastructure Teardown Timeout | N/A | 2s–3s | Flushes telemetry and cleanly drains database connection pools. |
| **Total Application Grace Timeout** | **30s** | **25s** | **Guarantees 5s safety margin before SIGKILL.** |

---

## 3. In-Flight Request Draining & HTTP Socket Management

### HTTP Server Listener Behavior
Calling `server.close(callback)` in Node.js stops the server from accepting *new* connections, but does not forcibly disconnect existing keep-alive connections.

```typescript
import { createServer, Server, IncomingMessage, ServerResponse } from 'http';

export class HttpServerManager {
  private readonly activeSockets = new Set<any>();

  constructor(private readonly server: Server) {
    this.trackConnections();
  }

  private trackConnections(): void {
    this.server.on('connection', (socket) => {
      this.activeSockets.add(socket);
      socket.on('close', () => this.activeSockets.delete(socket));
    });
  }

  public async closeAndDrain(timeoutMs: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        // Destroy stubborn keep-alive sockets after timeout
        for (const socket of this.activeSockets) {
          socket.destroy();
        }
        resolve();
      }, timeoutMs);

      this.server.close((err) => {
        clearTimeout(timer);
        if (err) return reject(err);
        resolve();
      });
    });
  }
}
```

---

## 4. Message Queue Consumer Draining

Worker processes handling asynchronous queues must halt intake immediately:

1. **BullMQ / Redis Queues**: Call `queue.pause()` and `worker.close()` to allow the current job to complete while preventing subsequent job dequeuing.
2. **Kafka**: Commit offsets for the current batch, pause partition consumption, and leave consumer group cleanly (`consumer.disconnect()`).
3. **RabbitMQ**: Issue `channel.cancel(consumerTag)` to stop receiving messages from the broker, then close channel and connection.

---

## 5. Mandatory Telemetry and Log Buffer Flushing

Modern logging frameworks (e.g. Pino with `pino/file` or sonic-boom) and OpenTelemetry exporters use asynchronous batch buffering to maximize throughput.

### Flushing Protocol
```typescript
/**
 * Flushes all pending telemetry spans and structured log streams.
 */
export async function flushObservabilityBuffers(logger: any): Promise<void> {
  // 1. Flush and terminate OpenTelemetry trace provider
  if (global.tracerProvider && typeof global.tracerProvider.shutdown === 'function') {
    await global.tracerProvider.shutdown();
  }

  // 2. Flush structured log buffers to stdout/disk
  if (logger && typeof logger.flushSync === 'function') {
    logger.flushSync();
  }
}
```

---

## 6. Exit Codes Semantics

| Exit Code | Meaning | Cause |
| :--- | :--- | :--- |
| `0` | Clean Success | All 11 shutdown steps executed and all connections closed within budget. |
| `1` | Grace Period Expired / Error | In-flight requests timed out, DB close failed, or unhandled rejection during shutdown. |
| `137` | Fatal `SIGKILL` | Orchestrator killed container because process exceeded `terminationGracePeriodSeconds`. |
| `143` | Raw `SIGTERM` Uncaught | Process lacked signal handlers and defaulted to immediate OS abort. |
