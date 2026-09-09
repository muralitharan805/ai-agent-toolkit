---
trigger: model_decision
description: "Enforces fail-fast startup configuration validation, strongly-typed central config services, prohibition of raw process.env scattering, zero hardcoded values, and junior-friendly .env.example parity."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-09"
---

# Central Environment Configuration & Secrets Standards

## Description
Enforces production-grade environment configuration, fail-fast application startup, secrets hygiene, and config decoupling across all backend services. Mandates strict schema validation on boot to prevent runtime crashes, requires a centralized, strongly-typed configuration service to eliminate raw environment variable access across business code, prohibits hardcoded operational parameters, and enforces 1:1 parity with junior-friendly documented `.env.example` templates.

## Constraints

### 1. Mandatory Fail-Fast Startup Schema Validation
- The application MUST validate all required configuration variables against an explicit schema (e.g. Zod, Joi, class-validator, Pydantic, or Viper) during the initial bootstrap sequence BEFORE initializing database connections, servers, or listeners.
- If ANY required variable is missing, malformed, or violates type constraints (e.g. non-numeric port, invalid URL format, un-enumed environment flag), the application MUST abort boot immediately, log a structured diagnostic error identifying the missing/invalid variable, and terminate with exit code `1`.
- Lazy or deferred configuration validation during request execution is STRICTLY FORBIDDEN.

### 2. Centralized Config Service Invariant (No Scattered Access)
- Application code MUST access configuration values exclusively through a centralized, strongly-typed Configuration Service or singleton object (e.g. `configService.get('PORT')` or `config.database.url`).
- Direct access to raw environment arrays or globals (such as `process.env.DB_URL`, `os.environ['DB_URL']`, `System.getenv()`, or `os.Getenv()`) inside controllers, services, repositories, or business utilities is STRICTLY FORBIDDEN.
- Configuration schemas MUST enforce type coercion (e.g. casting string ports to integers, parsing boolean feature flags).

### 3. Strict Zero Hardcoding Rule
- Operational parameters including server ports, database connection strings, statement timeouts, HTTP request timeouts, retry attempts, cache TTLs, and rate limits MUST be driven entirely by configuration.
- Inline magic numbers or hardcoded URLs in application logic are forbidden. Default fallback values are permitted only for non-sensitive operational settings (e.g. default port 3000 in local development).

### 4. Hierarchical Loading Order
- Configuration resolution MUST follow a deterministic 4-stage hierarchy:
  1. Safe default constants (non-sensitive local defaults only).
  2. Environment-specific configuration files (local `.env`, `.env.test`).
  3. Runtime secrets injection (Cloud Secrets Manager, HashiCorp Vault, Kubernetes Secrets).
  4. Explicit startup validation gate (crash on failure).
- Runtime secrets injection MUST override local file defaults.

### 5. Production Secrets Hygiene (No `.env` in Production)
- Production environments MUST NEVER rely on physical `.env` files stored on container filesystems or virtual machine disks.
- Production secrets MUST be injected dynamically via container environment variables, secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault), or Kubernetes Secret volumes.
- All `.env` and `.env.*` files containing credentials MUST be explicitly listed in `.gitignore`. Committing `.env` files to version control is STRICTLY FORBIDDEN.

### 6. Mandatory `.env.example` Parity & Junior-Friendly Documentation
- Every configuration variable consumed by the application MUST be present in `.env.example`.
- `.env.example` MUST NEVER contain real credentials, live API keys, or production database passwords. Safe local placeholders (e.g. `your_api_key_here`) must be used.
- Every variable in `.env.example` MUST be preceded by a clear, descriptive header comment documenting:
  - Business purpose of the variable.
  - Expected format and allowed values (e.g. enum options or URL dialect).
  - Where or how a new developer can obtain or generate the value locally.

## Examples

### 1. Fail-Fast Boot Schema Validation vs. Unvalidated Boot

```typescript
// ❌ FORBIDDEN: Raw access without validation (Crashes 2 days later at runtime)
export function startServer(): void {
  const port = process.env.PORT; // undefined if missing, leads to NaN or silent failure!
  const dbUrl = process.env.DATABASE_URL; // missing secret causes uncaught connection failure
  app.listen(port);
}

// ✅ CORRECT: Fail-fast schema validation during bootstrap
import { z } from 'zod';

export const EnvSchema = z.object({
  PORT: z.coerce.number().int().positive().default(3000),
  APP_ENV: z.enum(['development', 'test', 'staging', 'production']),
  DATABASE_URL: z.string().url('DATABASE_URL must be a valid connection URI'),
  JWT_SECRET: z.string().min(32, 'JWT_SECRET must be at least 32 characters long'),
  REDIS_URL: z.string().url(),
});

export type AppConfig = z.infer<typeof EnvSchema>;

export function loadAndValidateConfig(): AppConfig {
  const parseResult = EnvSchema.safeParse(process.env);
  if (!parseResult.success) {
    console.error('❌ FATAL: Application Configuration Validation Failed:');
    console.error(JSON.stringify(parseResult.error.format(), null, 2));
    process.exit(1); // Fail-fast on boot
  }
  return parseResult.data;
}
```

### 2. Centralized Strongly-Typed Config Service vs. Scattered `process.env`

```typescript
// ❌ FORBIDDEN: Scattered process.env access across business logic
export class PaymentService {
  async processPayment(): Promise<void> {
    const apiKey = process.env.STRIPE_API_KEY; // Leaky, untyped, untestable!
    // ...
  }
}

// ✅ CORRECT: Injected typed configuration service
export class PaymentService {
  constructor(private readonly config: AppConfig) {}

  async processPayment(): Promise<void> {
    const apiKey = this.config.STRIPE_API_KEY; // Strongly typed and easily mocked in tests
    // ...
  }
}
```

### 3. Junior-Friendly `.env.example` Documentation

```bash
# ==============================================================================
# Server Port
# Format: Positive integer (Default: 3000)
# Purpose: The TCP port on which the HTTP server listens
# ==============================================================================
PORT=3000

# ==============================================================================
# Runtime Environment Flag
# Allowed: development | test | staging | production
# Purpose: Governs log verbosity, error stack traces, and security controls
# ==============================================================================
APP_ENV=development

# ==============================================================================
# Database Connection URI
# Format: postgresql://[user]:[password]@[host]:[port]/[database]?schema=public
# Source: Start local database using 'docker-compose up -d postgres'
# ==============================================================================
DATABASE_URL="postgresql://postgres:postgres_local_password@localhost:5432/myapp_dev?schema=public"

# ==============================================================================
# JWT Authentication Secret
# Format: High-entropy cryptographic string (Minimum 32 characters)
# Generation: Run 'openssl rand -base64 32' in your terminal
# ==============================================================================
JWT_SECRET="replace_with_32_char_minimum_cryptographic_secret_key"
```
