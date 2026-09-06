# Google AdSense CMP Consent & Legal Policy Pages Guide

## Overview
Publishers serving advertisements to visitors located in the European Economic Area (EEA), the United Kingdom, or Switzerland must comply with privacy frameworks, including GDPR and ePrivacy directives. Additionally, Google AdSense program policies require strict publisher verification via `ads.txt` and mandatory disclosures on `/privacy` and `/terms`.

---

## 1. Consent Management Platform (CMP) & IAB TCF v2.2
Google mandates that all publishers serving ads to EEA/UK users MUST use a Google-certified CMP that integrates with the IAB Europe Transparency and Consent Framework (TCF) v2.2.

### Options for Compliance:
1. **Google Funding Choices / AdSense Privacy & Messaging**:
   - Free, built directly into the AdSense console.
   - Enables instant GDPR consent dialog generation with zero third-party license fees.
2. **Third-Party Certified CMP**:
   - Platforms such as Cookiebot, OneTrust, or Didomi.
   - Must be configured to pass the IAB TCF TC string to Google's tag.

---

## 2. Mandatory `ads.txt` Authorization
The Authorized Digital Sellers (`ads.txt`) file is a simple public record preventing unauthorized ad inventory sales. Missing or misconfigured `ads.txt` files lead to earnings warnings and ad serving suppression.

### Placement & Syntax:
- MUST be served at the root domain: `https://yourdomain.com/ads.txt`.
- Content syntax:
  ```text
  google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
  ```
  - Field 1: Exchange domain (`google.com`).
  - Field 2: Publisher account ID (`pub-XXXXXXXXXXXXXXXX` without the `ca-` prefix).
  - Field 3: Relationship type (`DIRECT` if you control the account).
  - Field 4: Certification authority tag (`f08c47fec0942fa0` is Google's canonical TAG ID).

---

## 3. Mandatory Legal Policy Pages

Google AdSense audits require publicly discoverable Privacy Policy and Terms of Service pages. Sites missing these pages will be rejected during site review.

### Required Disclosures on `/privacy`:
1. **Third-Party Vendors**: State that third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to your website or other websites.
2. **Google DART Cookies**: Disclose that Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to your sites and/or other sites on the Internet.
3. **Opt-Out Link**: Provide a direct link to Google Ads Settings (`https://adssettings.google.com/`) or `aboutads.info` where users may opt out of personalized advertising.

### Valuable Inventory & Content Gate Requirements:
- Do not place advertisements on pages behind authentication barriers (login walls) without providing substantial public textual content.
- Googlebot must be able to crawl the page text to verify topic safety and inventory value.
