# GA4 Stream Isolation & SPA Route Tracking Architecture

## Overview
Google Analytics 4 (GA4) uses an event-based data model centered on **Data Streams** and **Measurement IDs** (`G-XXXXXXXXXX`). In enterprise architectures and multi-tenant applications, improper stream configuration leads to cross-traffic pollution, duplicate pageviews, and PII leakage.

---

## 1. Subdomain Data Stream Isolation
When an organization deploys multiple services across subdomains (e.g., `company.com` marketing site, `app.company.com` authenticated portal, and `tools.company.com` developer utilities), each subdomain MUST be isolated:

### Recommended Setup
- **Dedicated Web Data Streams**: Create a distinct Web Data Stream in GA4 for each subdomain.
  - Marketing Portal: `G-MKT1000000`
  - Customer App: `G-APP2000000`
  - Utility Tools: `G-TLS3000000`
- **Avoid Cross-Stream Contamination**: Never hardcode the marketing measurement ID into the authenticated application codebase.
- **Rollup Property (Optional)**: If aggregate corporate analytics are required, configure GA4 360 Rollup Properties rather than sharing a single measurement ID across unrelated subdomains.

---

## 2. SPA Route Change Tracking (Angular / React / Vue)
Single Page Applications (SPAs) do not trigger full browser page reloads when users navigate between routes. By default, standard `gtag.js` snippets only capture the initial landing page.

### Critical SPA Configuration: Disable Auto Pageviews
When embedding `gtag.js` in an SPA `index.html`, disable automatic pageview dispatch to prevent duplicate initial tracking:

```html
<!-- Google tag (gtag.js) GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  // CRITICAL: Disable automatic page_view in SPAs
  gtag('config', 'G-XXXXXXXXXX', {
    send_page_view: false
  });
</script>
```

### Dispatching Pageviews on Route Change (Angular Example)
In Angular (v19+), listen to `Router` `NavigationEnd` events in the core analytics service:

```typescript
import { Injectable, inject } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';

declare global {
  interface Window {
    gtag?: (command: string, ...args: unknown[]) => void;
  }
}

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly router = inject(Router);

  initSpaTracking(measurementId: string): void {
    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event) => {
        this.trackPageView(event.urlAfterRedirects, measurementId);
      });
  }

  trackPageView(path: string, measurementId: string): void {
    if (typeof window.gtag === 'function') {
      window.gtag('event', 'page_view', {
        page_path: path,
        page_title: document.title,
        page_location: window.location.href,
        send_to: measurementId
      });
    }
  }
}
```

---

## 3. Mandatory PII Redaction
Google's terms of service strictly prohibit transmitting Personally Identifiable Information (PII) to GA4. Sending PII can result in immediate property suspension.

### Strict Redaction Rules
1. **Never Send Emails, Passwords, or User Names** in custom event parameters.
2. **Scrub URL Query Parameters**: Ensure tokens, reset codes, and email addresses (`?email=user@example.com`) are stripped from `page_location` before emitting `page_view`.
3. **Pseudonymous User IDs**: If tracking user journeys across sessions, pass exclusively opaque, salted hashes (e.g. `uuidv4` or SHA-256 user IDs):
   ```javascript
   gtag('set', 'user_properties', {
     user_id_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
   });
   ```

---

## 4. Debugging & GA4 DebugView
To test real-time events without waiting for standard 24-hour processing:
1. Pass `{ debug_mode: true }` in `gtag('config', ...)` during local development (`localhost` or staging).
2. Install the **Google Analytics Debugger** Chrome extension.
3. Open **Google Analytics > Admin > DebugView** to observe granular event parameters, user properties, and validation errors in real time.
