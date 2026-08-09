---
description: "Universal rules for Google Analytics 4 (GA4) measurement IDs, stream isolation, custom event payload masking, and PII privacy compliance."
trigger: always_on
---

# Universal Google Analytics 4 (GA4) Rules

## Description
Enforces mandatory standards for GA4 tracking scripts, Measurement ID isolation across subdomains, custom event taxonomy, and strict Personally Identifiable Information (PII) sanitization.

## Constraints

### 1. Data Stream Isolation Per Subdomain
- Applications operating across multiple subdomains (`app.domain.com`, `tool.domain.com`) MUST use dedicated GA4 Web Data Stream Measurement IDs (`G-XXXXXXXXXX`) to prevent cross-traffic data pollution.

### 2. Mandatory PII & Sensitive Data Masking
- Analytics payloads MUST NOT log plain-text user passwords, authorization tokens, credit card numbers, or email addresses in event attributes.

### 3. Client-Side Script Verification
- GA4 `gtag.js` scripts MUST be loaded asynchronously (`async`) from official Google tag endpoints (`https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX`).
