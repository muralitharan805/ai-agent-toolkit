# XML Sitemap, Robots.txt & Canonical URL Architecture

## 1. Overview & Search Console Indexing Principles

Google Search Console and modern search engine web crawlers (Googlebot) require clear, unambiguous signals to discover, index, and rank web pages. The primary signals are **XML Sitemaps**, **Robots.txt Directives**, and **Canonical Link Tags**.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                          SEO Discovery Architecture                            │
└────────────────────────────────────────────────────────────────────────────────┘
  [Googlebot / Web Crawler]
         │
         ├──► Fetches `/robots.txt` ──► Discovers `Sitemap: https://domain.com/sitemap.xml`
         │
         ├──► Fetches `/sitemap.xml` ──► Static file (SPA) OR Edge Streaming Handler (SSR)
         │                              Extracts canonical URLs, `<lastmod>`, `<priority>`
         ▼
  [Page Document Render]
         │
         ├──► Inspects `<link rel="canonical" href="...">`
         └──► Parses `<script type="application/ld+json">` structured data
```

---

## 2. Static Sitemaps (CSR / SPA) vs. Dynamic Edge Streaming (SSR)

### 2.1 Static XML Sitemaps (Single Page Applications)
For client-side rendered SPAs, maintain a static `public/sitemap.xml` updated during the build step:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yourdomain.com/</loc>
    <lastmod>2026-09-06</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://yourdomain.com/features</loc>
    <lastmod>2026-09-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

### 2.2 Edge Dynamic XML Streaming (Server-Side Rendering / Cloudflare Workers)
For SSR applications, stream `/sitemap.xml` dynamically from the edge server handler returning standard `application/xml` response headers:
```typescript
export function handleSitemapRequest(routes: readonly string[]): Response {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes
  .map(
    (route) => `  <url>
    <loc>https://yourdomain.com${route}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>`
  )
  .join('\n')}
</urlset>`;

  return new Response(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=86400, s-maxage=86400',
    },
  });
}
```

### 2.3 Cloudflare Edge Route Exclusion (`_routes.json`)
In Cloudflare Pages and Workers Edge deployments, exclude static assets and sitemaps from Worker execution to serve directly from global CDN edge caches:
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

---

## 3. Canonical Link Tag Normalization

To avoid duplicate content penalties in Google Search Console:
1. **Enforce Single Domain Format**: Enforce apex domain (`https://yourdomain.com/`) or `www` format via HTTP 301 redirects in Cloudflare / Nginx.
2. **Subdomain Self-Referencing**: Each subdomain (`https://tool.domain.com/`) MUST point to its own URL, NOT the apex domain.
3. **Tracking Parameter Stripping**: Dynamic canonical tag injectors must strip marketing query parameters (`?utm_source=...`, `?ref=...`, `?fbclid=...`).
