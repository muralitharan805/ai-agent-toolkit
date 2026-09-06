---
name: angular-ssr-google-suite
description: "Configures Google Search Console XML streams, Cloudflare Pages Edge route bypass, SSR hydration safety, GA4, AdSense, and legal policy pages for Angular SSR."
---

# Angular Edge SSR Google Suite & Cloudflare Deployment Skill

## 1. Overview & 5-Pillar Architecture

This skill provides an enterprise production blueprint for Angular Server-Side Rendered (SSR) applications running on Cloudflare Workers and Cloudflare Pages edge isolate runtime (`workerd`). It integrates dynamic Google Search Console XML sitemap streaming, edge route bypass manifests, hydration-safe SEO and metadata hydration, Google Analytics 4 (GA4) route tracking, AdSense monetization with Cumulative Layout Shift (CLS) layout space reservation, and mandatory legal policy pages.

```text
frameworks/angular/skills/angular-ssr-google-suite/
├── SKILL.md                          # Core procedural instruction (< 500 lines) + Gotchas
├── references/                       # Deep architectural specifications
│   ├── edge-ssr-cloudflare-architecture.md # V8 isolate safety, hydration (NG0500), TransferState
│   └── dynamic-xml-and-sitemap-streaming.md # Server streaming, CDN bypass (_routes.json), SEO
├── scripts/                          # Automated compliance audit CLI
│   └── audit_angular_ssr.py          # Standalone PEP 723 audit tool
├── assets/                           # Production drop-in templates
│   ├── server.ts                     # Edge server request handler with /sitemap.xml stream
│   ├── seo.service.ts                # SSR-safe canonical URL & Open Graph meta manager
│   ├── privacy-policy.component.ts   # SSR-safe GDPR & AdSense compliant privacy page
│   ├── terms-of-service.component.ts # SSR-safe Terms of service legal page
│   ├── _routes.json                  # Cloudflare Pages edge route bypass manifest
│   └── ads.txt                       # Authorized digital sellers declaration
└── evals/                            # Quality verification test suite
    ├── evals.json                    # Automated assertions and evaluation cases
    └── grading.json                  # Net skill lift and benchmark metrics
```

---

## 2. 6-Step Google Suite & SSR Setup Protocol

### Step 1: Add Dynamic Sitemap Stream in `src/server.ts`
Intercept `/sitemap.xml` inside `createRequestHandler` to return raw XML before AngularAppEngine executes:
```typescript
import { AngularAppEngine, createRequestHandler } from '@angular/ssr';

const angularApp = new AngularAppEngine();

const SITEMAP_XML = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://yourdomain.com/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://yourdomain.com/privacy</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>
  <url><loc>https://yourdomain.com/terms</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>
</urlset>`;

export const reqHandler = createRequestHandler(async (req: Request): Promise<Response> => {
  const url = new URL(req.url);
  const pathname = url.pathname.toLowerCase().replace(/\/$/, '');

  if (pathname === '/sitemap.xml') {
    return new Response(SITEMAP_XML, {
      status: 200,
      headers: {
        'Content-Type': 'application/xml; charset=UTF-8',
        'Cache-Control': 'public, max-age=86400, s-maxage=86400'
      }
    });
  }

  const response = await angularApp.handle(req);
  return response ?? new Response('Not Found', { status: 404 });
});

export default { fetch: reqHandler };
```

### Step 2: Configure Edge Route Bypass (`public/_routes.json`)
Bypass Cloudflare Workers for static assets, sitemaps, and robots protocol:
```json
{
  "version": 1,
  "include": ["/*"],
  "exclude": [
    "/sitemap.xml",
    "/robots.txt",
    "/ads.txt",
    "/favicon.ico",
    "/assets/*"
  ]
}
```

### Step 3: Inject Canonical, GA4 & Schema in `src/index.html`
Place the baseline fallback `<link rel="canonical">` and JSON-LD schema into `<head>`:
```html
<link rel="canonical" href="https://yourdomain.com/" />
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1649083292065809" crossorigin="anonymous"></script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Your Application Name",
  "url": "https://yourdomain.com",
  "applicationCategory": "UtilitiesApplication"
}
</script>
```

### Step 4: Configure SSR-Safe Dynamic `SeoService`
Implement `SeoService` using `PLATFORM_ID` to safely update `<link rel="canonical">` during server pre-rendering and client navigation.

### Step 5: Deploy `public/ads.txt` & `public/robots.txt`
1. Deploy `public/ads.txt`:
   ```text
   google.com, pub-1649083292065809, DIRECT, f08c47fec0942fa0
   ```
2. Deploy `public/robots.txt`:
   ```text
   User-agent: *
   Allow: /

   Sitemap: https://yourdomain.com/sitemap.xml
   ```

### Step 6: Register Standalone Legal Policy Routes (`app.routes.ts`)
Register `/privacy` and `/terms` with keyword-rich titles to satisfy AdSense Program Policies:
```typescript
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'Your Application — High-Performance Edge Computing Platform',
    loadComponent: () => import('./features/home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'privacy',
    title: 'Privacy Policy & Cookie Disclosures',
    loadComponent: () => import('./features/legal/privacy-policy.component').then(m => m.PrivacyPolicyComponent)
  },
  {
    path: 'terms',
    title: 'Terms of Service & User Agreement',
    loadComponent: () => import('./features/legal/terms-of-service.component').then(m => m.TermsOfServiceComponent)
  }
];
```

---

## 3. Core Architecture Implementations

### SSR-Safe Canonical & Meta Service (`src/app/core/services/seo.service.ts`)
```typescript
import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { DOCUMENT, isPlatformBrowser } from '@angular/common';

export interface SeoConfig {
  readonly title: string;
  readonly description: string;
  readonly url: string;
  readonly image?: string;
  readonly canonicalUrl?: string;
}

@Injectable({ providedIn: 'root' })
export class SeoService {
  private readonly meta = inject(Meta);
  private readonly title = inject(Title);
  private readonly document = inject(DOCUMENT);
  private readonly platformId = inject(PLATFORM_ID);

  setMetaTags(config: SeoConfig): void {
    this.title.setTitle(config.title);
    this.meta.updateTag({ name: 'description', content: config.description });
    this.meta.updateTag({ property: 'og:title', content: config.title });
    this.meta.updateTag({ property: 'og:description', content: config.description });
    this.meta.updateTag({ property: 'og:url', content: config.url });
    this.meta.updateTag({ property: 'og:image', content: config.image ?? `${config.url}/favicon.ico` });
    this.meta.updateTag({ property: 'twitter:card', content: 'summary_large_image' });

    this.setCanonicalUrl(config.canonicalUrl ?? config.url);
  }

  setCanonicalUrl(url?: string): void {
    const origin = isPlatformBrowser(this.platformId)
      ? this.document.location.origin
      : 'https://yourdomain.com';
    const path = isPlatformBrowser(this.platformId)
      ? this.document.location.pathname
      : '';
    const rawUrl = url ?? `${origin}${path}`;
    const cleanUrl = rawUrl.split('?')[0];

    let link: HTMLLinkElement | null = this.document.querySelector("link[rel='canonical']");
    if (!link) {
      link = this.document.createElement('link');
      link.setAttribute('rel', 'canonical');
      this.document.head.appendChild(link);
    }

    link.setAttribute('href', cleanUrl);
  }
}
```

### Standalone SSR-Safe Privacy Policy (`src/app/features/legal/privacy-policy.component.ts`)
```typescript
import { Component, ChangeDetectionStrategy, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-privacy-policy',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="legal-container">
      <header class="legal-header">
        <h1>Privacy Policy</h1>
        <p class="effective-date">Effective Date: August 16, 2026</p>
      </header>
      <section class="legal-section">
        <h2>1. Information We Collect</h2>
        <p>Minimal anonymized telemetry is collected via Google Analytics (GA4) to ensure server rendering health and client performance.</p>
      </section>
      <section class="legal-section">
        <h2>2. Cookies & Google AdSense Advertising</h2>
        <p>This website uses Google AdSense cookies. Users may opt out via <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener noreferrer">Google Ads Settings</a>.</p>
      </section>
    </article>
  `,
  styles: [`
    .legal-container { max-width: 800px; margin: 2rem auto; padding: 2rem; color: #e2e8f0; }
    .legal-header { margin-bottom: 2rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
    h1 { font-size: 2rem; color: #ffffff; }
    h2 { font-size: 1.25rem; color: #94a3b8; }
    p { color: #cbd5e1; line-height: 1.6; }
    a { color: #60a5fa; text-decoration: underline; }
  `]
})
export class PrivacyPolicyComponent {
  private readonly platformId = inject(PLATFORM_ID);
  protected readonly isBrowser = isPlatformBrowser(this.platformId);
}
```

---

## 4. Automated Compliance Verification

Run the bundled CLI audit tool to verify edge SSR compatibility:
```bash
# Audit project src directory
python3 frameworks/angular/skills/angular-ssr-google-suite/scripts/audit_angular_ssr.py src

# Run in strict mode for CI/CD gates
python3 frameworks/angular/skills/angular-ssr-google-suite/scripts/audit_angular_ssr.py --strict

# Output machine-readable JSON
python3 frameworks/angular/skills/angular-ssr-google-suite/scripts/audit_angular_ssr.py --json
```

---

## 5. Gotchas & Anti-Patterns

| Category | Deprecated / Broken Pattern (❌) | Modern Production Replacement (✅) |
|---|---|---|
| **Sitemap Serving** | Serving `/sitemap.xml` via Angular route template | Intercept `/sitemap.xml` in `src/server.ts` returning native XML `Response` |
| **Worker Invocations** | Allowing every static asset request to trigger Cloudflare Worker | Exclude static assets, sitemap, and robots in `public/_routes.json` |
| **Runtime Isolation** | Importing Node native modules (`fs`, `path`, `crypto`, `net`) | Use standard Web Fetch API and global `crypto.subtle` |
| **Browser Globals** | Directly referencing `window`, `document`, or `localStorage` during SSR | Inject `PLATFORM_ID` and guard with `isPlatformBrowser(platformId)` |
| **Hydration Safety** | Conditional template rendering based on `window.innerWidth` (NG0500) | Use `afterNextRender()` or server-safe neutral layouts with CSS media queries |
| **Route Titles** | Bare generic titles (`title: 'Home'`, `title: 'Login'`) | Keyword-rich titles (`title: 'Personal Finance & Net Worth Tracker'`) |
| **AdSense Eligibility** | Omitting `/privacy` and `/terms` or hiding links behind login gates | Public standalone legal components with persistent layout footer links |
| **Type Safety** | Writing explicit `any` types for server requests or global windows | Use strict types (`Request`, `Response`, `unknown` with type narrowing) |
