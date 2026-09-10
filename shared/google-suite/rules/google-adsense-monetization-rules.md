---
description: "Universal rules for Google AdSense monetization, publisher script placement, legal policy pages, CMP cookie consent compliance, and CLS layout shift prevention."
trigger: model_decision
---

# Universal Google AdSense Monetization Rules

## Description
Enforces mandatory standards for Google AdSense integration, Publisher ID (`ca-pub-XXXXXXXXXXXXXXXX`) management, Consent Management Platform (CMP) privacy compliance, mandatory Privacy Policy/Terms legal page scaffolding, and Web Vitals Cumulative Layout Shift (CLS) prevention.

## Constraints

### 1. Publisher ID & Script Placement
- The official AdSense script (`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX`) MUST be loaded asynchronously (`async`) in the HTML `<head>` with `crossorigin="anonymous"`.
- Duplicate AdSense script tags across individual component templates are STRICTLY FORBIDDEN.

### 2. Cumulative Layout Shift (CLS) Prevention
- Ad placement containers MUST declare explicit minimum vertical heights (`min-height: 250px` or `min-height: 100px`) to reserve layout space prior to asynchronous ad rendering, preventing Web Vitals CLS penalties.
- Bare `<ins class="adsbygoogle">` tags without container wrapper height reservations are strictly prohibited.

### 3. CMP GDPR & Privacy Consent Compliance
- Monetized web applications serving users in the EEA, UK, or Switzerland MUST adopt Google's certified Consent Management Platform (CMP) or equivalent IAB TCF v2.2 framework.

### 4. Mandatory `ads.txt` File Presence
- Applications displaying AdSense advertisements MUST deploy a valid `/ads.txt` file at root domain containing:
  ```text
  google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
  ```
- Unverified publisher sites missing `ads.txt` are strictly prohibited to prevent AdSense earnings risk warnings.
- The `ca-` prefix MUST NOT be included in `ads.txt` records.

### 5. Mandatory Legal Policy Pages (`/privacy` & `/terms`)
- Monetized web applications MUST deploy publicly accessible Privacy Policy (`/privacy`) and Terms of Service (`/terms`) pages.
- The Privacy Policy MUST explicitly disclose:
  1. Google AdSense third-party vendor advertising.
  2. Google DART cookie usage for personalized ad serving.
  3. User opt-out mechanisms via Google Ads Settings.

### 6. Public Content & Valuable Inventory Compliance
- Monetized applications MUST NOT restrict all site content behind authentication walls (`/auth/login`) without providing public landing text.
- Un-authenticated pages MUST render public feature text, `<h1>` / `<h2>` headers, and feature badges to satisfy AdSense "Valuable Inventory" requirements.

## Examples

### 1. Script Placement & Layout Shift Container Reservation
```html
<!-- ❌ FORBIDDEN: Unreserved 0px starting height causing jarring layout jumps -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-1234567890123456"
     data-ad-slot="9876543210"></ins>

<!-- ✅ CORRECT: Wrapper container with explicit min-height reservation -->
<div class="ad-banner-slot" style="min-height: 280px; width: 100%; display: flex; justify-content: center;">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-1234567890123456"
       data-ad-slot="9876543210"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
</div>
```

### 2. Valid Root ads.txt File Deployment
```text
# ❌ FORBIDDEN: Including ca- prefix or invalid relationship
google.com, ca-pub-1234567890123456, RESELLER

# ✅ CORRECT: Canonical Google TAG entry with DIRECT relationship and stripped ca- prefix
google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0
```

### 3. Legal Privacy Policy Disclosure Statement
```markdown
<!-- ✅ CORRECT: Explicit third-party advertising and DART cookie disclosure -->
## Third-Party Advertising & Cookies
We partner with Google AdSense to serve advertisements. Google uses cookies (including the DART cookie)
to serve personalized ads based on your prior visits to our website and other websites across the Internet.
You can manage or opt out of personalized advertising by visiting:
[Google Ads Settings](https://adssettings.google.com/)
```
