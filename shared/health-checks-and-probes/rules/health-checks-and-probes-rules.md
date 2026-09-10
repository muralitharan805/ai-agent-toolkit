---
trigger: model_decision
description: "Enforces Kubernetes and load balancer health check probe standards (/live, /ready, /startup, /health/details), strict liveness vs readiness separation, degraded 503 handling, and diagnostic endpoint IP restriction."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Health Checks & Probes Architecture Standards

## Description
Enforces resilient, production-grade health check probe architecture across all backend services, containerized workloads, and Kubernetes deployments. Establishes the mandatory operational separation between process liveness (`/live`), dependency readiness (`/ready`), warmup completion (`/startup`), and diagnostic telemetry (`/health/details`). Strictly prevents cascading restart loops caused by probing external dependencies in liveness checks, enforces HTTP 503 responses on degraded readiness, and mandates IP restrictions for deep diagnostic endpoints.

## Constraints

### 1. Mandatory Separation of Liveness and Readiness Probes
- Production backend applications MUST provide dedicated, distinct HTTP probe routes for process liveness and traffic readiness:
  1. **Liveness Probe (`GET /live`)**: Answers "Is the process event loop alive and responsive?".
  2. **Readiness Probe (`GET /ready`)**: Answers "Can the application currently accept and process user traffic?".
  3. **Startup Probe (`GET /startup`)**: Answers "Has the initial heavy bootstrap / cache warmup finished?".
- Merging liveness and readiness into a single `/health` endpoint that fails when external databases hiccup is STRICTLY FORBIDDEN.

### 2. Zero External I/O in Liveness Probe (`GET /live`)
- The `/live` endpoint MUST NOT perform database queries, Redis pings, network calls, or disk I/O operations.
- The `/live` handler MUST return HTTP `200 OK` immediately if the process runtime and event loop are responsive.
- **Rationale**: If a database experiences transient latency or downtime, a liveness check querying the database will fail, prompting the container orchestrator (Kubernetes, ECS) to kill and restart every container replica simultaneously. This creates a catastrophic cascading restart stampede across the entire cluster.

### 3. Comprehensive Dependency Evaluation in Readiness (`GET /ready`)
- The `/ready` endpoint MUST evaluate the availability of critical upstream backing services before acknowledging readiness:
  - Database connection ping (e.g. `SELECT 1` with a strict 1000ms timeout).
  - Cache connection ping (e.g. Redis `PING` with a strict 500ms timeout).
  - Message broker connection state.
- **Status Code Requirement**:
  - Return HTTP `200 OK` when all critical backing services are connected and responsive.
  - Return HTTP `503 Service Unavailable` immediately if any critical dependency fails or times out.
- A 503 response instructs ingress controllers, Kubernetes kube-proxy, and cloud load balancers to immediately detach the replica from active traffic distribution without restarting the process.

### 4. Startup Warmup Protection (`GET /startup`)
- Applications with non-trivial cold start times (e.g., loading in-memory caches, machine learning model weights, pre-compiling templates) MUST expose a `/startup` probe.
- The `/startup` probe returns HTTP `200 OK` only after initial bootstrap sequence and warmup routines complete.
- Orchestrators use startup probes to disable liveness and readiness failures during cold boot, eliminating false-positive restart loops.

### 5. Protected Diagnostic Endpoint (`GET /health/details`)
- Detailed diagnostic endpoints exposing component health, dependency round-trip latencies, service version, and server uptime MUST NOT be exposed publicly to the internet.
- `/health/details` MUST be restricted to internal VPC subnets, orchestrator probes, or protected by basic authentication / mutual TLS.
- Diagnostic response payloads MUST follow standard telemetry structure:
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-09-10T08:30:00Z",
    "version": "1.0.0",
    "uptime": 86400,
    "checks": {
      "database": { "status": "healthy", "responseTimeMs": 4 },
      "redis": { "status": "healthy", "responseTimeMs": 1 }
    }
  }
  ```

### 6. Strict Probe Timeout & Frequency Budgets
- Health check endpoints MUST enforce aggressive internal execution timeouts:
  - Database health ping: $\le 1000\text{ ms}$.
  - Redis health ping: $\le 500\text{ ms}$.
  - Total probe handler timeout: $\le 2000\text{ ms}$.
- Probe handlers MUST NOT execute expensive unbounded operations (such as table scans, `SELECT COUNT(*)`, or heavy filesystem traversals).

## Examples

### 1. Dangerous Liveness Probe vs. Correct Liveness Isolation

```typescript
// ❌ CRITICAL ANTI-PATTERN: Querying database inside liveness check
// If DB has 10s latency, K8s restarts all replicas, taking the entire fleet down!
app.get('/live', async (req, res) => {
  try {
    await db.query('SELECT 1'); // FORBIDDEN IN LIVENESS!
    res.status(200).send('OK');
  } catch (err) {
    res.status(500).send('DB Dead');
  }
});

// ✅ CORRECT: Pure process event loop liveness
app.get('/live', (req, res) => {
  // If the server process is alive and event loop can process this request, return 200 immediately
  res.status(200).json({ status: 'alive' });
});
```

### 2. Production Readiness Probe with 503 Degraded Handling

```typescript
// ✅ CORRECT: Evaluates dependencies with timeouts and returns 503 on failure
app.get('/ready', async (req, res) => {
  const isShuttingDown = lifecycleManager.isDraining();
  if (isShuttingDown) {
    return res.status(503).json({ status: 'draining', message: 'Server is terminating' });
  }

  const [dbHealthy, redisHealthy] = await Promise.all([
    checkDatabaseWithTimeout(1000),
    checkRedisWithTimeout(500),
  ]);

  if (dbHealthy && redisHealthy) {
    return res.status(200).json({ status: 'ready' });
  }

  // Instructs Load Balancer / K8s to stop routing incoming traffic to this replica
  return res.status(503).json({
    status: 'not_ready',
    dependencies: {
      database: dbHealthy ? 'up' : 'down',
      redis: redisHealthy ? 'up' : 'down',
    },
  });
});
```
