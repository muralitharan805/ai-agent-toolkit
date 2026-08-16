---
description: "Workflow to scaffold Google Search Console, GA4, AdSense, legal policy pages, and dynamic route titles in Angular CSR SPA applications. Triggered by 'setup-angular-spa-google-suite:' or '/setup-angular-spa-google-suite'."
trigger: manual
---

# Workflow: Setup Angular SPA Google Suite

## Step 1: Generate `public/sitemap.xml` & `public/robots.txt`
1. Place static `sitemap.xml` in `public/` including routes for `/`, `/privacy`, and `/terms`.
2. Place `robots.txt` in `public/` pointing to `sitemap.xml`.

## Step 2: Configure `wrangler.jsonc` Output Directory
Ensure `wrangler.jsonc` specifies `"pages_build_output_dir": "dist/<app-name>/browser"`.

## Step 3: Inject Canonical, GA4 & AdSense in `src/index.html`
1. Add default `<link rel="canonical" href="https://yourdomain.com/" />` tag in `index.html`.
2. Add GA4 script tag `G-XXXXXXXXXX`.
3. Add AdSense publisher tag `ca-pub-XXXXXXXXXXXXXXXX`.
4. Add JSON-LD WebApplication schema.

## Step 4: Setup `SeoService` for Dynamic Canonical & Meta Tags
Implement `setCanonicalUrl()` and `updateTitleAndMeta()` in `SeoService` to update `<link rel="canonical">` and meta tags on SPA route navigation.

## Step 5: Deploy `public/ads.txt` & SPA Routing `public/_redirects`
1. Create `public/ads.txt` declaring publisher authorization:
   ```text
   google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
   ```
2. Create `public/_redirects` for Cloudflare Pages SPA client routing fallback:
   ```text
   /*    /index.html   200
   ```

## Step 6: Scaffold Standalone Legal Policy Components (AdSense Compliance)
To prevent AdSense rejections under "Meet AdSense Program Policies", scaffold standalone `PrivacyPolicyComponent` and `TermsOfServiceComponent`.

### 1. `PrivacyPolicyComponent` (`src/app/features/legal/privacy-policy.component.ts`)
```typescript
import { Component, ChangeDetectionStrategy } from '@angular/core';

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
        <p>We respect your privacy. We collect minimal analytics data via Google Analytics (GA4) to improve application performance and user experience.</p>
      </section>

      <section class="legal-section">
        <h2>2. Cookies & Google AdSense Advertising</h2>
        <p>This website uses Google AdSense to serve advertisements. Google, as a third-party vendor, uses cookies to serve ads on our site.</p>
        <p>Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to our sites or other sites on the Internet.</p>
        <p>Users may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google Ads Settings</a>.</p>
      </section>

      <section class="legal-section">
        <h2>3. Data Protection & Contact</h2>
        <p>If you have any questions regarding this Privacy Policy, you may contact us via our official contact channels.</p>
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
export class PrivacyPolicyComponent {}
```

### 2. Register Routes in `app.routes.ts`
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

### 3. Add Footer Legal Links
Ensure layout footers include `<a routerLink="/privacy">Privacy Policy</a>` and `<a routerLink="/terms">Terms of Service</a>`.
