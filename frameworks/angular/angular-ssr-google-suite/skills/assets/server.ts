import { AngularAppEngine, createRequestHandler } from '@angular/ssr';

const angularApp = new AngularAppEngine();

/**
 * Standard XML Sitemap definition declaring canonical URLs for Google Search Console.
 */
const SITEMAP_XML = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yourdomain.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://yourdomain.com/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://yourdomain.com/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>`;

/**
 * Cloudflare Workers / Pages edge request handler.
 *
 * Intercepts `/sitemap.xml` directly to return high-performance, edge-cached XML
 * streams, bypassing Angular rendering overhead for search engine crawlers.
 * Delegates all other requests to AngularAppEngine for Server-Side Rendering.
 *
 * @param req - The incoming native Web Request object
 * @returns Web standard Response stream
 */
export const reqHandler = createRequestHandler(async (req: Request): Promise<Response> => {
  const url = new URL(req.url);
  const pathname = url.pathname.toLowerCase().replace(/\/$/, '');

  // Fast-path edge intercept for Google Search Console sitemap
  if (pathname === '/sitemap.xml') {
    return new Response(SITEMAP_XML, {
      status: 200,
      headers: {
        'Content-Type': 'application/xml; charset=UTF-8',
        'Cache-Control': 'public, max-age=86400, s-maxage=86400'
      }
    });
  }

  const response = await angularApp.handle(req);
  return response ?? new Response('Not Found', { status: 404 });
});

export default {
  fetch: reqHandler,
};
