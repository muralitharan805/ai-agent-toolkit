---
description: "Universal rules for Google Analytics 4 (GA4) measurement IDs, stream isolation, custom event payload masking, and PII privacy compliance."
trigger: model_decision
---

# Universal Google Analytics 4 (GA4) Rules

## Description
Enforces mandatory standards for GA4 tracking scripts, Measurement ID isolation across subdomains, custom event taxonomy, and strict Personally Identifiable Information (PII) sanitization.

## Constraints

### 1. Data Stream Isolation Per Subdomain
- Applications operating across multiple subdomains (`app.domain.com`, `tool.domain.com`) MUST use dedicated GA4 Web Data Stream Measurement IDs (`G-XXXXXXXXXX`) to prevent cross-traffic data pollution.
- Shared measurement IDs across unrelated business domains or staging/production environments are STRICTLY FORBIDDEN.

### 2. Mandatory PII & Sensitive Data Masking
- Analytics payloads MUST NOT log plain-text user passwords, authorization tokens, credit card numbers, or email addresses in event attributes.
- URLs logged in `page_location` MUST have sensitive tokens and query strings stripped prior to dispatch.

### 3. Client-Side Script Verification & SPA Routing
- GA4 `gtag.js` scripts MUST be loaded asynchronously (`async`) from official Google tag endpoints (`https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX`).
- Single Page Applications MUST configure `send_page_view: false` in the initial gtag configuration and dispatch explicit `page_view` events upon router navigation completion.

### 4. Event Taxonomy Standards
- Custom events MUST use `snake_case` naming and adhere to the `entity_action` convention (e.g., `button_click`, `form_submit`).
- Event names and parameter names MUST NOT exceed 40 characters.
- Reserved Google prefixes (`_`, `ga_`, `google_`, `firebase_`) MUST NOT be used.

## Examples

### 1. Asynchronous Script Placement with SPA Configuration
```html
<!-- ❌ FORBIDDEN: Synchronous script loading with default auto-pageviews causing duplicate SPA tracking -->
<script src="https://www.googletagmanager.com/gtag/js?id=G-1234567890"></script>
<script>
  gtag('config', 'G-1234567890');
</script>

<!-- ✅ CORRECT: Asynchronous loading with send_page_view: false for router-controlled navigation -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1234567890"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-1234567890', {
    send_page_view: false
  });
</script>
```

### 2. Custom Event Dispatch & PII Sanitization
```typescript
// ❌ FORBIDDEN: Logging raw email and password in analytics event
function onUserLogin(email: string, token: string): void {
  gtag('event', 'login', {
    user_email: email, // CRITICAL RISK: Transmitting PII to GA4!
    auth_token: token
  });
}

// ✅ CORRECT: Logging hashed pseudonymous identifiers and snake_case events
function onUserLogin(userIdHash: string): void {
  if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
    window.gtag('event', 'user_login', {
      user_id_hash: userIdHash,
      login_method: 'oauth_google'
    });
  }
}
```

### 3. Dedicated Measurement IDs Across Subdomains
```typescript
// ✅ CORRECT: Determining Measurement ID dynamically by host environment
export function getMeasurementIdForHost(hostname: string): string {
  if (hostname.startsWith('tools.')) {
    return 'G-TOOLS00001';
  }
  if (hostname.startsWith('app.')) {
    return 'G-APP0000002';
  }
  return 'G-MKT0000003'; // Apex marketing portal
}
```
