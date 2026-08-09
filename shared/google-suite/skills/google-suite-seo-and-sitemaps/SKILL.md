---
name: google-suite-seo-and-sitemaps
description: "Universal architecture, sitemap XML structures, robots.txt formatting, and JSON-LD rich snippet schema integration for Google Search Console."
---

# Universal Google Search Console & SEO Architecture Skill

## Purpose
Provides universal guidelines for search engine optimization, Googlebot indexing, sitemap generation, and JSON-LD structured data schemas across web applications.

## Key Principles

### 1. XML Sitemap Structure (`sitemap.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yourdomain.com/</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://yourdomain.com/tools</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
```

### 2. JSON-LD Rich Snippet Schemas
Inject JSON-LD schemas into document head for search result enhancement:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "SeyaliCraft Tools",
  "url": "https://seyalicraft.com",
  "description": "High-performance developer utility tools.",
  "author": {
    "@type": "Person",
    "name": "Muralitharan K"
  }
}
</script>
```
