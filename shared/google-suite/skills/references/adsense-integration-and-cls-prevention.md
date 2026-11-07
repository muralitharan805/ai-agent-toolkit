# Google AdSense Integration & Cumulative Layout Shift (CLS) Prevention

## Overview
Monetizing web applications with Google AdSense requires strict adherence to Web Vitals performance benchmarks and Google publisher policies. Improper ad insertion causes jarring layout shifts (CLS penalties), degrades user experience, and risks account demonetization.

---

## 1. Publisher Script Placement
The AdSense loader script must be embedded once in the document `<head>`:

```html
<script 
  async 
  src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" 
  crossorigin="anonymous">
</script>
```

### Script Requirements:
- **Asynchronous**: Always load with `async` to prevent blocking the initial page render.
- **Crossorigin**: Use `crossorigin="anonymous"` for security header compliance.
- **Single Script Instance**: Do not inject duplicate script tags for individual ad units.

---

## 2. Cumulative Layout Shift (CLS) Prevention
Google's Core Web Vitals penalize pages where content shifts abruptly as asynchronous advertisements load. Unreserved ad containers start with a height of `0px` and abruptly push content down by `250px`–`600px` upon rendering.

### The Minimum Height Reservation Rule
Every ad unit container MUST reserve its expected vertical dimensions in CSS before the advertisement renders:

```css
/* Container wrapper reserving space */
.ad-banner-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 280px; /* Reserves layout for 250px ad + padding */
  width: 100%;
  margin: 1.5rem 0;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  overflow: hidden;
}

/* Horizontal leaderboard container */
.ad-leaderboard-container {
  min-height: 100px; /* Reserves layout for 90px leaderboard */
  width: 100%;
  margin: 1rem 0;
}
```

### Template Markup (Responsive Ad Unit)
```html
<aside class="ad-banner-container" aria-label="Advertisement">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
       data-ad-slot="1234567890"
       data-ad-format="auto"
       data-full-width-responsive="true">
  </ins>
</aside>
```

---

## 3. SPA Route Navigation & Ad Refresh Lifecycle
In Single Page Applications (Angular, React, Vue), the DOM updates without full browser reloads. 

### Triggering AdSense in Modern SPAs
After dynamic route rendering completes:
```typescript
declare global {
  interface Window {
    adsbygoogle?: unknown[];
  }
}

export function pushAdUnit(): void {
  if (typeof window !== 'undefined' && Array.isArray(window.adsbygoogle)) {
    try {
      window.adsbygoogle.push({});
    } catch (e) {
      // Catch duplicate push errors safely during fast client-side transitions
      console.error('AdSense push suppressed:', e);
    }
  }
}
```

### Critical SPA Warning
- Never refresh ad units artificially using interval timers (`setInterval`). Google policies strictly prohibit refreshing ads without explicit user navigation or significant content updates.
