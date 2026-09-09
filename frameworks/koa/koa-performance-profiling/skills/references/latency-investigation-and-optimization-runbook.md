# Latency Investigation & Root Cause Runbook (3–4 Second Bottleneck Diagnosis)

## Overview
This runbook defines the systematic, evidence-based methodology for investigating and eliminating 3–4 second API latency bottlenecks in existing Koa + Node.js + Sequelize + MySQL applications.

---

## 1. The Anatomy of a 3.8-Second Request Breakdown

In JavaScript backends, CPU execution inside Node.js rarely exceeds 30–50ms. When an API takes 3–4 seconds, the delay is almost always localized in the database or connection layer:

```text
Total Request Latency: 3,800ms
├── Koa Middleware (Auth, CORS, Logging): 15ms  (0.4%)
├── Controller Validation & Parsing:      10ms  (0.3%)
├── Service Layer Business Logic:         25ms  (0.6%)
├── Sequelize ORM & MySQL Query Time:  3,400ms  (89.5%) 🔴 ROOT CAUSE
├── External Third-Party API Call:       300ms  (7.9%)
└── JSON Serialization & Network Write:   50ms  (1.3%)
```

---

## 2. Step-by-Step Diagnostic Protocol

### Step 1: Instrument Route Timing Breakdown
Mount `createTimingTracerMiddleware(500)` in `src/app.js`:
- Records high-resolution `process.hrtime.bigint()` duration.
- Emits structured JSON log event `http_request_finished` with `durationMs`.
- Tags response with `x-response-time: 3820ms` and `x-request-id`.

### Step 2: Instrument Sequelize Query Duration
Configure Sequelize with `benchmark: true`:
- Logs every SQL query exceeding **200ms**.
- Tags query with target model name, duration in ms, and sanitized query text.

### Step 3: Detect and Eliminate the Top 5 Database Bottlenecks

#### Bottleneck A: Missing Composite Indexes (Full Table Scans)
- **Symptom**: Query latency increases linearly as table size grows.
- **Diagnosis**: Extract raw SQL from log, run in MySQL: `EXPLAIN ANALYZE <SQL>;`.
- **Look for**: `type: ALL` (scanned 500,000 rows to return 20).
- **Remediation**: Add a composite B-Tree index covering the `WHERE` filters and `ORDER BY` sorting columns:
  ```sql
  CREATE INDEX idx_properties_status_branch_created 
  ON properties (status, branchId, createdAt DESC);
  ```

#### Bottleneck B: N+1 Query Cascades
- **Symptom**: 1 API request generates 51 database queries.
- **Diagnosis**: Loop iterating through parent records and querying child relations:
  ```javascript
  // ❌ N+1 ANTI-PATTERN:
  const properties = await Property.findAll();
  for (const prop of properties) {
    prop.branch = await Branch.findByPk(prop.branchId); // 50 separate queries!
  }
  ```
- **Remediation**: Use single eager loading query with indexed JOIN:
  ```javascript
  // ✅ OPTIMIZED:
  const properties = await Property.findAll({
    include: [{ model: Branch, as: 'branch', attributes: ['id', 'name'] }]
  });
  ```

#### Bottleneck C: Unbounded `SELECT *` and Heavy Blobs
- **Symptom**: Huge network payload between MySQL and Node.js process.
- **Diagnosis**: Fetching rich text descriptions, JSON metadata, or base64 images when only card titles and prices are displayed on the frontend.
- **Remediation**: Project strictly necessary columns using `attributes: ['id', 'title', 'price', 'slug']`.

#### Bottleneck D: Cartesian Product JOIN Explosion
- **Symptom**: Multiple `hasMany` relationships joined simultaneously (`include: [Images, Reviews, Agents]`) resulting in duplicated rows and high RAM usage.
- **Remediation**: Split into separate targeted queries or use subqueries.

#### Bottleneck E: MySQL Connection Pool Starvation
- **Symptom**: API takes 200ms when tested alone, but spikes to 4,000ms under 15 concurrent users.
- **Diagnosis**: `pool.max` is set too low (e.g. 5 connections), forcing incoming requests to queue in Node memory waiting for an available database socket.
- **Remediation**: Adjust `pool.max: 10` on 2GB RAM hosts. Ensure queries release connections immediately without open abandoned transactions.

---

## 3. The Before-and-After Verification Loop

Before deploying an optimization to production:
1. **Record Baseline**: Run k6 benchmark against staging (`p50`, `p95`, `p99`).
2. **Apply Index or Query Refactor**: Execute migration on staging MySQL.
3. **Verify with EXPLAIN ANALYZE**: Confirm row scan dropped from e.g. 250,000 rows to 20 rows.
4. **Re-Run k6 Benchmark**: Assert $p95$ reduced from 3.8s to $< 450\text{ms}$.
5. **Verify Zero Functional Regressions**: Run Vitest API & Integration test suites (`pnpm test`).
