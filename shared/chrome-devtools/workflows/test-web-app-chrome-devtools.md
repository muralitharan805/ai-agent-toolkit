---
description: "Workflow to perform end-to-end web testing, DOM verification, and visual auditing using Chrome DevTools MCP. Triggered by 'test-web-app:', 'browser-test:', or '/test-web-app-chrome-devtools'."
trigger: manual
---

# Web Application Browser & Visual Testing Workflow

## Prerequisites & Verification

1. **Dev Server Verification**:
   - Check if the target web server (e.g. `http://localhost:4200` for Angular, `http://localhost:5173` for React) is active.
   - If server is down, start it using `pnpm run dev` or `pnpm start`.

2. **Workspace Brain Setup**:
   - Ensure the artifact directory (`<appDataDir>/brain/<conversation-id>/`) exists for saving screenshots and audit reports.

---

## Step-by-Step Execution Guide

### Step 1: Initialize Browser Session
- List active tabs with `list_pages` or create a new session using `new_page`.
- Select the active tab with `select_page`.

### Step 2: Navigate & Wait for Hydration
- Execute `navigate_page` to load the target URL.
- Allow SPA component hydration, signal updates, and initial network requests to resolve completely.

### Step 3: DOM Snapshot & Visual Baseline
- Execute `take_snapshot` to extract the accessibility tree and element `uid` maps.
- Capture a baseline layout visual screenshot using `take_screenshot`.

### Step 4: Interactive Flow & State Assertions
- Trigger UI actions (button clicks, input entries, tab switches) using target `uid`s.
- After each state-changing action, execute `take_snapshot` to confirm DOM mutations.
- Check route navigation changes in URL and `<title>`.

### Step 5: Accessibility (A11y) & Performance Auditing
- Verify $44 \times 44\text{px}$ touch target compliance on mobile viewports.
- Check WCAG 2.1 AA text contrast ratios and ARIA landmark structures.
- Audit console logs for uncaught JavaScript exceptions or failed network requests.

### Step 6: Visual Audit Report Generation
- Scaffold or update `walkthrough.md` in the workspace brain directory.
- Embed visual screenshots (`![UI State](file:///path/to/screenshot.png)`).
- Document pass/fail metrics, DOM verification proofs, and recommended remediations.

