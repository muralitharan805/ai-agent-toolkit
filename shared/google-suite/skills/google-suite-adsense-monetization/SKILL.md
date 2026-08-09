---
name: google-suite-adsense-monetization
description: "Universal architecture for Google AdSense monetization, publisher script loading, CMP privacy consent management, and CLS layout shift prevention."
---

# Universal Google AdSense Monetization Architecture Skill

## Purpose
Provides universal guidelines for integrating AdSense ad units, publisher script management, and GDPR CMP consent.

## Key Implementation

### 1. Global Head Tag
```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
```

### 2. CLS Prevention Sizing
```css
.ad-slot-wrapper {
  display: block;
  min-height: 250px;
  width: 100%;
  margin: 1rem 0;
}
```
