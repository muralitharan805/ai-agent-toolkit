---
name: angular-ssr-google-suite
description: "Angular Edge SSR code templates for server.ts XML Response stream, TransferState meta tag hydration, and platform-guarded analytics."
---

# Angular Edge SSR Google Suite Skill

## Code Templates

### 1. Edge Server XML Response Stream (`src/server.ts`)
```typescript
import { AngularAppEngine, createRequestHandler } from '@angular/ssr';

const angularApp = new AngularAppEngine();

const SITEMAP_XML = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://seyalicraft.com/</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>`;

export const reqHandler = createRequestHandler(async (req: Request) => {
  const url = new URL(req.url);
  const path = url.pathname.toLowerCase().replace(/\/$/, '');

  if (path === '/sitemap.xml') {
    return new Response(SITEMAP_XML, {
      headers: {
        'Content-Type': 'application/xml; charset=UTF-8',
        'Cache-Control': 'public, max-age=86400'
      }
    });
  }

  const response = await angularApp.handle(req);
  return response ?? new Response('Not Found', { status: 404 });
});

export default {
  fetch: reqHandler,
};
```

### 2. Static HTML Head Fallback (`src/index.html`)
Declare the fallback canonical tag in document `<head>`:
```html
<link rel="canonical" href="https://seyalicraft.com/" />
```

### 3. SSR-Safe Dynamic Dynamic Canonical & Meta Service (`src/app/core/services/seo.service.ts`)
```typescript
import { Injectable, inject } from '@angular/core';
import { Meta } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';

export interface SeoConfig {
  title: string;
  description: string;
  url: string;
  image?: string;
  canonicalUrl?: string;
}

@Injectable({ providedIn: 'root' })
export class SeoService {
  private readonly meta = inject(Meta);
  private readonly document = inject(DOCUMENT);

  /**
   * Updates standard Open Graph, Twitter, and meta description tags.
   */
  setMetaTags(config: SeoConfig): void {
    this.meta.updateTag({ name: 'description', content: config.description });
    this.meta.updateTag({ property: 'og:title', content: config.title });
    this.meta.updateTag({ property: 'og:description', content: config.description });
    this.meta.updateTag({ property: 'og:url', content: config.url });
    this.meta.updateTag({ property: 'og:image', content: config.image || `${config.url}/favicon.ico` });
    this.meta.updateTag({ property: 'twitter:card', content: 'summary_large_image' });

    this.setCanonicalUrl(config.canonicalUrl || config.url);
  }

  /**
   * Injects or updates the canonical link tag (<link rel="canonical" href="...">)
   * in the document head during SSR pre-rendering and CSR navigation.
   */
  setCanonicalUrl(url?: string): void {
    const targetUrl = url || `https://seyalicraft.com${this.document.location?.pathname || ''}`;
    let link: HTMLLinkElement | null = this.document.querySelector("link[rel='canonical']");

    if (!link) {
      link = this.document.createElement('link');
      link.setAttribute('rel', 'canonical');
      this.document.head.appendChild(link);
    }

    link.setAttribute('href', targetUrl);
  }
}
```
