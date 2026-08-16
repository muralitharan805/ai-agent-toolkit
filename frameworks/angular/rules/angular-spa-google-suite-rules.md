---
description: "Rules for Angular Single Page Applications (CSR) integrating Google Search Console SEO, static sitemaps, GA4 SPA route tracking, legal pages, and AdSense."
trigger: always_on
---

# Angular SPA Google Suite Rules

## Description
Enforces mandatory standards for Angular Client-Side Rendered (CSR) applications integrating Google Search Console, GA4 Analytics, legal policy pages (`/privacy` & `/terms`), and AdSense.

## Constraints

### 1. Build Directory Alignment (`wrangler.jsonc`)
- Angular apps built with `@angular/build:application` MUST specify `pages_build_output_dir = "dist/<project-name>/browser"` in `wrangler.jsonc` to ensure static `sitemap.xml`, `robots.txt`, and `ads.txt` files residing in `public/` are served at root domain without SPA router 404 redirects.

### 2. GA4 NavigationEnd Tracking
- Single Page Applications MUST subscribe to `Router.events` (`NavigationEnd`) to emit `page_view` events to GA4 on route changes.

### 3. Keyword-Rich Route Title Rule (`app.routes.ts`)
- Route definitions MUST use descriptive, keyword-rich `title` strings (e.g. `title: 'Personal Finance & Net Worth Tracker'`).
- Bare, generic titles (such as `title: 'Login'` or `title: 'Home'`) are STRICTLY FORBIDDEN to prevent search crawlers from classifying the site as a private authentication gateway.

### 4. Legal Pages & Footer Navigation Rule
- Single Page Applications MUST declare standalone `PrivacyPolicyComponent` (`/privacy`) and `TermsOfServiceComponent` (`/terms`) components.
- Layout shells (`MainLayoutComponent`, `AuthLayoutComponent`) MUST include footer navigation links pointing to `/privacy` and `/terms`.
