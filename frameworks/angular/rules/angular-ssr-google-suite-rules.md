---
description: "Enforces mandatory Google Search Console XML streams, Cloudflare Edge bypass routing (_routes.json), SSR-safe legal policy pages, and hydration safety for Angular SSR."
trigger: model_decision
---

# Angular Edge SSR Google Suite & SEO Monetization Rules

## Description
This rule enforces mandatory search engine optimization (Google Search Console), client telemetry (GA4), advertising monetization (Google AdSense), and legal compliance standards for Angular Server-Side Rendered (SSR) applications running on Cloudflare Workers edge isolate runtime. Edge-rendered applications must stream valid XML sitemaps dynamically, bypass edge workers for static CDN assets, provide keyword-rich pre-rendered titles, and prevent hydration mismatch errors while complying with Google AdSense program policies.

---

## Constraints

### 1. Dynamic XML Response Stream (`src/server.ts`)
- Angular SSR applications on Cloudflare Workers MUST intercept incoming HTTP GET requests for `/sitemap.xml` inside the edge request handler (`createRequestHandler` or `server.ts`).
- The handler MUST return a raw, native Web `Response` object with:
  - Header `'Content-Type': 'application/xml; charset=UTF-8'`
  - Cache header `'Cache-Control': 'public, max-age=86400, s-maxage=86400'`
  - Canonical URL nodes for `/`, `/privacy`, `/terms`, and key domain features with `<lastmod>`, `<changefreq>`, and `<priority>` tags.
- Applications MUST NOT rely on client-side routing to serve `/sitemap.xml`.

### 2. Edge Route Bypass Manifest (`public/_routes.json`)
- To optimize edge execution costs and eliminate unnecessary V8 isolate worker invocations, Cloudflare Pages applications MUST maintain a `public/_routes.json` manifest.
- Static assets, sitemaps, robots protocol, and publisher verification files MUST be explicitly listed under the `exclude` array:
  ```json
  {
    "version": 1,
    "include": ["/*"],
    "exclude": [
      "/sitemap.xml",
      "/robots.txt",
      "/ads.txt",
      "/favicon.ico",
      "/assets/*"
    ]
  }
  ```

### 3. Hydration Guarding & Browser Global Isolation
- In SSR environments, Google Analytics (`gtag.js`) and Google AdSense (`adsbygoogle`) scripts MUST NEVER be invoked directly on the server.
- All telemetry and ad injection logic MUST check `isPlatformBrowser(this.platformId)` before accessing `window.gtag` or pushing to `window.adsbygoogle`.
- Server-side attempts to access `window` or `document` will crash the V8 isolate worker immediately.

### 4. Keyword-Rich Route Title Rule (`app.routes.ts`)
- Route definitions in Angular SSR applications MUST declare descriptive, keyword-rich `title` strings:
  - **Permitted**: `title: 'Real-Time Financial Dashboard & Net Worth Tracker'`
  - **Permitted**: `title: 'Privacy Policy & Cookie Disclosures'`
- Bare, generic titles (such as `title: 'Home'`, `title: 'Login'`, `title: 'Dashboard'`, `title: 'App'`) are STRICTLY FORBIDDEN. Search engine bots pre-render SSR HTML and categorize bare titles as low-quality or private login barriers.

### 5. Mandatory SSR-Safe Legal Policy Pages (`/privacy` & `/terms`)
- To fulfill Google AdSense Program Policies and avoid immediate application rejections under "Valuable Inventory" standards, applications MUST deploy public legal policy routes:
  1. `/privacy`: Standalone `PrivacyPolicyComponent` explicitly disclosing:
     - Collection of non-PII telemetry via Google Analytics (GA4).
     - Third-party advertising cookies utilized by Google AdSense.
     - Google DART cookie disclosures for personalized ad serving.
     - Direct hyperlink to opt out via Google Ads Settings (`https://www.google.com/settings/ads`).
  2. `/terms`: Standalone `TermsOfServiceComponent` establishing acceptable usage and disclaimers.
- Both components MUST be standalone, use `ChangeDetectionStrategy.OnPush`, and guard browser-only interactions using `PLATFORM_ID`.
- Application layout footers MUST maintain persistent, visible navigation links to both `/privacy` and `/terms`.

### 6. Cumulative Layout Shift (CLS) Prevention in Ad Units
- Google AdSense `<ins class="adsbygoogle">` containers MUST declare explicit minimum vertical dimensions (`min-height: 250px` or `min-height: 90px`) to reserve layout space prior to asynchronous script execution.
- Un-reserved ad units that cause layout shifts will trigger Google Web Vitals CLS penalties and lower SEO ranking.

### 7. Zero `any` Type Safety & Clean Code Compliance
- All SEO services, route configurations, analytics managers, and server handlers MUST be strictly typed without explicit `any` annotations.

---

## Examples

### 1. Correct Implementation: Edge Request Handler with XML Stream (`src/server.ts`)

```typescript
import { AngularAppEngine, createRequestHandler } from '@angular/ssr';

const angularApp = new AngularAppEngine();

/** Static XML sitemap payload with canonical route definitions */
const SITEMAP_XML = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yourdomain.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://yourdomain.com/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://yourdomain.com/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>`;

/**
 * Cloudflare Worker request handler intercepting static sitemaps
 * and delegating dynamic SSR rendering to AngularAppEngine.
 *
 * @param req - The incoming native Web Request object
 * @returns Web standard Response stream
 */
export const reqHandler = createRequestHandler(async (req: Request): Promise<Response> => {
  const url = new URL(req.url);
  const pathname = url.pathname.toLowerCase().replace(/\/$/, '');

  if (pathname === '/sitemap.xml') {
    return new Response(SITEMAP_XML, {
      status: 200,
      headers: {
        'Content-Type': 'application/xml; charset=UTF-8',
        'Cache-Control': 'public, max-age=86400, s-maxage=86400'
      }
    });
  }

  const response = await angularApp.handle(req);
  return response ?? new Response('Not Found', { status: 404 });
});

export default {
  fetch: reqHandler,
};
```

### 2. Incorrect Implementation (STRICTLY FORBIDDEN)

```typescript
// ❌ CRITICAL ERRORS:
// 1. Bare, generic route titles hurt SEO indexing.
// 2. Direct window access inside component constructor crashes V8 isolate on server.
// 3. Missing /privacy and /terms routes causes AdSense rejection.
// 4. Using explicit 'any' annotations violates Clean Code standards.

export const routes: Routes = [
  { path: '', title: 'Home', component: HomeComponent }, // ❌ Bare title forbidden!
  { path: 'login', title: 'Login', component: LoginComponent } // ❌ Bare title forbidden!
  // ❌ Missing /privacy and /terms legal routes!
];

@Component({ ... })
export class BrokenAnalyticsComponent {
  constructor() {
    // ❌ FATAL: Direct window.gtag call during SSR crashes Cloudflare worker!
    (window as any).gtag('config', 'G-XXXXXXXXXX');
  }
}
```
