---
trigger: model_decision
description: "Enforces enterprise authentication and authorization standards: Argon2id/bcrypt hashing, short-lived JWTs (15m), HTTP-Only SameSite=Strict refresh cookies, token rotation, reuse detection, RS256/JWKS, and RBAC/ABAC/Resource Ownership."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Authentication & Authorization Architecture Standards

## Description
Enforces enterprise authentication, token lifecycle management, and fine-grained authorization standards across all backend APIs and microservices. Mandates strong password hashing (Argon2id or bcrypt cost $\ge 12$), establishes the dual-token model with short-lived access tokens (15m) and HTTP-Only SameSite=Strict refresh cookies (7d), enforces automatic token rotation and reuse detection to mitigate token theft, prohibits symmetric HS256 shared secrets across microservice boundaries in favor of asymmetric RS256/EdDSA with JWKS verification, and requires defense-in-depth authorization combining Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC), and strict Resource Ownership verification.

## Constraints

### 1. Password Hashing Invariants
- Passwords MUST be hashed using **Argon2id** (memory: 64MB, iterations: 3, parallelism: 4) or **bcrypt** with a work factor cost of $\ge 12$.
- Storing plaintext passwords, unsalted hashes, or deprecated algorithms (MD5, SHA-1, SHA-256) is a CRITICAL VULNERABILITY and is STRICTLY FORBIDDEN.
- Password hashes MUST NEVER be returned in user profile responses or printed in application log streams.

### 2. Dual-Token Architecture & Storage Isolation
- Authentication MUST implement the two-token lifecycle:
  - **Access Token**: Short-lived (maximum `15 minutes`). Returned in the JSON response payload.
  - **Refresh Token**: Long-lived (maximum `7 days`). Stored strictly in an `HTTP-Only`, `Secure`, `SameSite=Strict` cookie partitioned to `/api/v1/auth/refresh`.
- **Zero LocalStorage Invariant**: Storing refresh tokens or authentication session tokens in browser `localStorage` or `sessionStorage` is STRICTLY FORBIDDEN due to catastrophic token exfiltration risks via Cross-Site Scripting (XSS).

### 3. Refresh Token Rotation & Theft Reuse Detection
- Every `/refresh` operation MUST execute automatic token rotation:
  1. Invalidate the submitted refresh token in the database.
  2. Issue a brand new access token and fresh refresh token pair.
- **Reuse Detection Protocol**:
  - If a refresh token that has ALREADY been rotated/invalidated is presented to the refresh endpoint:
  - The server MUST classify the event as **Token Theft / Compromise**.
  - The server MUST immediately invalidate ALL active refresh tokens, sessions, and credentials associated with that user account.
  - The server MUST log a high-severity security alert and force the user to re-authenticate.

### 4. Asymmetric Cryptographic Signatures (RS256 / EdDSA & JWKS)
- In multi-service and microservice architectures, symmetric signing (`HS256`) is STRICTLY FORBIDDEN. Sharing a single HMAC secret key across independent services creates severe leak risks.
- Authentication services MUST sign JWTs using private asymmetric keys (`RS256` or `EdDSA`).
- Downstream resource microservices MUST verify token signatures using public keys fetched from a standardized JSON Web Key Set endpoint (`GET /.well-known/jwks.json`).

### 5. Defense-in-Depth Authorization & Resource Ownership
- All non-public endpoints MUST enforce authorization at both the route middleware level and the service layer:
  - **RBAC**: Enforce role hierarchies (`ADMIN`, `MANAGER`, `USER`, `VIEWER`).
  - **ABAC**: Enforce contextual attributes (e.g., department, tenant ID, geographical restrictions).
  - **Resource Ownership Check**: When modifying or viewing individual user resources (`/invoices/:id`, `/orders/:id`), the handler MUST verify that `resource.ownerId === currentUser.id` or that the user possesses administrative override permissions. Failing to check ownership produces Insecure Direct Object Reference (IDOR) vulnerabilities.

### 6. Authentication Endpoint Rate Limiting
- Public authentication routes MUST enforce strict rate limiting to prevent credential stuffing and brute-force attacks:
  - Login (`POST /auth/login`): Maximum `5 requests/minute` per IP address.
  - Registration (`POST /auth/register`): Maximum `10 requests/hour` per IP address.
  - Password Reset (`POST /auth/forgot-password`): Maximum `3 requests/hour` per email account.

## Examples

### 1. Secure Cookie Configuration vs. Insecure LocalStorage

```typescript
// ❌ FORBIDDEN: Returning refresh token in response body for client localStorage
res.json({ accessToken, refreshToken }); // Allows XSS scripts to steal permanent user session!

// ✅ CORRECT: Partitioned HTTP-Only cookie with strict security flags
res.cookie('refreshToken', refreshToken, {
  httpOnly: true,                                // Inaccessible to JavaScript document.cookie
  secure: process.env.NODE_ENV === 'production',  // HTTPS only
  sameSite: 'strict',                            // Blocks CSRF request forgery
  path: '/api/v1/auth/refresh',                  // Sent only to the refresh endpoint
  maxAge: 7 * 24 * 60 * 60 * 1000,               // 7 days
});
res.status(200).json({ accessToken });           // Access token in memory/response body
```

### 2. Token Rotation & Reuse Detection Logic

```typescript
// ✅ CORRECT: Detecting refresh token reuse and revoking all user sessions
export async function rotateRefreshToken(tokenString: string): Promise<TokenPair> {
  const tokenRecord = await db.refreshTokens.findUnique({ where: { tokenHash: hash(tokenString) } });

  if (!tokenRecord) {
    throw new UnauthorizedException('Invalid refresh token');
  }

  // Detect reuse of already-revoked token
  if (tokenRecord.isRevoked) {
    logger.error({
      event: 'security.token_reuse_detected',
      userId: tokenRecord.userId,
      message: 'Revoked refresh token was presented! Possible token theft. Invalidating all sessions.',
    });
    // Immediately invalidate ALL active sessions for this user
    await db.refreshTokens.updateMany({
      where: { userId: tokenRecord.userId },
      data: { isRevoked: true },
    });
    throw new UnauthorizedException('Token reuse detected. All sessions terminated.');
  }

  // Normal rotation: revoke old token and issue fresh token
  await db.refreshTokens.update({ where: { id: tokenRecord.id }, data: { isRevoked: true } });
  return issueNewTokenPair(tokenRecord.userId);
}
```

### 3. Resource Ownership Guard

```typescript
// ✅ CORRECT: Preventing IDOR vulnerabilities via explicit ownership checks
export async function updateInvoice(invoiceId: string, currentUser: AuthUser, dto: UpdateInvoiceDto): Promise<Invoice> {
  const invoice = await db.invoices.findUnique({ where: { id: invoiceId } });
  if (!invoice) {
    throw new NotFoundException('Invoice not found');
  }

  // Assert ownership
  if (invoice.ownerId !== currentUser.id && !currentUser.roles.includes('ADMIN')) {
    throw new ForbiddenException('You do not have permission to modify this resource');
  }

  return db.invoices.update({ where: { id: invoiceId }, data: dto });
}
```
