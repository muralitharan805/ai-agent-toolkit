# JWT Token Lifecycle, Cryptography & Access Control Architecture

## Overview

Authentication and authorization form the foundational security boundary of any enterprise system. Flawed token storage, weak password hashing, symmetric secret leakage, or missing resource ownership checks expose systems to account takeovers, Insecure Direct Object References (IDOR), and cluster-wide privilege escalations.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Dual-Token Lifecycle Architecture                     │
└──────────────────────────────────────────────────────────────────────────────┘
  Client (Browser / Mobile)
       │ (1) POST /auth/login (email + password)
       ▼
  [Authentication Service]
       ├── Verify Password Hash (Argon2id / bcrypt cost ≥ 12)
       ├── Sign Access Token (15m, RS256 Private Key)
       ├── Generate Refresh Token (7d, cryptographically random 256-bit)
       │
       ▼ (2) Response:
       ├── JSON Body: { accessToken: "eyJ..." }
       └── Set-Cookie: refreshToken=abc...; HttpOnly; Secure; SameSite=Strict; Path=/auth/refresh
```

---

## 1. Storage Comparison: HTTP-Only Cookies vs. LocalStorage

| Threat Vector | `localStorage` / `sessionStorage` | `HttpOnly; Secure; SameSite=Strict` Cookie |
| :--- | :--- | :--- |
| **XSS Token Exfiltration** | **100% Vulnerable**: Any injected JavaScript can read `localStorage.getItem('token')` and send it to an attacker server. | **Immune**: JavaScript runtime has zero access to HTTP-Only cookies. |
| **CSRF Attack** | Immune (unless manually added to headers by script). | **Protected**: `SameSite=Strict` blocks browser from sending cookies on cross-origin requests. |
| **Subdomain Leakage** | Scoped strictly to origin. | Scoped to domain; easily restricted via `Path` attribute. |
| **Architectural Invariant** | **STRICTLY FORBIDDEN** for session/refresh tokens. | **MANDATORY** for refresh tokens. |

---

## 2. Token Rotation & The Automatic Theft Detection Flow

Token rotation replaces the refresh token every time it is used. This enables automatic detection of token theft:

```
[Attacker steals Refresh Token R1 from User]
                      │
[Legitimate User uses R1 to get new token]
                      │
                      ▼
[Server issues Token Pair R2; marks R1 as REVOKED]
                      │
                      ▼
[Later: Attacker attempts to use stolen R1]
                      │
                      ▼
[Server inspects R1 → Status: ALREADY REVOKED!]
                      │
                      ▼
[AUTOMATED THEFT RESPONSE TRIGGERED]
  1. Invalidate R1, R2, and ALL active sessions for User.
  2. Emit high-priority Security Alert to SIEM / Security Operations.
  3. Force legitimate user to re-authenticate with credentials + MFA.
```

---

## 3. Asymmetric Cryptography (RS256 / EdDSA) vs. Symmetric (HS256)

### The Single Secret Hazard of HS256
In a microservice topology using `HS256`, every microservice (Billing, Orders, Users, Inventory) must hold the exact same HMAC secret key to verify signatures:
- If a junior developer logs the key, or a single read-only service is breached, the attacker possesses the ability to forge valid administrator JWTs for every service in the company.

### The Asymmetric Solution (RS256 & JWKS)
- **Identity Service**: Holds the **Private Key** (kept in KMS / Vault). Signs all tokens.
- **Resource Microservices**: Hold ONLY the **Public Key** (downloaded via `GET /.well-known/jwks.json`).
- Even if a resource service is completely compromised, the attacker cannot forge new JWT tokens because they only possess the public verification key.

---

## 4. Authorization Models & IDOR Prevention

### 1. Role-Based Access Control (RBAC)
Maps users to functional roles:
- `ADMIN`: Full system administrative rights.
- `MANAGER`: Organizational read and update rights.
- `USER`: Standard operations on owned resources.
- `VIEWER`: Read-only access.

### 2. Attribute-Based Access Control (ABAC)
Enforces contextual policies:
```typescript
if (user.tenantId !== resource.tenantId) {
  throw new ForbiddenException('Cross-tenant data access is prohibited');
}
```

### 3. Resource Ownership Invariant (Mitigating IDOR)
Checking that a user has the `USER` role is NOT sufficient to access an order. You must verify ownership:
```typescript
if (order.ownerId !== currentUser.id && !currentUser.roles.includes('ADMIN')) {
  throw new ForbiddenException('Access denied: You do not own this resource');
}
```
Failing to verify `ownerId === currentUser.id` allows User A to view or delete User B's invoices simply by changing the ID in the URL.
