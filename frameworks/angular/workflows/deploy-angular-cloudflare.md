---
description: "Sequential workflow to build Angular 21 SSR application, run Vitest test suite, execute local Wrangler preview, and deploy to Cloudflare Pages/Workers."
trigger: manual
---
# Deploy Angular SSR to Cloudflare Workflow

## Objective
Provide a robust, end-to-end process for validating, testing, building, and deploying an Angular 21 SSR application (e.g. Seyalicraft Portfolio) to Cloudflare.

## Prerequisites
- Angular 21 project with `@angular/ssr` and `wrangler` CLI configured.
- Active Cloudflare authentication via `pnpm wrangler login`.

## Execution Steps

### Step 1: Pre-Build Test & Quality Validation
Execute Vitest test suite and type check:
````bash
pnpm test --run
pnpm ng build --configuration development
````

### Step 2: Production Bundle Build
Compile client browser bundles, server SSR engine, and static assets:
````bash
pnpm run build
````
- Verify build artifacts generated in `dist/[project-name]/browser/` and `dist/[project-name]/server/`.

### Step 3: Local Cloudflare Edge Preview
Launch local V8 isolate server via Wrangler to test SSR hydration and API endpoints:
````bash
pnpm run preview
````
- Test routing, asset loading, and browser console for NG0500 hydration warnings.

### Step 4: Production Cloudflare Deployment
Deploy the SSR application to Cloudflare Pages/Workers:
````bash
pnpm run deploy
````

### Step 5: Post-Deployment Verification
- Open deployed URL (e.g., `https://seyalicraft.com`).
- Check Network tab for HTTP 200 responses on server-rendered routes.
- Verify meta tags and OpenGraph headers for social showcase sharing.
