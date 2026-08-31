---
name: chrome-devtools
description: Uses Chrome DevTools via MCP for browser automation, DOM inspection, UI testing, accessibility (a11y) audits, and performance tuning across Angular, React, and web applications.
---

# Chrome DevTools & Browser Automation Skill

## Overview

This skill provides comprehensive operational guidelines, architectural patterns, and tool call workflows for executing browser automation, DOM tree snapshotting, visual verification, accessibility (a11y) auditing, and Core Web Vitals (LCP/CLS) performance debugging using Chrome DevTools MCP tools and subagents.

---

## Operational Architecture & Execution Protocol

```
[Server Readiness Check] ──► [Tab Navigation] ──► [Wait For Hydration/Signals] ──► [DOM Snapshot / UID Lookup] ──► [Interaction / Verification]
```

### 1. Pre-Flight Server Readiness Check
* Always verify target application server availability (e.g. `http://localhost:4200` for Angular, `http://localhost:5173` for Vite/React) prior to initiating browser loops.
* If the port is unresponsive, start the local development server via `pnpm run dev` or `pnpm start` before proceeding.

### 2. Page Navigation & Tab Management
* List active browser tabs using `list_pages` and attach to or select the primary workspace window (`select_page`).
* For single-page applications (SPAs) built with Angular Signals or React, wait for component hydration and initial network fetches to resolve before querying the DOM.

### 3. Text Snapshot vs. Visual Screenshot Strategy
* **Text Snapshots (`take_snapshot`)**: Primary mechanism for automation loops. Retrieves the compact accessibility tree with unique element `uid` identifiers. Use this to find click targets, form inputs, and dynamic text labels while minimizing token overhead.
* **Visual Screenshots (`take_screenshot`)**: Secondary mechanism for visual evidence. Capture full-page or element screenshots when auditing layout aesthetics, CSS flex/grid alignments, dark/light theme shifts, or saving verification evidence.

### 4. Component Interaction Protocol
* **Button & Link Triggering**: Use `uid`-based clicks (`click`) derived from the latest `take_snapshot` execution. Re-fetch snapshots after navigation or dynamic DOM mutations.
* **Form Submissions**: Set values on input controls using explicit target `uid`s rather than un-focused keypresses to trigger reactive Angular Form or React state bindings.
* **Navigation Assertions**: After triggering route transitions, verify page URL changes and check `<title>` updates.

---

## Accessibility (A11y) & Performance Auditing Protocol

### Accessibility (WCAG 2.1 AA Compliance)
* **Touch Target Area**: Ensure all interactive controls (buttons, icon triggers, chip filters) satisfy minimum $44 \times 44\text{px}$ touch target dimensions on mobile viewports.
* **Semantic Landmarks & ARIA**: Verify structural landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`, `<aside>`) are present and ARIA attributes (`aria-expanded`, `aria-label`, `aria-modal`) accurately reflect UI state.
* **Focus Management & Contrast**: Confirm modal dialogs trap keyboard focus and body text maintains minimum $4.5:1$ contrast ratio against background surfaces.

### Core Web Vitals & Performance Diagnostics
* **Largest Contentful Paint (LCP)**: Inspect hero images and primary content blocks to identify render-blocking CSS/JS assets.
* **Cumulative Layout Shift (CLS)**: Reserve layout space (`min-height`) for dynamic elements and asynchronous AdSense containers to prevent layout shifts.
* **Console Error Inspection**: Audit browser console logs for uncaught JavaScript exceptions, CORS failures, or 404 missing static assets.

---

## Fallback & Error Remediation Protocol

* **Timeout Handling**: If a browser session action fails to respond within 30 seconds, abort the blocking loop immediately.
* **Direct Content Fallback**: Fall back to `read_url_content` or `curl` HTTP requests to verify raw HTML response headers and server uptime.
* **Artifact Reporting**: Store screenshots, network logs, and DOM snapshots in the active workspace brain artifact directory for persistent user review.

