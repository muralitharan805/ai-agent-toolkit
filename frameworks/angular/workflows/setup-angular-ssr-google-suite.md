---
description: "Workflow to scaffold Google Search Console, GA4, AdSense, legal policy pages, and dynamic route titles in Angular Edge SSR applications. Triggered by 'setup-angular-ssr-google-suite:' or '/setup-angular-ssr-google-suite'."
trigger: manual
---

# Workflow: Setup Angular Edge SSR Google Suite

## Step 1: Add Sitemap Handler in `src/server.ts`
Implement raw XML Response handler for `/sitemap.xml` inside `createRequestHandler`. Include routes for `/`, `/privacy`, and `/terms`.

## Step 2: Configure `public/_routes.json`
Exclude `/sitemap.xml`, `/robots.txt`, `/ads.txt`, and `/assets/*` from Cloudflare Worker execution.

## Step 3: Inject Canonical, GA4 & AdSense Tags
1. Add default fallback `<link rel="canonical" href="https://yourdomain.com/" />` tag in `src/index.html`.
2. Add GA4 tag `G-XXXXXXXXXX` and AdSense publisher tag `ca-pub-XXXXXXXXXXXXXXXX` in `src/index.html` with `isPlatformBrowser` guarding.

## Step 4: Setup Dynamic Canonical `SeoService`
Implement SSR-safe `setCanonicalUrl()` in `SeoService` to update `<link rel="canonical">` during Edge SSR pre-rendering and CSR hydration.

## Step 5: Deploy `public/ads.txt`
Create `public/ads.txt` declaring publisher ownership:
```text
google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
```

## Step 6: Scaffold SSR-Safe Legal Policy Components (AdSense Compliance)
Scaffold standalone `PrivacyPolicyComponent` and `TermsOfServiceComponent` using `isPlatformBrowser` guards.

### 1. `PrivacyPolicyComponent` (`src/app/features/legal/privacy-policy.component.ts`)
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
        <p>We respect your privacy. Minimal analytics data is collected via Google Analytics (GA4) to optimize server-side rendering and client performance.</p>
      </section>

      <section class="legal-section">
        <h2>2. Cookies & Google AdSense Advertising</h2>
        <p>This website uses Google AdSense to serve advertisements. Google uses cookies to serve ads based on prior visits to our website or other websites.</p>
        <p>Users may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google Ads Settings</a>.</p>
      </section>
    </article>
  `,
  styles: [`
    .legal-container { max-width: 800px; margin: 2rem auto; padding: 2rem; color: #e2e8f0; }
    .legal-header { margin-bottom: 2rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
    .legal-section { margin-bottom: 1.5rem; }
    h1 { font-size: 2rem; font-weight: 700; color: #ffffff; }
    h2 { font-size: 1.25rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.5rem; }
    p { line-height: 1.6; color: #cbd5e1; font-size: 0.95rem; }
    a { color: #60a5fa; text-decoration: underline; }
  `]
})
export class PrivacyPolicyComponent {
  private platformId = inject(PLATFORM_ID);
  protected isBrowser = isPlatformBrowser(this.platformId);
}
```

### 2. Register SSR Routes in `app.routes.ts`
```typescript
{
  path: 'privacy',
  title: 'Privacy Policy & Cookie Disclosures',
  loadComponent: () => import('./features/legal/privacy-policy.component').then(m => m.PrivacyPolicyComponent)
},
{
  path: 'terms',
  title: 'Terms of Service',
  loadComponent: () => import('./features/legal/terms-of-service.component').then(m => m.TermsOfServiceComponent)
}
```
