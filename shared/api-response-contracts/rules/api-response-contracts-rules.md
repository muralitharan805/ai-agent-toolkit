---
trigger: model_decision
description: "Enforces universal JSON API response contracts, success envelopes, standard pagination metadata, error code catalog mappings, and zero internal database leakage."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Global Standard Request & Response Contract Standards

## Description
Enforces uniform, predictable JSON API response shapes, standardized error code catalogs, pagination metadata, response header contracts, and strict data leakage prevention across all backend services. Eliminates unformatted response payloads, guarantees that client applications consume a deterministic `{ success, data, meta }` envelope, prevents database error messages and stack traces from reaching clients, and mandates correlation ID propagation across all API boundaries.

## Constraints

### 1. Universal Success Response Envelope Invariant
- All successful HTTP responses (HTTP 200, 201, 204) returning a JSON body MUST adhere strictly to the universal success envelope schema:
  ```json
  {
    "success": true,
    "data": { ... },
    "meta": {
      "correlationId": "<uuid>",
      "timestamp": "<ISO-8601>",
      "version": "v1"
    }
  }
  ```
- Returning raw un-enveloped domain objects (e.g. `res.json(user)`) or naked arrays directly from route handlers is STRICTLY FORBIDDEN.

### 2. Standardized Paginated List Contract
- Endpoints returning paginated collections MUST embed pagination metadata as a first-class sibling to `data` and `meta`:
  ```json
  {
    "success": true,
    "data": [ ... ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 1500,
      "totalPages": 75,
      "hasNextPage": true,
      "hasPreviousPage": false
    },
    "meta": {
      "correlationId": "<uuid>",
      "timestamp": "<ISO-8601>"
    }
  }
  ```
- Ad-hoc pagination property names (e.g. `count`, `limit`, `offset`, `pages`) are forbidden.

### 3. Upfront Standard Error Code Catalog
- Error payloads MUST return an explicit, machine-readable string `code` from an upfront enum catalog mapped deterministically to HTTP status codes:
  - `VALIDATION_ERROR` → 400 Bad Request
  - `UNAUTHORIZED` → 401 Unauthorized
  - `FORBIDDEN` → 403 Forbidden
  - `NOT_FOUND` → 404 Not Found
  - `CONFLICT` → 409 Conflict
  - `UNPROCESSABLE_ENTITY` → 422 Unprocessable Entity
  - `RATE_LIMIT_EXCEEDED` → 429 Too Many Requests
  - `INTERNAL_SERVER_ERROR` → 500 Internal Server Error
  - `SERVICE_UNAVAILABLE` → 503 Service Unavailable
- Using arbitrary or dynamic error code strings in production responses is STRICTLY FORBIDDEN.

### 4. Zero Internal Data Leakage Invariant
- Production error responses MUST NEVER expose raw database error messages (e.g. PostgreSQL `duplicate key value violates unique constraint`, table names, SQL query strings) or raw programming stack traces to the client.
- Internal database exceptions MUST be caught, logged server-side with full diagnostic context under `ERROR` / `FATAL` severity, and mapped to a sanitized client-safe message (e.g. `A record with this identifier already exists`).

### 5. Mandatory Response Header Contract
- Every HTTP response emitted by the server MUST set standard operational tracking headers:
  - `X-Correlation-ID`: The unique UUID tracking the request lifecycle across microservices.
  - `X-Response-Time`: Total server route processing duration in milliseconds (e.g. `45ms`).
  - `X-API-Version`: The active major API version (e.g. `v1`).

### 6. Single Transformer Interceptor Pattern
- Route controllers MUST NOT manually assemble the `{ success: true, meta }` boilerplate on every endpoint.
- Controllers MUST return raw domain DTOs; a global response interceptor/transformer middleware MUST automatically wrap the payload in the standard envelope and inject metadata.

## Examples

### 1. Universal Success & Error Envelopes

```typescript
// ❌ FORBIDDEN: Inconsistent, raw, or leaky response payloads
// Endpoint A returns naked user:
res.json({ id: '123', name: 'Alice' });

// Endpoint B returns raw DB error:
res.status(500).json({ error: error.message, stack: error.stack });

// ✅ CORRECT: Predictable, type-safe envelope contract
// Success Envelope:
export interface ApiResponse<T> {
  readonly success: true;
  readonly data: T;
  readonly meta: {
    readonly correlationId: string;
    readonly timestamp: string;
    readonly version: string;
  };
}

// Error Envelope (RFC-7807 aligned):
export interface ApiErrorResponse {
  readonly success: false;
  readonly error: {
    readonly code: ErrorCode;
    readonly message: string;
    readonly details?: ReadonlyArray<{ readonly field: string; readonly message: string }>;
  };
  readonly meta: {
    readonly correlationId: string;
    readonly timestamp: string;
    readonly path: string;
  };
}
```

### 2. Global Response Transformer Interceptor

```typescript
// ✅ CORRECT: Global NestJS / Express Interceptor automatically wrapping responses
export function responseEnvelopeInterceptor(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const originalJson = res.json.bind(res);
  const startTime = Date.now();

  res.json = (body: unknown): Response => {
    const correlationId = (req.headers['x-correlation-id'] as string) || 'unknown';
    const durationMs = Date.now() - startTime;

    res.setHeader('X-Response-Time', `${durationMs}ms`);
    res.setHeader('X-API-Version', 'v1');

    // If body already an error envelope or explicit raw, pass through
    if (body && typeof body === 'object' && 'success' in body) {
      return originalJson(body);
    }

    const wrappedEnvelope: ApiResponse<unknown> = {
      success: true,
      data: body,
      meta: {
        correlationId,
        timestamp: new Date().toISOString(),
        version: 'v1',
      },
    };

    return originalJson(wrappedEnvelope);
  };

  next();
}
```

### 3. Masking Database Exceptions vs. Leaking Internal Details

```typescript
// ❌ FORBIDDEN: Exposing internal Postgres error to client
catch (err) {
  res.status(500).json({ error: err.message }); 
  // Exposes: "pg_catalog.users relation violates foreign key constraint 'fk_company_id'"
}

// ✅ CORRECT: Server logs raw error, client receives sanitized RFC envelope
catch (err) {
  logger.error({ event: 'database_query_error', error: err.stack, correlationId });
  res.status(409).json({
    success: false,
    error: {
      code: 'CONFLICT',
      message: 'The requested operation conflicts with existing relational records.',
    },
    meta: { correlationId, timestamp: new Date().toISOString(), path: req.path },
  });
}
```
