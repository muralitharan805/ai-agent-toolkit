# Health Check Probes & Container Orchestration Lifecycle

## Overview

In modern containerized deployments (Kubernetes, AWS ECS, Google Cloud Run, Nomad), orchestrators rely on automated health probes to make routing and lifecycle decisions. Improperly configured health checks are a leading cause of cluster-wide cascading outages.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Container Orchestrator Probe Semantics                    │
└──────────────────────────────────────────────────────────────────────────────┘
  Probe Type       Question Answered            Action on Failure
  ──────────       ─────────────────            ─────────────────
  GET /live        Is the process alive?        RESTART container (SIGTERM/SIGKILL)
  GET /ready       Can it serve user traffic?   DETACH from Load Balancer (No restarts)
  GET /startup     Has cold boot completed?     PAUSE liveness/readiness checks
  GET /health/...  Deep diagnostics             Telemetry only (No automated actions)
```

---

## The "Cascading Outage" Stampede

### The Anti-Pattern
A service embeds a database query (`SELECT 1`) inside the `/live` liveness probe.

```
[Database under heavy load or network blip]
                  │
                  ▼
[App replica A liveness probe queries DB → Timeouts after 2s]
                  │
                  ▼
[Kubernetes marks Replica A as DEAD → Kills container & starts new one]
                  │
                  ▼
[Replicas B, C, D, E also timeout on DB queries → All killed simultaneously]
                  │
                  ▼
[All replicas boot at once → Cold start creates thundering herd against DB]
                  │
                  ▼
[Database permanently overwhelmed → Entire production system down]
```

### The Invariant
- **Liveness probes MUST test process responsiveness ONLY**.
- If a database goes down, the application process is NOT dead. Restarting the application cannot fix the database.
- Instead, the **Readiness probe** (`/ready`) MUST fail, which cleanly detaches the application from load balancer ingress routing without restarting the container.

---

## Probe Specifications

### 1. Liveness Probe (`GET /live`)
- **Execution Target**: Immediate response (< 10ms).
- **Checks**: Node.js event loop lag, basic memory threshold.
- **Forbidden**: Database queries, Redis calls, file writes, remote HTTP requests.
- **Success Status**: `200 OK`.
- **Failure Condition**: Process hung, deadlock, event loop frozen > 5s.

### 2. Readiness Probe (`GET /ready`)
- **Execution Target**: Low latency (< 1000ms).
- **Checks**:
  - Primary database connection pool responsive.
  - Redis cache ping responsive.
  - Graceful shutdown state: If server received `SIGTERM` and is draining connections, `/ready` MUST return `503`.
- **Success Status**: `200 OK`.
- **Failure Status**: `503 Service Unavailable`.
- **Orchestrator Behavior**: Removes Pod IP from Service Endpoints / Load Balancer Target Group. Active connections finish draining; no new requests arrive.

### 3. Startup Probe (`GET /startup`)
- **Target**: Protects services with long warmup times (e.g. 30s–60s) from being killed prematurely by liveness probes.
- **Checks**: Configuration loaded, schema migrations verified, cache warm, initial model weights loaded into memory.
- **Configuration in Kubernetes**:
  ```yaml
  startupProbe:
    httpGet:
      path: /startup
      port: 8080
    failureThreshold: 30
    periodSeconds: 2
  ```

### 4. Diagnostic Endpoint (`GET /health/details`)
- **Payload**: Comprehensive health status with per-dependency breakdown, response time in milliseconds, uptime, and git commit SHA.
- **Security Constraint**: Must be restricted by IP whitelist, basic auth, or deployed on an internal administrative management port (e.g. `9090`).
