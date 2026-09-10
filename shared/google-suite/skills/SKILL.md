---
name: google-suite
description: "Universal architecture for Google AdSense monetization, Google Analytics 4 (GA4) integration, and Google Search Console SEO & Sitemaps."
---

# Google Suite: AdSense, GA4, & SEO Master Skill

## Purpose
Establishes production-grade Google Suite hygiene across three core pillars:
1. **AdSense Monetization**: Publisher script loading, CLS prevention, and CMP compliance.
2. **GA4 Analytics**: Measurement ID isolation, SPA route tracking, and custom event taxonomies.
3. **SEO & Sitemaps**: XML sitemap hierarchies, `robots.txt` directives, canonical normalization, and JSON-LD structured data.

## Architecture & Tooling Matrix
- **AdSense & CLS Architecture**: [references/adsense-integration-and-cls-prevention.md](references/adsense-integration-and-cls-prevention.md)
- **CMP & Legal Disclosures**: [references/cmp-gdpr-and-legal-pages-guide.md](references/cmp-gdpr-and-legal-pages-guide.md)
- **GA4 Stream Isolation**: [references/ga4-stream-isolation-and-spa-tracking.md](references/ga4-stream-isolation-and-spa-tracking.md)
- **GA4 Taxonomy Guide**: [references/custom-event-taxonomy-guide.md](references/custom-event-taxonomy-guide.md)
- **SEO & Canonical Guide**: [references/sitemap-and-canonical-architecture.md](references/sitemap-and-canonical-architecture.md)
- **JSON-LD Schema Guide**: [references/json-ld-structured-data-guide.md](references/json-ld-structured-data-guide.md)
- **Automated CLI Validators**: `scripts/audit_adsense_compliance.py`, `scripts/validate_ga4_integration.py`, `scripts/audit_seo_metadata.py`
- **Starter Templates**: Located in `assets/`
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Pillar 1: AdSense Monetization & Compliance
1. Embed the official AdSense script once in the document `<head>` asynchronously with `crossorigin="anonymous"`.
2. Wrap all ad slots in an enclosing container that declares explicit `min-height` in CSS to prevent CLS layout shifts.
3. Deploy `ads.txt` at the root of the domain: `https://yourdomain.com/ads.txt`.
4. Configure a Google-certified CMP for EEA/UK traffic and deploy public Privacy Policy and Terms of Service routes.

### Pillar 2: GA4 Analytics & SPA Tracking
1. Provision distinct Web Data Streams for each environment and subdomain (`marketing.domain.com`, `app.domain.com`).
2. In SPAs, disable automatic pageviews (`send_page_view: false`) and explicitly dispatch `page_view` events on router navigation completion.
3. Standardize custom event names in `snake_case` (e.g. `cta_click`) and implement defensive dispatch wrappers.
4. Sanitize payloads: Strip plaintext emails, passwords, auth tokens, and credit card numbers. Use salted cryptographic hashes for user tracking.

### Pillar 3: SEO, Sitemaps & Structured Data
1. Inject absolute canonical `<link rel="canonical" href="...">` tags, stripping dynamic query strings.
2. Deploy a `robots.txt` at the root domain that references the absolute `sitemap.xml` URL and blocks private `/api/` routes.
3. Scaffold a `sitemaps.org` compliant XML sitemap with tiered priority and change frequency (e.g., `1.0` for home).
4. Inject JSON-LD metadata via `<script type="application/ld+json">` for entities like `WebApplication` or `Article`.

---

## Gotchas & Common Pitfalls

| Pillar | Legacy / Faulty Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- | :--- |
| **AdSense** | **Unreserved Ad Heights** (`min-height: 0`) | **CSS `min-height` Space Reservation** | Content jumps down suddenly when ads load, severely failing Core Web Vitals CLS. |
| **AdSense** | **Missing Privacy Policy Page** | Public `/privacy` with DART disclosures | Automated crawler rejects account approval or revokes ad serving. |
| **GA4** | **Single ID on All Subdomains** | **Dedicated Data Streams per Subdomain** | Merging app and marketing traffic corrupts bounce rates and funnel metrics. |
| **GA4** | **Default Auto-Pageviews in SPAs** | `send_page_view: false` + Router Dispatch | Causes duplicate pageviews on initial load and misses route transitions. |
| **GA4** | **Transmitting Plaintext Emails** | Salted cryptographic hashes | Violates Terms of Service and triggers immediate account suspension. |
| **SEO** | **Relative Canonical Links** | **Absolute Canonical URLs** | Search engines require fully qualified absolute URLs; relative links trigger parsing errors. |
| **SEO** | **Subdomain to Apex Canonical** | **Self-Referencing Subdomain Canonical** | Points Googlebot away from the subdomain tool, preventing indexing. |
| **SEO** | **Missing `robots.txt` Sitemap** | Explicit `Sitemap: https://.../sitemap.xml` | Forces crawlers to guess locations, delaying indexing of deep routes. |
