---
description: "Enforces mandatory standards for Chrome DevTools MCP browser testing, visual DOM verification, accessibility compliance, and scratchpad error handling."
trigger: glob
---

# Chrome DevTools & Browser Automation Rules

## Description
Enforces mandatory standards for Chrome DevTools browser testing, visual DOM verification, accessibility compliance, scratchpad error handling, and performance auditing.

## Constraints

### 1. Mandatory DOM & Visual Verification Rule
- Agents MUST NOT report a browser UI test or interaction as successful based on assumption or speculative execution.
- Every UI interaction test MUST verify final DOM state via text snapshot (`take_snapshot`) or visual screenshot (`take_screenshot`).

### 2. Fast Fallback & Timeout Protocol
- If a browser automation action times out or fails to initialize within 30 seconds, agents MUST NOT loop indefinitely.
- Agents MUST fall back to `read_url_content` or direct HTTP status inspection (`curl`), log the precise root cause, and inform the user.

### 3. Hydration & Signal State Readiness Rule
- When auditing modern Single Page Applications (Angular Signals, React CSR/SSR), agents MUST allow component hydration and asynchronous data loading to complete before taking DOM snapshots.

### 4. Accessibility (A11y) & Mobile Touch Target Enforcement
- UI component audits MUST verify WCAG 2.1 AA minimum contrast ratios ($4.5:1$ for normal text) and enforce a minimum touch target size of $44 \times 44\text{px}$ on mobile viewports.

### 5. Persistent Artifact & Evidence Storage Rule
- Screenshots, heap snapshots, and performance traces MUST be saved to the active workspace brain artifact directory (`<appDataDir>/brain/<conversation-id>/`) and embedded in visual walkthrough reports using standard markdown image syntax.

