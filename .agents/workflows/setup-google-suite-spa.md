---
description: "Universal workflow to scaffold Google Search Console, GA4, and AdSense for Single Page Applications (SPA/CSR). Triggered by 'setup-google-suite-spa:' or '/setup-google-suite-spa'."
trigger: manual
---

# Universal Workflow: Setup Google Suite for SPA Applications

## Step 1: Create Static `public/sitemap.xml` & `public/robots.txt`
1. Create `public/sitemap.xml` containing all canonical page URLs.
2. Create `public/robots.txt` pointing to `https://yourdomain.com/sitemap.xml`.

## Step 2: Inject Canonical, GA4 & AdSense Head Tags
1. Add default fallback `<link rel="canonical" href="https://yourdomain.com/" />` tag in `index.html`.
2. Add GA4 tag `G-XXXXXXXXXX` in `index.html`.
3. Add AdSense publisher script `ca-pub-XXXXXXXXXXXXXXXX` in `index.html`.
4. Configure `SeoService` to update `<link rel="canonical">` dynamically on SPA route changes.

## Step 3: Enforce Domain 301 Redirections & Cloudflare Config
1. Turn ON "Always Use HTTPS" in Cloudflare.
2. Create 301 Page/Redirect Rule for `www` to apex domain (`https://yourdomain.com/`).

## Step 4: Configure Cloudflare Pages Output Directory
Ensure build configuration output directory points directly to static assets (e.g. `dist/app/browser`).
