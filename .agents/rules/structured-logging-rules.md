---
trigger: always_on
description: "Strict rules for structured JSON logging, correlation ID request tracing (x-correlation-id), and automatic PII secret masking."
---

# Structured Logging & Tracing Rules

## Description
Enforces mandatory standards for application logging, request tracing, secret masking, and log level configuration across backend services.

## Constraints

### 1. No Raw `console.log()` in Production
- Application code MUST NOT use raw `console.log()`, `console.error()`, or `console.warn()` statements in production code.
- All log events MUST use the application Logger service (`Logger` / `Pino` / `Winston`).

### 2. Mandatory Secret & PII Sanitization
- Passwords, JWT refresh tokens, authorization headers, credit card numbers, and secret keys MUST NOT be printed in plain text in log streams.
- All payload logs MUST pass through the `sanitizeLogPayload()` utility before output.

### 3. Correlation ID Propagation (`X-Correlation-ID`)
- Every HTTP request lifecycle MUST be assigned or propagate a unique correlation ID (`x-correlation-id`).
- All HTTP responses MUST include the `X-Correlation-ID` header.

### 4. HTTP Execution Latency Logging
- HTTP loggers MUST log route execution time in milliseconds (`[correlationId] GET /route 200 OK - 15ms`).
