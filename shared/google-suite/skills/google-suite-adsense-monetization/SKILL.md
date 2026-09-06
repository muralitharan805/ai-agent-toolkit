---
name: google-suite-adsense-monetization
description: "Universal architecture for Google AdSense monetization, publisher script loading, CMP privacy consent management, and CLS layout shift prevention."
---

# Google AdSense Monetization & Performance Optimization Skill

## Purpose
Establishes production-grade Google AdSense monetization hygiene, asynchronous script loading, Cumulative Layout Shift (CLS) layout space reservation, Consent Management Platform (CMP) compliance, and mandatory `ads.txt` and legal policy disclosures.

## Architecture & Tooling Matrix
- **AdSense & CLS Architecture**: [references/adsense-integration-and-cls-prevention.md](references/adsense-integration-and-cls-prevention.md)
- **CMP & Legal Disclosures**: [references/cmp-gdpr-and-legal-pages-guide.md](references/cmp-gdpr-and-legal-pages-guide.md)
- **Automated CLI Validator**: [scripts/audit_adsense_compliance.py](scripts/audit_adsense_compliance.py)
- **Starter Templates**:
  - Root Authorization: [assets/ads-txt-template.txt](assets/ads-txt-template.txt)
  - Privacy Policy: [assets/privacy-policy-template.md](assets/privacy-policy-template.md)
  - Terms of Service: [assets/terms-of-service-template.md](assets/terms-of-service-template.md)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Publisher Script Loading & Client Setup
1. Embed the official AdSense script once in the document `<head>`:
   ```html
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
   ```
2. Verify that `ca-pub-XXXXXXXXXXXXXXXX` matches your verified 16-digit publisher account ID.
3. Ensure the script tag executes asynchronously with `crossorigin="anonymous"`.

### Phase 2: Cumulative Layout Shift (CLS) Reservation
1. Never render unconstrained `<ins class="adsbygoogle">` tags directly inside content flows without an outer container.
2. Wrap all ad slots in an enclosing container that declares explicit minimum height in CSS:
   ```css
   .ad-banner-container {
     display: flex;
     justify-content: center;
     align-items: center;
     min-height: 280px; /* Reserves layout for 250px unit + padding */
     width: 100%;
     margin: 1.5rem 0;
   }
   ```
3. Use responsive sizing for desktop leaderboards (`min-height: 100px`) vs mobile banners.

### Phase 3: Root `ads.txt` Authorization Deployment
1. Deploy `ads.txt` at the root of the domain: `https://yourdomain.com/ads.txt`.
2. Populate the Google Authorized Digital Sellers entry:
   ```text
   google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
   ```
3. Omit the `ca-` prefix in the `ads.txt` second column.

### Phase 4: Consent Management Platform (CMP) & Legal Disclosures
1. For traffic originating in the EEA, UK, or Switzerland, configure a Google-certified CMP (e.g. Google Funding Choices / Privacy & Messaging) supporting IAB TCF v2.2.
2. Deploy public Privacy Policy (`/privacy`) and Terms of Service (`/terms`) routes.
3. Disclose third-party Google advertising, DART cookies, and explicit opt-out links (`https://adssettings.google.com/`).
4. Ensure ad-bearing pages render substantial public content to satisfy AdSense "Valuable Inventory" requirements.

### Phase 5: Automated Verification & Compliance Testing
1. Execute the automated CLI audit tool:
   ```bash
   python3 shared/google-suite/skills/google-suite-adsense-monetization/scripts/audit_adsense_compliance.py --path ./public --strict
   ```
2. Inspect the live application using Chrome DevTools Lighthouse to verify CLS remains under 0.1.
3. Check the AdSense console **Sites** dashboard to confirm zero `ads.txt` or policy alerts.

---

## Gotchas & Common Pitfalls

| Legacy / Faulty Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Unreserved Ad Heights** (`min-height: 0` or missing) | **CSS `min-height` Space Reservation** | Content jumps down suddenly when ads load, severely failing Core Web Vitals CLS. |
| **Including `ca-` in `ads.txt`** (`pub-ID` field) | Stripped `pub-XXXXXXXXXXXXXXXX` | Crawlers reject entries with `ca-` prefix, flagging ads.txt as invalid in AdSense. |
| **Missing Privacy Policy Page** | Public `/privacy` with DART cookie disclosures | Automated AdSense compliance crawler rejects account approval or revokes ad serving. |
| **Ads Behind Strict Authentication Walls** | Public feature copy + Valuable Inventory | Googlebot cannot crawl private authenticated dashboards, triggering "No Content" policy violations. |
| **Timer-Based Artificial Ad Refresh** (`setInterval`) | Route navigation ad refresh only | Artificially refreshing ads without user interaction triggers account suspension for fraud. |
| **Multiple Script Tags per Ad Unit** | Single global `<script async>` in `<head>` | Multiple script loads degrade page performance and cause script parsing conflicts. |
