---
description: "Rules for Angular Edge SSR applications integrating Google Search Console XML streams, Cloudflare Edge bypass routing, legal policy pages, and hydration safety."
trigger: always_on
---

# Angular Edge SSR Google Suite Rules

## Description
Enforces mandatory standards for Angular Server-Side Rendered (SSR) applications running on Cloudflare Workers edge isolate runtime integrating Google Search Console, GA4, AdSense, and legal policy pages (`/privacy` & `/terms`).

## Constraints

### 1. Dynamic XML Response Stream (`src/server.ts`)
- Angular SSR applications MUST intercept `/sitemap.xml` in `src/server.ts` `createRequestHandler` and return a raw `Response` with `application/xml; charset=UTF-8` content type.

### 2. Edge Route Bypass (`public/_routes.json`)
- Static sitemaps (`/sitemap.xml`), robots protocol (`/robots.txt`), AdSense authorization (`/ads.txt`), and asset paths MUST be explicitly listed under `exclude` in `public/_routes.json` to allow direct CDN streaming without Worker invocation.

### 3. Hydration Guarding (`isPlatformBrowser`)
- All Google Analytics (`gtag`) and AdSense (`adsbygoogle`) scripts MUST check `isPlatformBrowser(this.platformId)` before accessing `window` or `document` to prevent V8 isolate SSR execution crashes.

### 4. Keyword-Rich Route Title Rule (`app.routes.ts`)
- Route definitions MUST specify keyword-rich `title` properties (e.g. `title: 'Personal Finance & Net Worth Tracker'`).
- Bare titles like `'Login'` or `'Home'` are STRICTLY FORBIDDEN to prevent search engine bots from categorizing SSR pages as private login gates.

### 5. SSR Legal Policy Pages & Layout Shell Links
- SSR applications MUST register standalone `PrivacyPolicyComponent` (`/privacy`) and `TermsOfServiceComponent` (`/terms`) with SSR-safe `PLATFORM_ID` guarding.
- Application layout footers MUST include static links to `/privacy` and `/terms` to comply with AdSense Program Policies.
