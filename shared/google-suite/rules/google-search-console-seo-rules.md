---
description: "Universal rules for Google Search Console SEO, sitemap.xml indexing, robots.txt formatting, canonical link tags, and JSON-LD structured data schemas."
trigger: always_on
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

### 4. Domain 301 Redirection & SSL Enforcement
- Applications MUST enforce HTTPS and 301 Permanent Redirects for all non-canonical hostnames (e.g. `http://` to `https://`, `www` to non-`www` apex domain or vice-versa) to prevent duplicate content indexing penalties in Google Search Console.
