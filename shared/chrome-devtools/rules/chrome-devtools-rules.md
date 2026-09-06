---
description: "Enforces mandatory standards for Chrome DevTools MCP browser testing, visual DOM verification, accessibility (WCAG 2.1 AA) compliance, Core Web Vitals (CLS/LCP) layout reservation, and persistent brain artifact storage."
trigger: model_decision
---

# Chrome DevTools & Browser Automation Rules

## Description
Enforces mandatory engineering standards for Chrome DevTools Model Context Protocol (MCP) browser testing, accessibility (WCAG 2.1 AA) compliance, Core Web Vitals layout stability, and persistent artifact verification. Ensures that AI agents never report speculative test passes, always verify empirical DOM state mutations, enforce mobile touch targets ($44 \times 44\text{px}$), and eliminate layout-shifting regressions across modern Angular, React, and web applications.

## Constraints

### 1. Mandatory Empirical DOM & Visual Verification (Zero Speculative Testing)
- Agents MUST NOT report a browser UI test or navigation as successful based on speculative execution.
- Every state-altering user interaction (button clicks, form submissions, filter toggles, route changes) MUST be empirically verified:
  - Verify DOM mutation using text-based accessibility tree snapshotting (`take_snapshot`).
  - Extract and assert element values, text updates, or structural changes via element `uid`s.
  - Capture visual screenshots (`take_screenshot`) for layout milestones and walkthrough reports.

### 2. Fast Fallback & 30-Second Execution Timeout Protocol
- Agents MUST NOT loop indefinitely or hang when a browser navigation or remote session fails to respond.
- If a browser command does not complete within 30 seconds:
  - Immediately abort the hanging browser loop.
  - Diagnose the root failure by checking local dev server reachability via CLI (`curl -I <url>` or `audit_browser_readiness.py`).
  - Fall back to static HTTP inspection using `read_url_content` or raw response headers.
  - Log the failure reason, HTTP status, and actionable remediation steps.

### 3. Hydration Gate & Signal State Synchronization
- Modern Single Page Applications (Angular Signals `resource()` / `rxResource()`, React 19 transitions) require asynchronous hydration and network fetch settlement.
- Agents MUST NOT execute locator lookups immediately upon document navigation.
- **Prohibition of Blind Sleep Delays**: Using arbitrary `sleep(5000)` or hardcoded timers is STRICTLY FORBIDDEN.
- Agents MUST wait for key semantic landmarks or network idle before querying element `uid`s.
- When reactive state triggers DOM re-rendering, previous element `uid`s become stale; agents MUST re-execute `take_snapshot` before the next interaction.

### 4. Accessibility (WCAG 2.1 AA) & Mobile Touch Target Enforcement
- All browser UI evaluations and component audits MUST verify WCAG 2.1 Level AA standards:
  - **Touch Target Ergonomics**: Every interactive element (buttons, icon triggers, chip filters) MUST provide a minimum active touch target area of **$44 \times 44\text{px}$** on viewports $< 768\text{px}$.
  - **Adjacent Element Spacing**: Adjacent interactive controls MUST provide at least $8\text{px}$ physical separation.
  - **Color Contrast Thresholds**: Normal body text MUST maintain a minimum contrast ratio of **$4.5:1$** against adjacent surface backgrounds ($3.0:1$ for large text $\ge 18\text{pt}$ or $14\text{pt}$ bold).
  - **Semantic Structure**: Pages MUST provide exactly one `<h1>` heading and properly declared landmark roles (`<main>`, `<nav>`, `<header>`, `<footer>`).

### 5. Core Web Vitals (CLS/LCP) & Layout Reservation Invariants
- **Cumulative Layout Shift (CLS $\le 0.1$)**:
  - Asynchronously rendered elements (Google AdSense units, third-party widgets, lazy cards) MUST declare explicit vertical layout space (`min-height: 250px` or CSS `aspect-ratio`) prior to content rendering.
  - Images (`<img>`) and media tags MUST specify explicit `width` and `height` attributes to prevent layout displacement.
- **Largest Contentful Paint (LCP $\le 2.5\text{s}$)**:
  - Critical hero images MUST NOT be configured with `loading="lazy"`. Hero elements MUST use `fetchpriority="high"`.
- **Console Hygiene**: Browser console logs MUST be inspected during test runs. Uncaught JavaScript exceptions and network 4xx/5xx failures MUST be treated as test failures.

### 6. Persistent Brain Artifact Storage & Markdown Walkthroughs
- All visual test artifacts—including screenshots and performance audit reports—MUST be stored within the active workspace brain directory:
  `<appDataDir>/brain/<conversation-id>/`
- Agents MUST embed captured screenshots into `walkthrough.md` reports using markdown image syntax.
- Reports MUST summarize pass/fail metrics, DOM verification evidence, and remediation steps.

## Examples

### 1. Empirical DOM Snapshot Verification vs. Speculative Pass
```typescript
// ❌ FORBIDDEN: Speculative Pass (Assuming click succeeded without DOM assertion)
async function testAddToCartSpeculative(page: any): Promise<void> {
  await page.click('#add-to-cart-button');
  console.log('Added to cart successfully'); // No verification of cart badge mutation!
}

// ✅ CORRECT: Empirical DOM Verification (UID snapshot + post-mutation assertion)
async function testAddToCartEmpirical(client: ChromeDevToolsMcpClient): Promise<void> {
  const initialSnapshot = await client.takeSnapshot();
  const buttonUid = findElementUidByText(initialSnapshot, 'Add to Cart');
  await client.click({ uid: buttonUid });

  // Re-snapshot to empirically verify DOM mutation
  const updatedSnapshot = await client.takeSnapshot();
  const badgeUid = findElementUidBySelector(updatedSnapshot, '.cart-badge');
  const badgeText = getElementText(updatedSnapshot, badgeUid);
  
  if (badgeText !== '1') {
    throw new Error(`Cart badge mismatch: expected '1', found '${badgeText}'`);
  }
}
```

### 2. Signal Hydration Waiting vs. Flaky Sleep Delay
```typescript
// ❌ FORBIDDEN: Arbitrary Sleep Delay (Flaky and non-deterministic)
async function waitForProfileFlaky(page: any): Promise<void> {
  await page.goto('http://localhost:4200/profile');
  await new Promise((resolve) => setTimeout(resolve, 5000)); // Arbitrary sleep!
}

// ✅ CORRECT: Deterministic Signal Hydration Gate
async function waitForProfileSignal(client: ChromeDevToolsMcpClient): Promise<void> {
  await client.navigatePage({ url: 'http://localhost:4200/profile' });

  const startTime = Date.now();
  while (Date.now() - startTime < 10000) {
    const snapshot = await client.takeSnapshot();
    const container = findElementByRole(snapshot, 'region', 'User Profile');
    if (container && !container.attributes['aria-busy']) {
      return; // Signals resolved and DOM hydrated
    }
    await delay(200);
  }
  throw new Error('Signal hydration timed out after 10 seconds');
}
```

### 3. Mobile Touch Target & A11y Verification
```typescript
// ✅ CORRECT: Verifying 44x44px touch targets on mobile viewports
function auditMobileTouchTargets(elements: LayoutBox[]): AuditResult {
  const violations: TouchTargetViolation[] = [];
  const MIN_TOUCH_SIZE_PX = 44;

  for (const element of elements) {
    if (element.isInteractive && (element.width < MIN_TOUCH_SIZE_PX || element.height < MIN_TOUCH_SIZE_PX)) {
      violations.push({
        elementSelector: element.selector,
        actualDimensions: `${element.width}x${element.height}px`,
        requiredDimensions: `${MIN_TOUCH_SIZE_PX}x${MIN_TOUCH_SIZE_PX}px`,
        wcagCriterion: 'WCAG 2.1 AA - 2.5.5 / 2.5.8 Target Size'
      });
    }
  }

  return { passed: violations.length === 0, violations };
}
```
