---
description: "Sequential workflow to build Angular SPA (CSR), verify client-side _redirects fallback file, test local Wrangler Pages preview, and deploy to Cloudflare Pages. Triggered by 'deploy-spa:', 'cloudflare-spa:', or '/deploy-angular-spa-cloudflare'."
trigger: manual
---

# Deploy Angular SPA (CSR) to Cloudflare Pages Workflow

This workflow guides the developer and AI agent through building, testing, and deploying a pure Angular Single Page Application (CSR) to Cloudflare Pages with client-side fallback routing (`_redirects`).

---

## Step 1: Pre-Build Validation & Test Execution

1. Run Vitest / Karma test suite:
   ```bash
   pnpm test --run
   ```
2. Verify TypeScript type checking and production build configurations:
   ```bash
   pnpm ng build --configuration development
   ```

---

## Step 2: Configure SPA Client-Side Routing Fallback (`_redirects`)

1. Verify `public/_redirects` exists with exact content:
   ```text
   /*  /index.html  200
   ```
2. If missing, create `public/_redirects`:
   ```bash
   echo '/*  /index.html  200' > public/_redirects
   ```

---

## Step 3: Production Bundle Build

Execute production build:
```bash
pnpm run build
```
- Confirm build output generated in `dist/[project-name]/browser/` or `dist/[project-name]/`.
- Verify `index.html` and `_redirects` are present in the output folder.

---

## Step 4: Local Cloudflare Pages Preview

Launch Wrangler local dev server to test client-side routing and fallback:
```bash
pnpm wrangler pages dev dist/[project-name]/browser
```
- Open test URL (e.g. `http://localhost:8788/dashboard`).
- Refresh deep link routes to verify HTTP 200 SPA fallback response.

---

## Step 5: Production Cloudflare Deployment

Deploy static SPA bundle to Cloudflare Pages:
```bash
pnpm wrangler pages deploy dist/[project-name]/browser --project-name=[project-name]
```

---

## Step 6: Post-Deployment Verification

1. Access production URL (e.g. `https://<your-project-domain.com>`).
2. Test direct URL navigation to deep client routes (e.g. `/settings`, `/dashboard`).
3. Verify zero 404 errors on deep link reloads.
