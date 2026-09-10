---
name: authentication-and-authorization
description: "Implements and audits enterprise authentication and authorization: Argon2id hashing, short-lived JWT access tokens, HTTP-Only refresh cookies with rotation and reuse detection, RS256/JWKS, and RBAC/ABAC ownership checks. Triggered by 'auth:', 'jwt:', 'rbac:', 'authorization:', or '/authentication-and-authorization'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Authentication & Authorization Architecture Skill

## Overview

This skill establishes the production engineering protocol for **Enterprise Authentication (JWT Dual-Token Model)**, **Token Rotation & Reuse Detection**, **Asymmetric Signing (RS256/JWKS)**, and **Multi-Layer Authorization (RBAC, ABAC, Resource Ownership)** across backend architectures. It eliminates token theft risks via HTTP-Only cookie partitioning, stops credential stuffing with rate limits, and mitigates Insecure Direct Object Reference (IDOR) vulnerabilities.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         5-Phase Authentication Pipeline                        │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Password & Rate Limits]  ──► Argon2id / bcrypt >= 12 + IP rate limits
                │
  [Phase 2: Dual-Token Issuance]     ──► 15m Access Token + HTTP-Only 7d Cookie
                │
  [Phase 3: Rotation & Reuse Guard]  ──► Invalidate on use; revoke all on reuse
                │
  [Phase 4: Authorization & IDOR]    ──► RBAC/ABAC + resource.ownerId === user.id
                │
  [Phase 5: Conformance Audit]       ──► Run audit_auth_standards.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Strong Password Hashing & Endpoint Rate Limiting
1. **Hash All Passwords Securely**:
   - Use Argon2id or bcrypt with salt rounds $\ge 12$. Never use MD5, SHA-1, or unsalted SHA-256.
2. **Enforce Rate Limits**:
   - Limit login attempts: `5 requests/minute` per IP address.
   - Limit registration: `10 requests/hour` per IP address.

### Phase 2: Dual-Token Issuance & Cookie Partitioning
1. **Access Token Lifespan**:
   - Issue short-lived access tokens (maximum `15 minutes`). Return in response body for in-memory storage.
2. **Refresh Token Cookie Security**:
   - Store refresh tokens (7 days max) in an `HTTP-Only`, `Secure`, `SameSite=Strict` cookie partitioned to `/api/v1/auth/refresh`.
   - Never store tokens in browser `localStorage` or `sessionStorage` (critical XSS vulnerability).

### Phase 3: Token Refresh with Rotation & Theft Detection
1. **Rotate on Every Use**:
   - On every `/refresh` call, invalidate the submitted refresh token in the database and issue a new token pair.
2. **Theft Reuse Detection**:
   - If a refresh token that has ALREADY been revoked is presented to `/refresh`, immediately invalidate ALL active sessions and refresh tokens for that user ID to contain the breach.

### Phase 4: Route-Level RBAC/ABAC & IDOR Ownership Guards
1. **Verify Roles & Attributes**:
   - Check user roles (`ADMIN`, `MANAGER`, `USER`) using route guards.
2. **Enforce Resource Ownership**:
   - For entity mutations (`/orders/:id`, `/invoices/:id`), always verify:
     ```typescript
     if (resource.ownerId !== req.user.id && !req.user.roles.includes('ADMIN')) {
       throw new ForbiddenException('You do not own this resource');
     }
     ```

### Phase 5: Conformance Audit
1. Run the authentication and authorization audit tool:
   ```bash
   python3 shared/authentication-and-authorization/skills/scripts/audit_auth_standards.py ./src --strict
   ```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [JWT Token Lifecycle, Cryptography & Access Control](references/jwt-architecture-and-access-control.md) for RS256 vs HS256 security, token reuse attack scenarios, and IDOR remediation.
- **Production Template**: Review [auth-security-orchestrator.template.ts](assets/auth-security-orchestrator.template.ts) for production TypeScript password hashing, dual-token cookies, rotation logic, and RBAC/ownership guards.
- **CLI Auditor**: Execute [audit_auth_standards.py](scripts/audit_auth_standards.py) to detect localStorage token leakage and long-lived tokens.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Storing tokens in browser `localStorage` | `HTTP-Only`, `Secure`, `SameSite=Strict` cookie | Any Cross-Site Scripting (XSS) vulnerability allows full session hijacking. |
| Using symmetric `HS256` in microservices | Asymmetric `RS256` / `EdDSA` with public `/.well-known/jwks.json` | Shared secret must be distributed to all services; compromise of one service compromises all. |
| Long-lived access tokens (hours or days) | Short-lived access tokens (15 minutes max) | Stolen access tokens cannot be revoked before natural expiration. |
| Missing refresh token rotation | Rotate refresh token on every use; revoke all sessions on reuse | Stolen refresh tokens can be used indefinitely without detection. |
| Relying solely on `USER` role without checking ownership | Explicit ownership assertion (`resource.ownerId === currentUser.id`)| Insecure Direct Object Reference (IDOR): User A can access or delete User B's resources. |
