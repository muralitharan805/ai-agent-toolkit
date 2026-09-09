# Developer Testing Playbook: How to Test a Koa Backend

## Overview
This playbook provides a comprehensive developer guide for writing, running, debugging, and generating reports & benchmarks in a Koa + Node.js + Sequelize + MySQL project.

---

## Step 1: Choose Your Test Database Setup

You can run your database integration tests in two ways based on your machine resources and project size:

```text
┌──────────────────────────────────────────────────────────────┐
│                    CHOOSE YOUR ENVIRONMENT                  │
├──────────────────────────────┬───────────────────────────────┤
│    MODE A: LOCAL NATIVE      │      MODE B: DOCKER CONTAINER │
│        (NO DOCKER)           │        (CONTAINERIZED)        │
├──────────────────────────────┼───────────────────────────────┤
│ • Zero CPU/RAM Docker daemon │ • Completely isolated schema  │
│ • Best for small projects    │ • tmpfs in-memory disk writes │
│ • Best for 2-core/2GB VMs    │ • Identical to CI pipeline    │
│ • Uses local MySQL service   │ • No local MySQL needed       │
└──────────────────────────────┴───────────────────────────────┘
```

---

### Setup Mode A: Local Native (Zero Docker Overhead)

Best when you already have MySQL installed locally (`sudo systemctl status mysql`) and want zero CPU/RAM overhead from Docker.

1. **One-Command Auto-Provision**:
   Run the bundled provisioning script:
   ```bash
   node tests/setup/setup-local-db.js
   ```
   *(This automatically creates `koa_app_test` database if it doesn't already exist).*

2. **Configure `.env.test`**:
   ```bash
   NODE_ENV=test
   TEST_DB_HOST=127.0.0.1
   TEST_DB_PORT=3306
   TEST_DB_USER=root
   TEST_DB_PASSWORD=your_local_password
   TEST_DB_NAME=koa_app_test
   ```

3. **Run Tests Directly**:
   ```bash
   pnpm test
   ```

---

### Setup Mode B: Docker Containerized (High Isolation)

Best for team projects where developers may not have MySQL installed locally, or when you want guaranteed parity with GitHub Actions CI.

1. **Start In-Memory Test Database (1 Command)**:
   ```bash
   docker compose -f tests/docker-compose.test.yml up -d
   ```
   *Note: Runs MySQL on port `3307` and mounts data in `tmpfs` (RAM), making disk writes and resets instant.*

2. **Configure `.env.test`**:
   ```bash
   NODE_ENV=test
   TEST_DB_HOST=127.0.0.1
   TEST_DB_PORT=3307
   TEST_DB_USER=test_user
   TEST_DB_PASSWORD=test_password
   TEST_DB_NAME=koa_app_test
   ```

3. **Teardown when finished**:
   ```bash
   docker compose -f tests/docker-compose.test.yml down
   ```

---

## Step 2: Configure Package Scripts

Add convenient automation scripts to your `package.json`:
```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:unit": "vitest run tests/unit",
    "test:integration": "vitest run tests/integration",
    "test:api": "vitest run tests/api",
    "test:ui": "vitest --ui",
    "test:k6:smoke": "docker compose -f tests/docker-compose.test.yml run --rm k6-smoke",
    "test:k6:load": "docker compose -f tests/docker-compose.test.yml run --rm k6-load",
    "test:k6:stress": "docker compose -f tests/docker-compose.test.yml run --rm k6-stress",
    "benchmark:verify": "python3 tests/performance/run_performance_benchmarks.py --summary-json k6-load-summary.json --max-p95 500"
  }
}
```

---

## Step 3: Writing a Unit Test (60–70% Target)

Unit tests test business logic with zero HTTP and zero database dependencies.

**File**: `tests/unit/services/commission.spec.js`
```javascript
const { describe, it, expect } = require('vitest');
const { calculateCommission } = require('../../../src/services/commission.service');

describe('calculateCommission (Unit)', () => {
  it('should calculate 2% commission on standard property sale', () => {
    // 1. Arrange
    const salePrice = 300000;
    const rate = 2.0;

    // 2. Act
    const result = calculateCommission(salePrice, rate);

    // 3. Assert
    expect(result).toBe(6000);
  });

  it('should throw an error when sale price is negative', () => {
    expect(() => calculateCommission(-100, 2)).toThrow(/must be positive/i);
  });
});
```

---

## Step 4: Writing a Database Integration Test (20–30% Target)

Database integration tests verify Sequelize models, constraints, and relationships against real MySQL using transaction rollbacks.

**File**: `tests/integration/models/property.spec.js`
```javascript
const { describe, it, expect, beforeEach, afterEach, afterAll } = require('vitest');
const { testSequelize } = require('../../setup/database');
const { Property } = require('../../../src/models/property.model');

describe('Property Model (Database Integration)', () => {
  let transaction;

  beforeEach(async () => {
    // Begin transaction for complete test isolation
    transaction = await testSequelize.transaction();
  });

  afterEach(async () => {
    // Revert all database mutations made during this test
    await transaction.rollback();
  });

  afterAll(async () => {
    // Close pool so Vitest process exits cleanly
    await testSequelize.close();
  });

  it('should persist a valid property and auto-generate primary key', async () => {
    const property = await Property.create(
      { title: 'Seaside Villa', price: 750000, status: 'AVAILABLE' },
      { transaction }
    );

    expect(property.id).toBeDefined();
    expect(property.title).toBe('Seaside Villa');
  });

  it('should fail when creating property with duplicate slug', async () => {
    await Property.create(
      { title: 'Penthouse', slug: 'unique-penthouse', price: 500000 },
      { transaction }
    );

    await expect(
      Property.create(
        { title: 'Another Penthouse', slug: 'unique-penthouse', price: 600000 },
        { transaction }
      )
    ).rejects.toThrow(/unique/i);
  });
});
```

---

## Step 5: Writing an API Route Test with Supertest (10–15% Target)

API route tests test the complete Koa onion pipeline: routing, auth middleware, validation, controllers, and error formatting.

**File**: `tests/api/properties/create-property.spec.js`
```javascript
const { describe, it, expect, beforeAll, afterAll } = require('vitest');
const request = require('supertest');
const { createTestApp } = require('../../setup/app');
const { getAuthHeader } = require('../../fixtures/auth.fixture');
const { testSequelize } = require('../../setup/database');

describe('POST /api/properties (API Route Test)', () => {
  let app;

  beforeAll(async () => {
    app = createTestApp();
    // Mount your actual Koa router
    const propertyRouter = require('../../../src/routes/property.routes');
    app.use(propertyRouter.routes());
  });

  afterAll(async () => {
    await testSequelize.close();
  });

  it('should return 401 when Authorization header is omitted', async () => {
    const res = await request(app.callback())
      .post('/api/properties')
      .send({ title: 'Loft', price: 250000 });

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('should return 400 when title is missing in payload', async () => {
    const authHeader = getAuthHeader({ role: 'AGENT' });

    const res = await request(app.callback())
      .post('/api/properties')
      .set(authHeader)
      .send({ price: 250000 }); // Missing title

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
  });

  it('should return 201 and created resource when payload is valid', async () => {
    const authHeader = getAuthHeader({ role: 'AGENT' });

    const res = await request(app.callback())
      .post('/api/properties')
      .set(authHeader)
      .send({ title: 'Sunny Apartment', price: 320000 });

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.title).toBe('Sunny Apartment');
  });
});
```

---

## Step 6: Mocking Third-Party External APIs

When a service calls external HTTP endpoints (e.g. Stripe payment, SendGrid email), mock outbound calls to keep tests reliable and offline.

**File**: `tests/unit/services/payment.spec.js`
```javascript
const { describe, it, expect, beforeEach } = require('vitest');
const { createExternalApiMock } = require('../../mocks/external-api.mock');
const { PaymentService } = require('../../../src/services/payment.service');

describe('PaymentService - External Gateway Integration', () => {
  let mockHttpClient;
  let paymentService;

  beforeEach(() => {
    mockHttpClient = createExternalApiMock();
    paymentService = new PaymentService(mockHttpClient);
  });

  it('should process charge successfully when gateway returns 200', async () => {
    mockHttpClient.mockSuccess({ id: 'ch_123', status: 'succeeded' });

    const result = await paymentService.charge({ amount: 5000, currency: 'gbp' });

    expect(result.success).toBe(true);
    expect(result.chargeId).toBe('ch_123');
  });

  it('should gracefully handle gateway timeout', async () => {
    mockHttpClient.mockTimeout();

    await expect(
      paymentService.charge({ amount: 5000, currency: 'gbp' })
    ).rejects.toThrow(/Gateway Timeout/i);
  });
});
```

---

## Step 7: How to Run and Debug Tests

### Run all tests
```bash
pnpm test
```

### Run while developing (Watch Mode)
Vitest automatically re-runs only affected tests on file save:
```bash
pnpm test:watch
```

### Run a single test file
```bash
pnpm vitest run tests/api/properties/create-property.spec.js
```

### Filter tests by description name
```bash
pnpm vitest run -t "should return 401"
```

---

## Step 8: Generating Test Coverage Reports

Generate line-by-line coverage metrics to discover untested edge cases:

```bash
pnpm test:coverage
```

### Output Files Generated:
1. **Terminal Table Output**: Instant summary on stdout with Statements, Branches, Functions, and Lines percentages.
2. **Interactive HTML Report**: Saved in `coverage/index.html`. Open it in any browser:
   ```bash
   xdg-open coverage/index.html   # Linux
   open coverage/index.html       # macOS
   ```
   *Features: Visual red/green highlighting of exact lines and conditions that were not executed during tests.*
3. **CI Machine-Readable JSON**: Saved in `coverage/coverage-final.json` for automated tracking in PRs.

---

## Step 9: Using the Visual Vitest UI Dashboard

Start the interactive visual test runner:
```bash
pnpm test:ui
```
Opens an in-browser interface (`http://localhost:51204/__vitest__/`) that provides:
- Live file tree showing passing and failing specs.
- Execution speed breakdown per test file in milliseconds.
- Visual component call stack and console log inspector.
- Instant re-run buttons for specific failed assertions.

---

## Step 10: Generating Performance Benchmark Reports (k6)

Run the load test suite to benchmark your API endpoints under concurrent traffic without needing any host k6 installation:

```bash
# Run quick smoke test via Docker Compose (5 VUs, 30s)
pnpm test:k6:smoke

# Run full baseline & peak load test (25 VUs, 2m)
pnpm test:k6:load

# Run stress test to find breaking points (50 VUs)
pnpm test:k6:stress
```

### Output Reports Generated:
1. **Interactive HTML Dashboard (`k6-report.html`)**:
   Automatically generated by the bundled `handleSummary` hook. Open it in a browser to see:
   - Full latency distribution curves ($p50$, $p90$, $p95$, $p99$).
   - Request throughput graphs (Requests per Second vs Virtual Users).
   - Failed request rates and response status breakdowns.
2. **Machine-Readable JSON (`k6-summary.json`)**:
   Contains all raw timing metrics for automated parsing.
3. **Automated SLA Regression Verification**:
   Run the evaluation CLI to assert production thresholds:
   ```bash
   pnpm benchmark:verify
   ```
   *Passes with exit code `0` if $p95 < 500\text{ms}$ and error rate $< 1\%$; fails the build otherwise.*
