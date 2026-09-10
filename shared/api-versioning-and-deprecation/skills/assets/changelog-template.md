# CHANGELOG

All notable changes to this API are documented in this file.

Format: Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Breaking changes are marked with ⚠️ and require API version bump.

---

## [Unreleased]

---

## [2.0.0] — YYYY-MM-DD

### ⚠️ BREAKING CHANGES
- `GET /api/v2/users/:id`: Renamed field `fullName` → `displayName`
  - **Migration**: Replace all `fullName` references with `displayName`
  - **Migration Guide**: https://docs.company.com/api/v1-to-v2

### Deprecated
- All `/api/v1/*` endpoints deprecated as of YYYY-MM-DD
  - Sunset date: YYYY-MM-DD (6 months from this release)
  - Migration guide: https://docs.company.com/api/v1-to-v2
  - All v1 responses now include: `Deprecation: true` and `Sunset: {date}` headers

### Added
- `GET /api/v2/users/:id/activity` — New user activity log endpoint

### Changed
- `POST /api/v2/users` — Added optional `preferredLanguage` field

---

## [1.5.0] — YYYY-MM-DD

### Added
- `GET /api/v1/users/:id/preferences` — New user preferences endpoint
- `GET /api/v1/users/:id` — Added optional `nickname` field to response

---

## [1.0.0] — YYYY-MM-DD

### Initial Release
- `GET /api/v1/users` — List users
- `GET /api/v1/users/:id` — Get user by ID
- `POST /api/v1/users` — Create user
- `PATCH /api/v1/users/:id` — Update user
- `DELETE /api/v1/users/:id` — Delete user
