# GA4 Route Tracking & Google AdSense Monetization in Angular SPAs

This reference details the mechanics of Google Analytics 4 (GA4) client-side route telemetry and Google AdSense ad unit integration in Single Page Applications.

---

## 1. Why Standard GA4 Tags Fail in Single Page Applications

Traditional multi-page websites execute a full browser reload on every hyperlink navigation, triggering the Google tag (`gtag.js`) `<head>` script and recording a `page_view` event automatically.

In Angular SPAs:
1. The initial HTML shell (`index.html`) loads once.
2. Subsequent route transitions update the browser history API (`pushState`) without reloading the document.
3. **Failure Mode**: Standard GA4 tags only capture the initial landing route. Deep navigation through the app remains completely invisible in Google Analytics unless explicitly tracked via `Router.events`.

### The Solution: `NavigationEnd` Event Subscription

```typescript
this.router.events
  .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
  .subscribe((event: NavigationEnd) => {
    if (typeof window.gtag === 'function') {
      window.gtag('config', measurementId, {
        page_path: event.urlAfterRedirects,
      });
    }
  });
```

---

## 2. Web Vitals Cumulative Layout Shift (CLS) Prevention in AdSense

AdSense ads load asynchronously and inject responsive `<iframe>` elements whose exact vertical dimensions vary based on available inventory auctions.

### The Problem
If the container element has no predefined height, the page layout violently shifts downwards when the ad renders, triggering severe Google Core Web Vitals penalties (CLS > 0.1).

### Mandatory Container Architecture
AdSense units MUST reside inside fixed-height or min-height wrapper elements:
```html
<div class="ad-slot-container" style="min-height: 250px; width: 100%; display: block; overflow: hidden;">
  <ins class="adsbygoogle"
       style="display: block;"
       data-ad-client="ca-pub-1649083292065809"
       data-ad-slot="1234567890"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
</div>
```

---

## 3. Google AdSense Program Policy Compliance

Monetized web applications must fulfill specific legal criteria before Google approves an AdSense application:

### Mandatory Policy Pages
1. `/privacy`: Privacy Policy detailing:
   - Collection of non-PII analytics data.
   - Use of cookies by third-party vendors (Google).
   - Google DART cookie disclosure for personalized advertising.
   - User opt-out link pointing to `https://www.google.com/settings/ads`.
2. `/terms`: Terms of Service defining acceptable use and disclaimers.

### Footers & Navigation Access
Links to `/privacy` and `/terms` must be persistently visible in application layout footers (`MainLayoutComponent`).

### Publisher Authorization (`public/ads.txt`)
Deploy `public/ads.txt` declaring publisher authorization:
```text
google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
```
Missing or incorrectly formatted `ads.txt` will result in crawler crawling errors and blocked monetization revenue.
