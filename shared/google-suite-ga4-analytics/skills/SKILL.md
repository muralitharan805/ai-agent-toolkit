---
name: google-suite-ga4-analytics
description: "Universal architecture for Google Analytics 4 (GA4) measurement IDs, stream isolation, SPA route tracking, and custom event taxonomies."
---

# Google Analytics 4 (GA4) Enterprise Architecture Skill

## Purpose
Establishes production-grade Google Analytics 4 (GA4) instrumentation, subdomain data stream isolation, Single Page Application (SPA) route change tracking, custom interaction event taxonomies, and strict Personally Identifiable Information (PII) sanitization.

## Architecture & Tooling Matrix
- **Stream Isolation & SPA Tracking**: [references/ga4-stream-isolation-and-spa-tracking.md](references/ga4-stream-isolation-and-spa-tracking.md)
- **Event Taxonomy & Schema**: [references/custom-event-taxonomy-guide.md](references/custom-event-taxonomy-guide.md)
- **Automated CLI Validator**: [scripts/validate_ga4_integration.py](scripts/validate_ga4_integration.py)
- **Starter Templates**:
  - Global Head Tag: [assets/ga4-tag-template.html](assets/ga4-tag-template.html)
  - Custom Event Catalog: [assets/custom-events-catalog.json](assets/custom-events-catalog.json)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Data Stream Isolation & Measurement ID Management
1. Provision distinct Web Data Streams in Google Analytics for each environment and subdomain (`marketing.domain.com`, `app.domain.com`, `tools.domain.com`).
2. Inject the official `gtag.js` loader into `<head>` asynchronously:
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   ```
3. Initialize the global `dataLayer` and configure the environment-specific Measurement ID.

### Phase 2: SPA Route Tracking Configuration
1. In Single Page Applications (Angular, React, Vue), disable automatic pageview dispatches to avoid double-counting the initial entry page:
   ```javascript
   gtag('config', 'G-XXXXXXXXXX', { send_page_view: false });
   ```
2. Subscribe to router navigation events (e.g. `NavigationEnd` in Angular Router).
3. Dispatch explicit `page_view` events with current `page_path`, `page_title`, and `page_location` after navigation completes.

### Phase 3: Custom Interaction Taxonomy & Safe Wrappers
1. Standardize event names in `snake_case` using an `entity_action` pattern (`cta_click`, `tool_execute`, `form_submit`).
2. Enforce limits: Event names $\le 40$ characters; parameter names $\le 40$ characters.
3. Implement a defensive dispatch wrapper to ensure tracking calls never fail when ad blockers intercept `window.gtag`.

### Phase 4: Strict PII Sanitization Protocol
1. Strip plaintext email addresses, passwords, authentication tokens, and credit card numbers from all event payloads.
2. Sanitize URL query parameters before logging `page_location` to prevent leaking authentication tokens or reset credentials.
3. For user tracking across sessions, transmit exclusively salted cryptographic hashes (`user_id_hash`).

### Phase 5: Automated Verification & DebugView Testing
1. Execute the automated CLI audit tool:
   ```bash
   python3 shared/google-suite/skills/google-suite-ga4-analytics/scripts/validate_ga4_integration.py --path ./src --strict
   ```
2. Enable `{ debug_mode: true }` in development or use the Google Analytics Debugger extension.
3. Verify event payloads in real time within **Google Analytics > Admin > DebugView**.

---

## Gotchas & Common Pitfalls

| Legacy / Faulty Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Universal Analytics (UA-XXXXX-Y)** | **Google Analytics 4 (G-XXXXXXXXXX)** | Universal Analytics is fully deprecated and turned off by Google. |
| **Single Measurement ID on All Subdomains** | **Dedicated Data Streams per Subdomain** | Merging app and marketing traffic into one stream corrupts bounce rates and funnel metrics. |
| **Default Auto-Pageviews in SPAs** | `send_page_view: false` + Router Dispatch | Causes duplicate pageviews on initial load and misses subsequent client-side route transitions. |
| **Transmitting Plaintext Emails in Events** | Salted cryptographic hashes (`user_id_hash`) | Directly violates Google Terms of Service and triggers immediate account suspension. |
| **Unchecked `gtag()` Invocations** | Safe wrapper (`if (typeof window.gtag === 'function')`) | Throws unhandled `ReferenceError` when users run ad blockers or privacy extensions. |
| **CamelCase Event Names** (`toolExecute`) | **Normalized snake_case** (`tool_execute`) | Inconsistent casing creates fragmented duplicate events in GA4 reporting. |
