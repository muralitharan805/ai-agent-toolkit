---
name: api-response-contracts
description: "Focuses strictly on the JSON payload structure at runtime (success/error envelopes, pagination formats, and error codes). Not for OpenAPI/Swagger documentation. Triggered by 'api-contract:', 'response-envelope:', or '/api-response-contracts'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Global Standard Request & Response Contract Skill

## Overview

This skill establishes the production engineering protocol for **universal API response contracts**, **success and paginated envelopes**, **standardized error code catalogs**, and **zero-leakage security boundaries** across language-agnostic backend services. It ensures client applications (web, mobile, third-party) receive deterministic `{ success, data, meta }` payloads, prevents internal database errors or stack traces from reaching clients, and guarantees `X-Correlation-ID` header propagation.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Error Code Catalog]     ──► Define 9 standard machine-readable codes
               │
  [Phase 2: Envelope Schemas]       ──► Implement Success, Paginated, & Error schemas
               │
  [Phase 3: Response Transformer]   ──► Mount global interceptor to auto-wrap data
               │
  [Phase 4: Zero-Leakage Masking]   ──► Catch DB errors & sanitize client payloads
               │
  [Phase 5: Conformance Audit]      ──► Run audit_response_contracts.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Standard Error Code Catalog Definition
1. **Declare Global Error Code Enum**:
   Define the 9 standard machine-readable string codes mapped to HTTP status codes:
   - `VALIDATION_ERROR` (400)
   - `UNAUTHORIZED` (401)
   - `FORBIDDEN` (403)
   - `NOT_FOUND` (404)
   - `CONFLICT` (409)
   - `UNPROCESSABLE_ENTITY` (422)
   - `RATE_LIMIT_EXCEEDED` (429)
   - `INTERNAL_SERVER_ERROR` (500)
   - `SERVICE_UNAVAILABLE` (503)

### Phase 2: Success & Paginated Envelope Schema Implementation
1. **Standard Success Envelope**:
   ```typescript
   export interface ApiResponse<T> {
     readonly success: true;
     readonly data: T;
     readonly meta: {
       readonly correlationId: string;
       readonly timestamp: string;
       readonly version: string;
     };
   }
   ```
2. **Standard Paginated Envelope**:
   ```typescript
   export interface PaginatedApiResponse<T> extends ApiResponse<T[]> {
     readonly pagination: {
       readonly page: number;
       readonly pageSize: number;
       readonly totalItems: number;
       readonly totalPages: number;
       readonly hasNextPage: boolean;
       readonly hasPreviousPage: boolean;
     };
   }
   ```

### Phase 3: Global Response Transformer Interceptor Mounting
1. **Automatic Envelope Wrapping**:
   - Mount a global interceptor/middleware so route controllers return raw domain DTOs without manual boilerplate assembly.
   - Inject `X-Correlation-ID`, `X-Response-Time`, and `X-API-Version` response headers.

### Phase 4: Zero-Leakage Exception Sanitization
1. **Sanitize Database & System Errors**:
   - Log the raw exception, SQL query, and stack trace server-side alongside the `correlationId`.
   - In production, return an RFC-7807 error payload with a human-readable generic message:
   ```json
   {
     "success": false,
     "error": {
       "code": "INTERNAL_SERVER_ERROR",
       "message": "An unexpected error occurred while processing your request"
     },
     "meta": {
       "correlationId": "550e8400-e29b-41d4-a716-446655440000",
       "timestamp": "2026-09-09T09:18:00.123Z",
       "path": "/api/v1/orders"
     }
   }
   ```

### Phase 5: Conformance Audit & Quality Verification
1. **Execute Response Auditor CLI**:
   - Run the bundled audit script to detect naked JSON responses, leaked database stack traces, and non-standard error codes:
   ```bash
   python3 scripts/audit_response_contracts.py src/ --strict
   ```

---

## Working Checklist

- [ ] **Universal Success Envelope**: All successful responses return `{ success: true, data, meta }`.
- [ ] **Standard Pagination Shape**: Paginated endpoints return `data: []` with full `pagination` object.
- [ ] **Upfront Error Catalog**: Error codes adhere strictly to the 9 standard machine-readable string codes.
- [ ] **Zero Database Leakage**: Raw SQL errors, table names, and stack traces never reach the client.
- [ ] **Mandatory Response Headers**: `X-Correlation-ID`, `X-Response-Time`, and `X-API-Version` always emitted.
- [ ] **Global Interceptor Wrapping**: Controllers return raw data; interceptor handles envelope packaging.

---

## Authoritative References & Bundled Assets

- **API Contract & Error Catalog Guide**: [references/api-contract-and-error-catalog.md](references/api-contract-and-error-catalog.md)
- **Response Contract Auditor CLI**: [scripts/audit_response_contracts.py](scripts/audit_response_contracts.py)
- **JSON Schema Contract Specification**: [assets/standard-response-envelope.schema.json](assets/standard-response-envelope.schema.json)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Contracts)

| Legacy Antipattern | Modern Contract Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Inconsistent Response Shapes** (Naked arrays in one endpoint, objects in another) | **Deterministic Universal Envelope** | Client apps can build universal deserializers and error-handling interceptors. |
| **Leaking Database Internals** (`res.json(err.message)`) | **Server-Side Log + Sanitized Error Envelope** | Prevents attackers from mapping internal database schemas, tables, and credentials. |
| **Dynamic / Random Error Strings** (`"SOMETHING_BROKE"`) | **Standard 9-Code Enum Catalog** | Client frontend and mobile apps can write deterministic switch-case error recovery logic. |
| **Manual Boilerplate in Controllers** (`res.json({ success: true, data: user, ... })`) | **Global Interceptor / Middleware Wrapper** | Keeps controllers thin, DRY, and focused strictly on application use case delegation. |
| **Ad-Hoc Pagination Fields** (`count`, `limit`, `pages`, `offset`) | **Standardized Pagination Object** | Standardizes table and list pagination components across all frontend applications. |
