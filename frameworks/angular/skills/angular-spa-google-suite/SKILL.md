---
name: angular-spa-google-suite
description: "Configures Google Search Console SEO, canonical URLs, GA4 client route telemetry, AdSense monetization, legal policy pages, and Cloudflare Pages SPA fallback."
---

# Angular SPA Google Suite & Cloudflare Deployment Skill

## 1. Overview & 5-Pillar Architecture

This skill provides an enterprise production blueprint for pure Client-Side Rendered (CSR) Angular Single Page Applications. It integrates Google Search Console SEO, dynamic canonical URL resolution, Google Analytics 4 (GA4) route transition tracking, Google AdSense monetization with Cumulative Layout Shift (CLS) protection, mandatory legal policy pages, and Cloudflare Pages SPA fallback routing.

```text
frameworks/angular/skills/angular-spa-google-suite/
├── SKILL.md                          # Core procedural instruction (< 500 lines) + Gotchas
├── references/                       # In-depth architectural runbooks
│   ├── seo-and-canonical-urls.md     # AppTitleStrategy, canonical stripping, JSON-LD
│   └── ga4-route-tracking-and-adsense.md # NavigationEnd telemetry & CLS height reservation
├── scripts/                          # Automated compliance audit CLI
│   └── audit_angular_spa.py          # Standalone PEP 723 audit tool
├── assets/                           # Production-ready drop-in templates
│   ├── seo.service.ts                # Canonical URL & Open Graph meta manager
│   ├── analytics.service.ts          # GA4 NavigationEnd telemetry service
│   ├── adsense.component.ts          # CLS-safe responsive AdSense component
│   ├── privacy-policy.component.ts   # GDPR & AdSense compliant privacy page
│   ├── terms-of-service.component.ts # Terms of service legal page
│   ├── ads.txt                       # Authorized digital sellers declaration
│   └── _redirects                    # Cloudflare Pages 200 fallback rule
└── evals/                            # Quality verification test suite
    ├── evals.json                    # Automated assertions and evaluation cases
    └── grading.json                  # Net skill lift and benchmark metrics
```

---

## 2. 6-Step Google Suite & SPA Setup Protocol

### Step 1: Static `public/sitemap.xml` & `public/robots.txt`
1. Create `public/sitemap.xml` declaring canonical URLs for root and legal pages:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
     <url><loc>https://yourdomain.com/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
     <url><loc>https://yourdomain.com/privacy</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>
     <url><loc>https://yourdomain.com/terms</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>
   </urlset>
   ```
2. Create `public/robots.txt`:
   ```text
   User-agent: *
   Allow: /

   Sitemap: https://yourdomain.com/sitemap.xml
   ```

### Step 2: Build Output Alignment (`wrangler.jsonc`)
Ensure `wrangler.jsonc` points to the Angular application browser output:
```jsonc
{
  "name": "your-angular-spa",
  "pages_build_output_dir": "dist/your-angular-spa/browser"
}
```

### Step 3: Inject Canonical, GA4 & Schema in `src/index.html`
Add default canonical link, pre-connect tags, Google tag (`gtag.js`), AdSense script, and JSON-LD schema into `<head>`:
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

### Step 4: Configure TitleStrategy & Dynamic SeoService
Register `AppTitleStrategy` in `app.config.ts` to enforce keyword-rich route titles:
```typescript
import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter, TitleStrategy } from '@angular/router';
import { routes } from './app.routes';
import { AppTitleStrategy } from './core/strategies/page-title.strategy';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes),
    { provide: TitleStrategy, useClass: AppTitleStrategy }
  ]
};
```

### Step 5: Deploy `public/ads.txt` & SPA Fallback `public/_redirects`
1. Copy `assets/ads.txt` into `public/ads.txt`:
   ```text
   google.com, pub-1649083292065809, DIRECT, f08c47fec0942fa0
   ```
2. Copy `assets/_redirects` into `public/_redirects`:
   ```text
   /*    /index.html   200
   ```

### Step 6: Register Legal Policy Routes (`/privacy` & `/terms`)
In `src/app/app.routes.ts`, register standalone legal pages to comply with AdSense Program Policies:
```typescript
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'Your Product Name — High Precision Engineering Utilities',
    loadComponent: () => import('./features/home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'privacy',
    title: 'Privacy Policy & Cookie Disclosures',
    loadComponent: () => import('./features/legal/privacy-policy.component').then(m => m.PrivacyPolicyComponent)
  },
  {
    path: 'terms',
    title: 'Terms of Service & Usage Agreements',
    loadComponent: () => import('./features/legal/terms-of-service.component').then(m => m.TermsOfServiceComponent)
  }
];
```

---

## 3. Core Architecture Implementations

### Dynamic SEO & Canonical Link Service (`src/app/core/services/seo.service.ts`)
```typescript
import { Injectable, inject } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';

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
    const rawUrl = url ?? `${this.document.location.origin}${this.document.location.pathname}`;
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

### GA4 SPA Telemetry Service (`src/app/core/services/analytics.service.ts`)
```typescript
import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

export type GtagParamValue = string | number | boolean | null | undefined | readonly string[] | Record<string, unknown>;

declare global {
  interface Window {
    gtag?: (command: string, actionOrTarget: string, params?: Record<string, GtagParamValue>) => void;
  }
}

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly router = inject(Router);
  private readonly platformId = inject(PLATFORM_ID);

  init(measurementId: string): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        if (typeof window.gtag === 'function') {
          window.gtag('config', measurementId, {
            page_path: event.urlAfterRedirects,
          });
        }
      });
  }

  trackEvent(eventName: string, params: Record<string, GtagParamValue> = {}): void {
    if (isPlatformBrowser(this.platformId) && typeof window.gtag === 'function') {
      window.gtag('event', eventName, params);
    }
  }
}
```

### Cumulative Layout Shift Safe AdSense (`src/app/shared/components/adsense.component.ts`)
```typescript
import { Component, OnInit, inject, PLATFORM_ID, signal, input, ChangeDetectionStrategy } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

declare global {
  interface Window {
    adsbygoogle?: Array<Record<string, unknown>>;
  }
}

@Component({
  selector: 'app-adsense',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (!isLocalhost()) {
      <div class="ad-slot-container" style="min-height: 250px; width: 100%; display: block; overflow: hidden;">
        <ins class="adsbygoogle"
             style="display: block;"
             [attr.data-ad-client]="client()"
             [attr.data-ad-slot]="slot()"
             [attr.data-ad-format]="format()"
             data-full-width-responsive="true"></ins>
      </div>
    }
  `
})
export class AdsenseComponent implements OnInit {
  readonly slot = input<string>('');
  readonly format = input<string>('auto');
  readonly client = input<string>('ca-pub-1649083292065809');

  private readonly platformId = inject(PLATFORM_ID);
  protected readonly isLocalhost = signal<boolean>(true);

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1';
    this.isLocalhost.set(isLocal);

    if (!isLocal) {
      try {
        const queue = window.adsbygoogle ?? [];
        window.adsbygoogle = queue;
        queue.push({});
      } catch {
        // Suppress ad-blocker or network error
      }
    }
  }
}
```

---

## 4. Automated Compliance Verification

Verify codebase compliance using the bundled audit CLI:
```bash
# Run audit against src directory
python3 frameworks/angular/skills/angular-spa-google-suite/scripts/audit_angular_spa.py src

# Run in strict mode for CI/CD pipelines
python3 frameworks/angular/skills/angular-spa-google-suite/scripts/audit_angular_spa.py --strict

# Output machine-readable JSON
python3 frameworks/angular/skills/angular-spa-google-suite/scripts/audit_angular_spa.py --json
```

---

## 5. Gotchas & Anti-Patterns

| Category | Deprecated / Broken Pattern (❌) | Modern Production Replacement (✅) |
|---|---|---|
| **Cloudflare SPA Routing** | Relying on default 404 routing or missing `_redirects` file | Deploy `public/_redirects` with `/* /index.html 200` to prevent deep link 404s |
| **GA4 Route Tracking** | Static `<script>` tag only in `index.html` (only logs landing page) | Subscribe to `Router.events` (`NavigationEnd`) in `AnalyticsService` |
| **Route Titles** | Bare generic titles (`title: 'Home'`, `title: 'Login'`) | Keyword-rich titles (`title: 'EMI Calculator & Amortization Schedule'`) |
| **Canonical URL** | Missing canonical tag or retaining tracking queries (`?utm_source=...`) | Strip query strings deterministically in `SeoService.setCanonicalUrl()` |
| **AdSense Layout Shift** | Zero-height container causing violent CLS layout shifts when ad renders | Reserve container dimensions explicitly (`min-height: 250px`) |
| **AdSense Eligibility** | Gating entire site behind authentication walls without legal policies | Deploy public `/privacy` and `/terms` with persistent layout footer links |
| **Platform Safety** | Direct unchecked references to `window.gtag` or `window.location` | Inject `PLATFORM_ID` and check `isPlatformBrowser(platformId)` |
| **Type Safety** | Using `any[]` or `(...args: any[]) => void` for window globals | Strict typing with `GtagParamValue` and `Record<string, unknown>` |
