# Chrome DevTools MCP Browser Automation & Interaction Protocol

## 1. Overview & Architectural Principles

Chrome DevTools Model Context Protocol (MCP) integration empowers autonomous AI agents to inspect, manipulate, navigate, and audit live web applications running in desktop and mobile viewport configurations. When executing browser automation against modern single-page applications (Angular Signals, React 19, Vite, Vue 3), agents must operate through structured, deterministic protocols rather than heuristic assumptions.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           Agent Execution Lifecycle                            │
└────────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
[1. Server Port & Network Pre-Flight] ──► Uptime confirmation (HTTP 200/300)
        │
        ▼
[2. Tab Context Initialization]       ──► `list_pages` or `new_page` + `select_page`
        │
        ▼
[3. Page Navigation & Hydration Gate] ──► Wait for Signals, Hydration, Network Idle
        │
        ▼
[4. Accessibility Tree Snapshotting]  ──► `take_snapshot` (Extract element UIDs)
        │
        ▼
[5. Targeted Element Interaction]     ──► `click` / `fill` by explicit UID
        │
        ▼
[6. DOM Mutation Verification]        ──► Re-snapshot / Visual proof capture
```

---

## 2. Browser Tab Management & Lifecycle

### Tab Discovery and Selection
- **Session Enumeration**: Always invoke `list_pages` at session initialization to discover open tabs and targets before creating redundant windows.
- **Explicit Selection**: When multiple tabs are open, call `select_page` with the target `targetId` or `pageId` to ensure subsequent commands target the intended frame.
- **Session Creation**: Use `new_page` with explicit target URL when initializing a clean testing environment.

### Tab Teardown & Isolation
- Avoid accumulating orphaned tabs during test suites. Close disposable testing tabs upon completion, preserving only primary monitoring dashboards.

---

## 3. Hydration Synchronization & Signal Stability

Modern web applications utilizing fine-grained reactivity (Angular Signals `resource()`, `rxResource()`, `effect()`, or React 19 concurrent transitions) do not render all interactive elements immediately upon HTML document delivery.

### The Hydration Delay Invariant
1. **Never Assume Immediate Readiness**: Loading a route (`navigate_page`) returns when the initial HTML document arrives, but hydration scripts, lazy chunk downloads, and API fetches remain in flight.
2. **Deterministic Hydration Waiting**:
   - Do NOT use arbitrary, hardcoded `sleep` or `waitForTimeout` calls.
   - Poll for specific semantic landmarks or data attributes (e.g. `[data-hydrated="true"]`, `@if` content blocks, or user profile card containers).
   - Verify network idle states before querying element `uid`s for interaction.
3. **Reactive Signal Mutations**: When testing form controls or filter buttons bound to reactive signals, expect asynchronous UI re-renders. Re-fetch DOM snapshots after each mutation.

---

## 4. Snapshot-First vs. Visual Screenshot Strategy

To optimize token consumption, execution latency, and test accuracy, agents must balance text-based DOM snapshots against pixel visual screenshots:

| Strategy | Primary Tool | Token Overhead | Primary Use Cases |
| :--- | :--- | :--- | :--- |
| **Accessibility Tree Snapshot** | `take_snapshot` | Low (~500–2,000 tokens) | Locating element UIDs, verifying text content, checking ARIA labels, form input state assertions. |
| **Visual Pixel Screenshot** | `take_screenshot` | High (~3,000–8,000 tokens) | Visual layout regression, CSS flex/grid validation, dark/light theme shifts, walkthrough evidence. |

### Operational Rule
- **Execution Step**: Use `take_snapshot` for all locator lookups, clicks, and form submissions.
- **Verification Step**: Use `take_screenshot` only when capturing baseline UI evidence, validating responsive mobile transformations, or reporting final test milestone artifacts.

---

## 5. Element Interaction Protocol (UID-Driven)

### Robust Locator Selection
1. **UID Mapping**: Always extract the element `uid` from the most recent `take_snapshot` payload.
2. **Stale Element Reference Prevention**: After any click, navigation, or form submission that alters the DOM, the previous element UIDs become invalid. Re-execute `take_snapshot` prior to executing the next interaction.
3. **Form Inputs**: Use explicit input targeting rather than simulated global keystrokes:
   - Identify input control `uid`.
   - Set control value (`fill` / `set_value`).
   - Trigger change or blur events to ensure framework form bindings (Angular Typed Forms, React Hook Form) register value alterations.

---

## 6. Headless Browser Fault Tolerance & Fallback

When operating in continuous integration or sandboxed headless environments, browser automation can encounter execution timeouts or connection drops.

### Fast Fallback Matrix
- **30-Second Timeout Limit**: If a browser navigation or interaction fails to resolve within 30 seconds, immediately terminate the blocking loop.
- **Level 1 Fallback**: Check dev server process status and port responsiveness using `curl -I http://localhost:4200` or `netstat -tlpn`.
- **Level 2 Fallback**: Execute HTTP content extraction via `read_url_content` to verify static HTML structure, response headers, and SSR meta tags.
- **Level 3 Diagnostic**: Inspect browser console logs for fatal JavaScript execution errors (e.g. uncaught exception, missing environment variable, CORS error).
