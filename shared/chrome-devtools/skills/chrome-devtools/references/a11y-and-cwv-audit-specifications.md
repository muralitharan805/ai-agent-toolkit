# Accessibility (A11y) & Core Web Vitals (CWV) Audit Specifications

## 1. Scope & Standards Invariant

This specification establishes empirical audit criteria for evaluating web applications running within Chrome DevTools MCP sessions. All applications developed or audited under the `ai-agent-toolkit` ecosystem must adhere strictly to **WCAG 2.1 Level AA Accessibility Standards** and Google's **Core Web Vitals Performance Thresholds**.

---

## 2. WCAG 2.1 Level AA Accessibility Verification

### 2.1 Touch Target Ergonomics ($44 \times 44\text{px}$)
- **Mandatory Mobile Dimension**: All interactive controls—including buttons, icon triggers, chip filters, pagination items, and dropdown selectors—must maintain an active touch target area of at least **$44 \times 44\text{px}$** on viewports $< 768\text{px}$.
- **Spacing Invariant**: Interactive elements positioned adjacently must provide at least $8\text{px}$ physical separation to prevent accidental adjacent tap triggers.
- **Audit Rule**: Agents must verify element bounding boxes using DOM snapshot inspection or computed style evaluation.

### 2.2 Text & Graphical Contrast Ratios
- **Body & Normal Text**: Minimum contrast ratio of **$4.5:1$** against adjacent background colors.
- **Large Text ($18\text{pt}+$ or $14\text{pt}+$ bold)**: Minimum contrast ratio of **$3.0:1$**.
- **UI Components & Graphical Objects**: Minimum contrast ratio of **$3.0:1$** for input borders, focus rings, and visual icons essential to comprehension.
- **Dark Theme Verification**: Ensure custom dark themes (CSS variables, Angular Material palettes) preserve compliant contrast across elevated surface layers (cards, dialogs, drawers).

### 2.3 Semantic Landmarks & Document Structure
- **Landmark Elements**: Every page must establish explicit semantic landmarks:
  - `<header role="banner">`
  - `<nav role="navigation">`
  - `<main role="main">` (strictly one per page)
  - `<footer role="contentinfo">`
  - `<aside role="complementary">` (when auxiliary sidebars exist)
- **Heading Hierarchy**: Strictly one `<h1>` per page. Heading tags (`<h2>` through `<h6>`) must not skip hierarchical levels (e.g. `<h2>` directly to `<h4>` is forbidden).
- **Form Labels & ARIA**: Every `<input>`, `<select>`, and `<textarea>` must have an associated `<label for="...">` or explicit `aria-label` / `aria-labelledby` attribute.

### 2.4 Keyboard Navigation & Focus Management
- **Focus Visibility**: Focus indicators (outline or custom focus ring) must be visibly distinct and must not be hidden via `outline: none` without replacement.
- **Focus Trapping**: Modal dialogs and slide-out drawers must trap keyboard focus within their bounds until closed.
- **Escape Key Teardown**: Pressing `Escape` must close overlays and return focus to the trigger element.

---

## 3. Core Web Vitals (CWV) & Performance Tuning

### 3.1 Largest Contentful Paint (LCP)
- **Target Threshold**: **$\le 2.5\text{ seconds}$** under simulated standard 4G network conditions.
- **LCP Element Identification**: Hero images, featured banners, or top-level `<h1>` headings.
- **Optimization Invariants**:
  - Hero images must include `fetchpriority="high"` and must NOT be lazy-loaded (`loading="lazy"` on LCP images is strictly forbidden).
  - Preload critical font faces and hero image assets in HTML `<head>`.
  - Eliminate render-blocking synchronous scripts from the critical rendering path.

### 3.2 Cumulative Layout Shift (CLS)
- **Target Threshold**: **$\le 0.1$** throughout full page lifecycle.
- **Layout Shift Prevention**:
  - **Dynamic Elements & Ads**: Reserve container dimensions (`min-height: 250px` or explicit aspect ratio) for asynchronous elements such as Google AdSense units, embedded widgets, or lazy-loaded cards.
  - **Image Dimensions**: Every `<img>` and `<video>` tag must specify explicit `width` and `height` attributes or CSS `aspect-ratio` to reserve space before asset download completes.
  - **Font Swap Mitigation**: Use `font-display: swap` coupled with size-adjust matching to prevent layout shifts during custom web font loading.

### 3.3 Interaction to Next Paint (INP)
- **Target Threshold**: **$\le 200\text{ milliseconds}$**.
- **Execution Invariant**: Avoid long JavaScript tasks ($> 50\text{ms}$) on the main thread during user interactions. Defer non-critical compute using `requestIdleCallback` or web workers.

---

## 4. Console Hygiene & Diagnostic Error Auditing

During all automated browser verification runs, the agent must inspect the browser console log stream:

| Severity | Threshold | Action |
| :--- | :--- | :--- |
| **Uncaught Exceptions** | **Zero Allowed** | Fail test run immediately; locate stack trace and fix root cause. |
| **Network 4xx/5xx Errors** | **Zero Allowed** | Fail test run; verify API endpoints, static asset URLs, and proxies. |
| **CORS / Security Errors** | **Zero Allowed** | Fail test run; verify server Access-Control-Allow-Origin headers. |
| **Deprecation Warnings** | Informational | Document in walkthrough artifact with migration path. |
