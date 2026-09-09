---
name: chrome-devtools
description: Uses Chrome DevTools via MCP for browser automation, DOM inspection, UI testing, accessibility (a11y) audits, and performance tuning across Angular, React, and web applications. Triggered by 'test-web-app:', 'browser-test:', or '/test-web-app-chrome-devtools'.
---

# Chrome DevTools & Browser Automation Skill

## Overview

This skill provides an enterprise operational protocol for browser automation, DOM tree snapshotting, visual verification, accessibility (a11y) auditing, and Core Web Vitals performance tuning using Chrome DevTools Model Context Protocol (MCP) tools and subagents. It absorbs end-to-end browser testing workflows, replacing speculative testing with empirical DOM snapshots and visual artifact proof.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           6-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Pre-Flight & Tab Init]  ──► Verify server port & open browser context
               │
  [Phase 2: Hydration Gate]         ──► Synchronize Signals, React state, network idle
               │
  [Phase 3: Snapshot & UID Lookup]  ──► `take_snapshot` (Accessibility tree & UIDs)
               │
  [Phase 4: Targeted Interaction]   ──► `click` / `fill` by explicit element UID
               │
  [Phase 5: A11y & CWV Auditing]    ──► 44x44px touch targets, contrast, CLS checks
               │
  [Phase 6: Artifact & Reporting]   ──► Save screenshot to brain & update walkthrough
```

---

## 6-Phase Execution Guide

### Phase 1: Pre-Flight Server Readiness & Tab Initialization
1. **Server Verification**: Prior to launching browser loops, verify that the application server is responsive:
   ```bash
   python3 scripts/audit_browser_readiness.py --url http://localhost:4200 --timeout 5
   ```
   If the port is closed, start the application via `pnpm run dev` or `pnpm start`.
2. **Tab Context Management**:
   - Enumerate existing tabs using `list_pages`.
   - Attach to the active session using `select_page`, or create a fresh context via `new_page`.
   - Target desktop ($1280 \times 800\text{px}$) or mobile viewports ($375 \times 667\text{px}$) depending on test requirements.

### Phase 2: Hydration & Signal State Synchronization
1. **Route Navigation**: Load the target URL using `navigate_page`.
2. **Hydration Settlement**:
   - For modern Single Page Applications (Angular 19 Signals `resource()`, `rxResource()`, React 19 concurrent transitions), do NOT use blind sleep delays.
   - Wait for route transitions, signal-computed values, and initial network requests to resolve.
   - Look for key rendered semantic containers (e.g. `<main>`, profile cards, data tables).

### Phase 3: Accessibility Tree Snapshotting & UID Discovery
1. **Text Snapshots (`take_snapshot`)**:
   - Execute `take_snapshot` as the primary discovery mechanism.
   - Extracts the compact accessibility tree with unique element `uid`s while saving up to 80% context tokens compared to raw HTML dumps.
2. **UID Extraction**: Map interactive targets (buttons, inputs, links) to their assigned element `uid`s for subsequent actions.

### Phase 4: Resilient Element Interaction & State Mutations
1. **Targeted Interaction**:
   - Trigger clicks (`click`) or text inputs (`fill` / `set_value`) using explicit target `uid`s.
   - Avoid blind keyboard simulations or brittle CSS selectors.
2. **DOM Mutation Confirmation**:
   - After every state-altering action (form submission, tab switch, filter toggle), re-execute `take_snapshot` to confirm DOM mutation.
   - Verify route URL changes and document `<title>` updates.

### Phase 5: Accessibility (WCAG 2.1 AA) & Performance Auditing
1. **Mobile Touch Target Ergonomics**:
   - Verify that all interactive buttons, icon triggers, and chip filters satisfy the minimum **$44 \times 44\text{px}$** touch target area on mobile viewports ($< 768\text{px}$).
2. **Color Contrast & Landmarks**:
   - Confirm body text maintains at least **$4.5:1$** contrast ratio against background surfaces.
   - Verify structural landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`) and single `<h1>` hierarchy.
3. **Core Web Vitals & Console Hygiene**:
   - Check that dynamic elements (e.g. ad slots, lazy widgets) declare explicit `min-height` to prevent Cumulative Layout Shift (CLS).
   - Audit browser console logs for uncaught JavaScript errors or network 4xx/5xx failures.

### Phase 6: Artifact & Visual Verification Reporting
1. **Visual Evidence**: Capture high-resolution screenshots (`take_screenshot`) of key UI milestones and layout baselines.
2. **Persistent Storage**: Save screenshots and audit traces to the active workspace brain artifact directory:
   `<appDataDir>/brain/<conversation-id>/`
3. **Walkthrough Integration**: Update `walkthrough.md` embedding saved screenshot artifacts and documenting verification tables.

---

## Local References & Assets

- **MCP Protocol & Interaction Runbook**: [references/browser-automation-and-mcp-protocol.md](references/browser-automation-and-mcp-protocol.md)
- **A11y & Core Web Vitals Specifications**: [references/a11y-and-cwv-audit-specifications.md](references/a11y-and-cwv-audit-specifications.md)
- **Server Readiness & Audit CLI Script**: [scripts/audit_browser_readiness.py](scripts/audit_browser_readiness.py)
- **Browser Audit Report JSON Schema**: [assets/browser-audit-report-template.json](assets/browser-audit-report-template.json)
- **WCAG 2.1 AA Verification Checklist**: [assets/a11y-wcag-checklist.json](assets/a11y-wcag-checklist.json)

---

## Gotchas & Anti-Patterns

| Deprecated / Anti-Pattern | Why It Fails | Modern Recommended Practice |
| :--- | :--- | :--- |
| **Speculative Test Success** | Assuming a click succeeded without validating resulting DOM changes. | Re-run `take_snapshot` or visual comparison to empirically confirm mutation. |
| **Arbitrary Sleep Delays (`sleep(5000)`)** | Flaky, slow, and non-deterministic under varied CPU/network loads. | Synchronize on signal readiness, DOM landmark presence, or network idle. |
| **Raw HTML Dumps for Locators** | Consumes tens of thousands of tokens and overflows model context. | Use `take_snapshot` to extract concise accessibility tree and element `uid`s. |
| **Desktop-Only Viewport Audits** | Misses mobile touch target failures ($< 44\text{px}$) and notch layout overlaps. | Test both desktop ($1280\text{px}$) and mobile ($375\text{px}$) viewports. |
| **Ignoring Uncaught Console Errors** | Silent failures and broken JavaScript hydration degrade end-user experience. | Audit console logs; treat uncaught exceptions and network failures as test blockers. |
| **Zero Layout Reservation for Dynamic Ads/Widgets** | Asynchronous rendering shifts page content, penalizing Google Core Web Vitals (CLS $> 0.1$). | Reserve vertical container height (`min-height: 250px` or `aspect-ratio`) before render. |
