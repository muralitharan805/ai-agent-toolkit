# SEO & Canonical URL Architecture in Angular Single Page Applications

This reference documents the architectural requirements for achieving top-tier search engine indexing and zero duplicate content penalties in pure Client-Side Rendered (CSR) Angular SPAs.

---

## 1. The Duplicate Content Vulnerability in SPAs

Search engine web crawlers (Googlebot, Bingbot) discover pages through hyperlinks containing tracking query parameters, marketing campaign IDs, or session tags:
- `https://yourdomain.com/tools/calculator?utm_source=newsletter`
- `https://yourdomain.com/tools/calculator?ref=twitter&theme=dark`

In single-page applications without explicit canonical synchronization, crawlers treat these variations as distinct URLs serving duplicate content, severely diluting PageRank and triggering Search Console canonical warnings (*"Duplicate without user-selected canonical"*).

### Canonical URL Invariant
Every rendered client route MUST resolve a deterministic `<link rel="canonical" href="...">` tag where:
1. All tracking query parameters (`utm_*`, `ref`, `fbclid`) are stripped.
2. The domain is the canonical HTTPS host without trailing slash inconsistencies.
3. Path casing is normalized to lowercase.

---

## 2. Centralized Title Synchronization via `AppTitleStrategy`

Angular's built-in `TitleStrategy` intercepts route state changes and synchronizes the browser `<title>` tag automatically.

```typescript
// src/app/core/strategies/page-title.strategy.ts
import { Injectable, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AppTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);
  private static readonly APP_BRAND_SUFFIX = 'my-company Labs';
  private static readonly DEFAULT_FALLBACK_TITLE = 'Engineering Sandbox & Utility Tools';

  override updateTitle(routerState: RouterStateSnapshot): void {
    const routeTitle = this.buildTitle(routerState);
    if (routeTitle) {
      this.title.setTitle(`${routeTitle} | ${AppTitleStrategy.APP_BRAND_SUFFIX}`);
    } else {
      this.title.setTitle(`${AppTitleStrategy.DEFAULT_FALLBACK_TITLE} | ${AppTitleStrategy.APP_BRAND_SUFFIX}`);
    }
  }
}
```

### Route Title Best Practices
- **Forbidden**: Bare, generic route titles (`title: 'Home'`, `title: 'Login'`).
- **Required**: Keyword-rich titles describing primary capability (`title: 'EMI Loan Amortization Calculator & Schedule'`).

---

## 3. Dynamic Meta & Canonical Tag Management (`SeoService`)

```typescript
// Usage in a Feature Component
@Component({ ... })
export class LoanCalculatorComponent implements OnInit {
  private readonly seo = inject(SeoService);

  ngOnInit(): void {
    this.seo.setMetaTags({
      title: 'EMI Loan Amortization Schedule Calculator',
      description: 'Compute monthly principal and interest breakdowns with instant charts and PDF export.',
      url: 'https://yourdomain.com/tools/loan-calculator'
    });
  }
}
```

---

## 4. Structured Data (`JSON-LD`) for Web Applications

Embed a structured JSON-LD schema in `src/index.html` within the `<head>`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Engineering Sandbox & Utilities",
  "url": "https://yourdomain.com",
  "description": "Developer utility tools, calculators, and interactive sandboxes.",
  "applicationCategory": "UtilitiesApplication",
  "operatingSystem": "All",
  "browserRequirements": "Requires JavaScript. Requires HTML5.",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
</script>
```

---

## 5. Root Static Sitemap & Robots Protocol

Single Page Applications deployed to Cloudflare Pages serve static files directly from the build output root:
- `public/sitemap.xml`: Lists canonical URLs with `<lastmod>`, `<changefreq>`, and `<priority>`.
- `public/robots.txt`: Points explicitly to the full HTTPS URL of `sitemap.xml`.
