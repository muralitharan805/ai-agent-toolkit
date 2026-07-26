---
name: structured-logging-and-observability
description: "Enterprise guidelines for structured JSON logging, correlation ID (x-correlation-id) request tracing, automatic PII secret masking, log level management, and HTTP performance latency metrics."
---

# Structured Logging & Observability Architecture

## Goal
Guide AI coding agents and developers in implementing enterprise-grade structured JSON logging, request correlation ID tracing (`x-correlation-id`), automated PII secret masking, and HTTP performance timing in backend applications.

---

# Core Logging Principles

1. **Correlation ID Tracing (`x-correlation-id`)**: Every incoming HTTP request MUST be assigned or passed a unique UUID correlation ID. All log entries generated during that request lifecycle MUST include this `correlationId`.
2. **Structured JSON Output**: Production logs MUST be emitted as single-line JSON objects (`{ timestamp, level, correlationId, service, message, context, durationMs }`) to allow automated parsing by Datadog, Grafana Loki, or ELK Stack.
3. **Automated Secret & PII Sanitization**: Sensitive keys (`password`, `token`, `secret`, `creditCard`, `authorization`) MUST be scrubbed before writing to log streams.
4. **No Raw `console.log`**: Production application code MUST use a dedicated Logger service (`Logger` / `Pino` / `Winston`) instead of raw `console.log()`.

---

# NestJS Structured Logger & Correlation Interceptor

### 1. Correlation ID Middleware (`correlation-id.middleware.ts`)

```typescript
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class CorrelationIdMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    const correlationId = (req.headers['x-correlation-id'] as string) || uuidv4();
    
    // Attach to request object for downstream loggers
    req['correlationId'] = correlationId;
    
    // Set response header
    res.setHeader('X-Correlation-ID', correlationId);
    next();
  }
}
```

### 2. HTTP Performance & Tracing Interceptor (`logging.interceptor.ts`)

```typescript
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const ctx = context.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    const { method, originalUrl } = request;
    const correlationId = request['correlationId'] || 'N/A';
    const startTime = Date.now();

    return next.handle().pipe(
      tap(() => {
        const duration = Date.now() - startTime;
        const statusCode = response.statusCode;

        this.logger.log(
          `[${correlationId}] ${method} ${originalUrl} ${statusCode} - ${duration}ms`
        );
      }),
    );
  }
}
```

### 3. PII & Secret Sanitizer Utility (`log-sanitizer.util.ts`)

```typescript
const SENSITIVE_KEYS = ['password', 'token', 'authorization', 'secret', 'creditcard', 'ssn'];

/**
 * Recursively sanitizes objects to replace sensitive keys with '[REDACTED]'.
 */
export function sanitizeLogPayload(data: any): any {
  if (!data || typeof data !== 'object') return data;

  if (Array.isArray(data)) {
    return data.map(sanitizeLogPayload);
  }

  const sanitized: Record<string, any> = {};
  for (const key of Object.keys(data)) {
    if (SENSITIVE_KEYS.some((k) => key.toLowerCase().includes(k))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof data[key] === 'object') {
      sanitized[key] = sanitizeLogPayload(data[key]);
    } else {
      sanitized[key] = data[key];
    }
  }

  return sanitized;
}
```

---

# README Directory Structure Update

Update `README.md` to reflect `shared/logging/`:

```text
shared/
├── logging/               # Correlation ID tracing, JSON logs, secret masking
│   ├── skills/
│   └── rules/
```

---

# Verification Protocols

1. **Correlation ID Test**: Send HTTP request `curl -i http://localhost:3000/api/v1/health`; verify response header `X-Correlation-ID` is present and matches the log output.
2. **Secret Masking Test**: Pass body `{ "email": "test@example.com", "password": "SecretPassword123" }`; verify log output shows `"password": "[REDACTED]"`.
