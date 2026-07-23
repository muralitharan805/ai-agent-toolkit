---
trigger: always_on
description: "Mandates strict Cloudflare edge compatibility for Angular 21 SSR, requiring platformId guards for browser globals, Vitest SSR specs, and hydration safety."
---
# Angular 21 SSR & Cloudflare Edge Rule

## Description
Enforces runtime safety, Vitest SSR test compliance, and Cloudflare Worker runtime restrictions for all Angular Server-Side Rendered (SSR) components and services.

## Strict Rules

### 1. Browser Global Access Guarding
- NEVER directly reference `window`, `document`, `navigator`, `localStorage`, `sessionStorage`, or `location` at component initialization or constructor level.
- ALWAYS inject `PLATFORM_ID` and check `isPlatformBrowser(platformId)` before executing browser APIs:

```typescript
import { Component, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({ ... })
export class ShowcaseComponent {
  private platformId = inject(PLATFORM_ID);

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      // Browser-only code execution
      console.log(window.innerWidth);
    }
  }
}
```

### 2. Node.js Native Module Restrictions
- Do NOT import `fs`, `path`, `crypto` (Node native), `net`, or `child_process` in Angular SSR services or server routes. Cloudflare Workers execute on V8 isolate runtime (`workerd`), not standard Node.js binary.

### 3. Testing with Vitest (`vitest`)
- Component tests MUST mock `PLATFORM_ID` appropriately for both server and browser environments.
- Avoid using `jsdom` global state inside tests without proper cleanup.

### 4. Hydration Safety
- Ensure conditional layout elements (`*ngIf` / `@if`) depending on browser-only state (`isMobile`, `windowWidth`) do NOT render differently during server pre-rendering versus client hydration.
