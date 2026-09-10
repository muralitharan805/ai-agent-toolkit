---
name: api-documentation-and-contracts
description: "Implements and audits OpenAPI 3.x documentation, complete request/response schemas, consumer-driven contract testing via Pact, and production documentation route hardening. Triggered by 'openapi:', 'swagger:', 'api-docs:', 'contract-test:', or '/api-documentation-and-contracts'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# API Documentation & Contract Testing Skill

## Overview

This skill establishes the production engineering protocol for **OpenAPI 3.x Specifications**, **Exhaustive Error Modeling**, **Consumer-Driven Contract Testing (Pact Framework)**, and **Production Sandbox Access Hardening** across backend services. It guarantees that client developers receive up-to-date, typed API contracts, prevents breaking changes between frontend/mobile and backend services, and protects internal API topology from public disclosure in production.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        5-Phase API Contract Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: OpenAPI Schema Modeling] ──► Annotate endpoints, DTOs & body examples
                │
  [Phase 2: Exhaustive Error Models] ──► Document 400, 401, 404, 409, 500 schemas
                │
  [Phase 3: Contract Testing (Pact)] ──► Consumer pacts & provider verification
                │
  [Phase 4: Production Sandbox Lock] ──► Disable/restrict /docs in production
                │
  [Phase 5: Conformance Audit]       ──► Run audit_api_contracts.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: OpenAPI 3.x Endpoint & Schema Modeling
1. **Document Operation Metadata**:
   - Annotate every endpoint with `@ApiOperation` (summary, description), `@ApiTags`, and security schemes (`@ApiBearerAuth`).
2. **Provide Concrete Body Examples**:
   - Every request DTO property must include realistic examples and descriptions:
     ```typescript
     @ApiProperty({ example: 'usr_abc123', description: 'Unique customer identifier' })
     readonly customerId: string;
     ```

### Phase 2: Exhaustive Error Status Code Documentation
1. **Model Both Success and Failure**:
   - Never document only 200/201 success responses.
   - Document standard errors using the universal error envelope (`StandardApiErrorEnvelopeDto`):
     - `@ApiResponse({ status: 400, type: StandardApiErrorEnvelopeDto, description: 'Validation failure' })`
     - `@ApiResponse({ status: 401, description: 'Authentication required' })`
     - `@ApiResponse({ status: 409, description: 'Duplicate idempotency key' })`
     - `@ApiResponse({ status: 500, description: 'Internal operational error' })`

### Phase 3: Consumer-Driven Contract Testing (Pact)
1. **Consumer Expectation Definition**:
   - Web and mobile clients write Pact tests defining required endpoint interactions.
2. **CI/CD Provider Verification**:
   - Backend test pipelines download pact files and replay them against running controllers to guarantee compatibility before merging pull requests.

### Phase 4: Production Sandbox Access Hardening
1. **Lock Down Interactive Documentation**:
   - In production (`NODE_ENV === 'production'`), disable Swagger UI / Scalar (`GET /docs`) and raw JSON specs (`GET /docs/openapi.json`), or restrict access to internal VPN subnets.

### Phase 5: Conformance Audit
1. Run the API contract auditor across the codebase:
   ```bash
   python3 shared/api-documentation-and-contracts/skills/scripts/audit_api_contracts.py ./src --strict
   ```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [OpenAPI Specification Architecture & Consumer-Driven Contract Testing](references/openapi-specification-and-contract-testing.md) for breaking vs non-breaking rules, code-first vs design-first, and Pact Broker setup.
- **Production Template**: Review [openapi-contract-bootstrap.template.ts](assets/openapi-contract-bootstrap.template.ts) for production TypeScript Swagger DocumentBuilder setup and standard error DTO models.
- **CLI Auditor**: Execute [audit_api_contracts.py](scripts/audit_api_contracts.py) to detect undocumented routes and unprotected production documentation.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Exposing Swagger UI publicly in production | Disable `/docs` in production or restrict behind VPN / admin auth | Discloses entire internal route topology, parameters, and versions to malicious scanners. |
| Documenting only HTTP 200 success responses | Explicitly document all error statuses (400, 401, 404, 409, 500) | Client developers have zero visibility into error payload structures, causing broken error handling. |
| Silently modifying existing API field names | Additive changes only; bump major version (`v2`) for breaking changes | Frontend and mobile client apps crash unexpectedly upon receiving changed response shapes. |
| Relying solely on manual Postman collections | Auto-generated OpenAPI 3.x spec from code annotations or Git repo | Manual Postman collections drift from actual code within days, misleading integrations. |
| Lacking consumer contract verification | Consumer-Driven Contract Tests (Pact framework) in CI/CD | Backend updates inadvertently break mobile apps that cannot be instantly updated by users. |
