# Koa Testing Architecture Matrix & Strategy (JavaScript)

## Overview
This reference specifies the risk-weighted testing taxonomy for enterprise Koa.js applications in JavaScript backed by Sequelize ORM and MySQL databases. It details the boundaries, execution targets, and tooling across the 3 core layers.

---

## 1. Risk-Weighted Layer Distribution

| Test Layer | Volume Target | Primary Tooling | Execution Environment | Key Verification Focus |
| :--- | :--- | :--- | :--- | :--- |
| **Unit Testing** | **60–70%** | Vitest | In-Memory (Zero I/O) | Business calculations, data mappings, validation schemas, utility algorithms |
| **Database Integration** | **20–30%** | Vitest + Sequelize | Dedicated MySQL Test DB | Foreign key integrity, unique constraints, associations, pagination, transaction rollback |
| **API / Route Testing** | **10–15%** | Vitest + Supertest | Koa `app.callback()` | Middleware onion pipeline, auth headers, status codes, standardized error responses |

---

## 2. Directory Structure Standards

```text
tests/
├── unit/
│   ├── services/           # Business logic isolated from HTTP/DB
│   ├── utils/              # Pure algorithmic calculations & transformers
│   ├── validators/         # Input schema validation rules
│   └── mappers/            # Domain to DTO data mappers
│
├── integration/
│   ├── models/             # Real Sequelize model definitions & associations
│   ├── repositories/       # Query logic against real MySQL
│   └── transactions/       # Multi-step transactional rollback verifications
│
├── api/
│   ├── auth/               # Login, refresh token, password reset endpoints
│   ├── users/              # User management & RBAC route tests
│   └── properties/         # Core business domain endpoints
│
├── fixtures/               # Deterministic data factories (e.g. user.fixture.js)
├── mocks/                  # Mock implementations of external third-party APIs (Stripe, CRM)
└── setup/
    ├── database.js         # Test MySQL DB connection lifecycle & cleanup
    ├── app.js              # Koa app instance export with test middleware
    └── global.js           # Vitest global environment bootstrap
```

---

## 3. Layer Specifications

### Layer A: Unit Testing Standards
- **Isolation Principle**: Unit tests MUST NEVER import database models with live database connections or initialize HTTP listeners.
- **Fast Feedback**: The entire unit suite should execute in under 3 seconds in watch mode (`pnpm test:unit`).
- **Examples**:
  - Commission calculations: `calculateCommission(price, rate)`
  - Status transitions: `transitionLeadStatus(currentStatus, targetStatus)`
  - Slug generation: `generateUniqueSlug(title)`

### Layer B: Database Integration Standards
- **Real MySQL Requirement**: Mocking Sequelize queries (`vi.mock('../models')`) hides critical syntax errors, missing columns, and foreign key failures. Real MySQL instances are mandatory.
- **Transaction Rollback Pattern**:
  ```javascript
  let transaction;
  beforeEach(async () => {
    transaction = await sequelize.transaction();
  });
  afterEach(async () => {
    await transaction.rollback();
  });
  ```
- **Cleanup Invariant**: If table truncation is used instead of transactions, truncate only domain tables in reverse dependency order. Never drop schema tables during standard test runs.

### Layer C: API / Integration Route Standards
- **Supertest Harness**: Always test Koa using `request(app.callback())` instead of listening on a physical network port (`app.listen(0)`).
- **Middleware Flow**: Validates that authentication middleware sets `ctx.state.user`, validation middleware rejects invalid bodies with `400/422`, and error middleware catches unhandled exceptions and returns `{ success: false, message: '...' }`.

---

## 4. Test Naming Protocol
Test descriptions MUST specify:
1. The precondition / trigger.
2. The expected outcome or HTTP status code.

- ❌ `it('should work', ...)`
- ❌ `it('test user creation', ...)`
- ✅ `it('should return 401 when Authorization header is missing', ...)`
- ✅ `it('should rollback transaction and return 409 when email already exists', ...)`
- ✅ `it('should prevent agent from deleting property owned by another agent', ...)`
