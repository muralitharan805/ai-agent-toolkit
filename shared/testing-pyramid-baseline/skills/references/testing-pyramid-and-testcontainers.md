# Testing Pyramid & Testcontainers Architectural Reference

## Overview
This reference establishes the engineering principles and architectural patterns for implementing a robust, deterministic, and fast enterprise test suite. It details the **60/30/10 Testing Pyramid**, **Testcontainers Docker Lifecycle**, **Transaction Rollback Isolation**, **Post-Deployment Smoke Testing**, and **k6 Performance Benchmarking**.

---

## 1. Testing Pyramid Architecture & Layer Distribution

```
                    /\
                   /  \
                  / E2E \           → 10% (Deployment Smoke & Critical Path)
                 /--------\
                / Integration\      → 30% (Real DB & Redis via Testcontainers)
               /--------------\
              /   Unit Tests    \   → 60% (Fast, Isolated, In-Memory Mocks)
             /──────────────────\
```

### Layer Characteristics

| Layer | Proportion | Execution Target | Infrastructure Dependencies | Primary Objective |
| :--- | :--- | :--- | :--- | :--- |
| **Unit Tests** | ~60% | < 1ms per test | Zero external I/O (in-memory mocks) | Business logic, DTO validation, algorithms |
| **Integration Tests** | ~30% | 50ms–500ms per test | Ephemeral Docker containers (Testcontainers) | HTTP routing, DB queries, cache interactions |
| **E2E / Smoke Tests** | ~10% | 1s–5s per test | Deployed staging/production environment | Post-deploy sanity, critical user journeys |
| **Performance Tests** | Continuous/Nightly | Variable load profiles | Isolated performance testing cluster | Latency SLAs (p95 < 200ms), throughput, leaks |

---

## 2. Unit Testing Isolation & Coverage Thresholds

### Core Invariants
1. **Zero External I/O**:
   - Never initiate real HTTP requests, database connections, Redis queries, or filesystem writes in unit tests.
   - Inject verified mock implementations via constructor/functional dependency injection.
2. **Deterministic Execution**:
   - Never use non-deterministic sources (unseeded `Math.random()`, real system clock `Date.now()`).
   - Mock system timers with test runner utilities (`jest.useFakeTimers()`, `vi.useFakeTimers()`).
3. **CI Coverage Gates**:
   - Enforce minimum thresholds in test runner configuration:
     - Lines: $\ge 80\%$
     - Branches: $\ge 75\%$
     - Functions: $\ge 80\%$
     - Statements: $\ge 80\%$

```typescript
// vitest.config.ts / jest.config.ts coverage gate configuration
export default {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'json', 'lcov'],
    thresholds: {
      lines: 80,
      branches: 75,
      functions: 80,
      statements: 80,
    },
  },
};
```

---

## 3. Testcontainers Integration Testing Architecture

### Why In-Memory Database Mocks Are Forbidden
- Mocking databases with SQLite, H2, or in-memory arrays introduces severe semantic drift:
  - Dialect discrepancies (e.g. PostgreSQL JSONB operators `->>`, array columns, UUID generation).
  - Transaction isolation semantics and locking behaviors differ from production.
  - Foreign key cascades and constraint checks behave inconsistently.
- **Production Standard**: Execute integration tests against real PostgreSQL and Redis instances hosted in ephemeral Docker containers via the Testcontainers library.

### Testcontainers Singleton Lifecycle
To avoid container startup overhead on every test file, implement a singleton container manager:

```
[Test Runner Start]
        │
        ▼
[TestcontainersManager.init()]
        ├─► Spin up PostgreSQL Container (e.g. postgres:16-alpine)
        ├─► Spin up Redis Container (e.g. redis:7-alpine)
        ├─► Apply Database Migrations (e.g. Prisma / Knex / Liquibase)
        └─► Export Dynamic Connection Strings to Global Test Config
        │
        ▼
[Run Integration Test Files in Parallel/Serial]
        │
        ▼
[Test Runner Completion] ──► Testcontainers automatic Ryuk cleanup
```

### Transaction Rollback Isolation
Instead of slow table truncations (`TRUNCATE TABLE`) between tests, execute every test inside a dedicated transaction that unconditionally rolls back:

```typescript
/**
 * Executes a test block within an isolated transaction that rolls back automatically.
 *
 * @param dbPool - PostgreSQL connection pool
 * @param testFn - Test callback receiving an active client in a transaction
 */
export async function withRollbackTransaction(
  dbPool: Pool,
  testFn: (client: PoolClient) => Promise<void>
): Promise<void> {
  const client = await dbPool.connect();
  try {
    await client.query('BEGIN');
    await testFn(client);
  } finally {
    await client.query('ROLLBACK');
    client.release();
  }
}
```

---

## 4. Post-Deployment Smoke Testing Gate

### Smoke Test Sequence
Smoke tests execute immediately post-rollout before switching live traffic in Blue/Green or Canary deployments.

```bash
#!/usr/bin/env bash
set -euo pipefail

TARGET_BASE_URL="${1:-https://staging.api.example.com}"
echo "Running post-deploy smoke tests against: ${TARGET_BASE_URL}"

# 1. Verify /health/ready returns 200 with all dependencies UP
READY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${TARGET_BASE_URL}/api/v1/health/ready")
if [ "${READY_STATUS}" != "200" ]; then
  echo "❌ FAILED: Health readiness returned ${READY_STATUS}"
  exit 1
fi
echo "✅ Health check passed."

# 2. Verify security error contract on unauthenticated endpoint
AUTH_ERROR_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TARGET_BASE_URL}/api/v1/protected/resource")
if [ "${AUTH_ERROR_CODE}" != "401" ]; then
  echo "❌ FAILED: Unauthenticated access returned ${AUTH_ERROR_CODE} instead of 401"
  exit 1
fi
echo "✅ Security contract passed."

# 3. Verify critical path login and authenticated ping
echo "✅ All smoke tests passed successfully."
```

---

## 5. Performance & Load Testing with k6

### Performance Test Profiles

| Profile | Concurrency | Duration | Objective |
| :--- | :--- | :--- | :--- |
| **Load Test** | 1x normal traffic (e.g. 50 VUs) | 10–30 minutes | Validate baseline SLA compliance under standard traffic. |
| **Stress Test** | 2x–5x peak traffic (e.g. 500 VUs) | 15–30 minutes | Identify database connection saturation, OOM, and CPU bottlenecks. |
| **Spike Test** | Instant jump from 10 to 1000 VUs | 2–5 minutes | Verify autoscaling triggers, rate limiting, and recovery speed. |
| **Soak Test** | Moderate load (e.g. 100 VUs) | 4–12 hours | Detect gradual memory leaks, connection pool leaks, and disk exhaustion. |

### Concrete SLA Threshold Definitions
```javascript
export const options = {
  thresholds: {
    // Latency percentiles
    'http_req_duration{status:200}': [
      'p(50)<50',   // 50% of requests must complete under 50ms
      'p(95)<200',  // 95% of requests must complete under 200ms
      'p(99)<500',  // 99% of requests must complete under 500ms
    ],
    // Reliability threshold
    'http_req_failed': ['rate<0.001'], // Less than 0.1% HTTP 5xx failures
  },
};
```
