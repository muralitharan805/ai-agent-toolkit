---
description: "Mandatory security audit rules enforcing OWASP Top 10 vulnerability remediation, automated pnpm audit dependency scanning, Security Headers (CSP, HSTS, CORS), and JWT/auth token protection."
trigger: always_on
---

# DevSecOps & Penetration Testing Rules

## Description
Enforces mandatory security controls, vulnerability scanning, security header protection, dependency auditing, and OWASP Top 10 remediation across all backend and frontend applications.

## Constraints

### 1. Mandatory Dependency Vulnerability Audits
- Applications MUST pass `pnpm audit --audit-level high` cleanly in CI/CD pipelines.
- Known critical or high-severity CVE vulnerabilities in `package.json` dependencies MUST be updated or overridden immediately.

### 2. OWASP Top 10 Protection Rules
- **Injection Prevention**: Database queries MUST use parameterized ORMs (Prisma, TypeORM, Knex) or prepared statements. Raw un-sanitized string concatenation in SQL queries is STRICTLY FORBIDDEN.
- **XSS Mitigation**: User-generated content rendered in HTML templates MUST be sanitized using DOMPurify or framework native escaping mechanisms (`{{ }}` in Angular).
- **Broken Authentication**: Auth endpoints MUST enforce rate limiting, strong bcrypt/argon2 password hashing (minimum 10 rounds), and secure HTTP-Only cookies for refresh tokens.

### 3. HTTP Security Headers Requirement
- Production web applications and backend APIs MUST serve mandatory security headers:
  - `Content-Security-Policy (CSP)`
  - `Strict-Transport-Security (HSTS)`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### 4. Secret & Token Handling
- JWT tokens MUST be signed with strong algorithms (HS256/RS256) and explicit expiration (`expiresIn: '15m'`).
- Hardcoding JWT secrets or API keys in source code is STRICTLY FORBIDDEN.
