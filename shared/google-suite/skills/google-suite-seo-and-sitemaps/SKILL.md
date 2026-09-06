---
name: google-suite-seo-and-sitemaps
description: "Universal architecture, sitemap XML structures, robots.txt formatting, and JSON-LD rich snippet schema integration for Google Search Console."
---

# Google Search Console SEO, Sitemaps & Structured Data Skill

## Purpose
Establishes production-grade Google Search Console indexing hygiene, XML sitemap hierarchies, crawler directives via `robots.txt`, canonical URL normalization, and Schema.org JSON-LD structured data rich snippets across web applications and Single Page Applications (SPAs).

## Architecture & Tooling Matrix
- **Core Specification**: [references/sitemap-and-canonical-architecture.md](references/sitemap-and-canonical-architecture.md)
- **Schema.org Guide**: [references/json-ld-structured-data-guide.md](references/json-ld-structured-data-guide.md)
- **Automated CLI Validator**: [scripts/audit_seo_metadata.py](scripts/audit_seo_metadata.py)
- **Starter Templates**:
  - XML Sitemap: [assets/sitemap-template.xml](assets/sitemap-template.xml)
  - Crawler Directives: [assets/robots-template.txt](assets/robots-template.txt)
  - WebApp Schema: [assets/json-ld-webapp-template.json](assets/json-ld-webapp-template.json)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Canonical URL Normalization
1. Inject a static or dynamic canonical `<link rel="canonical" href="https://yourdomain.com/path">` tag in the `<head>` of every route.
2. Strip dynamic query strings, session IDs, and UTM tracking parameters (`?utm_source=...`) from the canonical URL target.
3. Enforce hostname consistency across apex domains vs `www` via 301 redirects, ensuring the canonical tag matches the authoritative host.
4. On independent subdomains (e.g., `tool.domain.com`), configure self-referencing canonical URLs rather than pointing to the apex domain.

### Phase 2: Crawler Directives (`robots.txt`)
1. Deploy `robots.txt` at the root domain: `https://yourdomain.com/robots.txt`.
2. Allow broad indexing for general content while explicitly disallowing private application routes (`/api/`, `/admin/`, `/_app/`, `/dashboard/`).
3. Include an absolute URL reference to the primary sitemap:
   ```text
   User-agent: *
   Allow: /
   Disallow: /api/
   Disallow: /admin/

   Sitemap: https://yourdomain.com/sitemap.xml
   ```

### Phase 3: XML Sitemap Generation & Priority Tiering
1. Scaffold an XML sitemap conforming to the `sitemaps.org` schema specification.
2. Implement tiered priority and change frequency based on route importance:
   - **Root / Hero Landing Page**: `priority: 1.0`, `changefreq: weekly`.
   - **Core Utility & Feature Routes**: `priority: 0.8`, `changefreq: weekly`.
   - **Secondary & Informational Pages**: `priority: 0.5`, `changefreq: monthly`.
   - **Legal & Compliance Pages** (`/privacy`, `/terms`): `priority: 0.3`, `changefreq: monthly`.
3. Keep individual sitemaps under 50,000 URLs and 50MB uncompressed (split into `sitemap-index.xml` if exceeding limits).

### Phase 4: Schema.org JSON-LD Structured Data
1. Inject JSON-LD metadata via `<script type="application/ld+json">` tags inside the document `<head>`.
2. Select appropriate entity types:
   - `WebApplication` or `SoftwareApplication` for interactive utilities.
   - `Article` or `BlogPosting` for documentation and editorial content.
   - `Organization` or `Person` for publisher credentials.
3. Validate schema syntax using Google's Rich Results Test and Schema.org validators.

### Phase 5: Automated Verification & Google Search Console Submission
1. Execute the automated CLI audit tool to verify compliance:
   ```bash
   python3 shared/google-suite/skills/google-suite-seo-and-sitemaps/scripts/audit_seo_metadata.py --path ./public --strict
   ```
2. In Google Search Console, submit `https://yourdomain.com/sitemap.xml` under **Sitemaps**.
3. Use the **URL Inspection Tool** to verify live crawl rendering, canonical resolution, and rich result extraction.

---

## Gotchas & Common Pitfalls

| Legacy / Faulty Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Relative Canonical Links** (`<link rel="canonical" href="/tools">`) | **Absolute Canonical URLs** (`https://yourdomain.com/tools`) | Search engines require fully qualified absolute URLs; relative links trigger parsing errors. |
| **Pointing Subdomain to Apex Domain** (`tool.domain.com` -> `domain.com`) | **Self-Referencing Subdomain Canonical Tag** | Points Googlebot away from the subdomain tool, preventing subdomain pages from indexing. |
| **Missing `robots.txt` Sitemap Reference** | Explicit `Sitemap: https://.../sitemap.xml` | Forces crawlers to guess sitemap locations, delaying indexing of deep routes. |
| **Dynamic Parameters in Canonical URL** (`href="...?ref=fb"`) | Stripped Clean Canonical URL (`href="..."`) | Fragments search equity across tracking URLs and creates duplicate content flags. |
| **Unescaped JSON-LD Content** | Valid serialized JSON without unescaped HTML characters | Corrupted JSON-LD payloads are discarded silently by search engine crawlers. |
| **Disallowing CSS/JS in `robots.txt`** | Allow public assets required for page rendering | Googlebot requires CSS/JS to render the DOM; blocking them triggers mobile-unfriendly penalties. |
