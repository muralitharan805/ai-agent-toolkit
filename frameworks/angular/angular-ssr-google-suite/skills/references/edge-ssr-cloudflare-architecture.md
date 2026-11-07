# Edge SSR & Cloudflare Worker Runtime Architecture

This reference documents the technical constraints and engineering architecture required for running Angular Server-Side Rendered (SSR) applications on Cloudflare Workers and Cloudflare Pages Functions (`workerd` runtime).

---

## 1. Cloudflare Workers V8 Isolate vs Node.js Binary Runtime

Unlike standard Node.js server environments (e.g. AWS EC2, traditional Docker containers), Cloudflare Workers execute within **V8 isolates**:
- **Zero Process Overhead**: Multiple worker isolates run inside a single memory space with strict tenant separation, enabling sub-millisecond cold starts globally.
- **Absence of Node.js Native Binaries**: The `workerd` runtime does NOT contain Node.js OS bindings such as `fs`, `node:fs`, `path`, `net`, or `child_process`.
- **Global Standards**: Uses modern Web Standards: `fetch`, `Request`, `Response`, `URL`, `ReadableStream`, and Web Crypto (`crypto.subtle`).

### Fatal Node Module Imports
Importing Node-specific packages in SSR services will crash at edge deployment time or throw runtime exceptions:
```typescript
// ❌ FATAL: Crashes workerd runtime
import * as fs from 'fs';
import * as path from 'path';

// ✅ CORRECT: Use Web Fetch and Edge KV/D1 bindings
const apiData = await fetch('https://api.yourdomain.com/v1/data');
```

---

## 2. Browser Global Guarding & `PLATFORM_ID` Injection

Angular components execute on BOTH the edge server (during initial HTML pre-rendering) and the client browser (during user navigation).

### Failure Mechanism
Referencing browser identifiers (`window`, `document`, `navigator`, `localStorage`) during class construction or property initialization throws immediate `ReferenceError: window is not defined` on the server isolate.

### Mandatory Guarding Pattern
```typescript
import { Component, OnInit, inject, PLATFORM_ID, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({ ... })
export class PlatformAwareComponent implements OnInit {
  private readonly platformId = inject(PLATFORM_ID);
  readonly isBrowser = signal<boolean>(false);

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.isBrowser.set(true);
      // Safe to access window, navigator, localStorage
    }
  }
}
```

---

## 3. Hydration Safety & Avoiding NG0500 Mismatches

Angular's non-destructive hydration reconciles client-side reactive components with the pre-rendered server DOM.

### Why Hydration Fails (NG0500)
If the server HTML template outputs a different DOM tree than the client's initial render, Angular detects a DOM mismatch:
- `NG0500: During hydration Angular expected a node of type...`
This breaks hydration and forces Angular to destroy and re-render the entire DOM node, triggering severe Cumulative Layout Shift (CLS) and Largest Contentful Paint (LCP) performance penalties.

### Rules for Hydration Consistency
1. **Never toggle `@if` blocks based on browser-only state** on initial render:
   ```typescript
   // ❌ BAD: Causes NG0500 hydration error!
   // Server renders false, client renders true on load.
   @if (isMobile()) { <mobile-layout /> } @else { <desktop-layout /> }
   ```
2. **Use `afterNextRender()` for Post-Hydration DOM Modifications**:
   `afterNextRender()` guarantees execution only in the browser AFTER initial hydration has safely stabilized.
3. **Reserve Layout Dimensions**:
   Always set explicit CSS `min-height` on containers whose contents depend on client capabilities (e.g. ad banners, charts).

---

## 4. TransferState: Preventing Duplicate HTTP Queries

When the server fetches API data to pre-render HTML, the client should not execute a redundant HTTP call upon hydration.

```typescript
import { Injectable, inject, makeStateKey, TransferState } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom, of } from 'rxjs';
import { tap } from 'rxjs/operators';

const PORTFOLIO_KEY = makeStateKey<PortfolioItem[]>('portfolio_data');

@Injectable({ providedIn: 'root' })
export class PortfolioService {
  private readonly http = inject(HttpClient);
  private readonly transferState = inject(TransferState);

  async getPortfolio(): Promise<PortfolioItem[]> {
    // Check if server already fetched and transferred the state
    if (this.transferState.hasKey(PORTFOLIO_KEY)) {
      const data = this.transferState.get(PORTFOLIO_KEY, []);
      this.transferState.remove(PORTFOLIO_KEY); // Clean up
      return data;
    }

    // Otherwise execute HTTP query and store in TransferState on server
    const items = await firstValueFrom(this.http.get<PortfolioItem[]>('/api/portfolio'));
    this.transferState.set(PORTFOLIO_KEY, items);
    return items;
  }
}
```
