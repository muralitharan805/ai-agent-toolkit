---
trigger: always_on
description: "Mandates SPA routing fallback (_redirects), build output configuration, and client-side performance standards for Angular SPAs deployed on Cloudflare Pages."
---

# Angular Single Page Application (SPA) Cloudflare Pages Rules

## Description
Enforces mandatory static routing rules, SPA fallback configuration (`_redirects`), client-side asset caching, and Cloudflare Pages deployment safety for pure Angular Single Page Applications (CSR).

## Constraints

### 1. Mandatory SPA Client-Side Routing Fallback (`_redirects`)
- Every Angular SPA deployed to Cloudflare Pages MUST contain a `public/_redirects` file (or `src/assets/_redirects` configured in `angular.json` assets):
  ```text
  /*  /index.html  200
  ```
- Direct link navigations (e.g. `/dashboard`, `/transactions`, `/settings`) MUST NOT return Cloudflare 404 errors.

### 2. Output Directory & Wrangler Alignment
- `angular.json` build output path MUST match `pages_build_output_dir` in `wrangler.jsonc` (typically `dist/[project-name]/browser` or `dist/[project-name]`).
- Verification check MUST confirm `index.html` exists in the deployment target directory before triggering `wrangler pages deploy`.

### 3. Client-Side Only Constraints
- Angular SPA components do NOT run on server V8 isolates; all lifecycle hooks (`ngOnInit`, `ngAfterViewInit`) execute in the browser.
- Browser APIs (`window`, `localStorage`, `document`) are directly available, but MUST still handle SSR mock compatibility if the app is later upgraded to SSR.

### 4. Package Manager & Script Standards
- All build and deployment commands MUST strictly use `pnpm` (`pnpm run build`, `pnpm run deploy`).
- `wrangler` dependency MUST be declared under `devDependencies` in `package.json`.
