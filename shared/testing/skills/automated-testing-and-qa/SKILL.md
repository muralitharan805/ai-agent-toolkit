---
name: automated-testing-and-qa
description: "Guides deterministic unit and integration testing with Vitest/Jest, Playwright E2E automation, coverage threshold enforcement, and mock isolation."
---

# Automated Testing & Quality Assurance Architecture

Establishes enterprise testing standards across frontend and backend applications. Enforces deterministic mock isolation, minimum 80% line and 75% branch test coverage thresholds, colocated spec files, and Playwright end-to-end (E2E) automation.

---

## 5-Pillar Architecture Directory Layout

```text
shared/testing/skills/automated-testing-and-qa/
├── SKILL.md                                           # Core procedural testing guidance (< 500 lines)
├── references/                                        # Authoritative deep-dive runbooks
│   ├── vitest-and-jest-mocking-patterns.md           # Mock providers, spies, and deterministic cleanup
│   └── playwright-e2e-best-practices.md              # Resilient POM, accessibility locators, and auth state
├── scripts/                                           # Standalone automation tools
│   └── verify_test_coverage.py                       # CLI test coverage and missing spec auditor
├── assets/                                            # Reusable configurations and templates
│   ├── vitest.config.ts                              # Vitest config with 80% / 75% coverage thresholds
│   ├── playwright.config.ts                          # Playwright multi-browser E2E configuration
│   └── service.spec.template.ts                      # Isolated service unit test boilerplate
└── evals/                                             # Verifiable test cases and grading
    ├── evals.json
    └── grading.json
```

---

## 5-Phase Procedural Testing Protocol

Follow this 5-phase sequence to build, run, and enforce automated testing quality gates:

### Phase 1: Unit & Service Spec Authoring
1. Colocate spec files directly alongside source files:
   - `src/modules/orders/orders.service.ts` $\rightarrow$ `src/modules/orders/orders.service.spec.ts`
2. Mock all external dependencies (database repositories, HTTP clients, message queues) using `vi.fn()` or `jest.fn()`. Real network calls or database writes in unit tests are STRICTLY FORBIDDEN (see `references/vitest-and-jest-mocking-patterns.md`).
3. Always reset mock state in `beforeEach()` / `afterEach()` hooks using `vi.clearAllMocks()`.

### Phase 2: Modern Angular Component & Signal Testing
1. Configure `TestBed` using zoneless change detection:
   ```typescript
   await TestBed.configureTestingModule({
     imports: [UserProfileComponent],
     providers: [provideZonelessChangeDetection()],
   }).compileComponents();
   ```
2. Test Signal inputs and outputs directly using component signal instances rather than legacy fixture trigger methods.

### Phase 3: NestJS Controller & Integration Testing
1. Use `Test.createTestingModule` to instantiate controllers with mocked service providers.
2. Override authentication guards to test role-based access control deterministically:
   ```typescript
   const module = await Test.createTestingModule({ ... })
     .overrideGuard(JwtAuthGuard)
     .useValue({ canActivate: () => true })
     .compile();
   ```

### Phase 4: Playwright End-to-End (E2E) Automation
1. Author critical user flows in `e2e/*.spec.ts` using the Page Object Model (see `references/playwright-e2e-best-practices.md`).
2. Use accessible locators (`page.getByRole()`, `page.getByLabel()`, `page.getByTestId()`); avoid brittle CSS or XPath selectors.
3. Leverage web-first auto-waiting assertions (`await expect(locator).toBeVisible()`); arbitrary `waitForTimeout()` calls are STRICTLY FORBIDDEN.

### Phase 5: Automated Coverage Enforcement & CI Quality Gates
1. Run the test suite with coverage:
   ```bash
   pnpm test:cov
   ```
2. Audit coverage reports and check for missing colocated specs using the bundled CLI script:
   ```bash
   python3 scripts/verify_test_coverage.py --coverage-file coverage/coverage-summary.json --strict
   ```
3. Enforce CI failure if line coverage drops below 80% or branch coverage drops below 75%.

---

## Gotchas & Testing Anti-Patterns

| Anti-Pattern / Insecure Shortcut | Deterministic Enterprise Standard | Why It Matters |
|---|---|---|
| Arbitrary `await page.waitForTimeout(3000)` | Playwright auto-waiting assertions (`expect(locator).toBeVisible()`) | Hard-coded sleeps introduce massive CI latency and fail unpredictably under variable server loads. |
| Making real HTTP calls or DB queries in unit tests | Mocking network adapters with `vi.fn()` / `mockResolvedValue()` | Real I/O causes intermittent test failures, polluted databases, and dependency on external services. |
| Storing test spec files in distant `tests/` folders | Colocating `*.spec.ts` files directly next to implementation | Distant test directories are frequently forgotten during feature refactoring, causing untested dead code. |
| Forgetting `vi.clearAllMocks()` in `beforeEach()` | Mandatory mock reset in `beforeEach()` / `afterEach()` hooks | Previous test invocations pollute mock call history, leading to brittle order-dependent test runs. |
| Testing private methods or internal state directly | Testing public API contracts and observable outputs | Refactoring internal implementation details breaks tests even when business behavior is unchanged. |
| Skipping branch coverage checks (only tracking lines) | Enforcing $\ge 80\%$ line and $\ge 75\%$ branch thresholds | Line coverage alone masks untested `if/else` error branches and edge-case exceptions. |
