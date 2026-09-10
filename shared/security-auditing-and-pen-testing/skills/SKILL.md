---
name: security-auditing-and-pen-testing
description: "Focuses strictly on static code analysis, vulnerability scanning, OWASP Top 10 auditing, and finding hardcoded secrets. Not for configuring runtime headers/CORS."
---

# Security Auditing & Penetration Testing

Systematically audits web applications, backend APIs, Docker infrastructure, and dependencies for security vulnerabilities, enforces OWASP compliance, and patches security flaws before production deployment.

---

## 5-Pillar Architecture Directory Layout

```text
shared/security/skills/security-auditing-and-pen-testing/
├── SKILL.md                                           # Core procedural security guidance (< 500 lines)
├── references/                                        # Authoritative deep-dive runbooks
│   ├── owasp-top-10-remediation.md                   # OWASP Top 10 mitigation code patterns
│   └── security-headers-and-csp.md                   # Helmet, CSP, HSTS, and CORS lockdown
├── scripts/                                           # Standalone automation tools
│   └── audit_security_posture.py                     # CLI security scanner and secrets hygiene tool
├── assets/                                            # Reusable reporting assets
│   ├── security-audit-report-template.md             # Standardized findings markdown report
│   └── security-hardening-checklist.json             # 15-point automated security checklist
└── evals/                                             # Verifiable test cases and grading
    ├── evals.json
    └── grading.json
```

---

## 5-Phase Procedural Execution Protocol

Follow this 5-phase sequence to conduct a security posture audit and penetration test:

### Phase 1: Automated Supply Chain & Dependency Audit
1. Run dependency vulnerability audit:
   ```bash
   pnpm audit --audit-level high
   ```
2. If vulnerabilities are reported:
   - Update the vulnerable package: `pnpm update <package-name>`.
   - If transitive dependency cannot be updated directly, enforce version override in root `package.json` under `"pnpm.overrides"`.
3. Verify that only `pnpm-lock.yaml` exists; remove any residual `package-lock.json` or `yarn.lock`.

### Phase 2: Static Code Security & Injection Audit
1. Run the bundled automated security scanner:
   ```bash
   python3 scripts/audit_security_posture.py --target-dir . --strict
   ```
2. Check database queries for SQL injection vulnerabilities:
   - Ensure all queries use parameterized ORMs (Prisma, TypeORM, Knex) or prepared statements.
   - Raw string concatenation or template literal queries (`$queryRawUnsafe` with `${...}`) are STRICTLY FORBIDDEN (see `references/owasp-top-10-remediation.md`).
3. Verify template rendering does not bypass HTML escaping via raw un-sanitized bindings (`innerHTML`).

### Phase 3: Secrets Hygiene & `.env.example` Parity
1. Verify `.gitignore` explicitly includes `.env` and `.env.*`.
2. Confirm `.env.example` strictly mirrors all required variables in `.env`.
3. Check that `.env.example` contains ZERO sensitive credentials (use placeholder strings like `your_api_key_here`).
4. Ensure every variable in `.env.example` has a descriptive comment explaining what it does, expected format, and where to obtain it.

### Phase 4: HTTP Security Headers & Authentication Hardening
1. Verify `main.ts` or server entrypoint registers `helmet` to set HSTS, CSP, X-Frame-Options, and X-Content-Type-Options (see `references/security-headers-and-csp.md`).
2. Verify CORS origin is restricted to an explicit domain whitelist; reject wildcard origins (`'*'`) when credentials are enabled.
3. Confirm sensitive refresh tokens are stored exclusively in HTTP-Only, Secure, SameSite cookies, NEVER in browser `localStorage`.
4. Ensure authentication endpoints enforce rate limiting (`@nestjs/throttler`).

### Phase 5: Verification & Audit Report Generation
1. Execute compile check and test suites:
   ```bash
   pnpm build
   pnpm test
   ```
2. Generate a comprehensive findings report using `assets/security-audit-report-template.md`.

---

## Gotchas & Security Pitfalls

| Insecure Shortcut / Anti-Pattern | Modern Enterprise Hardening | Why It Matters |
|---|---|---|
| Committing API keys or DB passwords into `.env.example` | Placeholder strings (`your_key_here`) with junior-friendly setup comments | Committing live tokens to public or team repositories leads to immediate automated credential scrapers. |
| Storing JWT refresh tokens in browser `localStorage` | HTTP-Only, Secure, SameSite cookies | `localStorage` is accessible to JavaScript, allowing any Cross-Site Scripting (XSS) exploit to exfiltrate sessions. |
| Raw SQL string interpolation (`$queryRawUnsafe(\`...\${id}\`)`) | Parameterized queries or Prisma/TypeORM query builders | Direct concatenation enables trivial SQL injection, exposing or dropping database tables. |
| Wildcard CORS (`Access-Control-Allow-Origin: *`) with credentials | Explicit domain whitelist (`https://app.yourdomain.com`) | Broad wildcard CORS allows malicious external websites to make authenticated cross-origin requests. |
| Omitting `helmet()` in backend server bootstrap | Registering `app.use(helmet())` with custom CSP | Leaves APIs vulnerable to MIME-sniffing, clickjacking (`<iframe>`), and unencrypted HTTP downgrade attacks. |
| Leaving `package-lock.json` in a `pnpm` repository | Deleting legacy lockfiles and enforcing `pnpm-lock.yaml` | Multiple package managers cause ghost dependencies and non-deterministic production deployment builds. |
