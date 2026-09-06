---
name: structured-logging-and-observability
description: Enforces enterprise structured JSON logging, correlation ID (x-correlation-id) request tracing, automatic PII secret masking, log level management, and HTTP performance latency metrics. Triggered by 'logging:', 'tracing:', or 'observability:'.
---

# Structured Logging & Observability Architecture Skill

## Overview

This skill establishes production-grade observability standards across backend services and APIs. It mandates single-line structured JSON output, request correlation ID tracing (`x-correlation-id`), automatic PII and secret masking, and HTTP latency metrics while eliminating raw `console.log` statements and explicit `any` types.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        5-Phase Logging & Tracing Pipeline                      │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Correlation Middleware]  ──► Assign/extract UUID; attach to request & response
                 │
  [Phase 2: Latency Interceptor]     ──► Track execution duration in milliseconds (ms)
                 │
  [Phase 3: Recursive Sanitization]  ──► Scrub passwords, tokens, and credit cards
                 │
  [Phase 4: Structured JSON Logs]    ──► Emit single-line JSON with ECS/OTel fields
                 │
  [Phase 5: Raw Console Prohibition] ──► Enforce dedicated Logger service & log levels
```

---

## 5-Phase Implementation Protocol

### Phase 1: Correlation ID Middleware & Response Propagation
Every incoming HTTP request must be assigned a unique UUID correlation ID. The ID must be captured from incoming `x-correlation-id` headers or generated freshly, and propagated to the response:

```typescript
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';

export interface CorrelatedRequest extends Request {
  correlationId?: string;
}

@Injectable()
export class CorrelationIdMiddleware implements NestMiddleware {
  use(req: CorrelatedRequest, res: Response, next: NextFunction): void {
    const correlationId = (req.headers['x-correlation-id'] as string) || uuidv4();
    req.correlationId = correlationId;
    res.setHeader('X-Correlation-ID', correlationId);
    next();
  }
}
```

### Phase 2: HTTP Execution Latency & Route Interception
Track execution time in milliseconds and log structured route metrics upon stream completion:

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
import { Response } from 'express';
import { CorrelatedRequest } from './correlation-id.middleware';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const ctx = context.switchToHttp();
    const request = ctx.getRequest<CorrelatedRequest>();
    const response = ctx.getResponse<Response>();

    const { method, originalUrl } = request;
    const correlationId = request.correlationId ?? 'system-context';
    const startTime = Date.now();

    return next.handle().pipe(
      tap(() => {
        const durationMs = Date.now() - startTime;
        const statusCode = response.statusCode;

        this.logger.log(
          `[${correlationId}] ${method} ${originalUrl} ${statusCode} - ${durationMs}ms`
        );
      }),
    );
  }
}
```

### Phase 3: Recursive PII & Secret Redaction (Zero-`any`)
Scrub sensitive credentials (passwords, tokens, credit card numbers) recursively before serializing to log streams:

```typescript
const SENSITIVE_PATTERNS: readonly string[] = [
  'password',
  'token',
  'authorization',
  'secret',
  'creditcard',
  'cardnumber',
  'cvv',
  'ssn',
  'apikey',
  'cookie'
];

/**
 * Recursively sanitizes unknown data structures, redacting sensitive keys.
 */
export function sanitizeLogPayload(input: unknown): unknown {
  if (input === null || typeof input !== 'object') {
    return input;
  }

  if (Array.isArray(input)) {
    return input.map((item) => sanitizeLogPayload(item));
  }

  const record = input as Record<string, unknown>;
  const sanitized: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(record)) {
    const isSensitive = SENSITIVE_PATTERNS.some((pattern) =>
      key.toLowerCase().includes(pattern)
    );

    if (isSensitive) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeLogPayload(value);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}
```

### Phase 4: Single-Line Structured JSON Output
Format log entries as single-line JSON objects with standard fields (`timestamp`, `level`, `correlationId`, `service`, `message`, `context`, `durationMs`) for direct ingestion into Datadog, Grafana Loki, or ELK.

### Phase 5: Raw `console.log` Prohibition & Log Level Management
1. **Zero Raw Console**: Application code must never use raw `console.log`, `console.error`, or `console.warn` statements.
2. **Dedicated Logger**: Inject or instantiate the framework Logger service (`Pino`, `Winston`, or NestJS `Logger`).
3. **Environment Calibration**: Enforce `INFO` level in production and `DEBUG` level in staging/development.

---

## Local References & Assets

- **Structured JSON Logging & Tracing Guide**: [references/structured-json-logging-and-tracing.md](references/structured-json-logging-and-tracing.md)
- **PII Sanitization & Compliance Guide**: [references/pii-sanitization-and-compliance.md](references/pii-sanitization-and-compliance.md)
- **Automated Log Hygiene CLI Auditor**: [scripts/audit_log_hygiene.py](scripts/audit_log_hygiene.py)
- **Structured Log Record JSON Schema**: [assets/structured-log-schema.json](assets/structured-log-schema.json)
- **Sensitive Keys & Redaction Catalog**: [assets/sensitive-keys-catalog.json](assets/sensitive-keys-catalog.json)

---

## Automated Verification Protocol

Run the bundled CLI tool to audit source directories for logging hygiene compliance:
```bash
python3 scripts/audit_log_hygiene.py --path src/ --strict
```

---

## Gotchas & Anti-Patterns

| Anti-Pattern | Why It Fails | Modern Recommended Practice |
| :--- | :--- | :--- |
| **Using Raw `console.log()`** | Outputs un-structured text without correlation IDs, timestamps, or log levels. | Use application `Logger` service emitting single-line JSON records. |
| **Logging Plain-Text Passwords or Tokens** | Severe security violation (GDPR/PCI-DSS); credentials stored permanently in log storage. | Always pass request bodies through `sanitizeLogPayload()` prior to logging. |
| **Missing `X-Correlation-ID` Response Header** | Clients cannot correlate frontend errors with backend server log traces. | Propagate `X-Correlation-ID` header on all HTTP responses via middleware. |
| **Multi-Line Formatted JSON in Production** | Log shippers (Filebeat, Fluentbit) split multi-line output into fragmented log events. | Emit strictly single-line stringified JSON objects (`JSON.stringify`). |
| **Using Explicit `any` in Logging Types** | Violates clean code typing standards and disables compiler safety. | Use `unknown`, generic parameters, and `Record<string, unknown>`. |
| **Measuring Duration in Seconds** | Sub-second latency metrics lose precision and rounding detail. | Always calculate route execution duration in whole milliseconds (`ms`). |
