---
description: "Universal rules for Google AdSense monetization, publisher script placement, legal policy pages, CMP cookie consent compliance, and CLS layout shift prevention."
trigger: always_on
---

# Universal Google AdSense Monetization Rules

## Description
Enforces mandatory standards for Google AdSense integration, Publisher ID (`ca-pub-XXXXXXXXXXXXXXXX`) management, Consent Management Platform (CMP) privacy compliance, mandatory Privacy Policy/Terms legal page scaffolding, and Web Vitals Cumulative Layout Shift (CLS) prevention.

## Constraints

### 1. Publisher ID & Script Placement
- The official AdSense script (`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX`) MUST be loaded asynchronously (`async`) in the HTML `<head>` with `crossorigin="anonymous"`.

### 2. Cumulative Layout Shift (CLS) Prevention
- Ad placement containers MUST declare explicit minimum vertical heights (`min-height: 250px` or `min-height: 90px`) to reserve layout space prior to asynchronous ad rendering, preventing Web Vitals CLS penalties.

### 3. CMP GDPR & Privacy Consent Compliance
- Monetized web applications serving users in the EEA, UK, or Switzerland MUST adopt Google's certified Consent Management Platform (CMP) or equivalent IAB TCF v2.2 framework.

### 4. Mandatory `ads.txt` File Presence
- Applications displaying AdSense advertisements MUST deploy a valid `/ads.txt` file at root domain containing:
  ```text
  google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
  ```
- Unverified publisher sites missing `ads.txt` are strictly prohibited to prevent AdSense earnings risk warnings.

### 5. Mandatory Legal Policy Pages (`/privacy` & `/terms`)
- Monetized web applications MUST deploy publicly accessible Privacy Policy (`/privacy`) and Terms of Service (`/terms`) pages.
- The Privacy Policy MUST explicitly disclose:
  1. Google AdSense third-party vendor advertising.
  2. Google DART cookie usage for personalized ad serving.
  3. User opt-out mechanisms via Google Ads Settings.
- Missing Privacy Policy or Terms pages will trigger automated AdSense rejections (`Meet AdSense program policies`).

### 6. Public Content & Valuable Inventory Compliance
- Monetized applications MUST NOT restrict all site content behind authentication walls (`/auth/login`) without providing public landing text.
- Un-authenticated pages MUST render public feature text, `<h1>` / `<h2>` headers, and feature badges to satisfy AdSense "Valuable Inventory" requirements.
