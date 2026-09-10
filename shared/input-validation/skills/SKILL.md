---
name: input-validation
description: "Implements and audits multi-layer input validation, schema assertion DTOs, mass assignment mitigation, and data sanitization across backend APIs. Triggered by 'validation:', 'input-sanitization:', or '/input-validation'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Input Validation & Data Sanitization Skill

## Overview

This skill establishes the production engineering protocol for **3-layer input validation**, **zero-trust DTO schema parsing**, **mass assignment vulnerability mitigation**, and **inbound string sanitization** across language-agnostic backend systems. It guarantees that all inbound request data (body, query parameters, route parameters, and headers) are validated before reaching application use cases, enforces strict whitelisting to prevent unauthorized parameter tampering, collects all field errors into an aggregated array, and mitigates XSS risks.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Inbound DTO Schema]     ──► Define schema for body, query, & route params
               │
  [Phase 2: Whitelist Guard]        ──► Enable strict() / extra='forbid' mode
               │
  [Phase 3: Error Aggregation]      ──► Collect all field errors into details array
               │
  [Phase 4: String Sanitization]    ──► Trim whitespace, normalize unicode, strip HTML
               │
  [Phase 5: Conformance Audit]      ──► Run audit_input_validation.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Inbound DTO & Schema Specification
1. **Declare Strict Typed Schemas**:
   - Define explicit validation schemas for request body, query parameters, and route parameters using your framework's schema engine (Zod, class-validator, Pydantic v2):
   ```typescript
   export const CreateOrderDtoSchema = z.object({
     customerId: z.string().uuid(),
     quantity: z.number().int().positive(),
     unitPriceInCents: z.number().int().nonnegative(),
   });
   ```
2. **Standard Format Assertions**:
   - Validate international phone numbers with E.164 (`^\+[1-9]\d{1,14}$`).
   - Validate email formats with RFC-5322 regex.
   - Validate entity identifiers as UUIDv4 or positive integers.

### Phase 2: Whitelist & Mass Assignment Guard Configuration
1. **Strip or Reject Undeclared Fields**:
   - Enforce whitelist mode to prevent attackers from submitting unauthorized administrative parameters:
   - **Zod**: Append `.strict()` to schemas.
   - **NestJS / class-validator**: `{ whitelist: true, forbidNonWhitelisted: true }`.
   - **Pydantic**: `ConfigDict(extra='forbid')`.

### Phase 3: Field-Level Validation Error Aggregation
1. **Collect All Validation Errors**:
   - Avoid aborting on the first validation failure. Inspect the entire payload and map all issues into the standard RFC-7807 error format:
   ```json
   {
     "success": false,
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Input validation failed on 2 field(s)",
       "details": [
         { "field": "body.emailAddress", "message": "Invalid email address format" },
         { "field": "body.age", "message": "Must be at least 18 years of age" }
       ]
     }
   }
   ```

### Phase 4: String Sanitization & XSS Defense Layer
1. **Sanitize Text Inputs**:
   - Trim leading and trailing whitespace automatically.
   - Normalize unicode representations (NFKC normalization).
   - Strip or escape dangerous HTML and JavaScript `<script>` tags before persistence.

### Phase 5: Conformance Audit & Quality Verification
1. **Run Validation Auditor CLI**:
   - Execute the bundled audit tool to detect untyped request bodies and missing whitelist configurations:
   ```bash
   python3 scripts/audit_input_validation.py src/ --strict
   ```

---

## Working Checklist

- [ ] **Fail at the Gate**: Validation executes before controller/service execution.
- [ ] **Full Surface Covered**: Request body, query params, and route params are all validated.
- [ ] **Whitelist Enforced**: Unknown properties are stripped or rejected (Mass Assignment mitigation).
- [ ] **Error Aggregation**: Validation errors across all fields returned in a structured `details` array.
- [ ] **Standard Formats Asserted**: Emails, E.164 phone numbers, and UUIDs validated against strict regexes.
- [ ] **Clean 3-Layer Separation**: Pure schema validation in transport pipes; business invariants in domain services.

---

## Authoritative References & Bundled Assets

- **Multi-Layer Validation Guide**: [references/multi-layer-validation-and-sanitization.md](references/multi-layer-validation-and-sanitization.md)
- **Validation Auditor CLI Tool**: [scripts/audit_input_validation.py](scripts/audit_input_validation.py)
- **Standard Validation Schema Template**: [assets/standard-validation-schemas.template.ts](assets/standard-validation-schemas.template.ts)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Input Validation)

| Legacy Antipattern | Modern Validation Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Unbounded Payload Acceptance** (`req.body` passed directly to ORM) | **Strict Whitelist Mode (`.strict()`)** | Prevents Mass Assignment attacks where malicious callers escalate privileges (`role: "ADMIN"`). |
| **First-Error-Only Aborting** (Halting validation on the first field) | **Field-Level Error Aggregation** | Improves frontend user experience by showing all form errors in a single submission cycle. |
| **Database Checks in Schema Validators** (Async DB calls in DTO pipe) | **3-Layer Separation of Concerns** | Keeps transport layer pipes fast, pure, and decoupled from persistence infrastructure. |
| **Untyped Controller Bodies** (`body: any`) | **Strongly Typed DTO Classes** | Guarantees compile-time type safety and prevents runtime null pointer dereferences. |
| **Permissive String Validation** (Accepting un-trimmed strings with HTML) | **String Sanitization & Format Regex** | Mitigates Stored Cross-Site Scripting (XSS) and database indexing inconsistencies. |
