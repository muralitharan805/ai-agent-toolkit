---
trigger: model_decision
description: "Enforces testing pyramid ratio (60% unit, 30% integration, 10% E2E/smoke), Testcontainers isolation with transaction rollback, deterministic seeding, CI coverage thresholds (80% line, 75% branch), and k6 performance SLA baselines."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Testing Pyramid Baseline Standards

## Description
Enforces the enterprise testing pyramid ratio (60% Unit, 30% Integration, 10% E2E/Smoke), strict unit test isolation without real external I/O, production-parity integration testing via Testcontainers with transaction rollback isolation, automated post-deployment smoke tests, deterministic seeding, and k6 performance testing against concrete latency and error rate SLAs. Mandates CI/CD coverage thresholds of minimum 80% line coverage and 75% branch coverage.

## Constraints

### 1. Testing Pyramid Distribution Invariant
- Test suites MUST adhere to the enterprise testing pyramid distribution:
  - **Unit Tests (~60%)**: Fast, isolated execution testing domain logic, validation schemas, and utility transformations.
  - **Integration Tests (~30%)**: Real HTTP controller $\rightarrow$ service $\rightarrow$ database/cache roundtrips against real containerized infrastructure via Testcontainers.
  - **End-to-End (E2E) & Smoke Tests (~10%)**: Critical user journey verification and deployment smoke tests validating real deployed environments.
- Inverted test pyramids ("ice cream cone" anti-pattern with heavy E2E tests and few unit tests) are STRICTLY FORBIDDEN due to execution cost, slow CI cycle times, and flakiness.

### 2. Unit Test Purity, Isolation & Coverage Thresholds
- Unit tests MUST NOT perform real network I/O, database queries, disk writes, or message queue calls. All external dependencies MUST be replaced with verified mocks.
- Individual unit tests MUST execute in sub-millisecond time (< 1ms per test).
- Each unit test MUST focus on a single logical assertion or behavior.
- CI pipelines MUST enforce automated code coverage thresholds:
  - Minimum **80% Line Coverage**.
  - Minimum **75% Branch Coverage**.
- Pull requests failing these thresholds MUST be automatically blocked by CI.

### 3. Integration Testing with Testcontainers & Transaction Rollback
- Integration tests MUST NOT mock databases (e.g. SQLite mocking PostgreSQL). They MUST execute against real database engines (PostgreSQL, MySQL) and caches (Redis) running in ephemeral Docker containers via Testcontainers.
- **Pre-Suite Lifecycle**:
  - Testcontainers MUST be launched once per test runner process (singleton lifecycle).
  - Database schema migrations MUST execute completely prior to running the test suite.
- **Test Isolation via Transaction Rollback**:
  - Every integration test MUST execute within an isolated database transaction that is unconditionally rolled back upon test completion (`ROLLBACK`).
  - Tests MUST NOT leak mutated state to subsequent tests.
  - Hard database truncations (`TRUNCATE TABLE`) per test are forbidden due to severe performance degradation.

### 4. Post-Deployment Smoke Test Gate
- Deployment pipelines MUST execute automated post-deployment smoke tests immediately following rollout before routing live traffic:
  1. Readiness probe `GET /health/ready` returns HTTP 200 with all healthy dependencies.
  2. The critical user happy path (e.g. login $\rightarrow$ authenticated profile fetch $\rightarrow$ logout).
  3. Security error contracts (e.g. unauthenticated request returns HTTP 401 standard error envelope).
- Manual "click around" verification in lieu of automated smoke tests is STRICTLY FORBIDDEN.

### 5. Performance Testing & SLA Thresholds
- Core APIs MUST establish performance baselines using automated load testing tools (k6, Locust, or Artillery) covering 4 standard profiles:
  - **Load Test**: Normal expected concurrency baseline.
  - **Stress Test**: 2x–5x peak traffic to discover the system breaking point.
  - **Spike Test**: Sudden traffic burst to verify auto-scaling and rate-limiting resilience.
  - **Soak Test**: Sustained load over multiple hours to detect memory and connection leaks.
- Performance tests MUST evaluate against predefined SLA thresholds:
  - **p50 Latency**: < 50ms
  - **p95 Latency**: < 200ms
  - **p99 Latency**: < 500ms
  - **Error Rate**: < 0.1% (HTTP 5xx failures)

### 6. Test Determinism & Flakiness Prohibition
- Tests MUST be 100% deterministic. Flaky tests are treated as critical bugs.
- Unseeded pseudo-random generators (`Math.random()`) are FORBIDDEN in assertions. Fixed seeds or deterministic sequential generators MUST be used.
- System time dependencies MUST use fake timers (`jest.useFakeTimers()`, `vi.useFakeTimers()`). Real sleep pauses are forbidden.
- Tests MUST NOT depend on execution order; test runners MUST support randomized test execution (`--randomize`).

## Examples

### 1. Unit Test Mock Isolation & Deterministic Assertions
```typescript
// ✅ CORRECT: Fast, pure unit test with mocked dependencies and deterministic inputs
describe('CalculateMonthlyEmiUseCase', () => {
  let useCase: CalculateMonthlyEmiUseCase;
  let mockAuditLogger: jest.Mocked<AuditLoggerService>;

  beforeEach(() => {
    mockAuditLogger = { logEvent: jest.fn().mockResolvedValue(undefined) } as unknown as jest.Mocked<AuditLoggerService>;
    useCase = new CalculateMonthlyEmiUseCase(mockAuditLogger);
  });

  it('should compute exact amortized monthly installment deterministically', async () => {
    const inputDto: CalculateEmiDto = { principalAmount: 100000, annualInterestRate: 8.5, tenureInMonths: 240 };
    const result = await useCase.execute(inputDto);

    expect(result.monthlyInstallment).toBe(867.82);
    expect(mockAuditLogger.logEvent).toHaveBeenCalledTimes(1);
  });
});
```

### 2. Testcontainers Integration Test with Transaction Rollback
```typescript
// ✅ CORRECT: Real PostgreSQL in Testcontainers with transaction rollback per test
describe('OrdersRepository Integration (PostgreSQL)', () => {
  let dbPool: DatabasePool;
  let client: PoolClient;
  let repository: OrdersRepository;

  beforeAll(async () => {
    dbPool = await TestcontainersManager.getPostgresPool();
  });

  beforeEach(async () => {
    client = await dbPool.connect();
    await client.query('BEGIN'); // Start isolated transaction
    repository = new OrdersRepository(client);
  });

  afterEach(async () => {
    await client.query('ROLLBACK'); // Unconditionally rollback state
    client.release();
  });

  it('should persist and query order without polluting shared test database', async () => {
    const order = await repository.createOrder({
      id: 'ord_01HXYZ1234567890',
      customerId: 'usr_test_001',
      totalAmountCents: 4999,
    });
    const fetched = await repository.findById('ord_01HXYZ1234567890');
    expect(fetched?.totalAmountCents).toBe(4999);
  });
});
```

### 3. k6 Performance Testing Script with Strict SLA Thresholds
```javascript
// ✅ CORRECT: k6 performance test with explicit latency and error rate SLA gates
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },  // Ramp-up to 50 virtual users
    { duration: '1m', target: 50 },   // Steady state load
    { duration: '15s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    'http_req_duration{status:200}': ['p(50)<50', 'p(95)<200', 'p(99)<500'],
    'http_req_failed': ['rate<0.001'], // Error rate strictly < 0.1%
  },
};

export default function () {
  const res = http.get('http://api-service:3000/api/v1/health/ready');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```
