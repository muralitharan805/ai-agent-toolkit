---
description: "Mandates runtime safety, isPlatformBrowser guarding, Node.js native API isolation, and hydration safety for Angular SSR applications running on Cloudflare Workers edge isolate runtime."
trigger: model_decision
---

# Angular SSR & Cloudflare Edge Isolate Architecture Rules

## Description
This rule enforces strict runtime safety, V8 isolate compatibility, Vitest SSR test isolation, and DOM hydration consistency for all Angular Server-Side Rendered (SSR) applications running on Cloudflare Workers (`workerd`) or Cloudflare Pages Functions. Cloudflare edge compute executes within lightweight V8 isolate sandboxes that do not supply Node.js standard runtime binaries or browser DOM APIs. Any un-guarded reference to browser globals or Node.js native modules causes fatal runtime crashes at the edge.

---

## Constraints

### 1. Mandatory Browser Global Access Guarding
- Component constructors, field initializers, and dependency injection tokens MUST NEVER directly reference browser-only globals:
  - Prohibited un-guarded identifiers: `window`, `document`, `navigator`, `localStorage`, `sessionStorage`, `location`, `history`, `screen`, `matchMedia`.
- ALL browser-specific logic MUST inject `PLATFORM_ID` and execute conditionally within an `isPlatformBrowser(this.platformId)` guard block:
  ```typescript
  import { inject, PLATFORM_ID } from '@angular/core';
  import { isPlatformBrowser } from '@angular/common';

  private readonly platformId = inject(PLATFORM_ID);

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      // Safely access window or localStorage
    }
  }
  ```
- Direct assignment of browser globals to component class properties (e.g. `private readonly width = window.innerWidth;`) is STRICTLY FORBIDDEN because class property initializers execute during server pre-rendering.

### 2. Strict Node.js Native Module Prohibition
- Cloudflare Workers execute within the `workerd` V8 isolate runtime, NOT a standard Node.js process.
- The following Node.js native modules MUST NEVER be imported into Angular SSR application services, components, or server route handlers:
  - `fs`, `node:fs`, `fs/promises`
  - `path`, `node:path`
  - `crypto`, `node:crypto` (use the global Web Crypto API `crypto.subtle` instead)
  - `net`, `child_process`, `os`, `cluster`, `http`, `https`
- If server-side data persistence or caching is required, the application MUST utilize Cloudflare Workers KV, D1 SQL Database, or standard HTTP fetch against a centralized API service.

### 3. Hydration Safety & Layout Shift Prevention (NG0500 Mitigation)
- Angular Server-Side Rendering uses non-destructive hydration to bind client-side reactive components to server-rendered DOM nodes.
- Conditional template blocks (`@if`, `@switch`) MUST NOT depend on browser-only state (such as `isMobile`, `window.innerWidth`, or `localStorage` auth flags) during initial component rendering.
- Rendering divergent HTML markup on the server versus the client causes fatal Hydration Mismatch Errors (`NG0500: During hydration Angular expected a node of type...`) and destroys performance.
- When responsive layout adaptations or user-specific preferences (such as Dark Mode tokens) must be applied:
  1. Render a consistent, server-safe neutral layout during SSR.
  2. Transition client-specific layouts inside `afterNextRender()` or signal updates inside browser-guarded lifecycles.
  3. Reserve explicit CSS container dimensions (e.g. `min-height`) to eliminate Cumulative Layout Shift (CLS).

### 4. Vitest SSR Test Isolation & Platform Mocking
- Unit tests (`*.spec.ts`) for SSR-enabled components MUST explicitly provide and verify both server and browser runtime environments:
  ```typescript
  TestBed.configureTestingModule({
    providers: [
      { provide: PLATFORM_ID, useValue: 'server' }
    ]
  });
  ```
- Tests simulating browser behavior MUST clean up `jsdom` or global window spy properties in `afterEach()` hooks (`vi.restoreAllMocks()`) to avoid test leakage across suites.

### 5. Build Output & Artifact Directory Integrity
- Edge SSR deployments compile two distinct bundle outputs:
  - `dist/<project-name>/browser`: Static client-side JavaScript, CSS, images, and `index.html`.
  - `dist/<project-name>/server`: Edge V8 request handler and compiled Angular server engine.
- Production configurations MUST verify both directories exist and match Cloudflare Pages / Wrangler deployment definitions (`pages_build_output_dir` in `wrangler.jsonc`).

### 6. Zero `any` Type Safety & Clean Code Compliance
- All server request handlers, edge context objects, and platform utilities MUST use strict TypeScript typing.
- Writing `any` in SSR services, interceptors, or route handlers is strictly prohibited. Use `unknown` with type narrowing or strongly typed request DTOs.

---

## Examples

### 1. Correct Implementation: Platform Guarding & Hydration Safe Component

```typescript
import { Component, OnInit, inject, PLATFORM_ID, signal, ChangeDetectionStrategy, afterNextRender } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

/**
 * User device telemetry component safely distinguishing between
 * Edge V8 isolate execution and client-side browser hydration.
 */
@Component({
  selector: 'app-viewport-metrics',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="metrics-card">
      <h2>Device Display Metrics</h2>
      @if (screenWidth() !== null) {
        <p>Viewport Width: <strong>{{ screenWidth() }}px</strong></p>
      } @else {
        <p class="neutral-placeholder">Calculating viewport dimensions...</p>
      }
    </section>
  `,
  styles: [`
    .metrics-card {
      padding: 1.5rem;
      border-radius: 8px;
      min-height: 120px; /* CLS reservation */
    }
    .neutral-placeholder {
      color: #94a3b8;
    }
  `]
})
export class ViewportMetricsComponent implements OnInit {
  private readonly platformId = inject(PLATFORM_ID);
  
  /** Signal holding client viewport width; defaults to null during SSR pre-rendering */
  readonly screenWidth = signal<number | null>(null);

  constructor() {
    // afterNextRender runs exclusively in the browser after initial DOM hydration completes
    afterNextRender(() => {
      this.screenWidth.set(window.innerWidth);
    });
  }

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      // Safe to attach browser-only listeners or inspect client capabilities
    }
  }
}
```

### 2. Incorrect Implementation (STRICTLY FORBIDDEN)

```typescript
// ❌ CRITICAL ERRORS:
// 1. Direct window property assignment at field initializer causes ReferenceError in workerd.
// 2. Direct localStorage access during SSR causes immediate server crash.
// 3. Importing Node.js native 'fs' crashes Cloudflare V8 isolate runtime.
// 4. Untyped 'any' annotations violate clean code rules.

import { Component, OnInit } from '@angular/core';
import * as fs from 'fs'; // ❌ FATAL: Node native module forbidden in workerd!

@Component({
  selector: 'app-broken-ssr',
  standalone: true,
  template: `<div>{{ width }}</div>`
})
export class BrokenSsrComponent implements OnInit {
  width: any = window.innerWidth; // ❌ FATAL: Un-guarded window access throws ReferenceError during SSR!

  ngOnInit(): void {
    const userToken: any = localStorage.getItem('auth_token'); // ❌ FATAL: localStorage undefined on server!
  }
}
```
