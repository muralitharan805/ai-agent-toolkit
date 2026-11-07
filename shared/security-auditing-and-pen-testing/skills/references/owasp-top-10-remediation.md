# OWASP Top 10 Vulnerability Remediation Guide

## Overview

This guide provides technical remediation patterns and architectural defenses for the OWASP Top 10 web application vulnerabilities across TypeScript, NestJS, and modern frontend ecosystems.

---

## 1. A01: Broken Access Control

### Vulnerability Mechanics:
Attackers manipulate URL parameters, request bodies, or JWT payloads to access or modify resources belonging to other tenants or roles (IDOR - Insecure Direct Object References).

### Production Remediation:
1. **Never rely on client-supplied identifiers without ownership verification**:
```typescript
// src/modules/orders/orders.service.ts
async findOrderForUser(orderId: string, userId: string): Promise<Order> {
  const order = await this.prisma.order.findFirst({
    where: { id: orderId, userId }, // Mandatory tenant/user ownership bound
  });
  if (!order) {
    throw new NotFoundException(`Order ${orderId} not found`);
  }
  return order;
}
```
2. **Apply functional guards across all sensitive routes**:
```typescript
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(UserRole.ADMIN)
@Delete(':id')
async deleteRecord(@Param('id', ParseUUIDPipe) id: string): Promise<void> { ... }
```

---

## 2. A02: Cryptographic Failures

### Vulnerability Mechanics:
Hardcoded API keys, unencrypted passwords, weak hashing algorithms (MD5/SHA1), or insecure plain HTTP transmissions.

### Production Remediation:
1. **Password Hashing**: Minimum 12 rounds of bcrypt or Argon2id:
```typescript
import * as bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;
export async function hashPassword(plain: string): Promise<string> {
  return bcrypt.hash(plain, SALT_ROUNDS);
}
```
2. **Strict Environment Loading**: Never commit secret keys:
```typescript
// Load through validated ConfigService
const jwtSecret = this.configService.getOrThrow<string>('JWT_SECRET');
```

---

## 3. A03: Injection (SQL, NoSQL, OS Command)

### Vulnerability Mechanics:
Hostile data is sent to an interpreter as part of a command or query without parameterized separation.

### Production Remediation:
1. **Prepared Statements & Parameterized ORMs**:
```typescript
// ✅ SAFE: Prisma/TypeORM automatically parameterize inputs
const results = await prisma.user.findMany({
  where: { email: { contains: searchInput, mode: 'insensitive' } },
});

// ❌ FORBIDDEN: Raw string interpolation in queries
await prisma.$queryRawUnsafe(`SELECT * FROM users WHERE email = '${searchInput}'`);
```
2. **Never invoke OS child processes with unsanitized user inputs**:
Avoid `child_process.exec()` with user string templates. If required, use `execFile` or `spawn` with an explicit argument array.

---

## 4. A04: Insecure Design & Missing Rate Limiting

### Vulnerability Mechanics:
Lack of rate limiting allows credential stuffing, brute force login attacks, and resource exhaustion (DoS).

### Production Remediation:
Enforce `@nestjs/throttler` across authentication endpoints:
```typescript
// app.module.ts
ThrottlerModule.forRoot([{
  ttl: 60000,
  limit: 10, // Max 10 requests per minute
}]),

// auth.controller.ts
@Throttle({ default: { limit: 5, ttl: 60000 } })
@Post('login')
async login(@Body() dto: LoginDto): Promise<AuthTokens> { ... }
```

---

## 5. A05: Security Misconfiguration

### Vulnerability Mechanics:
Default credentials left unchanged, overly permissive CORS (`Access-Control-Allow-Origin: *` with credentials), verbose stack traces leaked in production HTTP responses.

### Production Remediation:
1. **Helmet Middleware**: Configures essential security headers:
```typescript
import helmet from 'helmet';
app.use(helmet());
```
2. **Explicit CORS Whitelist**:
```typescript
app.enableCors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') ?? ['https://example.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
});
```

---

## 6. A06: Vulnerable and Outdated Components

### Vulnerability Mechanics:
Using outdated npm dependencies containing known Common Vulnerabilities and Exposures (CVEs).

### Production Remediation:
```bash
# Automated audit in CI/CD pipeline
pnpm audit --audit-level high

# Fix or update vulnerable transitive packages via package.json overrides:
"pnpm": {
  "overrides": {
    "vulnerable-pkg": ">=2.1.4"
  }
}
```

---

## 7. A07: Identification and Authentication Failures

### Vulnerability Mechanics:
Session fixation, weak passwords, refresh tokens stored in browser `localStorage` vulnerable to XSS exfiltration.

### Production Remediation:
1. **Store Refresh Tokens in HTTP-Only, SameSite Cookies**:
```typescript
res.cookie('refreshToken', refreshToken, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  path: '/api/v1/auth/refresh',
  maxAge: 7 * 24 * 60 * 60 * 1000,
});
```
2. **Short-Lived Access Tokens**:
Sign JWT access tokens with a strict 15-minute expiration (`expiresIn: '15m'`).

---

## 8. A08: Software and Data Integrity Failures

### Vulnerability Mechanics:
Relying on untrusted CDNs without Subresource Integrity (SRI) hashes or deserializing unvalidated external objects.

### Production Remediation:
Pin exact package versions in `package.json` and enforce frozen lockfiles in CI:
```bash
pnpm install --frozen-lockfile
```

---

## 9. A09: Security Logging and Monitoring Failures

### Vulnerability Mechanics:
Authentication failures, high-privilege operations, or exceptions are unlogged or silently suppressed without alert hooks.

### Production Remediation:
Log structured audit events with correlation IDs (`x-correlation-id`) and mask sensitive PII (passwords, tokens, card numbers) using a centralized `sanitizePayload()` utility.

---

## 10. A10: Server-Side Request Forgery (SSRF)

### Vulnerability Mechanics:
Web applications fetch remote resources without validating user-supplied destination URLs, allowing attackers to probe internal cloud metadata (`169.254.169.254`) or loopback services (`localhost:6379`).

### Production Remediation:
Validate external URLs against an explicit domain whitelist and reject private IP subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.169.254`).
