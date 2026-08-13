---
description: "Rules for Angular Single Page Applications (CSR) integrating Google Search Console SEO, static sitemaps, GA4 SPA route tracking, and AdSense."
trigger: always_on
---

# Angular SPA Google Suite Rules

## Description
Enforces mandatory standards for Angular Client-Side Rendered (CSR) applications integrating Google Search Console, GA4 Analytics, and AdSense.

## Constraints

### 1. Build Directory Alignment (`wrangler.jsonc`)
- Angular apps built with `@angular/build:application` MUST specify `pages_build_output_dir = "dist/<project-name>/browser"` in `wrangler.jsonc` to ensure static `sitemap.xml`, `robots.txt`, and `ads.txt` files residing in `public/` are served at root domain without SPA router 404 redirects.

### 2. GA4 NavigationEnd Tracking
- Single Page Applications MUST subscribe to `Router.events` (`NavigationEnd`) to emit `page_view` events to GA4 on route changes.
