# API Versioning Strategies & Deprecation Lifecycle Guide

## 1. Versioning Strategy Comparison

| Strategy | URL Example | Pros | Cons | Verdict |
|---|---|---|---|---|
| **URL Path** (Recommended) | `/api/v1/users` | Explicit, cacheable, debuggable in browser | URL changes on version bump | ✅ Use this |
| **Header-based** | `Accept: application/vnd.api.v1+json` | Clean URLs | Hard to test in browser, not cache-friendly | ❌ Avoid |
| **Query param** | `/api/users?version=1` | Easy to add | Not a true REST resource | ❌ Avoid |
| **Subdomain** | `v1.api.company.com` | Full isolation | DNS overhead, CORS complexity | ⚠️ Only for full separate deployments |

**Decision: URL path versioning is the only acceptable pattern** for REST APIs in this toolkit.

---

## 2. Version Bump Decision Tree

```
Is the API change breaking? (If YES to any → BREAKING)
  ├── Removing or renaming a response field?      → BREAKING
  ├── Changing a field's data type?               → BREAKING
  ├── Changing the URL structure or HTTP method?  → BREAKING
  ├── Adding a new REQUIRED request field?        → BREAKING
  ├── Changing auth mechanism?                    → BREAKING
  ├── Tightening validation rules?                → BREAKING
  └── Changing error response structure?          → BREAKING

  Non-breaking (safe to add to same version):
  ├── Adding new optional response fields?        → NON-BREAKING ✅
  ├── Adding new optional request fields?         → NON-BREAKING ✅
  ├── Adding entirely new endpoints?              → NON-BREAKING ✅
  ├── Loosening validation (wider input accepted)?→ NON-BREAKING ✅
  └── Adding new enum values?                     → NON-BREAKING ✅ *
  * Only if consumers handle unknown enum values gracefully
```

---

## 3. Consumer-Driven Contract Testing

Track which consumers use which fields to safely determine what's truly breaking:

```typescript
// Middleware to track field usage per API key
function trackFieldUsage(req: Request, res: Response, next: NextFunction): void {
  const originalJson = res.json.bind(res);
  res.json = (body: Record<string, unknown>) => {
    analytics.track({
      apiKey: req.headers['x-api-key'],
      version: 'v1',
      endpoint: req.path,
      fieldsPresent: Object.keys(body),
    });
    return originalJson(body);
  };
  next();
}
```

Before removing a field, check if ANY consumer's API key has accessed it in the last 90 days.

---

## 4. CHANGELOG.md Format Standard

```markdown
# CHANGELOG

## [2.0.0] — 2026-12-01

### ⚠️ BREAKING CHANGES
- `GET /api/v2/users/:id`: Renamed field `fullName` → `displayName`
  - Migration: Update client code to use `displayName` instead of `fullName`
  - Migration guide: https://docs.company.com/api/v1-to-v2

### Added
- `GET /api/v2/users/:id/activity`: New endpoint for user activity log
- `POST /api/v2/users`: Added optional `preferredLanguage` field

### Deprecated
- `GET /api/v1/*`: All v1 endpoints deprecated as of 2026-12-01
  - Sunset date: 2027-06-01 (6 months)
  - Migration guide: https://docs.company.com/api/v1-to-v2

## [1.5.0] — 2026-09-01

### Added
- `GET /api/v1/users/:id/preferences`: New preferences endpoint
```

---

## 5. Versioning at Scale — Mono-Repo Router Organization

```typescript
// src/api/v1/router.ts
export const apiV1Router = Router();
apiV1Router.use(addDeprecationHeaders({
  sunsetDate: '2027-06-01',
  successorVersion: 'v2',
}));
apiV1Router.use('/users', usersV1Router);
apiV1Router.use('/orders', ordersV1Router);

// src/api/v2/router.ts
export const apiV2Router = Router();
apiV2Router.use('/users', usersV2Router);
apiV2Router.use('/orders', ordersV2Router);

// src/app.ts — mount both versions simultaneously
app.use('/api/v1', apiV1Router);
app.use('/api/v2', apiV2Router);
```

---

## 6. Developer Portal Versioning Communication

Steps for announcing a new version publicly:
1. **Publish migration guide** in developer docs (v1→v2 diff, code examples).
2. **Email all API key holders** registered for affected endpoints.
3. **Update OpenAPI spec** — publish v2 spec, mark v1 spec as deprecated.
4. **Add `Deprecation` + `Sunset` headers** immediately on day of v2 GA launch.
5. **Monitor v1 usage** via API analytics dashboards throughout sunset period.
6. **Send reminders** at 3 months, 1 month, and 2 weeks before sunset.
7. **Switch to 410 Gone** responses on sunset date (do NOT remove immediately — monitor 410s for missed consumers).
8. **Remove v1 code** 30 days after confirming 410 responses are stable.
