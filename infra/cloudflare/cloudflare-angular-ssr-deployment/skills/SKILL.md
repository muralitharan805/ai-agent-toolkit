---
name: cloudflare-angular-ssr-deployment
description: "Best practices, architecture, wrangler configuration, and hydration guidelines for deploying Angular 21 SSR applications on Cloudflare Pages and Workers."
---
# Cloudflare Angular 21 SSR Deployment Skill

## Goal
Enforce high-performance, edge-rendered Angular 21 SSR (Server-Side Rendering) patterns on Cloudflare Workers/Pages using Wrangler CLI.

## Core Architecture Principles

### 1. Angular 21 SSR Engine Configuration
- Utilize `@angular/ssr` with standalone server routing (`app.routes.server.ts`).
- Leverage Event-driven Hydration (`withEventReplay()`) in `app.config.ts`.
- Ensure all browser-only DOM access (`window`, `document`, `localStorage`) is strictly guarded with `isPlatformBrowser(this.platformId)`.

### 2. Cloudflare Wrangler Integration
- Maintain configuration in `wrangler.jsonc` or `wrangler.toml` at the project root.
- Route server entry point to build output: `dist/[project-name]/server/server.mjs`.
- Configure static asset routing for the browser build: `dist/[project-name]/browser`.

### 3. Build & Deployment Pipeline (`package.json`)
```json
{
  "scripts": {
    "build": "ng build",
    "preview": "ng build && wrangler dev",
    "deploy": "ng build && wrangler deploy"
  }
}
```

### 4. `.gitignore` Configuration
The agent MUST ensure the following Cloudflare and build temporary directories are added to the project's `.gitignore`:
```text
# Cloudflare Pages / Wrangler
.wrangler/
.dev.vars
dist/
.angular/cache/
```

### 5. Environment Variables & Build Configuration
The agent MUST document the following in the README:
- **Local Dev**: Use a `.dev.vars` file for local Wrangler secrets (this is auto-ignored).
- **Cloudflare Dashboard**: The user MUST set the `NODE_VERSION` environment variable (e.g., `20`) in the Cloudflare Pages settings so the Angular CLI runs in the correct environment during CI builds.

## Performance & SEO Standards for Portfolio Showcase

### 1. Hydration & Transfer State
- Use `TransferState` to pass API responses or static metadata from server pre-render to client hydration without duplicate HTTP calls.
- Avoid dynamic DOM mutations during SSR to prevent client-side hydration mismatches (Error NG0500).

### 2. Edge Asset Caching
- Ensure static images (avatars, showcase screenshots) in `public/` are served with aggressive Cache-Control headers via Cloudflare edge.

## Constraints & Anti-Patterns
- **Deployment Execution (Anti-Automation)**: The AI Agent **MUST NOT** automatically execute Cloudflare deployment commands (e.g., `pnpm run deploy` or `wrangler deploy`) on behalf of the user. Automatically pushing to Cloudflare consumes deployment quota limits and generates unnecessary project URLs. Instead, the agent MUST strictly provide the command and instruct the user to run the deployment manually in their own terminal.
- Do NOT use Node.js-native binary modules (e.g. `fs`, `child_process`, `net`) inside server routes destined for Cloudflare Workers environment.
- Do NOT invoke non-serializable browser APIs inside component constructors or `ngOnInit` during SSR execution.
