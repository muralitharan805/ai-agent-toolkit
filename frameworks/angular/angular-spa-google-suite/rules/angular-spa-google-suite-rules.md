---
trigger: model_decision
description: "Enforces standards for Angular Single Page Applications (CSR) integrating Google Search Console SEO, static sitemaps, GA4 SPA route tracking, legal pages, and AdSense."
---

# Angular Single Page Application (SPA) Google Suite Rules

## Description
This rule enforces enterprise-grade search engine optimization, privacy compliance, and web monetization standards for Angular Single Page Applications (CSR). It mandates dynamic canonical tag synchronization, keyword-rich route titles, Google Analytics 4 (GA4) route transition tracking via `Router.events` (`NavigationEnd`), Google AdSense Cumulative Layout Shift (CLS) prevention, and mandatory legal policy pages (`/privacy` and `/terms`) required for AdSense program policy compliance.

## Constraints

### 1. Keyword-Rich Route Title Invariant (`app.routes.ts`)
- All route definitions in `app.routes.ts` MUST declare descriptive, keyword-rich, human-readable `title` strings (e.g. `title: 'Personal Finance & Net Worth Tracker | Company Labs'`).
- Bare, generic, single-word titles (such as `title: 'Login'`, `title: 'Home'`, `title: 'Dashboard'`, `title: 'App'`) are STRICTLY FORBIDDEN.
- Generic titles trigger automated classification by search engine web crawlers as private authentication portals, resulting in crawler de-indexing and AdSense "Valuable Inventory: No Content" rejections.

### 2. Dynamic Canonical Tag & Meta Synchronization (`SeoService`)
- Every route navigation MUST synchronize the document's `<link rel="canonical">` element via a centralized `SeoService`.
- Canonical links MUST strip tracking query parameters (e.g. `?utm_source=...`, `?fbclid=...`, `?ref=...`) to eliminate duplicate indexing penalties across Google Search Console.
- Meta description (`<meta name="description">`), Open Graph (`og:title`, `og:description`, `og:url`), and Twitter card (`twitter:card`) tags MUST be updated dynamically upon each route change.

### 3. GA4 NavigationEnd Event Tracking (`AnalyticsService`)
- Single Page Applications do not trigger full browser document reload cycles during navigation. Therefore, the application MUST subscribe to `Router.events` filtered by `NavigationEnd` to emit page view events to Google Analytics 4 (`gtag('config', id, { page_path })`).
- Analytics payloads MUST NOT transmit Personally Identifiable Information (PII) such as plain-text passwords, auth tokens, email addresses, or phone numbers in route paths or event attributes.
- Google Analytics initialization MUST be guarded with `isPlatformBrowser(platformId)` to prevent runtime crashes if upgraded to SSR.

### 4. Mandatory Legal Policy Pages & Layout Footer Links
- Single Page Applications applying for or displaying Google AdSense MUST declare standalone `PrivacyPolicyComponent` (mapped to route `/privacy`) and `TermsOfServiceComponent` (mapped to route `/terms`).
- The Privacy Policy MUST explicitly disclose:
  1. Google AdSense third-party vendor advertising.
  2. Google DART cookie usage for personalized advertising.
  3. Direct opt-out instructions via Google Ads Settings (`https://www.google.com/settings/ads`).
- Application layout shells (`MainLayoutComponent`, `AuthLayoutComponent`) MUST include visible, crawlable footer navigation links pointing to `/privacy` and `/terms`.

### 5. Google AdSense Cumulative Layout Shift (CLS) Prevention
- Ad placement wrappers hosting `<ins class="adsbygoogle">` elements MUST declare an explicit minimum container height (`min-height: 250px` for medium rectangles or `min-height: 90px` for leaderboards) with `display: block`.
- Rendering dynamic ads without reserved container dimensions violates Core Web Vitals (CLS > 0.1) and triggers search ranking penalties.
- Ad rendering MUST be suppressed in local development environments (`localhost`, `127.0.0.1`) to prevent invalid impression logging.

### 6. Root Static Assets & Output Directory Alignment
- Applications MUST deploy valid static `public/sitemap.xml`, `public/robots.txt`, and `public/ads.txt` files.
- `public/ads.txt` MUST declare the verified publisher authorization line:
  ```text
  google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
  ```
- The build output directory in `wrangler.jsonc` (`pages_build_output_dir`) MUST match the Angular build output directory (`dist/<project-name>/browser`) to ensure root files are served at the apex domain without client router fallback intercepts.

## Examples

### Correct Implementation

```typescript
// src/app/app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'Enterprise Portfolio & Technology Showcase | Labs',
    loadComponent: () => import('./features/home/home-page.component').then(m => m.HomePageComponent)
  },
  {
    path: 'privacy',
    title: 'Privacy Policy & Cookie Disclosures | Labs',
    loadComponent: () => import('./features/legal/privacy-policy.component').then(m => m.PrivacyPolicyComponent)
  },
  {
    path: 'terms',
    title: 'Terms of Service & Usage Agreement | Labs',
    loadComponent: () => import('./features/legal/terms-of-service.component').then(m => m.TermsOfServiceComponent)
  }
];
```

```typescript
// src/app/core/services/analytics.service.ts
import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly router = inject(Router);
  private readonly platformId = inject(PLATFORM_ID);

  init(measurementId: string): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        if (typeof window !== 'undefined' && typeof (window as any).gtag === 'function') {
          (window as any).gtag('config', measurementId, {
            page_path: event.urlAfterRedirects
          });
        }
      });
  }
}
```

```html
<!-- AdSense Container with CLS Space Reservation -->
<div class="ad-wrapper" style="min-height: 250px; width: 100%; display: block;">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-1649083292065809"
       data-ad-slot="1234567890"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
</div>
```

### Incorrect Implementation (STRICTLY FORBIDDEN)

```typescript
// ❌ ANTI-PATTERN: Bare titles, missing GA4 route tracking, unreserved ad containers
export const badRoutes: Routes = [
  // FORBIDDEN: Bare, non-descriptive title flags site as private gateway
  { path: '', title: 'Home', component: HomeComponent },
  { path: 'login', title: 'Login', component: LoginComponent }
  // FORBIDDEN: Missing /privacy and /terms routes triggers AdSense rejection
];

// FORBIDDEN: Zero container reservation causes severe CLS layout shifts!
// <div class="ad-box"><ins class="adsbygoogle"></ins></div>
```
