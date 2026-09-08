---
description: "Enforces strict testing pyramid boundaries, Vitest and Supertest correctness suites, real Sequelize MySQL integration, transaction rollbacks, k6 performance SLAs, and request-level query profiling for Koa Node.js backends."
trigger: model_decision
---
# Koa Testing Architecture and Performance Profiling Standards

## Description
This rule enforces enterprise testing architecture, database transaction safety, request observability, brownfield safety, and continuous performance profiling for existing production Koa + Node.js backends using Sequelize and MySQL. It defines strict boundaries between unit, integration, and API tests, bans mocking database queries for relational logic, mandates non-destructive transaction rollbacks, enforces sub-second latency SLAs under concurrency, and establishes request timing and slow-query instrumentation for constrained production environments (e.g. 2-core / 2GB RAM instances).

## Constraints

### 1. Brownfield Safety & Port Decoupling
- Tests MUST NOT modify production configuration or run destructive migrations against non-test databases.
- The application MUST separate Koa instance creation (`createApp()`) from HTTP listener initialization (`server.listen()`) so Supertest can test `app.callback()` directly without binding network ports or interfering with live PM2 processes.
- Test suites MUST execute exclusively against an isolated test database (`koa_app_test`).

### 2. Risk-Weighted Pyramid & P0–P3 Prioritization
- APIs MUST be prioritized by operational risk before writing tests:
  - **P0 (Critical)**: Authentication, financial transactions, core mutations.
  - **P1 (High)**: High-traffic read routes and critical business logic.
  - **P2 / P3 (Medium / Low)**: Utility endpoints and low-frequency queries.
- Test distribution MUST adhere to risk coverage:
  - **Unit Tests (60–70%)**: Business logic, calculations, data mappings. Zero I/O, purely in-memory.
  - **Database Integration (20–30%)**: Real Sequelize models against isolated MySQL test DB with transaction rollbacks.
  - **API Tests (10–15%)**: Critical route pipelines tested via Supertest wrapping `app.callback()`.

### 3. Prohibition of Database Mocking in Critical Workflows
- Engineers MUST NOT mock Sequelize models (`vi.mock`) when verifying business transactions, cascading updates, foreign keys, or relational queries.
- Integration tests MUST wrap operations inside a Sequelize transaction and rollback changes in `afterEach()`, or execute deterministic table truncation in a centralized setup hook.

### 4. Security & Access Control Test Scenarios
- **Authentication**: Protected routes MUST assert `401 Unauthorized` on missing, malformed, or expired tokens, and `200 OK` with valid signed JWTs.
- **Authorization & RBAC**: Routes MUST test matrix boundaries across all roles (e.g. Admin permitted, Agent restricted, Public denied).
- **IDOR Prevention**: Endpoints accepting resource IDs (e.g. `GET /api/properties/:id`) MUST verify that User A cannot access User B's resource, asserting `403 Forbidden` or `404 Not Found`.

### 5. Deterministic Error Contracts & Input Validation
- Controller routes MUST test input validation boundaries (missing fields, boundary values, invalid types).
- Error responses MUST strictly match the project error contract (`{ success: false, message: string, code?: string }`). Stack traces MUST NEVER leak in test assertions or production payloads.

### 6. Request Tracing & Correlation Propagation
- Applications MUST register a correlation middleware generating or forwarding an `x-request-id` header (UUID v4).
- The correlation ID MUST attach to Koa's `ctx.state.requestId` and propagate into structured logs and response headers.
- Route execution duration MUST be logged in whole milliseconds (`durationMs`) upon completion.

### 7. Sequelize Query Profiling & Evidence-Based Indexing
- Development and staging environments MUST activate Sequelize query duration profiling (`benchmark: true`).
- Any query exceeding **200ms** MUST trigger a structured `WARN` log with SQL and duration.
- Proposed indexes MUST be validated with MySQL `EXPLAIN ANALYZE` demonstrating elimination of full table scans (`type: ALL`) or disk filesorts.

### 8. Performance SLA Thresholds & Safe k6 Testing
- Aggressive k6 stress/spike tests MUST NEVER run directly against production environments.
- Standard read endpoints MUST maintain a 95th percentile latency ($p95$) of less than **500ms** under 25 concurrent users.
- Complex search endpoints MUST maintain $p95 < 1000\text{ms}$. Regressions (> 20% increase in $p95$) MUST fail deployment quality gates.

### 9. Constrained Resource Optimization (2-Core / 2GB VMs)
- PM2 single worker vs cluster mode (2 workers) MUST be benchmarked before production deployment to prevent memory thrashing.
- MySQL connection pool size MUST NOT exceed 10 connections per Node process on 2GB hosts.
- Test suites MUST drain database connections in `afterAll()` hooks via `sequelize.close()`.

### 10. Clean Code & JSDoc Standards in JavaScript
- Code written in JavaScript MUST use clear naming and JSDoc annotations documenting parameters and return types.
- Test descriptions MUST describe real business behavior (e.g. `it('should return 401 when token is expired')`).
- Tests MUST NOT leave orphaned records or open timers.

## Examples

### 1. Supertest API & IDOR Security Test with Koa (JavaScript)
```javascript
const { describe, it, expect, beforeAll, afterAll } = require('vitest');
const request = require('supertest');
const { app } = require('../../src/app');
const { generateAuthToken } = require('../helpers/auth.helper');
const { createTestProperty } = require('../fixtures/property.fixture');
const { sequelize } = require('../../src/database');

describe('Property API - Authorization & Security', () => {
  let userAToken;
  let userBToken;
  let userAPropertyId;

  beforeAll(async () => {
    userAToken = generateAuthToken({ userId: 101, role: 'AGENT' });
    userBToken = generateAuthToken({ userId: 102, role: 'AGENT' });
    const property = await createTestProperty({ ownerId: 101, title: 'Luxury Suite' });
    userAPropertyId = property.id;
  });

  afterAll(async () => {
    await sequelize.close();
  });

  it('should return 401 when authorization header is missing', async () => {
    const res = await request(app.callback()).get(`/api/properties/${userAPropertyId}`);
    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('should prevent User B from deleting User A property (IDOR protection)', async () => {
    const res = await request(app.callback())
      .delete(`/api/properties/${userAPropertyId}`)
      .set('Authorization', `Bearer ${userBToken}`);

    expect(res.status).toBe(403);
    expect(res.body.success).toBe(false);
  });
});
```

### 2. Sequelize Transaction Rollback Integration Test (JavaScript)
```javascript
const { describe, it, expect, beforeEach, afterEach } = require('vitest');
const { sequelize } = require('../../src/database');
const { PropertyService } = require('../../src/services/property.service');

describe('PropertyService - Database Transaction Guarantees', () => {
  let transaction;
  let propertyService;

  beforeEach(async () => {
    transaction = await sequelize.transaction();
    propertyService = new PropertyService(transaction);
  });

  afterEach(async () => {
    await transaction.rollback();
  });

  it('should rollback property creation when branch assignment fails', async () => {
    const invalidPayload = { title: 'City Penthouse', price: 500000, branchId: 999999 };
    await expect(propertyService.createProperty(invalidPayload)).rejects.toThrow();

    const count = await sequelize.models.Property.count({
      where: { title: 'City Penthouse' },
      transaction,
    });
    expect(count).toBe(0);
  });
});
```
