---
description: "Mandatory security audit rules enforcing OWASP Top 10 vulnerability remediation, automated pnpm audit dependency scanning, Security Headers (CSP, HSTS, CORS), zero-hardcoded secrets, and JWT/auth token protection."
trigger: always_on
---

# DevSecOps & Penetration Testing Rules

## Description
Enforces mandatory security controls, vulnerability scanning, security header protection, dependency auditing, zero-hardcoded secrets, and OWASP Top 10 remediation across all backend and frontend applications.

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

### 4. Secret & Token Handling & Zero-Hardcoding
- The agent MUST NOT write hardcoded secret strings (API keys, JWT secrets, passwords, SSH keys) in source files, tests, or config files.
- JWT tokens MUST be signed with strong algorithms (HS256/RS256) and explicit expiration (`expiresIn: '15m'`).
- All sensitive credentials, secret tokens, private keys, and database passwords MUST be loaded exclusively through environment variables (`process.env.API_KEY`, `process.env.DATABASE_URL`) or secret management services.
- The agent MUST ensure `.env` files are included in `.gitignore`.
- **`.env.example` Strict Parity**: Every variable required in `.env` MUST be present in `.env.example`.
- **No Sensitive Data in `.env.example`**: The `.env.example` file MUST NEVER contain real sensitive data (use placeholder values like `your_api_key_here`).
- **Junior-Friendly Documentation**: The agent MUST add a clear, descriptive comment above every variable in `.env.example`. The comment must explain what the variable does, its expected format, and where to obtain it, so that any junior developer or newcomer can easily set up the project without confusion.

## Examples

### 1. Parameterized Query vs Forbidden Raw Concatenation
```typescript
// ✅ CORRECT: Parameterized ORM prepared query prevents SQL Injection
async function findUserByEmail(email: string): Promise<User | null> {
  return prisma.user.findUnique({
    where: { email },
  });
}

// ❌ FORBIDDEN: String concatenation vulnerable to SQL Injection
async function findUserByEmail(email: string): Promise<User | null> {
  return prisma.$queryRawUnsafe(`SELECT * FROM users WHERE email = '${email}'`);
}
```

### 2. Secure HTTP-Only Cookie Authentication vs Insecure Storage
```typescript
// ✅ CORRECT: Secure HTTP-Only, SameSite cookie prevents XSS token theft
response.cookie('refreshToken', token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
});

// ❌ FORBIDDEN: Storing sensitive refresh tokens in browser localStorage
localStorage.setItem('refreshToken', token); // Vulnerable to XSS exfiltration!
```

### 3. Junior-Friendly `.env.example` Documentation & Strict Parity
```bash
# ==============================================================================
# Database Connection URI
# Format: postgresql://[user]:[password]@[host]:[port]/[database]?schema=public
# Source: Obtain from your local Docker Compose service or AWS RDS instance
# ==============================================================================
DATABASE_URL="postgresql://postgres:your_local_password@localhost:5432/myapp_dev?schema=public"

# ==============================================================================
# JWT Secret Signing Key
# Format: Minimum 32-character high-entropy cryptographic string
# Generation: Run `openssl rand -base64 32` to generate a secure key
# ==============================================================================
JWT_SECRET="replace_with_32_char_cryptographic_secret_key"
```
