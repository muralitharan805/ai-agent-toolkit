---
description: "Universal workflow to scaffold Google Search Console, GA4, and AdSense for Edge Server-Side Rendered (SSR) Applications. Triggered by 'setup-google-suite-ssr:' or '/setup-google-suite-ssr'."
trigger: manual
---

# Universal Workflow: Setup Google Suite for Edge SSR Applications

## Step 1: Create Edge Dynamic XML Response Handler
Implement `/sitemap.xml` request handler in `server.ts` returning direct `Response` with `application/xml` headers.

## Step 2: Configure Edge Route Exclusion (`_routes.json`)
Exclude `/sitemap.xml`, `/robots.txt`, and `/assets/*` from Worker execution to allow direct CDN streaming.

## Step 3: Inject GA4 & AdSense Tags with SSR Platform Guarding
Ensure all browser APIs (`window.gtag`, `window.adsbygoogle`) are strictly guarded during server isolates.
