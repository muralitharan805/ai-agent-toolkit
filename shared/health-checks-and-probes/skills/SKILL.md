---
name: health-checks-and-probes
description: "Implements and audits Kubernetes and load balancer health check probes (/live, /ready, /startup, /health/details), strict liveness vs readiness isolation, and degraded 503 status handling. Triggered by 'health-check:', 'liveness:', 'readiness:', or '/health-checks-and-probes'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Health Checks & Probes Architecture Skill

## Overview

This skill establishes the production engineering protocol for **Kubernetes and Load Balancer Health Probes** across containerized backend services. It guarantees clear operational isolation between process liveness (`/live`), backing service readiness (`/ready`), warmup completion (`/startup`), and deep diagnostic inspection (`/health/details`). Following this standard prevents catastrophic cascading restart loops and thundering herd outages.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Health Probe Pipeline                        │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Pure Liveness /live]     ──► Event loop responsiveness (Zero external I/O)
                │
  [Phase 2: Readiness /ready]        ──► Backing service pings + 503 on degradation
                │
  [Phase 3: Startup /startup]        ──► Warmup guard against premature cold kills
                │
  [Phase 4: Diagnostics /details]    ──► Internal diagnostic breakdown + IP whitelist
                │
  [Phase 5: Conformance Audit]       ──► Run audit_health_probes.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Pure Process Liveness (`GET /live`)
1. **Zero External I/O Invariant**:
   - The `/live` endpoint must NEVER query databases, ping caches, or execute network calls.
   - If the runtime event loop can process the HTTP request, return HTTP `200 OK` immediately:
     ```typescript
     router.get('/live', (_req, res) => {
       res.status(200).json({ status: 'alive' });
     });
     ```
2. **Failure Semantics**:
   - In Kubernetes, a failed liveness probe causes the kubelet to issue `SIGTERM`/`SIGKILL` to restart the container. External database downtime must NEVER trigger process restarts.

### Phase 2: Dependency Readiness Probe (`GET /ready`)
1. **Evaluate Critical Backing Services**:
   - Run lightweight ping checks in parallel with strict execution timeouts:
     - Database: `SELECT 1` (timeout: $\le 1000\text{ ms}$)
     - Redis / Cache: `PING` (timeout: $\le 500\text{ ms}$)
2. **HTTP 503 on Failure**:
   - Return HTTP `200 OK` only when all critical dependencies are healthy.
   - Return HTTP `503 Service Unavailable` if any critical dependency fails or times out.
3. **Connection Draining Guard**:
   - If the service process received a termination signal (`SIGTERM`) and is draining connections, `/ready` MUST immediately return `503` so load balancers detach the instance.

### Phase 3: Startup Warmup Probe (`GET /startup`)
1. **Cold Boot Guard**:
   - If the service executes non-trivial bootstrap routines (e.g. database schema migrations, caching warmups, loading ML models), expose `GET /startup`.
   - Return `503` during startup routines, and `200` once initialization concludes.

### Phase 4: Protected Diagnostics (`GET /health/details`)
1. **Comprehensive Breakdown**:
   - Expose uptime, git commit hash/version, and per-dependency round-trip response times in milliseconds.
2. **Access Restriction**:
   - Restrict `/health/details` to internal VPC subnets or require administrative authentication headers. Never expose deep diagnostics to public traffic.

### Phase 5: Conformance Audit
1. Run the health probe auditor across the codebase:
   ```bash
   python3 shared/health-checks-and-probes/skills/scripts/audit_health_probes.py ./src --strict
   ```
2. Confirm zero external I/O in `/live`, presence of `/ready`, and correct `503` error handling.

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [Health Check Probes & Container Orchestration Lifecycle](references/health-probes-and-kubernetes-lifecycle.md) for Kubernetes failure cascading analysis, thundering herd scenarios, and probe timeout budgets.
- **Production Template**: Review [health-check-orchestrator.template.ts](assets/health-check-orchestrator.template.ts) for full TypeScript implementation of the 4 endpoints.
- **CLI Auditor**: Execute [audit_health_probes.py](scripts/audit_health_probes.py) to audit repository compliance.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Querying database inside `/live` | Keep `/live` purely in-process; test database in `/ready` only | Database blips cause K8s to kill every container at once (cascading cluster outage). |
| Returning `200 OK` with `{ status: "degraded" }` in `/ready` | Return HTTP `503 Service Unavailable` on any critical dependency failure | Load balancers only inspect HTTP status codes; they will continue sending traffic to broken pods. |
| Exposing detailed internal diagnostics publicly | Restrict `/health/details` via IP whitelist / reverse-proxy ACLs | Leaks internal infrastructure topology, connection latencies, and service versions to attackers. |
| Expensive table scans in health probes (`SELECT COUNT(*) FROM users`) | Minimal lightweight ping query (`SELECT 1`) with $\le 1000\text{ms}$ timeout | Frequent probe scraping adds heavy CPU and connection load to production databases. |
| Missing `/startup` probe for slow-starting applications | Configure Kubernetes `startupProbe` with adequate failureThreshold | Kubelet kills slow-starting containers before they can complete initialization. |
