---
description: "Universal workflow to scaffold Google Search Console, GA4, and AdSense for Edge Server-Side Rendered (SSR) Applications. Triggered by 'setup-google-suite-ssr:' or '/setup-google-suite-ssr'."
trigger: manual
---

# Universal Workflow: Setup Google Suite for Edge SSR Applications

## Step 1: Create Edge Dynamic XML Response Handler
Implement `/sitemap.xml` request handler in `server.ts` returning direct `Response` with `application/xml` headers.

## Step 2: Configure Edge Route Exclusion (`_routes.json`)
Exclude `/sitemap.xml`, `/robots.txt`, and `/assets/*` from Worker execution to allow direct CDN streaming.

## Step 3: Inject Canonical, GA4 & AdSense Tags with SSR Platform Guarding
1. Add default fallback `<link rel="canonical" href="https://yourdomain.com/" />` tag in `index.html`.
2. Ensure `SeoService` dynamically updates `<link rel="canonical">` during Edge SSR pre-rendering and CSR hydration.
3. Ensure all browser APIs (`window.gtag`, `window.adsbygoogle`) are strictly guarded during server isolates.

## Step 4: Enforce Domain 301 Redirections & Cloudflare Config
1. Turn ON "Always Use HTTPS" in Cloudflare.
2. Create 301 Page/Redirect Rule for `www` to apex domain (`https://yourdomain.com/`).
