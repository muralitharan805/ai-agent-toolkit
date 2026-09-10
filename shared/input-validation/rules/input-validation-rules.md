---
trigger: model_decision
description: "Enforces 3-layer input validation, strict DTO schema parsing, whitelist unknown property stripping (mass assignment prevention), and field-level error aggregation."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Input Validation & Data Sanitization Standards

## Description
Enforces strict 3-layer validation boundaries, mandatory DTO schema validation, whitelist unknown property stripping (mass assignment attack mitigation), comprehensive field-level error aggregation, and input string sanitization across all backend APIs. Prohibits direct access to unvalidated request payloads, eliminates mass assignment security vulnerabilities, ensures all inbound parameters (body, query, route params) adhere to strict format constraints, and standardizes validation error reporting.

## Constraints

### 1. Mandatory 3-Layer Validation Architecture
Validation MUST be separated cleanly across 3 distinct architectural layers:
- **Layer 1: Schema / Type Validation** (Transport / Pipe Layer): Validates shape, types, string lengths, enum values, regex formats, and required fields. Runs before controller/use case execution.
- **Layer 2: Business Invariant Validation** (Application / Domain Layer): Validates contextual business state (e.g. checking if an account has sufficient balance, or if a user exists). Must NOT be embedded into transport schema validators.
- **Layer 3: Authorization Validation** (Guards / Middlewares): Validates if the authenticated caller has permission to perform the action. Runs prior to Layer 1.

### 2. Comprehensive Inbound Surface Validation (Zero-Trust)
- Every incoming HTTP request property consumed by the application MUST be validated against an explicit schema:
  - **Request Body**: Validated via strict input DTO schemas.
  - **Query Parameters**: Validated and type-coerced (e.g. converting `?page=1` from string to positive integer).
  - **Route Parameters**: Validated (e.g. asserting `:id` is a valid UUIDv4 or positive integer).
  - **Headers**: Validated when custom operational headers are required.
- Accessing raw unvalidated request objects (e.g. `req.body.something`) without prior schema validation is STRICTLY FORBIDDEN.

### 3. Strict Whitelist & Unknown Property Stripping (Mass Assignment Prevention)
- Validation schemas MUST enforce strict whitelisting (e.g. Zod `.strict()`, class-validator `whitelist: true, forbidNonWhitelisted: true`, Pydantic `extra = 'forbid'`).
- Any property submitted by the client that is not explicitly declared in the schema MUST be automatically stripped or cause the validation gate to reject the request with HTTP 400.
- Allowing undeclared fields (such as `role: "ADMIN"`, `isVerified: true`, `balance: 999999`) to pass into application services is a CRITICAL SECURITY VULNERABILITY and is STRICTLY FORBIDDEN.

### 4. Field-Level Error Aggregation Invariant
- Validation pipes MUST inspect the entire payload and collect ALL validation errors across all fields.
- Aborting validation on the first encountered field failure is forbidden.
- The returned error payload MUST contain a structured `details` array identifying each invalid field:
  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Input validation failed on 2 fields",
      "details": [
        { "field": "emailAddress", "message": "Must be a valid email format" },
        { "field": "tenureInMonths", "message": "Must be between 6 and 360" }
      ]
    }
  }
  ```

### 5. Standard Format Assertions
- Inbound data fields MUST assert industry-standard format constraints:
  - **Emails**: Validated against RFC 5322 regex format.
  - **Phone Numbers**: Validated against international E.164 format (e.g. `^\+[1-9]\d{1,14}$`).
  - **Entity Identifiers**: Validated as UUIDv4 (`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`) or positive integer IDs.
  - **Financial / Quantity Values**: Strictly non-negative numbers (`min(0)` or `positive()`).
  - **Dates**: Validated as ISO-8601 strings and checked for logical ranges (e.g. birthdates in the past).

### 6. String Sanitization & XSS Mitigation
- User-supplied text strings MUST undergo automatic sanitization:
  - Trim leading and trailing whitespace.
  - Normalize unicode sequences (NFKC normalization).
  - Strip or escape dangerous HTML/script tags before storing or reflecting into templates.

## Examples

### 1. Strict Whitelist Schema vs. Vulnerable Unbounded Payload

```typescript
// ❌ FORBIDDEN: Naive validation allowing Mass Assignment attacks
export async function updateUser(req: Request, res: Response): Promise<void> {
  const data = req.body; // Attacker submits { "role": "SUPERADMIN", "isVerified": true }
  await userService.update(req.params.id, data); // Security breach!
}

// ✅ CORRECT: Strict Zod schema stripping unknown fields and validating types
import { z } from 'zod';

export const UpdateUserDtoSchema = z.object({
  displayName: z.string().trim().min(2).max(100),
  phoneNumber: z.string().regex(/^\+[1-9]\d{1,14}$/, 'Must be valid E.164 phone format').optional(),
  bio: z.string().trim().max(500).optional(),
}).strict(); // Rejects or strips undeclared fields like 'role' or 'isAdmin'

export type UpdateUserDto = z.infer<typeof UpdateUserDtoSchema>;
```

### 2. Validation Pipe Aggregating Field Errors

```typescript
// ✅ CORRECT: Collecting all field errors into standard error contract
export function validateDto<T>(schema: z.ZodType<T>, payload: unknown): T {
  const result = schema.safeParse(payload);
  if (!result.success) {
    const errorDetails = result.error.errors.map(err => ({
      field: err.path.join('.'),
      message: err.message,
    }));

    throw new ValidationError(
      `Input validation failed on ${errorDetails.length} field(s)`,
      errorDetails
    );
  }
  return result.data;
}
```

### 3. Query & Route Parameter Validation

```typescript
// ✅ CORRECT: Validating route params and query string parameters
export const PaginationQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().trim().max(100).optional(),
});

export const UuidParamSchema = z.object({
  id: z.string().uuid('Invalid entity identifier format'),
});
```
