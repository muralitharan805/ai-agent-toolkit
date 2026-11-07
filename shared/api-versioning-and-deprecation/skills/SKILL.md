---
name: api-versioning-and-deprecation
description: "Enforces URL path versioning (/api/v1/), breaking vs non-breaking change classification, RFC 8594 Deprecation and Sunset HTTP header standards, minimum 6-month sunset periods, HTTP 410 Gone responses, CHANGELOG.md format, and consumer usage tracking before version removal. Triggered by 'api-versioning:', 'deprecation:', 'breaking-change:', 'sunset:', or '/api-versioning-and-deprecation'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# API Versioning & Deprecation Strategy Skill

## Overview

This skill establishes production engineering standards for **URL Path Versioning** (`/api/v1/` → `/api/v2/`), **Breaking vs Non-Breaking Change Classification**, **RFC 8594-Compliant Deprecation Headers** (`Deprecation`, `Sunset`, `Link`), **Minimum 6-Month Sunset Enforcement**, **HTTP 410 Gone Responses** (not 404) after sunset, **CHANGELOG.md Format Standards**, and **Consumer Usage Tracking Before Version Removal**. It prevents silent consumer breakage, eliminates "API versioning debt", and enforces a contractual migration culture.

```
┌──────────────────────────────────────────────────────────────────────────┐
│               API Deprecation Lifecycle (4 Phases)                       │
│                                                                          │
│  Phase 1: ANNOUNCE                                                       │
│    → Add Deprecation + Sunset headers to ALL v1 responses               │
│    → Publish migration guide + CHANGELOG entry                           │
│    → Notify consumers (email / developer portal)                         │
│                                                                          │
│  Phase 2: MONITOR (6+ months)                                            │
│    → Track v1 usage per consumer (API key / user-agent analytics)       │
│    → Contact consumers still on v1                                       │
│                                                                          │
│  Phase 3: SUNSET                                                         │
│    → After Sunset date → return HTTP 410 Gone (not 404)                 │
│    → Body includes migration guide URL                                   │
│                                                                          │
│  Phase 4: REMOVE                                                         │
│    → Delete v1 code 30 days after 410 responses confirmed stable        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3-Phase Execution Guide

### Phase 1: Versioning Strategy Selection
1. **Recommended: URL Path Versioning**:
   - `GET /api/v1/users` → `GET /api/v2/users`.
   - Explicit, testable in browser, cache-friendly, easy to debug.
2. **Version only on MAJOR breaking changes**:
   - Non-breaking additions (new optional fields, new endpoints) → SAME version, no bump.
   - Breaking changes (removed field, type change, required new field) → NEW major version.
3. **Support N (current) and N-1 (previous) simultaneously** — minimum overlap period.
4. **Version the ENTIRE API surface** — never per-endpoint versioning:
   - `/api/users/v2/:id` is forbidden — creates inconsistent routing chaos.

### Phase 2: Deprecation Header Implementation (RFC 8594)
Add these headers to EVERY response from the deprecated version:
```
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/users>; rel="successor-version"
```
- **Why RFC standards**: API clients and monitoring tools detect these headers automatically.
- Consumers can configure automated warnings when they receive `Deprecation: true`.
- `Sunset` header tells consumers exactly when to migrate by.

### Phase 3: Sunset Response (HTTP 410)
After the Sunset date, ALL v1 endpoints MUST return:
```json
HTTP/1.1 410 Gone

{
  "error": "API_DEPRECATED",
  "message": "v1 API was sunset on 2027-01-01. Please migrate to /api/v2/.",
  "migrationGuide": "https://docs.company.com/api/v1-to-v2",
  "sunsetDate": "2027-01-01"
}
```
- **Use 410 Gone, NOT 404 Not Found** — consumers know it's intentional deprecation, not a bug.

---

## Breaking vs Non-Breaking Change Reference
```
NON-BREAKING (safe — same version, no migration needed):
  ✅ Adding new optional response fields
  ✅ Adding new optional request fields
  ✅ Adding new endpoints entirely
  ✅ Loosening validation (previously rejected → now accepted)
  ✅ Adding new enum values (if consumer handles unknown gracefully)

BREAKING (requires new major version + full deprecation lifecycle):
  ❌ Removing or renaming any response field
  ❌ Changing field data type (string → number, object → array)
  ❌ Changing URL structure or HTTP method
  ❌ Adding a REQUIRED request field
  ❌ Changing authentication mechanism
  ❌ Tightening validation (previously valid input → now rejected)
  ❌ Changing error response structure
```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/api-versioning-strategies-and-lifecycle.md](references/api-versioning-strategies-and-lifecycle.md) for header versioning vs URL versioning trade-offs, consumer-driven contracts, and versioning at scale.
- **Production Asset**: Inspect [assets/changelog-template.md](assets/changelog-template.md) for CHANGELOG.md format with breaking change notation and migration guide structure.
- **CLI Auditor Tool**: Execute [scripts/audit_api_versioning.py](scripts/audit_api_versioning.py) to detect missing deprecation headers, absent sunset dates, and 404 vs 410 routing after deprecation.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Risk |
| :--- | :--- | :--- | :--- |
| **Breaking Changes** | Breaking change in minor/patch release | Major version bump + full deprecation lifecycle | Silent breakage for all consumers |
| **Sunset Period** | No sunset date announced | Minimum 6-month sunset from announcement | Consumers never migrate → v1 maintained forever |
| **Post-Sunset Response** | Return 404 after removal | Return HTTP 410 Gone with migration guide URL | Consumers think it's a bug, not deprecation |
| **Consumer Tracking** | No usage analytics on old version | Track usage per API key before removal | Remove v1 while active consumers still use it |
| **Deprecation Headers** | No `Deprecation` / `Sunset` headers | RFC 8594 headers on ALL deprecated responses | Consumers miss migration deadline |
| **Per-Endpoint Versioning** | `/api/users/v2/:id` | `/api/v2/users/:id` (surface-level versioning) | Inconsistent routing — impossible to maintain |
| **CHANGELOG** | No CHANGELOG maintained | Breaking changes clearly marked per release | New engineers can't understand what changed |
