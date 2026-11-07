---
name: graceful-shutdown
description: "Enforces deterministic 11-step graceful shutdown sequence, SIGTERM/SIGINT signal handling, readiness probe invalidation (503), in-flight request draining (<30s), telemetry/log flushing, and connection teardown. Triggered by 'graceful-shutdown:', 'shutdown:', 'sigterm:', 'sigint:', or '/graceful-shutdown'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Graceful Shutdown Skill

## Overview

This skill establishes the production engineering standards for the **Deterministic 11-Step Graceful Shutdown Sequence**, **POSIX Signal Trapping (`SIGTERM` / `SIGINT`)**, **Readiness Probe Invalidation (HTTP 503)**, **Kubernetes Grace Timeout Budgeting (<30s)**, **Telemetry/Log Buffer Flushing**, and **Clean Resource Deallocation**. It guarantees zero-downtime rolling deployments, prevents dropped in-flight requests, and ensures no telemetry or log records are lost during container termination.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                   11-Step Graceful Shutdown Execution Pipeline                 │
│                                                                                │
│   [Phase 1: Signal Trapping]       ──► Catch SIGTERM/SIGINT; mark /ready 503   │
│                 │                                                              │
│   [Phase 2: LB Propagation Delay]  ──► Wait 2-5s for Kube-proxy / ALB drain    │
│                 │                                                              │
│   [Phase 3: Connection Draining]   ──► server.close() & await in-flight reqs   │
│                 │                                                              │
│   [Phase 4: Telemetry & Logs Flush]──► tracerProvider.shutdown() & flushSync() │
│                 │                                                              │
│   [Phase 5: Resource Teardown]     ──► Drain DB pools & Redis; process.exit(0) │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Phase Execution Guide

### Phase 1: Dual Signal Trapping & Readiness Invalidation
1. **Bind OS Signals Early**:
   - Register listeners for both `SIGTERM` and `SIGINT` during initialization before opening network listeners.
2. **Invalidate Readiness Immediately**:
   - Flip the internal state `isReady = false` so that subsequent calls to `GET /health/ready` return HTTP 503.
   - Prevents the Kubernetes Endpoint controller or cloud load balancers from routing new requests to the terminating instance.

### Phase 2: Load Balancer Propagation Sleep Delay
1. **Apply Safety Delay**:
   - Sleep 2 to 5 seconds before calling `server.close()`.
2. **Reason**:
   - Network routing tables (iptables/IPVS in Kube-proxy and cloud load balancers) take a few seconds to update after a readiness probe fails. Closing the server socket immediately results in HTTP 502 Bad Gateway for requests already in transit.

### Phase 3: In-Flight Connection Draining & Grace Budgeting
1. **Stop Accepting New HTTP Traffic**:
   - Call `server.close()` to stop accepting new connections while letting active sockets finish.
2. **Budget Grace Timeout Below Orchestrator Ceiling**:
   - Kubernetes defaults to `terminationGracePeriodSeconds: 30`.
   - Set internal application grace timeout to **25 seconds** to guarantee a 5-second safety margin before the uncatchable kernel `SIGKILL` (Exit 137).

### Phase 4: Message Queue Pause & Telemetry/Log Buffer Flushing
1. **Pause Asynchronous Consumers**:
   - Stop pulling messages from Kafka, BullMQ, or RabbitMQ. Complete in-progress jobs.
2. **Flush Observability Streams**:
   - Await OpenTelemetry tracer provider shutdown: `await tracerProvider.shutdown()`.
   - Synchronously flush logging buffers: `logger.flushSync()`. Prevents dropping error diagnostics emitted during the final seconds.

### Phase 5: Resource Deallocation & Deterministic Exit
1. **Tear Down Infrastructure Pools**:
   - Drain database connection pools: `await pool.end()`.
   - Disconnect in-memory caches: `await redis.quit()`.
2. **Deterministic Exit Codes**:
   - Log completion message with process uptime: `Shutdown complete. Uptime: {N}s`.
   - Exit with code `0` on clean shutdown, or code `1` if the grace timeout expired.

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/graceful-shutdown-and-process-lifecycle.md](references/graceful-shutdown-and-process-lifecycle.md) for detailed Kubernetes pod lifecycle diagrams, in-flight socket tracking, and exit code semantics.
- **Production Asset**: Inspect [assets/graceful-shutdown-orchestrator.template.ts](assets/graceful-shutdown-orchestrator.template.ts) for a production-ready 11-step TypeScript shutdown coordinator.
- **CLI Auditor Tool**: Execute [scripts/audit_graceful_shutdown.py](scripts/audit_graceful_shutdown.py) to audit signal handlers, readiness 503 invalidation, and timeout budgeting.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Architectural Risk |
| :--- | :--- | :--- | :--- |
| **Timeout Budgeting** | Setting internal timeout $\ge$ 30s matching K8s ceiling | Internal timeout set to **25s** (< K8s 30s ceiling) | Kernel issues uncatchable `SIGKILL` (137) mid-flight, corrupting state. |
| **Readiness Invalidation** | Closing HTTP server immediately upon `SIGTERM` | Invalidate `/ready` $\rightarrow$ 503, **sleep 2–5s**, then close | In-flight LB requests receive connection refused (HTTP 502 Bad Gateway). |
| **Log Buffer Draining** | Exiting process without flushing log streams | Explicitly calling **`logger.flushSync()`** and tracer shutdown | Last 5–15 seconds of shutdown errors and traces are permanently lost. |
| **Resource Teardown Order** | Closing database pool before draining HTTP requests | **Drain HTTP requests first**, then close DB and cache pools | Active requests crash with "Database pool is closed" errors. |
| **Queue Consumer Handling** | Killing worker processes mid-job on shutdown | **Pause consumers**, wait for active jobs to checkpoint, then close | Message loss or duplicate processing due to unacknowledged broker jobs. |
| **Exit Code Semantics** | Calling `process.exit(0)` on timeout failures | Exit **code 0 on clean completion**, **code 1 on timeout/failure** | Orchestrator cannot distinguish clean rollouts from crashed services. |
