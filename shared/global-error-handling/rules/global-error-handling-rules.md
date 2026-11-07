---
trigger: model_decision
description: "Enforces domain error class hierarchies (BaseAppError), operational vs programmer error triage, automated on-call alert triggers on 500s, and global catch-all exception filtering."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Global Error Handling & Domain Error Standards

## Description
Enforces a unified, language-agnostic domain exception hierarchy, deterministic operational versus programmer error classification, automated on-call incident dispatching on internal 500 errors, and terminal catch-all exception filters across all backend systems. Eliminates untyped generic errors, prevents silent exception swallowing, guarantees consistent mapping to HTTP status codes, and ensures that unexpected system crashes trigger alerts without exposing stack traces to clients.

## Constraints

### 1. Mandatory `BaseAppError` Domain Hierarchy
- All application and business domain errors MUST extend from an abstract `BaseAppError` base class (or language equivalent) containing:
  - `code`: Explicit machine-readable error code string from the standard catalog.
  - `httpStatus`: Numerical HTTP status code (400, 401, 403, 404, 409, 422, 429, 500, 503).
  - `isOperational`: Boolean flag indicating whether the error is an expected business condition (`true`) or an unexpected programmer bug (`false`).
  - `details`: Optional structured list of field-level validation errors.
- Throwing raw strings (e.g. `throw 'Invalid user'`) or generic base exceptions (e.g. `throw new Error('User not found')`) inside domain or application services is STRICTLY FORBIDDEN.
- Standard subclasses MUST be used:
  - `ValidationError` (400)
  - `UnauthorizedError` (401)
  - `ForbiddenError` (403)
  - `NotFoundError` (404)
  - `ConflictError` (409)
  - `UnprocessableEntityError` (422)
  - `RateLimitError` (429)
  - `InternalServerError` (500)

### 2. Operational vs. Programmer Error Triage Invariant
- The global error handler MUST classify incoming exceptions into two distinct categories:
  1. **Operational Errors** (`isOperational: true`): Expected runtime conditions caused by user input, invalid authentication, or business conflicts.
     - Handled gracefully.
     - Logged at `WARN` level with request context and correlation ID.
     - Formatted and returned with corresponding 4xx HTTP status code.
  2. **Programmer Errors** (`isOperational: false` or unhandled exceptions): Unexpected bugs, null pointer dereferences, syntax errors, or sudden database connection failures.
     - Logged at `ERROR` or `FATAL` level with full stack trace and correlation ID.
     - Automatically triggers an on-call alert dispatch hook (PagerDuty, Sentry, Slack).
     - Formatted and returned as a generic sanitized 500 `INTERNAL_SERVER_ERROR`.

### 3. Automated On-Call Alerting on 500 Errors
- When an unexpected programmer error (HTTP 500) occurs, the global error filter MUST invoke an automated incident alerting hook (e.g. `sendAlertToOnCallTeam(error, correlationId)`).
- Operational 4xx errors (e.g. invalid password, entity not found) MUST NOT trigger on-call alerts to prevent alert fatigue.

### 4. Framework Exception Normalization
- All third-party library and framework exceptions (e.g. JSON parsing errors, Zod/Joi validation failures, ORM duplicate key errors) MUST be intercepted by the global error handler and normalized into the standard error envelope.
- Framework exceptions must not leak unformatted vendor-specific JSON bodies to API consumers.

### 5. Prohibition of Swallowed Exceptions
- Empty `catch` blocks or `catch` blocks that silently ignore errors without logging or re-throwing are STRICTLY FORBIDDEN:
  ```typescript
  // ❌ FORBIDDEN: Silent exception swallowing
  try {
    await saveAuditLog();
  } catch (e) {}
  ```
- If an error is intentionally non-fatal, it MUST be explicitly logged at `WARN` or `DEBUG` level with an explanatory comment justifying why execution continues.

## Examples

### 1. Domain Error Class Hierarchy

```typescript
// ✅ CORRECT: Type-safe BaseAppError and standard subclasses
export abstract class BaseAppError extends Error {
  public readonly isOperational = true;

  constructor(
    public readonly code: string,
    public readonly message: string,
    public readonly httpStatus: number,
    public readonly details?: ReadonlyArray<{ readonly field: string; readonly message: string }>
  ) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);
    Error.captureStackTrace(this, this.constructor);
  }
}

export class NotFoundError extends BaseAppError {
  constructor(entityName: string, identifier: string) {
    super('NOT_FOUND', `${entityName} with identifier '${identifier}' was not found`, 404);
  }
}

export class ValidationError extends BaseAppError {
  constructor(message: string, details: ReadonlyArray<{ readonly field: string; readonly message: string }>) {
    super('VALIDATION_ERROR', message, 400, details);
  }
}
```

### 2. Global Error Handler Triage & Alerting

```typescript
// ✅ CORRECT: Structured triage distinguishing operational from programmer errors
export function globalErrorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  const correlationId = (req.headers['x-correlation-id'] as string) || 'unknown';

  // 1. Operational Domain Error
  if (err instanceof BaseAppError) {
    logger.warn({
      event: 'operational_error',
      correlationId,
      code: err.code,
      message: err.message,
      httpStatus: err.httpStatus,
      path: req.originalUrl,
    });

    res.status(err.httpStatus).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details,
      },
      meta: { correlationId, timestamp: new Date().toISOString(), path: req.originalUrl },
    });
    return;
  }

  // 2. Unexpected Programmer Error
  logger.error({
    event: 'unhandled_programmer_error',
    correlationId,
    errorName: err.name,
    message: err.message,
    stack: err.stack,
    path: req.originalUrl,
  });

  // Trigger On-Call Alert (PagerDuty / Slack)
  sendAlertToOnCallTeam({
    correlationId,
    errorName: err.name,
    message: err.message,
    stack: err.stack,
    path: req.originalUrl,
  });

  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected internal error occurred. Our engineering team has been notified.',
    },
    meta: { correlationId, timestamp: new Date().toISOString(), path: req.originalUrl },
  });
}
```
