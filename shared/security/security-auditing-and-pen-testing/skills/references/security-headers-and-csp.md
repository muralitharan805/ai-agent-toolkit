# HTTP Security Headers & Content Security Policy (CSP) Guide

## Overview

HTTP security headers instruct client browsers to enforce strict runtime security boundaries, blocking Cross-Site Scripting (XSS), clickjacking, MIME-type sniffing, and man-in-the-middle downgrade attacks.

---

## 1. Mandatory HTTP Security Headers

| Header | Production Recommended Value | Purpose |
|---|---|---|
| **`Content-Security-Policy`** | `default-src 'self'; script-src 'self' ...` | Restricts resources (scripts, styles, images) that can be loaded and executed. |
| **`Strict-Transport-Security`** | `max-age=31536000; includeSubDomains; preload` | Enforces HTTPS connections and prevents SSL stripping attacks. |
| **`X-Frame-Options`** | `DENY` | Prevents the page from being rendered inside an `<iframe>` (clickjacking defense). |
| **`X-Content-Type-Options`** | `nosniff` | Prevents MIME-type sniffing; enforces declared Content-Type. |
| **`Referrer-Policy`** | `strict-origin-when-cross-origin` | Protects privacy by omitting full path/query strings on cross-origin requests. |
| **`Permissions-Policy`** | `geolocation=(), camera=(), microphone=()` | Restricts browser device hardware APIs. |

---

## 2. NestJS / Express Configuration via Helmet

In Node.js backend applications, register `helmet` during application bootstrap:

```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import helmet from 'helmet';
import { AppModule } from './app.module';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);

  // Configure Helmet with custom CSP directives
  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", 'data:', 'https:'],
          connectSrc: ["'self'", process.env.API_URL ?? ''],
          fontSrc: ["'self'", 'https://fonts.gstatic.com'],
          objectSrc: ["'none'"],
          frameAncestors: ["'none'"],
          upgradeInsecureRequests: [],
        },
      },
      crossOriginEmbedderPolicy: false,
      hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true,
      },
    }),
  );

  await app.listen(3000);
}
void bootstrap();
```

---

## 3. Cloudflare Pages `_headers` Configuration

For Single Page Applications (Angular, React) deployed to Cloudflare Pages, define security headers in `public/_headers` (or build output `_headers`):

```text
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self' https://pagead2.googlesyndication.com https://www.googletagmanager.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.yourdomain.com https://www.google-analytics.com; frame-src https://googleads.g.doubleclick.net; object-src 'none';
```

---

## 4. Nginx Production Configuration

```nginx
# /etc/nginx/conf.d/security_headers.conf
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

---

## 5. Verification Commands

```bash
# 1. Test live endpoint headers via curl
curl -I https://yourdomain.com/api/v1/health

# 2. Automated audit using security CLI tool
python3 shared/security/skills/security-auditing-and-pen-testing/scripts/audit_security_posture.py --target-dir .
```
