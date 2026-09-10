---
trigger: model_decision
description: "Enforces URL path versioning (/api/v1/), breaking vs non-breaking change classification, RFC 8594 Deprecation and Sunset HTTP headers on all deprecated responses, minimum 6-month sunset periods, HTTP 410 Gone responses after sunset (not 404), and consumer usage tracking before version removal."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# API Versioning & Deprecation Strategy Standards

## Description
Enforces production engineering standards for API lifecycle management. Mandates URL path versioning (`/api/v1/`, `/api/v2/`) decided before the first public endpoint ships, clear breaking vs non-breaking change classification (removing fields is breaking; adding optional fields is non-breaking), RFC 8594-compliant `Deprecation: true` and `Sunset: {date}` HTTP headers on ALL responses from deprecated API versions (enabling automated client detection), a minimum 6-month sunset period from public announcement to service removal, HTTP 410 Gone responses (not 404) after the sunset date to clearly signal intentional deprecation, consumer usage analytics tracking before any version removal, and CHANGELOG.md maintenance with explicit breaking change notation.

## Constraints

### 1. URL Path Versioning — Mandatory from Day 1
- All API routes MUST include a version prefix in the URL path: `/api/v1/`, `/api/v2/`.
- API versioning MUST be decided and implemented before the first public endpoint is released — retrofitting versioning into an unversioned API is STRICTLY PROHIBITED due to the consumer breakage it causes.
- The version prefix MUST cover the entire API surface, not individual endpoints — per-endpoint versioning (e.g., `/api/users/v2/:id`) is STRICTLY FORBIDDEN.
- Non-breaking changes (new optional fields, new endpoints, loosened validation) MUST NOT result in a version increment.
- Breaking changes (removed fields, type changes, required new fields, auth mechanism changes) MUST increment the major version.

### 2. RFC 8594 Deprecation Headers on All Deprecated Responses
- After introducing a successor API version, every response from the deprecated version MUST include:
  - `Deprecation: true`
  - `Sunset: {RFC 7231 HTTP-date format}` — the exact date the API will be deactivated.
  - `Link: </api/v{N+1}/{path}>; rel="successor-version"`.
- These headers MUST be applied at the API version router/middleware layer — not manually per endpoint.

### 3. Minimum 6-Month Sunset Period
- The minimum period between the public deprecation announcement and the service shutdown date MUST be 6 months.
- Consumer usage analytics (API key usage, user-agent tracking) MUST be monitored throughout the sunset period.
- Consumers with active usage of the deprecated version MUST be proactively contacted before the sunset date.

### 4. HTTP 410 Gone After Sunset (Not 404)
- After the sunset date, all requests to deprecated version endpoints MUST return `HTTP 410 Gone`.
- Returning `HTTP 404 Not Found` after deprecation is STRICTLY FORBIDDEN — it signals a bug, not intentional retirement.
- The 410 response body MUST include: `error code`, `human-readable message`, and `migrationGuide URL`.

### 5. CHANGELOG.md Maintenance
- Every API release MUST update `CHANGELOG.md` with a version entry.
- Breaking changes MUST be explicitly labeled with a ⚠️ BREAKING marker.
- A migration guide link MUST be included in every breaking change entry.

## Examples

### 1. RFC 8594 Deprecation Middleware (Correct)
```typescript
// ✅ CORRECT: Applied at router level — covers all v1 endpoints automatically
app.use('/api/v1', (req: Request, res: Response, next: NextFunction) => {
  res.setHeader('Deprecation', 'true');
  res.setHeader('Sunset', 'Sat, 01 Jan 2027 00:00:00 GMT');
  res.setHeader('Link', '</api/v2>; rel="successor-version"');
  next();
});
```

### 2. HTTP 410 Response After Sunset (Correct)
```typescript
// ✅ CORRECT: 410 Gone with migration guide — not 404
app.use('/api/v1', (_req: Request, res: Response) => {
  res.status(410).json({
    error: 'API_DEPRECATED',
    message: 'v1 API was sunset on 2027-01-01. Please migrate to /api/v2/.',
    migrationGuide: 'https://docs.company.com/api/v1-to-v2',
    sunsetDate: '2027-01-01',
  });
});
```

### 3. Forbidden — Breaking Change Without Version Bump
```typescript
// ❌ FORBIDDEN: Removing field in place without version bump
// Before (v1): { id, fullName, email }
// After (same v1): { id, firstName, lastName, email }
// → fullName removed → breaks all consumers silently
```
