---
trigger: model_decision
description: "Mandates SPA routing fallback (_redirects), build output configuration, security headers, and deployment safety for Angular SPAs deployed on Cloudflare Pages."
---

# Angular Single Page Application (SPA) Cloudflare Pages Deployment Rule

## Description
This rule enforces mandatory static routing fallback configurations (`_redirects`), edge cache headers (`_headers`), build output directory alignment, and deployment safety for client-side rendered (CSR) Angular Single Page Applications hosted on Cloudflare Pages. It prevents HTTP 404 routing errors on deep links, prevents stale client chunk caching, and ensures deterministic CI/CD deployments.

## Constraints

### 1. Mandatory Client-Side Routing Fallback (`_redirects`)
- Every Angular SPA deployed to Cloudflare Pages MUST include a `public/_redirects` file (or `src/assets/_redirects` registered in `angular.json` assets).
- The `_redirects` file MUST contain the exact wildcard fallback rule:
  ```text
  /*  /index.html  200
  ```
- Direct deep link browser navigation (e.g. `https://example.com/dashboard`, `https://example.com/settings/profile`) MUST NOT return Cloudflare 404 Not Found errors.
- Pre-deployment validation scripts MUST verify that `_redirects` exists in the build output target directory prior to deployment.

### 2. Edge Cache Invalidation & Security Headers (`_headers`)
- To prevent browsers and Cloudflare edge nodes from aggressively caching `index.html` across application releases, the project MUST include a `public/_headers` file.
- The `_headers` file MUST enforce `no-cache` on HTML documents while applying security headers:
  ```text
  /*
    X-Frame-Options: DENY
    X-Content-Type-Options: nosniff
    Referrer-Policy: strict-origin-when-cross-origin
  /index.html
    Cache-Control: no-cache, no-store, must-revalidate
  ```
- Hashed JavaScript and CSS chunks (`main-[hash].js`, `styles-[hash].css`) benefit from immutable caching automatically; `index.html` must remain fresh.

### 3. Build Output Directory & `wrangler.jsonc` Alignment
- Angular applications built with `@angular/build:application` output artifacts to `dist/<project-name>/browser`.
- The `wrangler.jsonc` configuration file MUST align its build output path with this exact path:
  ```jsonc
  {
    "$schema": "node_modules/wrangler/config-schema.json",
    "name": "<project-name>",
    "pages_build_output_dir": "dist/<project-name>/browser",
    "compatibility_date": "2026-07-26"
  }
  ```
- Any mismatch between `angular.json` output path and `wrangler.jsonc` will result in empty deployment payloads and broken sites.

### 4. Client-Side Only Runtime Boundaries
- Pure Angular SPAs execute strictly within the browser DOM context, not within server V8 isolates.
- Browser APIs (`window`, `localStorage`, `document`) are directly available at runtime. However, code interacting with these globals MUST still check `isPlatformBrowser(platformId)` to maintain forward-compatibility should the application ever migrate to Server-Side Rendering (SSR).
- Services communicating with local backend APIs during development MUST route through relative paths (`/api`) via development proxies rather than hardcoded URLs.

### 5. Package Manager & Script Standards (`package.json`)
- All build, preview, and deployment commands MUST strictly use `pnpm`:
  - `"build"`: `ng build --configuration=production`
  - `"preview"`: `pnpm run build && wrangler pages dev dist/<project-name>/browser`
  - `"deploy"`: `pnpm run build && wrangler pages deploy dist/<project-name>/browser --project-name=<project-name>`
- `wrangler` MUST be installed under `devDependencies` in `package.json`.

### 6. Anti-Automation Deployment Guard
- AI agents MUST NOT unilaterally execute live production deployment commands (e.g. `wrangler pages deploy` or `pnpm run deploy`) without explicit user consent.
- Automated deployments consume Cloudflare project build quotas and generate unwanted deployment URLs. Agents MUST verify builds locally using `wrangler pages dev` preview and provide the deployment CLI command for user execution.

## Examples

### Correct Implementation

```jsonc
// wrangler.jsonc (Root directory)
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "enterprise-spa",
  "pages_build_output_dir": "dist/enterprise-spa/browser",
  "compatibility_date": "2026-07-26"
}
```

```text
# public/_redirects (Ensures client-side router handles deep links)
/*  /index.html  200
```

```text
# public/_headers (Prevents stale index.html and injects security headers)
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
/index.html
  Cache-Control: no-cache, no-store, must-revalidate
```

```json
// package.json (Standardized scripts using pnpm)
{
  "scripts": {
    "build": "ng build --configuration=production",
    "preview": "pnpm run build && wrangler pages dev dist/enterprise-spa/browser",
    "deploy": "pnpm run build && wrangler pages deploy dist/enterprise-spa/browser --project-name=enterprise-spa"
  },
  "devDependencies": {
    "wrangler": "^3.100.0"
  }
}
```

### Incorrect Implementation (STRICTLY FORBIDDEN)

```text
# ❌ FORBIDDEN: Missing public/_redirects causes Cloudflare 404 on deep links
# Navigating directly to https://example.com/dashboard returns Cloudflare 404!
```

```jsonc
// ❌ FORBIDDEN: Mismatched output directory
{
  "name": "broken-spa",
  // ERROR: Points to root dist instead of dist/broken-spa/browser!
  "pages_build_output_dir": "dist"
}
```
