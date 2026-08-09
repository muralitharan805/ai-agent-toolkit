---
description: "Universal rules for Google AdSense monetization, publisher script placement, CMP cookie consent compliance, and CLS layout shift prevention."
trigger: always_on
---

# Universal Google AdSense Monetization Rules

## Description
Enforces mandatory standards for Google AdSense integration, Publisher ID (`ca-pub-XXXXXXXXXXXXXXXX`) management, Consent Management Platform (CMP) privacy compliance, and Web Vitals Cumulative Layout Shift (CLS) prevention.

## Constraints

### 1. Publisher ID & Script Placement
- The official AdSense script (`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX`) MUST be loaded asynchronously (`async`) in the HTML `<head>` with `crossorigin="anonymous"`.

### 2. Cumulative Layout Shift (CLS) Prevention
- Ad placement containers MUST declare explicit minimum vertical heights (`min-height: 250px` or `min-height: 90px`) to reserve layout space prior to asynchronous ad rendering, preventing Web Vitals CLS penalties.

### 3. CMP GDPR & Privacy Consent Compliance
- Monetized web applications serving users in the EEA, UK, or Switzerland MUST adopt Google's certified Consent Management Platform (CMP) or equivalent IAB TCF v2.2 framework.
