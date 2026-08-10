---
description: "Workflow to scaffold Google Search Console, GA4, and AdSense in Angular Edge SSR applications. Triggered by 'setup-angular-ssr-google-suite:' or '/setup-angular-ssr-google-suite'."
trigger: manual
---

# Workflow: Setup Angular Edge SSR Google Suite

## Step 1: Add Sitemap Handler in `src/server.ts`
Implement raw XML Response handler for `/sitemap.xml` inside `createRequestHandler`.

## Step 2: Configure `public/_routes.json`
Exclude `/sitemap.xml`, `/robots.txt`, and `/assets/*` from Cloudflare Worker execution.

## Step 3: Inject Canonical, GA4 & AdSense Tags
1. Add default fallback `<link rel="canonical" href="https://yourdomain.com/" />` tag in `src/index.html`.
2. Add GA4 tag `G-XXXXXXXXXX` and AdSense publisher tag `ca-pub-XXXXXXXXXXXXXXXX` in `src/index.html` with `isPlatformBrowser` guarding.

## Step 4: Setup Dynamic Canonical `SeoService`
Implement SSR-safe `setCanonicalUrl()` in `SeoService` to update `<link rel="canonical">` during Edge SSR pre-rendering and CSR hydration.
