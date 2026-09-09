# JSON-LD Structured Data & Rich Snippets Reference

## 1. Schema.org Standards & Google Search Enhancement

JSON-LD (JavaScript Object Notation for Linked Data) is Google's recommended format for structured data markup. By injecting `<script type="application/ld+json">` blocks into HTML `<head>`, web applications earn enhanced SERP appearances (site links, application ratings, breadcrumbs, search boxes).

---

## 2. Core Schema.org Types

### 2.1 WebApplication & SoftwareApplication
For software tools, SaaS products, and single page applications:
```json
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "EMI Loan Amortization Calculator",
  "url": "https://my-company.com/tools/emi-calculator",
  "applicationCategory": "FinanceApplication",
  "operatingSystem": "All",
  "browserRequirements": "Requires JavaScript. Requires HTML5.",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "INR"
  },
  "creator": {
    "@type": "Organization",
    "name": "my-company Inc",
    "url": "https://my-company.com"
  }
}
```

### 2.2 Organization & Brand
Used on homepages and legal pages:
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "my-company",
  "url": "https://my-company.com",
  "logo": "https://my-company.com/assets/logo.png",
  "sameAs": [
    "https://github.com/my-company",
    "https://twitter.com/my-company"
  ]
}
```

---

## 3. Dynamic Injection Invariants
1. **Valid JSON**: The content within `<script type="application/ld+json">` must be strictly valid JSON (no trailing commas, double-quoted keys).
2. **Platform Guarding**: In Angular / React SSR applications, structured data must render server-side during initial HTML delivery so crawlers ingest it without executing client JavaScript.
