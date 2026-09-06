---
trigger: always_on
description: "Enforces structured JSON logging, correlation ID request tracing (x-correlation-id), HTTP latency metrics, and automatic PII secret masking."
---

# Structured Logging & Tracing Rules

## Description
Enforces mandatory engineering standards for application logging, request tracing, secret masking, and log level configuration across all backend services and APIs. Eliminates raw `console.log` statements in production code, requires deterministic correlation ID propagation (`X-Correlation-ID`), guarantees sub-second HTTP route latency tracking, and mandates recursive redaction of sensitive credentials.

## Constraints

### 1. Zero Raw `console.log()` in Production
- Application code MUST NOT use raw `console.log()`, `console.error()`, or `console.warn()` statements in production code.
- All log events MUST use the application Logger service (`Logger` / `Pino` / `Winston`).
- Log output in production environments MUST be emitted as single-line serialized JSON objects.

### 2. Mandatory Secret & PII Sanitization
- Passwords, JWT refresh tokens, authorization headers, credit card numbers, and secret keys MUST NOT be printed in plain text in log streams.
- All payload logs MUST pass through the `sanitizeLogPayload()` utility before output.
- Log sanitization utilities MUST be strictly typed without explicit `any` types (`unknown`, `Record<string, unknown>`).

### 3. Correlation ID Propagation (`X-Correlation-ID`)
- Every HTTP request lifecycle MUST be assigned or propagate a unique correlation ID (`x-correlation-id`).
- All HTTP responses MUST include the `X-Correlation-ID` header.
- Downstream microservice and database query logs MUST inherit and emit this correlation ID.

### 4. HTTP Execution Latency Logging
- HTTP interceptors MUST log route execution time in whole milliseconds (`durationMs`):
  `[correlationId] GET /api/v1/resource 200 OK - 15ms`.

## Examples

### 1. Dedicated Logger Service vs. Forbidden Raw `console.log()`
```typescript
// ❌ FORBIDDEN: Raw un-structured console.log in production
export class PaymentService {
  processPayment(amount: number): void {
    console.log('Payment processed for amount: ' + amount); // Missing timestamp, correlationId, level!
  }
}

// ✅ CORRECT: Dedicated Logger Service with Correlation ID and Structured Context
@Injectable()
export class PaymentService {
  private readonly logger = new Logger(PaymentService.name);

  processPayment(amount: number, correlationId: string): void {
    this.logger.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      correlationId,
      message: 'Payment processed successfully',
      amount
    }));
  }
}
```

### 2. Recursive PII Sanitization vs. Leaking Plain-Text Secrets
```typescript
// ❌ FORBIDDEN: Logging raw request body containing sensitive credentials
@Post('login')
async login(@Body() loginDto: LoginDto): Promise<AuthResponse> {
  this.logger.log(`Login attempt for payload: ${JSON.stringify(loginDto)}`);
  // CRITICAL RISK: Prints plain-text password to log stream!
  return this.authService.authenticate(loginDto);
}

// ✅ CORRECT: Sanitizing payload before logging
@Post('login')
async login(@Body() loginDto: LoginDto, @Req() req: CorrelatedRequest): Promise<AuthResponse> {
  const sanitizedPayload = sanitizeLogPayload(loginDto);
  this.logger.log(`[${req.correlationId}] Login attempt: ${JSON.stringify(sanitizedPayload)}`);
  // SAFE: Replaces password field with '[REDACTED]'
  return this.authService.authenticate(loginDto);
}
```

### 3. Correlation ID Middleware & Response Propagation
```typescript
// ✅ CORRECT: Assigning and propagating X-Correlation-ID
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
