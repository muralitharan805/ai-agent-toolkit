---
description: "Mandates minimum 80% line and branch test coverage, mock isolation for external dependencies, deterministic test setup, and forbidden production test mocks."
trigger: always_on
---

# Automated Testing & Coverage Quality Rules

## Description
Enforces mandatory test coverage thresholds, unit and integration test isolation, E2E testing protocols, and deterministic mock management across frontend and backend projects.

## Constraints

### 1. Mandatory Minimum Test Coverage Thresholds
- Applications MUST achieve a minimum of **80% line coverage** and **75% branch coverage** across core business logic services and components.
- CI/CD build scripts MUST fail if code coverage drops below threshold boundaries (`pnpm test:cov`).

### 2. Dependency Mocking & Test Isolation Rule
- Unit tests (`*.spec.ts`) MUST mock all external network adapters, database connections, and third-party API services using mock providers or spy functions (`vi.fn()`, `jest.fn()`).
- Tests MUST NOT make real outbound HTTP network calls or modify external production database records.

### 3. Test File Colocation & Naming Standard
- Component and service test spec files MUST be colocated in the exact same directory as the source file:
  - Component: `user-profile.component.ts` $\rightarrow$ `user-profile.component.spec.ts`
  - Service: `user.service.ts` $\rightarrow$ `user.service.spec.ts`

### 4. Deterministic Test Setup & Tear-Down
- Every test suite MUST reset mock calls and state in `beforeEach()` / `afterEach()` hooks (`vi.clearAllMocks()` or `jest.clearAllMocks()`).
- Tests MUST NOT depend on execution order or shared mutable global state.
