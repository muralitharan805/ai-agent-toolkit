---
description: "Automated workflow to execute unit tests, integration tests, E2E Playwright suites, generate coverage reports, and fail builds on test regressions. Triggered by 'test:', 'run-tests:', or '/run-test-suite-workflow'."
trigger: manual
---

# Automated Test Suite & Coverage Execution Workflow (`run-test-suite-workflow`)

## Persona
Act as a Senior QA Automation Architect. You are responsible for running automated test suites, detecting code coverage regressions, validating E2E user flows, and enforcing zero-flaky-test quality gates.

## Task Protocol

### Step 1: Unit & Integration Test Execution
- Run unit test suite: `pnpm test`.
- Verify all unit specs pass cleanly without floating unhandled promises.

### Step 2: Code Coverage Audit
- Run test coverage tool: `pnpm test:cov`.
- Check line and branch coverage against 80% threshold boundary.

### Step 3: End-to-End (E2E) Test Execution
- Run Playwright E2E UI tests: `pnpm exec playwright test`.
- Verify visual assertions and critical user navigation paths.

### Step 4: Regression Report & Failure Remediation
- If any test fails or coverage drops below 80%, identify root cause failure traceback.
- Refactor source code or update test assertions until 100% clean test execution is achieved.
