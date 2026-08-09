---
name: google-suite-ga4-analytics
description: "Universal architecture for Google Analytics 4 (GA4) measurement IDs, stream isolation, and custom event tracking."
---

# Universal GA4 Analytics Architecture Skill

## Purpose
Provides universal guidelines for setting up GA4 data streams, tracking pageviews, and emitting custom interaction events.

## Key Implementation

### 1. Global Head Tag (`index.html`)
```html
<!-- Google tag (gtag.js) GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### 2. Custom Event Payload Protocol
```javascript
if (typeof window.gtag === 'function') {
  window.gtag('event', 'tool_compute', {
    tool_name: 'wkt_to_geojson',
    execution_time_ms: 12
  });
}
```
