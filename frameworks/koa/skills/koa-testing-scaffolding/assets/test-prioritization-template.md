# Production Testing Audit & Coverage Matrix

Use this audit matrix to inventory all existing Koa backend endpoints, evaluate business risk, and track test coverage implementation progress.

---

## 1. Feature & Endpoint Inventory

| Endpoint / Feature | Priority | Unit Test File | Integration Test File | API Test File | Performance Benchmark | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST /api/auth/login** | `P0` | `tests/unit/services/auth.spec.js` | — | `tests/api/auth/login.spec.js` | 25 VUs | `PLANNED` |
| **POST /api/payments/charge** | `P0` | `tests/unit/services/payment.spec.js` | `tests/integration/transactions/payment.spec.js` | `tests/api/payments/charge.spec.js` | 10 VUs | `PLANNED` |
| **DELETE /api/properties/:id** | `P0` | — | — | `tests/api/properties/delete.spec.js` (IDOR) | — | `PLANNED` |
| **GET /api/properties** | `P1` | `tests/unit/mappers/property.spec.js` | `tests/integration/models/property.spec.js` | `tests/api/properties/list.spec.js` | 50 VUs (p95<500ms) | `PLANNED` |
| **POST /api/leads** | `P1` | — | `tests/integration/models/lead.spec.js` | `tests/api/leads/create.spec.js` | 10 VUs | `PLANNED` |
| **GET /api/reports/analytics** | `P2` | `tests/unit/services/report.spec.js` | `tests/integration/repositories/report.spec.js` | — | 10 VUs (p95<1000ms) | `PLANNED` |
| **GET /health** | `P3` | — | — | `tests/api/health.spec.js` | Smoke | `PLANNED` |

---

## 2. Priority Definition Key
- **P0 (Critical)**: Auth, payments, data mutation, security/IDOR. Blocks release if failing.
- **P1 (High)**: Core customer search and CRUD flows.
- **P2 (Medium)**: Secondary reporting, background jobs, utility endpoints.
- **P3 (Low)**: Static lookups, ping/health routes.

---

## 3. Progress Tracking Checklist
- [ ] P0 Endpoints fully covered with Supertest assertions (401, 403, 400, 200/201).
- [ ] P0 Multi-table database mutations verified with transaction rollback.
- [ ] P1 Search endpoints benchmarked under 25 concurrent users in k6.
- [ ] CI pipeline configured to fail if any P0 test fails.
