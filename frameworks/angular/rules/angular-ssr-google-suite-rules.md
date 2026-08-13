---
description: "Rules for Angular Edge SSR applications integrating Google Search Console XML streams, Cloudflare Edge bypass routing, and hydration safety."
trigger: always_on
---

# Angular Edge SSR Google Suite Rules

## Description
Enforces mandatory standards for Angular Server-Side Rendered (SSR) applications running on Cloudflare Workers edge isolate runtime.

## Constraints

### 1. Dynamic XML Response Stream (`src/server.ts`)
- Angular SSR applications MUST intercept `/sitemap.xml` in `src/server.ts` `createRequestHandler` and return a raw `Response` with `application/xml; charset=UTF-8` content type.

### 2. Edge Route Bypass (`public/_routes.json`)
- Static sitemaps (`/sitemap.xml`), robots protocol (`/robots.txt`), AdSense authorization (`/ads.txt`), and asset paths MUST be explicitly listed under `exclude` in `public/_routes.json` to allow direct CDN streaming without Worker invocation.

### 3. Hydration Guarding (`isPlatformBrowser`)
- All Google Analytics (`gtag`) and AdSense (`adsbygoogle`) scripts MUST check `isPlatformBrowser(this.platformId)` before accessing `window` or `document`.
