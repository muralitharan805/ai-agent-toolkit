# API Response Contracts, Error Catalogs & Pagination Reference

## 1. Architectural Philosophy

> **Predictable Client Shape**: Whether an endpoint returns a single entity, a paginated list, or a validation error, the response root MUST present a predictable structure. Frontend web, iOS, Android, and third-party consumers must be able to write universal network middleware that reliably asserts `response.data.success` before branching logic.

---

## 2. The 3 Standard Response Payloads

### 1. Single Entity / Mutation Success
```json
{
  "success": true,
  "data": {
    "id": "usr_94a8e2b1",
    "emailAddress": "alex@example.com",
    "displayName": "Alex Chen",
    "role": "MEMBER",
    "createdAt": "2026-09-09T09:15:00.000Z"
  },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00.123Z",
    "version": "v1"
  }
}
```

### 2. Paginated Collection Success
```json
{
  "success": true,
  "data": [
    { "id": "ord_101", "totalAmount": 4900, "status": "COMPLETED" },
    { "id": "ord_102", "totalAmount": 1250, "status": "PENDING" }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 1500,
    "totalPages": 75,
    "hasNextPage": true,
    "hasPreviousPage": false
  },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00.123Z",
    "version": "v1"
  }
}
```

### 3. Standard Error Envelope (RFC-7807 Aligned)
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "emailAddress", "message": "Must be a valid email address format" },
      { "field": "tenureInMonths", "message": "Must be a positive integer between 6 and 360" }
    ]
  },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00.123Z",
    "path": "/api/v1/users"
  }
}
```

---

## 3. Standard Error Code Catalog Specification

| Error Code String | HTTP Status | Standard Business Trigger |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | **400 Bad Request** | Request body, query parameters, or route params fail DTO schema validation. |
| `UNAUTHORIZED` | **401 Unauthorized** | Missing, expired, or invalid JWT signature or session cookie. |
| `FORBIDDEN` | **403 Forbidden** | Authenticated user lacks required RBAC role or resource ownership. |
| `NOT_FOUND` | **404 Not Found** | Target entity identifier does not exist in the database. |
| `CONFLICT` | **409 Conflict** | Unique constraint violation (e.g. email already taken) or optimistic locking failure. |
| `UNPROCESSABLE_ENTITY`| **422 Unprocessable** | Syntactically valid payload violates business invariants (e.g. debit amount exceeds balance). |
| `RATE_LIMIT_EXCEEDED`| **429 Too Many Requests**| IP or user token has exceeded the sliding window rate quota. |
| `INTERNAL_SERVER_ERROR`| **500 Server Error** | Unhandled exception or unexpected database connection loss. |
| `SERVICE_UNAVAILABLE`| **503 Unavailable** | Circuit breaker open, maintenance mode, or external payment vendor down. |

---

## 4. Zero Data Leakage Implementation Strategy

To ensure database driver internals never leak to client applications:
1. **Never pass raw exception messages**:
   ```typescript
   // ❌ BAD: Exposes DB internals
   res.status(500).json({ error: error.message });

   // ✅ GOOD: Masked & Sanitized
   logger.error({ event: 'unhandled_db_error', error: error.stack, correlationId });
   res.status(500).json({
     success: false,
     error: {
       code: 'INTERNAL_SERVER_ERROR',
       message: 'An internal error occurred while processing your request',
     },
     meta: { correlationId, timestamp: new Date().toISOString(), path: req.originalUrl }
   });
   ```
2. **Environment Stripping**:
   - In `development` and `test` modes, an optional `debug` field may be attached to the error payload.
   - In `production` and `staging` modes, the `debug` field MUST be completely stripped before transmission.
