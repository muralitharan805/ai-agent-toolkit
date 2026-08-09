---
description: "Universal workflow to scaffold Google Search Console, GA4, and AdSense for Single Page Applications (SPA/CSR). Triggered by 'setup-google-suite-spa:' or '/setup-google-suite-spa'."
trigger: manual
---

# Universal Workflow: Setup Google Suite for SPA Applications

## Step 1: Create Static `public/sitemap.xml` & `public/robots.txt`
1. Create `public/sitemap.xml` containing all canonical page URLs.
2. Create `public/robots.txt` pointing to `https://yourdomain.com/sitemap.xml`.

## Step 2: Inject GA4 & AdSense Head Tags
1. Add GA4 tag `G-XXXXXXXXXX` in `index.html`.
2. Add AdSense publisher script `ca-pub-XXXXXXXXXXXXXXXX` in `index.html`.

## Step 3: Configure Cloudflare Pages Output Directory
Ensure build configuration output directory points directly to static assets (e.g. `dist/app/browser`).
