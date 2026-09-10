---
name: security-baseline
description: "Focuses strictly on runtime implementation controls (CSP/HSTS headers, CORS, rate limiting, and payload size bounds). Not for static vulnerability scanning. Triggered by 'security-baseline:', 'helmet:', 'cors:', 'rate-limit:', or '/security-baseline'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Runtime Security Baseline & Defense Skill

## Overview

This skill establishes the production engineering protocol for **Runtime Security Baselines**, **Transport Security Headers**, **CORS Whitelisting**, **Multi-Tiered Rate Limiting**, and **Ingress Payload Bounds** across backend services. It eliminates XSS, Clickjacking, MIME-sniffing, Cross-Origin request forgery, and memory exhaustion Denial of Service (DoS) attacks.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        5-Phase Runtime Security Pipeline                       │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Security Headers]       ──► Helmet: CSP, HSTS 1yr, X-Frame-Options: DENY
                │
  [Phase 2: CORS Whitelisting]      ──► Strict origin checking; zero wildcard creds
                │
  [Phase 3: Rate Limiting Matrix]   ──► Auth (5/min), Public (100/min), User (1000/min)
                │
  [Phase 4: Payload Size Bounds]    ──► 1MB JSON limit, 10MB upload limit, 8KB headers
                │
  [Phase 5: Conformance Audit]      ──► Run audit_security_baseline.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: HTTP Security Headers via Helmet
1. **Apply Security Headers Middleware**:
   - Serve the complete suite of security headers on all HTTP responses:
     - `Content-Security-Policy`: `default-src 'self'`.
     - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`.
     - `X-Frame-Options`: `DENY`.
     - `X-Content-Type-Options`: `nosniff`.
     - `Referrer-Policy`: `strict-origin-when-cross-origin`.
     - `Permissions-Policy`: `camera=(), microphone=(), geolocation=()`.

### Phase 2: Strict CORS Whitelist Configuration
1. **Validate Allowed Origins**:
   - Maintain an explicit whitelist of trusted frontend domains (e.g. `https://app.example.com`).
2. **Prohibit Wildcard with Credentials**:
   - NEVER configure `Access-Control-Allow-Origin: *` alongside `credentials: true`.
3. **Preflight Caching**:
   - Set `maxAge: 600` (10 minutes) on CORS preflight responses to eliminate redundant `OPTIONS` requests.

### Phase 3: Multi-Tiered Ingress Rate Limiting
1. **Apply Tiered Limits**:
   - **Auth Login**: 5 requests / 1 minute per IP.
   - **Auth Registration**: 10 requests / 1 hour per IP.
   - **Password Reset**: 3 requests / 1 hour per IP.
   - **Authenticated API**: 1,000 requests / 1 minute per User ID.
   - **Public API**: 100 requests / 1 minute per IP.
   - **File Upload**: 10 requests / 1 minute per User ID.
2. **Standard 429 Response**:
   - Return HTTP `429 Too Many Requests` with `Retry-After` header when throttled.

### Phase 4: Inbound Payload & Resource Size Bounds
1. **Enforce Size Ceilings**:
   - JSON Request Body: Hard limit of `1MB`.
   - File Uploads: Hard limit of `10MB` per file (isolated to dedicated upload endpoints).
   - URL Length: Hard limit of `2048` characters.
   - Header Size: Bounded to `8KB`.

### Phase 5: Conformance Audit
1. Run the security baseline auditor across the codebase:
   ```bash
   python3 shared/security-baseline/skills/scripts/audit_security_baseline.py ./src --strict
   ```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [HTTP Security Headers, CORS & Ingress Defense](references/http-security-headers-and-runtime-defense.md) for CSP directives, CORS preflight specifications, and DoS mitigation.
- **Production Template**: Review [security-baseline-middleware.template.ts](assets/security-baseline-middleware.template.ts) for production TypeScript Helmet, CORS, and rate limit definitions.
- **CLI Auditor**: Execute [audit_security_baseline.py](scripts/audit_security_baseline.py) to detect missing security headers and CORS wildcard flaws.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| `origin: "*"` with `credentials: true` | Explicit whitelist of allowed origin domains | Security vulnerability rejected by browsers; dynamic reflection enables credential theft. |
| Missing `Content-Security-Policy` header | Strict CSP (`default-src 'self'`) | Script injection vulnerabilities execute directly without browser containment. |
| Unbounded JSON body parser (`express.json()`) | Explicit limit (`express.json({ limit: '1mb' })`) | A single oversized 50MB payload causes CPU loop lockup and memory exhaustion DoS. |
| Uniform rate limits across all routes | Differentiated tiers (Auth: 5/min, User: 1000/min) | Allows credential stuffing and brute force attacks on authentication endpoints. |
| Missing `X-Frame-Options: DENY` | Strict `DENY` or `frame-ancestors 'none'` | Allows malicious sites to iframe the application and perform UI redress / Clickjacking. |
