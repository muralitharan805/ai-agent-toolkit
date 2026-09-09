# Playwright End-to-End (E2E) Automation Best Practices

## Overview

Playwright provides resilient, fast, and cross-browser end-to-end automation for modern Single Page Applications (Angular, React, Vue). Flaky tests in E2E automation are almost always caused by fragile CSS/XPath selectors, unmanaged network races, and arbitrary sleep statements.

---

## 1. Resilient Locator Hierarchy

Always prefer user-facing and accessibility attributes over DOM structure:

| Preference | Method | Example |
|---|---|---|
| **1. Explicit Role (Best)** | `page.getByRole('button', { name: 'Submit' })` | Accessible to screen readers and resilient to redesigns. |
| **2. Form Label** | `page.getByLabel('Email Address')` | Mirrors real user interaction with input fields. |
| **3. Test ID** | `page.getByTestId('checkout-total')` | Stable contract between engineering and QA. |
| **4. Text Content** | `page.getByText('Order Confirmation')` | Good for static confirmation text. |
| **❌ Forbidden** | `page.locator('div > .btn-primary:nth-child(2)')` | Extremely fragile; breaks on any CSS change. |

---

## 2. Page Object Model (POM) Pattern

Encapsulate UI interactions into reusable page classes:

```typescript
// e2e/pages/login.page.ts
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(private readonly page: Page) {
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign In' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  async login(email: string, pass: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.submitButton.click();
  }

  async expectError(message: string): Promise<void> {
    await expect(this.errorMessage).toContainText(message);
  }
}
```

---

## 3. Web-First Auto-Waiting Assertions

Never use arbitrary delays (`await page.waitForTimeout(3000)`). Playwright assertions automatically retry until the expectation passes or timeouts:

```typescript
// ✅ Good: Auto-waits until element is visible and contains text
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 5000 });

// ❌ Bad: Arbitrary hard sleep slows test suites and causes CI flakiness
await page.waitForTimeout(3000); // FORBIDDEN!
```

---

## 4. Reusable Authentication via `storageState`

Avoid logging in via the UI before every test. Save authentication state once in a setup project and reuse it:

```typescript
// e2e/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('testuser@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Sign In' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

  await page.context().storageState({ path: authFile });
});
```

---

## 5. Network Mocking with `page.route()`

When testing frontend edge cases (e.g. 500 Internal Server Error, slow 3G latency), intercept network requests:

```typescript
test('displays error toast when backend API fails', async ({ page }) => {
  // Mock 500 error on orders endpoint
  await page.route('**/api/v1/orders', (route) => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Internal Database Failure' }),
    });
  });

  await page.goto('/orders');
  await expect(page.getByRole('alert')).toContainText('Internal Database Failure');
});
```
