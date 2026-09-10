# Domain Error Hierarchy, Triage & On-Call Alerting Reference

## 1. Architectural Philosophy

> **Operational vs. Programmer Errors**: Not all errors are created equal. A user requesting an order with an invalid ID is an **Operational Error** (expected, recoverable, user-facing). A `TypeError: Cannot read properties of undefined` or database connection drop is a **Programmer Error** (unexpected bug, system failure). Conflating the two leads to false alarm on-call pages or silent production crashes.

```
Exception Occurs in Application
              │
    Is error an instance of
        BaseAppError?
        /          \
      YES           NO
      /              \
[Operational Error]  [Programmer Error]
  - Handled by design   - Unexpected bug / crash
  - Log as WARN         - Log as ERROR / FATAL with full stack trace
  - No on-call alert    - Trigger On-Call Incident Alert (PagerDuty/Slack)
  - Return 4xx status   - Return generic sanitized 500 status
```

---

## 2. The Standard Domain Error Class Hierarchy

```
BaseAppError (Abstract Base Class: code, httpStatus, isOperational, details)
  │
  ├── ValidationError        (HTTP 400 - Bad input payload / schema violation)
  ├── UnauthorizedError      (HTTP 401 - Missing / invalid authentication token)
  ├── ForbiddenError         (HTTP 403 - Authenticated but lacks permissions)
  ├── NotFoundError          (HTTP 404 - Requested resource does not exist)
  ├── ConflictError          (HTTP 409 - Relational conflict or duplicate key)
  ├── UnprocessableError     (HTTP 422 - Syntactically valid but semantic violation)
  ├── RateLimitError         (HTTP 429 - Quota / token bucket exhausted)
  └── InternalServerError    (HTTP 500 - Explicit internal failure)
```

---

## 3. Multi-Language Implementations

### TypeScript / Node.js
```typescript
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
  constructor(entity: string, id: string) {
    super('NOT_FOUND', `${entity} with identifier '${id}' was not found`, 404);
  }
}
```

### Python (FastAPI / Starlette)
```python
class BaseAppError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or []
        self.is_operational = True

class NotFoundError(BaseAppError):
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{entity} with identifier '{identifier}' was not found",
            http_status=404
        )
```

### Go
```go
package errors

import "net/http"

type AppError struct {
	Code          string
	Message       string
	HTTPStatus    int
	IsOperational bool
	Details       map[string]string
}

func (e *AppError) Error() string {
	return e.Message
}

func NewNotFoundError(entity, identifier string) *AppError {
	return &AppError{
		Code:          "NOT_FOUND",
		Message:       entity + " with identifier '" + identifier + "' was not found",
		HTTPStatus:    http.StatusNotFound,
		IsOperational: true,
	}
}
```

---

## 4. On-Call Alert Dispatching Patterns

When an unexpected programmer error (500) occurs:
1. **Deduplication / Throttling**:
   - Multiple identical 500 errors in a tight loop should be throttled (e.g. max 1 alert per 5 minutes per unique error stack hash) to prevent alerting cascades.
2. **Alert Payload Format**:
   - Must include: `serviceName`, `environment`, `correlationId`, `errorName`, `message`, `stack`, and `routePath`.
3. **Integration Channels**:
   - Webhook to PagerDuty Events API v2
   - Webhook to Slack `#alerts-backend-production` channel
   - Sentry / Datadog APM exception capture
