---
name: cloudflare-angular-spa-deployment
description: Best practices, Wrangler configuration, client-side routing fallback (_redirects), asset caching, and deployment guidelines for Angular Single Page Applications (SPA/CSR) on Cloudflare Pages.
---

# Cloudflare Pages Angular SPA (Client-Side Rendering) Deployment Skill

## Goal
Guide developers and AI coding agents in configuring, building, and deploying pure **Angular Single Page Applications (SPA / CSR)** to **Cloudflare Pages** with high performance, instant client-side route fallback handling (`/index.html`), edge static caching, and automated deployment pipelines for **ANY Angular project**.

---

## Core Architecture Principles

### 1. Angular SPA (CSR) Build Output
Unlike Angular SSR, pure Angular SPA applications compile exclusively into a static client-side bundle:
- **Build Output Directory**: `dist/<project-name>/browser/` (or `dist/<project-name>/`)
- **Key Files**: `index.html`, main JavaScript chunks (`main.js`, `polyfills.js`), component styles (`styles.css`), and static assets (`public/` or `assets/`).

### 2. Client-Side Routing Fallback (`_redirects` / `_routes.json`)
Since Angular SPAs use client-side router (`RouterModule` / `provideRouter`), any direct deep link (e.g. `https://<your-domain.com>/dashboard` or `/settings`) requested from Cloudflare edge must fall back to `/index.html` with HTTP 200 status code:

#### `public/_redirects` (Recommended for Cloudflare Pages):
```text
/*  /index.html  200
```
*Note: Placing `_redirects` in `public/_redirects` (or `src/assets/_redirects`) ensures Angular CLI copies it directly to the root of the build output.*

### 3. Custom Headers (`_headers`)
To prevent aggressive caching of `index.html` (ensuring users always get the latest version of the app) and apply security headers, the agent MUST generate a `public/_headers` (or `src/assets/_headers`) file:
```text
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
/index.html
  Cache-Control: no-cache, no-store, must-revalidate
```

---

## Wrangler & Deployment Configuration

### 1. Generic `wrangler.jsonc` Configuration
```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "<project-name>",
  "pages_build_output_dir": "dist/<project-name>/browser",
  "compatibility_date": "2026-07-26"
}
```

### 2. Generic `package.json` Deployment Scripts
```json
{
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build --configuration production",
    "preview": "pnpm run build && wrangler pages dev dist/<project-name>/browser",
    "deploy": "pnpm run build && wrangler pages deploy dist/<project-name>/browser --project-name=<project-name>"
  }
}
```

### 3. `.gitignore` Configuration
The agent MUST ensure the following Cloudflare and build temporary directories are added to the project's `.gitignore`:
```text
# Cloudflare Pages / Wrangler
.wrangler/
.dev.vars
dist/
.angular/cache/
```

### 4. `package.json` Scripts Configuration
The agent MUST explicitly inject the following Cloudflare CLI commands into the target project's `package.json` under `"scripts"` (adjusting `<project-name>` accordingly):
- `"preview": "pnpm run build && wrangler pages dev dist/<project-name>/browser"`
- `"deploy": "pnpm run build && wrangler pages deploy dist/<project-name>/browser --project-name=<project-name>"`

### 5. Environment Variables & Build Configuration
The agent MUST document the following in the README:
- **Local Dev**: Use a `.dev.vars` file for local Wrangler secrets (this is auto-ignored).
- **Cloudflare Dashboard**: The user MUST set the `NODE_VERSION` environment variable (e.g., `20`) in the Cloudflare Pages settings so the Angular CLI runs in the correct environment during CI builds.

---

## Performance & Cache Optimization

1. **Aggressive Static Asset Caching**:
   - Cloudflare Pages automatically caches hashed JavaScript and CSS bundles with long TTLs.
   - Serve static images and web fonts with immutable cache headers.
2. **Preconnect Links**:
   - Embed `<link rel="preconnect" href="https://fonts.gstatic.com">` in `src/index.html` for zero render-blocking Google Fonts loading.
3. **PWA & Web Worker Integration**:
   - Angular SPAs on Cloudflare Pages seamlessly integrate with `@angular/service-worker` for offline asset caching.

---

## README Execution Documentation Standard

The agent MUST generate or update a dedicated section in the `README.md` explaining how to execute and deploy the application. It MUST include:
1. **Local Preview**: Instructions on how to build and test the app locally using Wrangler (`pnpm run preview`).
2. **Cloudflare Deployment**: Instructions on how to manually deploy the SPA bundle directly to Cloudflare Pages (`pnpm run deploy`).

---

## Deployment CLI Commands

```bash
# Build production bundle
pnpm run build

# Preview SPA locally on Cloudflare Pages dev server
pnpm run preview

# Deploy SPA bundle directly to Cloudflare Pages
pnpm run deploy
```
