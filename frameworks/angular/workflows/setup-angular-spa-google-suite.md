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

## Step 3: Inject GA4 & AdSense in `src/index.html`
1. Add GA4 script tag `G-XXXXXXXXXX`.
2. Add AdSense publisher tag `ca-pub-XXXXXXXXXXXXXXXX`.
3. Add JSON-LD WebApplication schema.
