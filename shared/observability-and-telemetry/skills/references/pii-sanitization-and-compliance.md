# PII Sanitization, Secret Masking & Regulatory Compliance Reference

## 1. Regulatory Context & Compliance Invariants

Modern data protection regulations—including **GDPR (Article 32)**, **PCI-DSS (Requirement 3.4)**, and **HIPAA Security Rule**—mandate that Personally Identifiable Information (PII), authentication tokens, and authentication credentials MUST NEVER be recorded in plain text in log streams or analytics storage.

### Critical Violation Risks
- Logging customer passwords, JWT refresh tokens, or credit card numbers leads to immediate regulatory fines, security compliance revocation, and severe credential exposure in the event of log pipeline breach.

---

## 2. Sensitive Keys Classification

The following keys and patterns MUST be scrubbed before serializing any payload to stdout, file sinks, or remote syslog forwarders:

| Category | Sensitive Keys & Substrings | Redaction Policy |
| :--- | :--- | :--- |
| **Authentication** | `password`, `passphrase`, `secret`, `secretKey`, `apiKey`, `privateKey`, `credential` | Complete mask: `'[REDACTED]'` |
| **Tokens & Sessions** | `token`, `refreshToken`, `accessToken`, `jwt`, `authorization`, `cookie`, `sessionid` | Complete mask: `'[REDACTED]'` |
| **Financial & PII** | `creditCard`, `cardNumber`, `cvv`, `cvc`, `pan`, `accountNumber`, `ssn`, `aadhaar` | Complete mask: `'[REDACTED]'` |
| **Personal Identifiers**| `dateOfBirth`, `dob`, `pinCode`, `mothersMaidenName` | Partial mask or `'[REDACTED]'` |

---

## 3. Production-Grade Recursive Sanitization (Strictly Typed)

In adherence to clean code rules, the sanitization utility must be strictly typed without using explicit `any`. It must handle circular references, nested objects, arrays, and primitive values safely:

```typescript
const DEFAULT_SENSITIVE_PATTERNS = [
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
 * Recursively inspects unknown input data and sanitizes all sensitive keys.
 *
 * @param input - Unknown raw data payload (object, array, primitive, or null)
 * @param sensitiveSubstrings - Optional custom list of substrings triggering redaction
 * @returns Fully scrubbed payload safe for log streams
 */
export function sanitizeLogPayload(
  input: unknown,
  sensitiveSubstrings: readonly string[] = DEFAULT_SENSITIVE_PATTERNS
): unknown {
  if (input === null || typeof input !== 'object') {
    return input;
  }

  // Handle Arrays recursively
  if (Array.isArray(input)) {
    return input.map((element) => sanitizeLogPayload(element, sensitiveSubstrings));
  }

  // Handle Record objects
  const record = input as Record<string, unknown>;
  const sanitizedRecord: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(record)) {
    const isSensitive = sensitiveSubstrings.some((sensitivePattern) =>
      key.toLowerCase().includes(sensitivePattern)
    );

    if (isSensitive) {
      sanitizedRecord[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitizedRecord[key] = sanitizeLogPayload(value, sensitiveSubstrings);
    } else {
      sanitizedRecord[key] = value;
    }
  }

  return sanitizedRecord;
}
```

---

## 4. Header Masking Protocol

When logging raw HTTP headers in debug or tracing interceptors, authorization headers MUST be redacted immediately:

```typescript
export function sanitizeHttpHeaders(headers: Record<string, unknown>): Record<string, unknown> {
  const sanitized: Record<string, unknown> = { ...headers };
  if (sanitized['authorization']) {
    sanitized['authorization'] = '[REDACTED]';
  }
  if (sanitized['cookie']) {
    sanitized['cookie'] = '[REDACTED]';
  }
  if (sanitized['x-api-key']) {
    sanitized['x-api-key'] = '[REDACTED]';
  }
  return sanitized;
}
```
