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
