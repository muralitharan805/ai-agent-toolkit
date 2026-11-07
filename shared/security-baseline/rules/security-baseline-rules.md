---
trigger: model_decision
description: "Enforces production runtime security baselines: mandatory HTTP security headers (CSP, HSTS, X-Frame-Options), strict CORS origin whitelisting, concrete rate-limiting tiers, and request payload size limits (1MB JSON, 10MB uploads, 8KB headers)."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Runtime Security Baseline & Defense Standards

## Description
Enforces mandatory production runtime security controls, transport-layer defense, and ingress request sanitization across all backend APIs and web applications. Mandates the complete HTTP security header suite (Content-Security-Policy, HSTS for 1 year, X-Frame-Options: DENY, nosniff, Referrer-Policy, Permissions-Policy), strict CORS origin whitelisting prohibiting credentialed wildcards, concrete multi-tiered rate limiting (auth, public, authenticated, and uploads), strict inbound request payload and header size limits to eliminate memory exhaustion DoS attacks, runtime XSS/CSRF mitigation, and zero hardcoded secrets.

## Constraints

### 1. Mandatory HTTP Security Headers
- Every production HTTP response MUST include the complete suite of security headers (via Helmet or equivalent middleware):
  - `Content-Security-Policy`: Must define strict sources (`default-src 'self'`). Inline scripts without cryptographic nonces or hashes are strictly forbidden.
  - `Strict-Transport-Security (HSTS)`: Must enforce HTTPS for a minimum of 1 year: `max-age=31536000; includeSubDomains; preload`.
  - `X-Frame-Options`: Must be set to `DENY` to eliminate clickjacking.
  - `X-Content-Type-Options`: Must be set to `nosniff` to prevent MIME-type confusion attacks.
  - `Referrer-Policy`: Must be set to `strict-origin-when-cross-origin`.
  - `Permissions-Policy`: Must disable unused browser device APIs (e.g. `camera=(), microphone=(), geolocation=()`).

### 2. Strict Cross-Origin Resource Sharing (CORS) Governance
- **Prohibition of Credentialed Wildcards**: Configuring `Access-Control-Allow-Origin: *` while simultaneously enabling `credentials: true` is a CRITICAL SECURITY VULNERABILITY and is STRICTLY FORBIDDEN.
- Production applications MUST maintain an explicit, validated origin whitelist:
  - Whitelist origins matching exact authorized domains (e.g. `https://app.company.com`).
  - Allowed methods: Explicitly restricted to `GET, POST, PUT, PATCH, DELETE, OPTIONS`.
  - Preflight Caching: Preflight responses MUST specify `maxAge: 600` (10 minutes) to eliminate redundant `OPTIONS` round-trips.

### 3. Concrete Multi-Tiered Rate Limiting Matrix
- Ingress routers MUST implement rate limiting differentiated by endpoint risk profile:
  - **Auth Login (`/auth/login`)**: Strict `5 requests / 1 minute` per IP address.
  - **Auth Registration (`/auth/register`)**: `10 requests / 1 hour` per IP address.
  - **Password Reset (`/auth/forgot-password`)**: `3 requests / 1 hour` per IP address.
  - **Authenticated API Routes**: `1,000 requests / 1 minute` per User ID.
  - **Public / Anonymous API Routes**: `100 requests / 1 minute` per IP address.
  - **File Upload Endpoints**: `10 requests / 1 minute` per User ID.
- Rate-limited responses MUST return HTTP `429 Too Many Requests` along with standard `Retry-After` headers.

### 4. Inbound Request Payload & Size Limits
- Inbound body parsers MUST configure explicit size ceilings to prevent Denial of Service (DoS) memory exhaustion:
  - **JSON Request Body**: Hard limit of `1MB` (server returns HTTP `413 Payload Too Large`).
  - **File Uploads**: Maximum `10MB` per file; MUST be isolated to dedicated streaming upload endpoints.
  - **URL Length**: Maximum `2,048 characters` (server returns HTTP `414 URI Too Long`).
  - **HTTP Header Size**: Maximum `8KB` (server returns HTTP `431 Request Header Fields Too Large`).

### 5. Injection, XSS & CSRF Runtime Defenses
- **SQL Injection Prevention**: Raw unparameterized SQL string concatenation is STRICTLY FORBIDDEN. All queries must use parameterized ORM query builders or prepared statements.
- **XSS Mitigation**: User-submitted rich text rendered in web contexts MUST pass through strict HTML whitelisting (DOMPurify or sanitize-html).
- **CSRF Defense**: Session cookies MUST declare `SameSite=Strict` or `SameSite=Lax`.

### 6. Zero Hardcoded Secrets & Secret Hygiene
- Source code, commit messages, Dockerfiles, and test files MUST NEVER contain hardcoded secrets, database passwords, or private keys.
- Configuration must be loaded from environment variables or external secret managers (AWS Secrets Manager, HashiCorp Vault).

## Examples

### 1. Hardened Security Headers with Helmet

```typescript
// ✅ CORRECT: Complete HTTP security headers configuration
import helmet from 'helmet';

export const securityHeadersMiddleware = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"], // Or hash-based
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", 'https://api.company.com'],
      frameAncestors: ["'none'"],
      objectSrc: ["'none'"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
  frameguard: { action: 'deny' },
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  permittedCrossDomainPolicies: { permittedPolicies: 'none' },
});
```

### 2. Strict CORS Configuration with Dynamic Origin Whitelist

```typescript
// ✅ CORRECT: Whitelist-checked CORS with credential protection
import cors from 'cors';

const ALLOWED_ORIGINS = new Set([
  'https://app.company.com',
  'https://admin.company.com',
]);

export const corsMiddleware = cors({
  origin: (origin, callback) => {
    // Allow non-browser requests (curl, server-to-server) where origin is undefined
    if (!origin || ALLOWED_ORIGINS.has(origin)) {
      callback(null, true);
    } else {
      callback(new Error(`Origin '${origin}' not allowed by CORS security policy`));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  credentials: true,
  maxAge: 600, // 10 minutes preflight cache
});
```

### 3. Payload Body Limit Configuration

```typescript
// ✅ CORRECT: Guarding against memory exhaustion via explicit body limits
import express from 'express';

export function configureBodyParsers(app: express.Application): void {
  // Reject JSON payloads > 1MB with HTTP 413
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true, limit: '1mb' }));
}
```
