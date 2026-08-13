---
description: "Workflow to scaffold Google Search Console, GA4, and AdSense in Angular CSR SPA applications. Triggered by 'setup-angular-spa-google-suite:' or '/setup-angular-spa-google-suite'."
trigger: manual
---

# Workflow: Setup Angular SPA Google Suite

## Step 1: Generate `public/sitemap.xml` & `public/robots.txt`
1. Place static `sitemap.xml` in `public/`.
2. Place `robots.txt` in `public/`.

## Step 2: Configure `wrangler.jsonc` Output Directory
Ensure `wrangler.jsonc` specifies `"pages_build_output_dir": "dist/<app-name>/browser"`.

## Step 3: Inject Canonical, GA4 & AdSense in `src/index.html`
1. Add default `<link rel="canonical" href="https://yourdomain.com/" />` tag in `index.html`.
2. Add GA4 script tag `G-XXXXXXXXXX`.
3. Add AdSense publisher tag `ca-pub-XXXXXXXXXXXXXXXX`.
4. Add JSON-LD WebApplication schema.

## Step 4: Setup `SeoService` for Dynamic Canonical Tags
Implement `setCanonicalUrl()` in `SeoService` to update `<link rel="canonical">` on SPA route navigation.

## Step 5: Deploy `public/ads.txt` & SPA Routing `public/_redirects`
1. Create `public/ads.txt` declaring publisher authorization:
   ```text
   google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
   ```
2. Create `public/_redirects` for Cloudflare Pages SPA client routing fallback:
   ```text
   /*    /index.html   200
   ```
