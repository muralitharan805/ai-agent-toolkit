---
description: "Universal rules for Google Search Console SEO, sitemap.xml indexing, robots.txt formatting, canonical link tags, and JSON-LD structured data schemas."
trigger: model_decision
---

# Universal Google Search Console & SEO Rules

## Description
Enforces mandatory universal standards for search engine indexing, sitemap generation, robots.txt configurations, canonical link tags, and JSON-LD rich snippet schemas across all web applications.

## Constraints

### 1. Sitemap & Robots Protocol
- Applications MUST provide a valid `/sitemap.xml` listing all canonical page URLs with proper `<lastmod>`, `<changefreq>`, and `<priority>` tags.
- Applications MUST provide a `/robots.txt` referencing the full sitemap location:
  ```text
  User-agent: *
  Allow: /

  Sitemap: https://yourdomain.com/sitemap.xml
  ```

### 2. JSON-LD Structured Data Schema Requirement
- Every public landing page MUST include a valid `<script type="application/ld+json">` block defining appropriate Schema.org types (`WebApplication`, `SoftwareApplication`, `Article`, `FinanceApplication`, or `Organization`).

### 3. Canonical Link Tags
- Every page MUST render a canonical link tag (`<link rel="canonical" href="https://yourdomain.com/page">`) to eliminate duplicate content penalties across subdomains or parameter variations.
- Subdomains MUST use self-referencing canonical URLs (`https://sub.yourdomain.com/`) rather than referencing apex domains.
- Dynamic query strings and tracking tokens (`?utm_source=...`) MUST be stripped from canonical target URLs.

### 4. Domain 301 Redirection & SSL Enforcement
- Applications MUST enforce HTTPS and 301 Permanent Redirects for all non-canonical hostnames (e.g. `http://` to `https://`, `www` to non-`www` apex domain or vice-versa) to prevent duplicate content indexing penalties in Google Search Console.

## Examples

### 1. Canonical Link Tag & Normalization
```html
<!-- ❌ FORBIDDEN: Relative path or tracking parameters inside canonical tag -->
<link rel="canonical" href="/tools/converter?utm_source=newsletter" />

<!-- ✅ CORRECT: Absolute, normalized URL with tracking parameters stripped -->
<link rel="canonical" href="https://yourdomain.com/tools/converter" />
```

### 2. Robots.txt with Authoritative Sitemap Directives
```text
# ❌ FORBIDDEN: Missing sitemap reference and blocking essential styling assets
User-agent: *
Disallow: /assets/

# ✅ CORRECT: Permitting asset crawling while disallowing private routes and referencing sitemap
User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /_app/

Sitemap: https://yourdomain.com/sitemap.xml
```

### 3. Schema.org JSON-LD Structured Data Injection
```html
<!-- ❌ FORBIDDEN: Unescaped, invalidly typed structured metadata -->
<script type="text/javascript">
  var schemaData = { name: "Tool" };
</script>

<!-- ✅ CORRECT: Standard application/ld+json block conforming to Schema.org standards -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Developer Code Generator",
  "url": "https://yourdomain.com",
  "description": "High-performance enterprise scaffolding utility.",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "All",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
</script>
```
