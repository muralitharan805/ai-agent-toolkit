# HTTP Security Headers, CORS & Runtime Ingress Defense

## Overview

A robust runtime security baseline provides defense-in-depth against client-side and network-level attack vectors. Misconfigured CORS policies, missing security headers, unthrottled endpoints, and unbounded body parsers expose applications to Cross-Site Scripting (XSS), Clickjacking, Credential Stuffing, and Denial of Service (DoS) memory exhaustion.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    The 4 Ingress Defense Boundaries                          │
└──────────────────────────────────────────────────────────────────────────────┘
  1. SECURITY HEADERS ──► Helmet: CSP, HSTS, X-Frame-Options: DENY, nosniff
  2. CORS WHITELIST   ──► Strict origin checking; zero wildcard with credentials
  3. RATE LIMITING    ──► Multi-tiered limits (Auth: 5/min, API: 1000/min)
  4. PAYLOAD BOUNDS   ──► 1MB JSON ceiling, 10MB upload ceiling, 8KB header ceiling
```

---

## 1. HTTP Security Headers Specification

Every production HTTP response must serve the standardized security headers:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; frame-ancestors 'none'; object-src 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

### Explanations & Threat Mitigations

| Header | Production Directive | Threat Mitigated |
| :--- | :--- | :--- |
| **Content-Security-Policy** | `default-src 'self'; object-src 'none'` | Cross-Site Scripting (XSS), packet injection, clickjacking. |
| **Strict-Transport-Security** | `max-age=31536000; includeSubDomains; preload` | SSL-stripping, man-in-the-middle downgrade attacks. |
| **X-Frame-Options** | `DENY` | Clickjacking / iframe overlay UI redress attacks. |
| **X-Content-Type-Options** | `nosniff` | MIME-sniffing exploits where browsers execute non-executable files. |
| **Referrer-Policy** | `strict-origin-when-cross-origin` | Sensitive URL path / token leakage in HTTP Referer headers. |
| **Permissions-Policy** | `camera=(), microphone=(), geolocation=()` | Unauthorized access to browser hardware APIs. |

---

## 2. Cross-Origin Resource Sharing (CORS) Lockdown

### The Wildcard + Credentials Hazard
When an application sets `Access-Control-Allow-Origin: *` while enabling `Access-Control-Allow-Credentials: true`, browsers reject the response per the fetch specification. Bypassing this by dynamically echoing the incoming `Origin` header without validation effectively allows any malicious website to issue authenticated credentialed requests to your API.

### Standard Origin Whitelist Implementation
Always match against an explicit whitelist of trusted production domains:

```typescript
const TRUSTED_ORIGINS = new Set([
  'https://app.example.com',
  'https://admin.example.com',
]);

export function validateCorsOrigin(
  origin: string | undefined,
  callback: (err: Error | null, allow?: boolean) => void
): void {
  // Allow curl, Postman, or server-to-server requests where origin is undefined
  if (!origin || TRUSTED_ORIGINS.has(origin)) {
    callback(null, true);
  } else {
    callback(new Error(`Origin '${origin}' blocked by CORS security policy`));
  }
}
```

---

## 3. Concrete Multi-Tiered Rate Limiting Matrix

Ingress endpoints must enforce differentiated rate limits based on operational risk:

| Endpoint Tier | Rate Limit Threshold | Window | Identifier Key | Target Threat |
| :--- | :--- | :--- | :--- | :--- |
| **Auth / Login** | `5 requests` | `1 minute` | IP Address | Credential stuffing, brute force. |
| **Auth / Registration**| `10 requests`| `1 hour` | IP Address | Fake account creation bots. |
| **Password Reset** | `3 requests` | `1 hour` | IP / Email | Email inbox flooding, account takeover. |
| **Authenticated API** | `1,000 requests` | `1 minute` | User ID / JWT sub | Resource scraping, tenant abuse. |
| **Public / Anonymous API**| `100 requests`| `1 minute` | IP Address | DDoS, unauthenticated scraping. |
| **File Upload** | `10 requests` | `1 minute` | User ID | Disk storage exhaustion, bandwidth DoS. |

---

## 4. Ingress Payload & Resource Limits

Parsing unbounded JSON strings consumes significant CPU and RAM. A single malicious 50MB JSON payload can monopolize the Node.js event loop for seconds, dropping all concurrent user traffic.

```typescript
// Explicit size bounds
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));
```

- **JSON Body**: Hard limit of `1MB`.
- **Multipart File Upload**: Hard limit of `10MB` per file; stream directly to object storage (S3/GCS) without buffering in server memory.
- **URL Length**: Hard limit of `2048` characters.
- **Header Size**: Bounded to `8KB`.
