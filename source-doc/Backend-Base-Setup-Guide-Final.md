# 🏗️ Production Backend Project — Language-Agnostic Base Setup Guide (v2.0 Final)

> **Scope**: Every section here applies to **any language or framework** — Node.js, Python, Go, Java, .NET, Rust, etc.
> Examples use pseudocode or multi-language snippets. Pick what fits your stack.
> **Style**: Each section has a philosophy, concrete working checklist, and gotchas.

---

## 1. Standard Folder & Clean Architecture

### Philosophy
> **Domain-first, not layer-first.** Clean Architecture dependency rule strict-a follow pannanum — inner layers outer layers pathi theriya koodadhu.

### 4-Layer Dependency Rule
```
┌─────────────────────────────────────────┐
│  Adapters / Controllers                 │  ← HTTP, gRPC, CLI, WebSocket handlers
│  (Protocol handling only)               │
├─────────────────────────────────────────┤
│  Use Cases / Application Services       │  ← Orchestrate business rules
├─────────────────────────────────────────┤
│  Domain / Entities                      │  ← Pure business models (ZERO deps)
├─────────────────────────────────────────┤
│  Infrastructure / Repositories          │  ← DB, Cache, External APIs, Queues
└─────────────────────────────────────────┘

Dependency arrows: outer → inner ONLY. Never reverse.
```

### Recommended Folder Structure
```
project-root/
├── src/
│   ├── modules/              # Feature domains (user, order, payment...)
│   │   └── user/
│   │       ├── user.controller    # Adapter layer — HTTP only
│   │       ├── user.service       # Use case / application logic
│   │       ├── user.repository    # Infrastructure — DB access
│   │       ├── user.dto           # Input/output contracts
│   │       ├── user.entity        # Domain model
│   │       └── user.test          # Co-located tests
│   ├── common/               # Shared cross-cutting concerns
│   │   ├── decorators/
│   │   ├── filters/          # Global error handlers
│   │   ├── guards/           # Auth/permission guards
│   │   ├── interceptors/     # Logging, response transform
│   │   ├── middlewares/      # Correlation ID, request logger
│   │   ├── pipes/            # Validation pipes
│   │   └── utils/            # Pure, stateless utility functions
│   ├── config/               # Central environment config service
│   ├── database/
│   │   ├── migrations/
│   │   ├── seeders/
│   │   └── connection        # Pool setup
│   ├── observability/        # Logger, metrics, tracer bootstrap
│   └── main                  # App entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── docs/
│   ├── architecture.md
│   ├── development.md
│   ├── testing.md
│   ├── deployment.md
│   ├── database.md
│   └── troubleshooting.md
├── scripts/                  # Migration runners, CI helpers, seed scripts
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example              # Every variable with descriptive comment — mandatory
├── .env                      # NEVER commit — gitignore mandatory
├── CHANGELOG.md              # Version history and breaking changes
└── README.md
```

### Unit of Work & Transaction Boundaries
In Clean Architecture, a single Use Case often needs to write across multiple repositories atomically (e.g., `orderRepository.create()` and `inventoryRepository.decrement()`).
> **The Dependency Invariant**: Domain Use Cases must NEVER import or receive raw database transaction objects (e.g., `PrismaClient`, `EntityManager`, `Knex.Transaction`, `java.sql.Connection`). Doing so violates the dependency rule by leaking persistence implementation details into the domain core.

```typescript
// ✅ Clean Architecture Unit of Work abstraction (defined in Application/Domain layer)
export interface TransactionalContext {
  readonly orderRepo: OrderRepository;
  readonly inventoryRepo: InventoryRepository;
}

export interface UnitOfWork {
  executeInTransaction<T>(
    work: (ctx: TransactionalContext) => Promise<T>
  ): Promise<T>;
}
```

### Working Checklist
- [ ] Strict dependency rule: outer → inner only (no domain importing infrastructure)
- [ ] Pluggable abstractions: Interface/Trait/Protocol for DB, Cache, Mailers
- [ ] Unit of Work abstraction for multi-repository atomic transactions (no ORM leaks into domain)
- [ ] Core business logic zero coupling to framework internals
- [ ] `common/` only for truly cross-cutting concerns

### Gotchas
- ❌ Never: `controllers/`, `services/`, `repositories/` as top-level folders
- ❌ Never: Mix domain model with ORM entity annotations directly
- ❌ Never: Pass raw database/ORM transaction objects into Domain Use Cases
- ✅ Co-locate tests with source — `user.service.test` next to `user.service`

---

## 2. Central Environment Configuration & Secrets

### Philosophy
> **Fail-fast on boot.** Missing variables prod runtime-la crash aaga koodadhu — config validation at startup mandatory.

### Config Loading Order
```
1. Hardcoded safe defaults (non-sensitive only)
2. Environment-specific file (local / test / staging / prod)
3. Runtime secrets injection (Secrets Manager / Vault)
4. Validate ALL required vars → CRASH with clear message if any missing
5. always set and get config variables from .env files never hardcode
```

### Required Variables Reference
```
VARIABLE              TYPE     EXAMPLE                          REQUIRED
────────────────────────────────────────────────────────────────────────
PORT                  number   3000                             YES
APP_ENV               enum     development|staging|production   YES
LOG_LEVEL             enum     debug|info|warn|error            YES
DATABASE_URL          string   postgresql://...                 YES
JWT_SECRET            string   min 32 chars                     YES
JWT_EXPIRES_IN        string   15m                              YES
JWT_REFRESH_EXPIRES_IN string  7d                               YES
REDIS_URL             string   redis://localhost:6379           YES
```

### .env.example Template (mandatory, junior-friendly comments)
```bash
# ==============================================================
# Server Port — The HTTP port the application listens on
# ==============================================================
PORT=3000

# ==============================================================
# Runtime environment — controls log level, error verbosity
# Allowed: development | staging | production
# ==============================================================
APP_ENV=development

# ==============================================================
# Log verbosity. Allowed: debug | info | warn | error
# ==============================================================
LOG_LEVEL=info

# ==============================================================
# Database Connection URI
# Format: <dialect>://<user>:<pass>@<host>:<port>/<database>
# Local: use docker-compose postgres service
# ==============================================================
DATABASE_URL="postgresql://postgres:password@localhost:5432/myapp_dev"

# ==============================================================
# JWT Secret — Minimum 32-character high-entropy string
# Generate: openssl rand -base64 32
# ==============================================================
JWT_SECRET="replace_with_32_char_cryptographic_secret"
JWT_EXPIRES_IN="15m"
JWT_REFRESH_EXPIRES_IN="7d"

# ==============================================================
# Redis — Caching, rate limiting, session store
# Local: use docker-compose redis service
# ==============================================================
REDIS_URL="redis://localhost:6379"
```

### Feature Flags & Dynamic Runtime Configuration

Production backends require two distinct runtime configuration categories:

#### 1. Static Boot Configuration (Fail-Fast)
- Database credentials, port, log level, JWT secrets.
- Validated strictly at boot time. Invalid → process crashes immediately with a clear error message.

#### 2. Dynamic Runtime Flags & Kill-Switches (Zero-Downtime)
> **Rule**: Never redeploy just to toggle an integration on/off. Use feature flags.

**Flag Types:**
```
Boolean  → isNewCheckoutEnabled: true/false     (kill switch / feature toggle)
String   → paymentGateway: "stripe"|"razorpay"  (provider switch without redeploy)
Number   → maxUploadSizeMb: 10                  (config tuning without redeploy)
JSON     → checkoutConfig: { timeout: 30 }      (complex config objects)
```

**Use Cases:**
```
Kill switch:       Disable broken 3rd-party integration instantly (no deploy)
Gradual rollout:   10% → 25% → 50% → 100% user exposure (safe feature launch)
A/B testing:       Route user cohorts to different implementations
Manual override:   Force circuit breaker OPEN during a known incident
Maintenance mode:  Show maintenance banner without code change
Canary release:    Enable feature for internal @company.com users only first
```

**OpenFeature Integration (Vendor-Neutral Standard):**
```
// Bootstrap — once at startup
featureClient = OpenFeature.getClient()
featureClient.setProvider(
  new UnleashProvider(config.unleashUrl, config.unleashApiKey)
  // alternatives: LaunchDarklyProvider | FliptProvider | FlagsmithProvider
)

// Evaluation — microsecond latency (in-memory cached, background sync)
isNewCheckoutEnabled = await featureClient.getBooleanValue(
  'new-checkout-flow',         // flag key
  false,                       // safe default if flag service unreachable
  { userId, tenantId, email }  // targeting context
)

if isNewCheckoutEnabled:
    return newCheckoutService.process(order)
else:
    return legacyCheckoutService.process(order)
```

**Targeting Rules (configured in UI — zero code change):**
```
→ Enable for emails ending in @company.com (internal dogfooding)
→ Enable for 10% of userId hash (gradual percentage rollout)
→ Enable for tenantId = 'enterprise-tier'
→ Disable for country = 'EU' (GDPR compliance kill-switch)
→ Enable for userId in [beta-tester-list]
```

**Tools:**
```
OpenFeature SDK  → openfeature.dev (vendor-neutral interface — avoids lock-in)
Backends:
  Unleash      → Open-source, self-hosted (recommended for cost control)
  LaunchDarkly → Managed SaaS, enterprise-grade, paid
  Flagsmith    → Open-source with managed option
  Flipt        → Self-hosted, GitOps-friendly
  Redis HSET   → DIY minimal flag store (simple booleans only)
```

### Working Checklist
- [ ] Schema validation on startup — all required vars present + correct type
- [ ] Zero hardcoding: ports, URLs, timeouts, retry counts — all config-driven
- [ ] Hierarchical config: defaults → env-specific → secrets injection
- [ ] Static configuration strictly separated from dynamic runtime feature flags/kill-switches
- [ ] Secret sanitization: passwords and API keys auto-mask (`***`) in logs
- [ ] `.env` in `.gitignore` — verified in CI pipeline
- [ ] `.env.example` has 1:1 parity with all required vars + descriptive comments

### Gotchas
- ❌ Never scatter `process.env.DB_URL` / `os.environ['DB']` across business logic files
- ❌ Never redeploy an application just to toggle an integration off (use dynamic kill-switch flags)
- ❌ Never commit `.env` (add gitignore check to CI)
- ✅ Production secrets via Secrets Manager — never `.env` file in prod

---

## 3. Application Bootstrap & Server Lifecycle

### Philosophy
> App boot = infrastructure wiring only. Business logic here = architecture smell.

### Boot Sequence (Universal Order)
```
1.  Load & validate environment config           ← CRASH if invalid
2.  Initialize structured logger                 ← First thing, before any failure
3.  Register process-level crash handlers        ← Unhandled rejections / panics
4.  Connect to database (with retry + timeout)   ← Health check on connect
5.  Connect to cache / Redis
6.  Connect to message broker (if applicable)
7.  Wire dependency injection container
8.  Register middlewares (order matters!)
9.  Register routes / controllers
10. Register global error handler               ← LAST middleware
11. Register graceful shutdown hooks            ← SIGTERM / SIGINT
12. Start HTTP server
13. Log: "Server ready at 0.0.0.0:{PORT}"
```

### Process-Level Crash Handlers (Pseudocode)
```
ON unhandledRejection(error):
    logger.fatal({ event: 'unhandled_rejection', error })
    gracefulShutdown(exitCode: 1)

ON uncaughtException(error):
    logger.fatal({ event: 'uncaught_exception', error })
    gracefulShutdown(exitCode: 1)

ON SIGTERM / SIGINT:
    gracefulShutdown(exitCode: 0)
```

### Working Checklist
- [ ] Explicit DI wiring at bootstrap (DB pool, logger, redis — all resolved at startup)
- [ ] Database connection with retry logic (exponential backoff — 3 retries before fatal)
- [ ] Process-level handlers: unhandled rejections + uncaught exceptions + panics
- [ ] All shutdown hooks registered before server.listen()
- [ ] Server only starts after all infrastructure connections are healthy

### Gotchas
- ❌ Never `process.exit(1)` without logging WHY with full context
- ❌ Never start HTTP server if DB connection fails
- ❌ Never hardcode port — always from validated config

---

## 4. Server, Routing & Middleware Pipeline

### Server Configuration
```
SETTING                  VALUE              REASON
──────────────────────────────────────────────────────────────────────
Request read timeout     30s                Prevent Slowloris attacks
Write timeout            30s                Prevent slow client resource hold
Keep-alive timeout       65s                Must be > load balancer timeout (ALB = 60s)
Max request body         1MB JSON           Reject oversized payloads early
Max URL length           2048 chars         Standard browser limit
Compression              gzip / brotli      Responses > 1kb — bandwidth save
Trust proxy              true               When behind Nginx / Cloudflare / ALB
```

### API URL Conventions
```
# Versioning — mandatory from day 1
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/:id
PUT    /api/v1/users/:id
DELETE /api/v1/users/:id

# Nested resources — max 2 levels deep
GET    /api/v1/orders/:id/items

# Non-CRUD actions — verb as last path segment
POST   /api/v1/orders/:id/cancel
POST   /api/v1/users/:id/deactivate
POST   /api/v1/auth/refresh
```

### Middleware Execution Order (Critical — Wrong Order = Security Holes)
```
Request →
  [1]  Correlation ID           → Assign/propagate X-Correlation-ID (uuid)
  [2]  Real IP Resolver         → Extract true client IP (X-Forwarded-For / CF-Connecting-IP)
  [3]  Request Logger           → Log method, path, userAgent, ip, timestamp
  [4]  Security Headers         → Helmet equivalent (CSP, HSTS, X-Frame-Options...)
  [5]  CORS                     → Origin whitelist check
  [6]  Compression              → gzip/brotli response compression
  [7]  Body Parser              → JSON, form-data parse
  [8]  Request Size Limiter     → Reject oversized payloads early
  [9]  Rate Limiter             → IP + user-based throttling
  [10] Authentication           → JWT / session verification
  [11] Authorization            → Role / permission check
  [12] Input Validation         → Schema validation before business logic
  [13] Route Handler            → Business logic (thin — delegates to service)
  [14] Response Transformer     → Standard response envelope wrapper
  [15] Error Handler            → LAST — catches everything above
→ Response
```

### Working Checklist
- [ ] All server timeouts configured (read, write, idle, keep-alive)
- [ ] Payload size limits enforced (JSON: 1MB, multipart: 10MB)
- [ ] Real IP resolver for reverse proxy / Cloudflare setups
- [ ] Middleware registered in correct order (verified)
- [ ] API versioned from day 1 (`/api/v1/`)
- [ ] Compression enabled
- [ ] Route handlers are thin — delegate immediately to service layer

### Gotchas
- ❌ Real IP resolver missing → rate limiting applies to proxy IP, not real client IP
- ❌ Error handler not last → uncaught errors bypass global handler
- ❌ Compression middleware before body parse → parse errors

---

## 5. Global Standard Request & Response Contract

### Philosophy
> Client apps must receive a **predictable, consistent shape** — always. No surprises.

### Success Response
```json
{
  "success": true,
  "data": { },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00Z",
    "version": "v1"
  }
}
```

### Paginated List Response — Two Strategies

#### Strategy 1: Offset-Based Pagination (Simple — use only for small datasets < 50K records)
```json
{
  "success": true,
  "data": [],
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
    "timestamp": "2026-09-09T09:18:00Z"
  }
}
```
```
SQL: SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 980

Problems at scale:
  ❌ OFFSET 980 → DB scans and discards 980 rows before returning 20 (O(n) cost)
  ❌ Page drift: New records inserted during pagination → items appear on wrong page
  ❌ Inconsistent results: Deleted item shifts all subsequent pages → records skipped
  ✅ Use ONLY when: total records < 50K AND admin dashboards (jump-to-page UX needed)
```

#### Strategy 2: Cursor-Based Pagination (Production Standard — use for all large datasets)
```json
{
  "success": true,
  "data": [],
  "pagination": {
    "pageSize": 20,
    "nextCursor": "eyJpZCI6Im9yZF94eXoiLCJjcmVhdGVkQXQiOiIyMDI2LTA5LTAxVDEwOjAwOjAwWiJ9",
    "previousCursor": "eyJpZCI6Im9yZF9hYmMiLCJjcmVhdGVkQXQiOiIyMDI2LTA5LTAyVDEwOjAwOjAwWiJ9",
    "hasNextPage": true,
    "hasPreviousPage": true
  },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00Z"
  }
}
```
```
Cursor = base64(JSON({ id: "ord_xyz", createdAt: "2026-09-01T10:00:00Z" }))

SQL: SELECT * FROM orders
     WHERE (created_at, id) < (:cursorCreatedAt, :cursorId)
     ORDER BY created_at DESC, id DESC
     LIMIT 20

Advantages:
  ✅ O(1) cost regardless of page depth — no scanning skipped rows
  ✅ Stable results — inserts/deletes never shift pages mid-pagination
  ✅ Infinite scroll / mobile feeds work perfectly
  ✅ DB uses composite index efficiently (index on sort columns mandatory)

Disadvantages:
  ❌ Cannot jump to arbitrary page (no "go to page 50")
  ❌ Approximate total count only (exact COUNT(*) expensive at scale)

Required DB index:
  CREATE INDEX idx_orders_cursor ON orders (created_at DESC, id DESC);
```

#### Pagination Strategy Decision Rule
```
Records < 50K  + Admin dashboard  → Offset (jump-to-page UX)
Records > 50K  + API / Feed       → Cursor (performance + stability)
Infinite scroll / real-time feed  → Cursor ONLY (never offset)
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "emailAddress", "message": "Must be a valid email address" },
      { "field": "password", "message": "Minimum 8 characters required" }
    ]
  },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00Z",
    "path": "/api/v1/users"
  }
}
```

### Standard Error Code Catalog
```
VALIDATION_ERROR        → 400
UNAUTHORIZED            → 401
FORBIDDEN               → 403
NOT_FOUND               → 404
CONFLICT                → 409
UNPROCESSABLE_ENTITY    → 422
RATE_LIMIT_EXCEEDED     → 429
INTERNAL_SERVER_ERROR   → 500
SERVICE_UNAVAILABLE     → 503
```

### Standard Response Headers
```
X-Correlation-ID  → <uuid>   (always)
X-Response-Time   → 45ms
X-API-Version     → v1
```

### Working Checklist
- [ ] Single response transformer middleware wraps all success responses
- [ ] Zero leakage: DB errors, stack traces never reach client
- [ ] Error code catalog defined upfront before first endpoint
- [ ] `correlationId` in every response (success + error)
- [ ] `X-Correlation-ID` response header always set

---

## 6. Global Error Handling

### Domain Error Hierarchy
```
BaseAppError (base class)
  ├── ValidationError        → 400
  ├── UnauthorizedError      → 401
  ├── ForbiddenError         → 403
  ├── NotFoundError          → 404
  ├── ConflictError          → 409
  ├── RateLimitError         → 429
  └── InternalServerError    → 500
```

### Global Error Handler (Pseudocode)
```
function globalErrorHandler(error, request, response):
    correlationId = request.correlationId

    if error is BaseAppError (operational):
        logger.warn({ correlationId, code: error.code, message: error.message })
        return response.status(error.httpStatus).json(formatError(error, correlationId))

    if error is FrameworkValidationError:
        logger.warn({ correlationId, 'validation_failed', details: error.details })
        return response.status(400).json(formatValidationError(error, correlationId))

    # Unknown programmer error
    logger.error({ correlationId, error, stack: error.stack })
    sendAlertToOnCallTeam(error, correlationId)   # PagerDuty / OpsGenie / Slack
    return response.status(500).json(formatGenericError(correlationId))
```

### Working Checklist
- [ ] Domain error hierarchy defined with HTTP status mapping
- [ ] All framework exceptions mapped through global handler
- [ ] 500 errors trigger on-call alert
- [ ] Stack traces logged server-side, never sent to client
- [ ] `correlationId` in every error response

---

## 7. Input Validation & Data Sanitization

### Validation Layers
```
Layer 1: Schema / Type      → Correct shape? (string, number, email format...)
Layer 2: Business Rule      → Valid value? (user exists? stock available?)
Layer 3: Authorization      → Caller allowed? (handled in middleware before this)
```

### What to Validate on Every Request
```
✅ Required fields present
✅ Correct data types
✅ String lengths (min / max)
✅ Enum values in allowed set
✅ Email format
✅ Phone number format (E.164)
✅ Date format and range
✅ Numeric ranges (no negative prices)
✅ UUID format for IDs
✅ No unexpected extra fields (strip unknown — mass assignment prevention)
```

### Working Checklist
- [ ] Validation runs before business logic — fail at the gate
- [ ] Query params + route params + request body + headers — all validated
- [ ] Unknown fields stripped or rejected
- [ ] HTML tags stripped from string inputs (XSS prevention)
- [ ] Validation errors collected and returned as array (not first-error-only)

### Tools by Language
```
Node.js / TypeScript  → Zod / class-validator + class-transformer
Python                → Pydantic v2
Go                    → go-playground/validator
Java                  → Jakarta Validation (Bean Validation)
.NET                  → FluentValidation / DataAnnotations
Rust                  → validator crate
```

---

## 8. Observability & Telemetry — The Three Pillars

### Overview
```
Logs    → WHAT happened (events, errors, state changes)
Metrics → HOW MUCH / HOW FAST (rates, latency distributions)
Traces  → WHERE time was spent (distributed request journey)

Without all three → Production blind spots.
```

---

### Pillar 1: Logs

#### Log Levels
```
TRACE  → Ultra-verbose (DB queries, loops) — dev only
DEBUG  → Internal state debugging — dev / staging
INFO   → Business events (user created, order placed)
WARN   → Unexpected but handled (retry, deprecated API)
ERROR  → Failure handled (payment failed, external API timeout)
FATAL  → Unrecoverable crash (DB unreachable at boot)
```

#### Structured Log Format (JSON — mandatory in production)
```json
{
  "timestamp": "2026-09-09T09:18:00.000Z",
  "level": "INFO",
  "service": "order-service",
  "version": "2.4.1",
  "environment": "production",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "usr_abc123",
  "event": "order.created",
  "orderId": "ord_xyz789",
  "durationMs": 45,
  "message": "Order created successfully"
}
```

#### Mandatory Fields in Every Log
```
timestamp      → ISO 8601 UTC
level          → log level string
service        → app / service name
correlationId  → request trace ID
message        → human-readable description
```

#### Mandatory Redaction List
```
passwords             → "[REDACTED]"
JWT tokens            → "[REDACTED]"
Authorization headers → "[REDACTED]"
Credit card numbers   → "[REDACTED]"
National ID / SSN     → "[REDACTED]" or hash
```

#### Logger Tools by Language
```
Node.js   → Pino (fastest) / Winston
Python    → structlog / loguru
Go        → zerolog / zap
Java      → Logback + SLF4J (JSON appender)
.NET      → Serilog / NLog
Rust      → tracing crate
```

---

### Pillar 2: Metrics

#### RED Metrics (Minimum Required — Every Service)
```
R — Rate:     http_requests_total{method, route, status}       Counter
E — Errors:   errors_total{type, code}                         Counter
D — Duration: http_request_duration_seconds{method, route}     Histogram
```

#### Extended Metric Set
```
http_active_connections                            → Gauge
db_query_duration_seconds{operation, table}        → Histogram
db_connection_pool_active / waiting / idle         → Gauge
cache_hits_total / cache_misses_total              → Counter
queue_depth{queue_name}                            → Gauge
```

#### Exposure
```
GET /metrics  → Prometheus text format
              → Scrape interval: 15s
              → IP-restrict or basic-auth protected
```

---

### Pillar 3: Distributed Traces

#### Concept
```
One user request spans multiple services / DB / cache calls:

User Request
  └── [Span] HTTP Handler (50ms total)
        ├── [Span] Auth verification (5ms)
        ├── [Span] DB query: SELECT user (20ms)
        ├── [Span] Redis cache GET (2ms)
        └── [Span] External API call (23ms)

Trace = full journey. Span = one unit of work.
```

#### Standard: OpenTelemetry (Language-Agnostic)
```
Use OpenTelemetry SDK for your language.
Export to: Jaeger / Zipkin / Grafana Tempo / Datadog / AWS X-Ray

W3C Trace Context propagation headers:
  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

### Working Checklist
- [ ] Structured JSON logging (no raw console.log in production)
- [ ] `correlationId` propagated from middleware through all logs
- [ ] PII redaction utility applied before logging
- [ ] RED metrics exposed at `/metrics` (Prometheus format)
- [ ] System metrics: memory, CPU, DB pool saturation
- [ ] OpenTelemetry SDK integrated — W3C `traceparent` propagated
- [ ] Log aggregation: app → collector → Loki / Elasticsearch / CloudWatch

### GDPR & Data Privacy Compliance

#### PII Data Classification — Every Table Must Be Audited
```
Red (Sensitive PII):   password_hash, SSN, credit_card, biometric, medical_data
Amber (PII):           email, phone, full_name, IP address, location, date_of_birth
Green (Non-PII):       order_id, product_name, amounts, timestamps

Rules per classification:
  Red:   Encrypt at rest + in transit. NEVER log. Strict access control. Audit every read.
  Amber: Log with redaction ([REDACTED]). Anonymize in non-prod. Enforce retention limit.
  Green: Standard handling.
```

#### Right to Erasure (GDPR Article 17) — Implementation
```
User requests account deletion:

Step 1: Soft delete → set deleted_at = NOW() (immediate access revoked)
Step 2: Background job (executes within 30 days):
  → Anonymize PII: email → "deleted_{hash}@anon.invalid"
  → NULL out: phone, full_name, date_of_birth, address, IP history
  → RETAIN: order/invoice records (financial legal obligation — 7 years)
  → DELETE: session tokens, refresh tokens, activity logs with PII
  → Notify: send confirmation email before anonymization begins

NEVER physically delete financial/legal records — retain but anonymize the user link.
```

#### Data Retention Policy
```
Data Type                  Retention      Action After Expiry
──────────────────────────────────────────────────────────────────
User profiles (active)     Indefinite     N/A
User profiles (deleted)    30 days        Anonymize PII fields
Session tokens             7 days         Auto-expire (Redis TTL)
Application logs           90 days        Auto-delete (log rotation)
Security audit logs        2 years        Archive to cold storage
Financial records          7 years        Legal retention — keep
Support tickets            3 years        Anonymize after retention
```

#### Non-Production Data Masking (Critical)
```
❌ NEVER copy production database directly to staging/local (real PII exposed to devs)
✅ ALWAYS run masking script before restoring to non-prod:
  email   → user_{id}@example.com
  phone   → +1555000{id}
  name    → "Test User {id}"
  SSN     → 000-00-{id}

Tools: pg_anonymizer (Postgres), Faker (seed generation)
```

#### Audit Trail for Sensitive Operations
```sql
-- Append-only audit table (no UPDATE or DELETE ever)
CREATE TABLE audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event       VARCHAR NOT NULL,   -- 'user.profile_viewed', 'user.deleted'
  actor_id    UUID NOT NULL,      -- Who performed the action
  subject_id  UUID NOT NULL,      -- Who was affected
  ip_address  VARCHAR,
  user_agent  VARCHAR,
  metadata    JSONB,              -- Sanitized context (no raw PII values)
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Mandatory events to audit:
--   Admin views user PII          → GDPR accountability
--   User exports their data       → GDPR data portability (Article 20)
--   Account deletion requested    → Record with expected anonymization date
--   Failed login attempts         → Security audit trail
```

#### GDPR Checklist
- [ ] PII data inventory documented (Red/Amber/Green classification per table)
- [ ] Right to erasure endpoint implemented (`DELETE /api/v1/users/me`)
- [ ] Anonymization background job (completes within 30 days)
- [ ] Data retention cron job (auto-purge expired data per policy)
- [ ] Non-prod data masking script committed to repo
- [ ] Audit log table (append-only, immutable) for sensitive operations
- [ ] Privacy policy accessible (link in API docs)

---

## 9. Health Checks & Probes

### Endpoints
```
GET /live     → Liveness: Is process alive? (NO external checks)
               → 200 immediately
               → K8s liveness probe → fail = restart container

GET /ready    → Readiness: Can app accept traffic?
               → Checks: DB connected? Redis connected?
               → 200 = healthy, 503 = not ready
               → K8s readiness probe / Load balancer fail = stop routing

GET /startup  → Startup: Heavy warmup complete?
               → Prevents liveness kills during cold start
               → K8s startup probe only

GET /health/details  → Full diagnostic (internal only, IP-restricted)
```

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2026-09-09T09:18:00Z",
  "version": "2.4.1",
  "uptime": 86400,
  "checks": {
    "database":    { "status": "healthy",  "responseTimeMs": 5    },
    "redis":       { "status": "healthy",  "responseTimeMs": 1    },
    "externalApi": { "status": "degraded", "responseTimeMs": 2500 }
  }
}
```

### Working Checklist
- [ ] `/live` — zero external dependency checks (pure process liveness)
- [ ] `/ready` — DB ping + Redis ping + critical external deps
- [ ] `/startup` — only if heavy warmup needed
- [ ] Degraded state returns `503`
- [ ] `/health/details` IP-restricted (not public)

---

## 10. Database Foundation

### Connection Pool Configuration & Multi-Pod Budgeting
```
SETTING              VALUE      REASON
──────────────────────────────────────────────────────────────
pool.min             2          Keep warm connections
pool.max             5 - 10     Prevent DB connection starvation
pool.acquireTimeout  30s        Fail fast if pool exhausted
pool.idleTimeout     10m        Release idle connections
connectionTimeout    5s         Initial connect fail fast
queryTimeout         30s        Kill runaway queries
ssl                  true       Always in production
```

#### The Multi-Pod Connection Budget Formula
In containerized architectures (Kubernetes / ECS), every replica runs its own pool:
```
Total Active Connections = (Max Replicas × pool.max)

Invariant: Total Active Connections ≤ (Database max_connections × 0.8)
```
> **Enterprise Standard (PgBouncer / AWS RDS Proxy)**: When running > 10 pods, direct database connections cause CPU and memory thrashing on Postgres/MySQL. Place an external multiplexer (**PgBouncer** in `transaction` mode or **AWS RDS Proxy**) between the application and database. App pods keep small pools (`pool.max: 3–5`), allowing hundreds of pods to share a modest pool of 30–50 real database connections.

### Zero-Downtime Migration Policy: Expand & Contract Pattern
In continuous delivery with rolling deployments, **v1 (old) and v2 (new) pods run concurrently**. Running a destructive DDL migration will instantly crash v1 pods.

```
Phase 1: Expand      → Add new column/table (MUST be NULLABLE or have DEFAULT). Run migration.
Phase 2: Dual-Write  → Deploy app code writing to both OLD and NEW columns, reading from OLD.
Phase 3: Backfill    → Execute background worker/script to copy existing records to NEW column.
Phase 4: Read-New    → Deploy app code reading from NEW column, writing to NEW.
Phase 5: Contract    → Drop OLD column in a subsequent release after verifying stability.
```

#### DDL Lock Safety Rules
```sql
-- 1. Always set lock_timeout to prevent queueing behind long transactions
SET lock_timeout = '2s';

-- 2. Create indexes concurrently (never block table writes in production)
-- Postgres example:
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);

-- 3. Avoid adding columns with non-constant volatile defaults that require table rewrites
```

### Audit Columns — Every Table
```sql
id          UUID / BIGINT        PRIMARY KEY  (UUIDv7 recommended — K-sortable)
created_at  TIMESTAMP NOT NULL   DEFAULT NOW()
updated_at  TIMESTAMP NOT NULL   DEFAULT NOW()  -- auto-update via trigger / ORM hook
deleted_at  TIMESTAMP NULL       -- NULL = active, non-NULL = soft deleted
created_by  UUID / VARCHAR NULL  -- who created this record
updated_by  UUID / VARCHAR NULL  -- who last modified
```

### Index Strategy
```
✅ Primary key (auto)
✅ Foreign key columns (always index foreign keys)
✅ Columns in frequent WHERE clauses
✅ Columns in ORDER BY
✅ Unique constraints (email, username, slug)
✅ Composite indexes for multi-column filters
✅ Partial indexes (WHERE deleted_at IS NULL)

❌ Don't over-index — write performance degrades per index
❌ Use EXPLAIN ANALYZE before adding indexes
```

### Seeder Strategy
```
dev-seed     → Large fake dataset (realistic volume for local dev)
test-seed    → Minimal deterministic data (fixed IDs for integration tests)
prod-seed    → Reference data ONLY (countries, currencies, roles, enums)
               NEVER user/customer data in prod seeders
```

### Transaction Isolation & Locking Strategies

#### Isolation Levels
```
LEVEL                    DIRTY   NON-REPEATABLE  PHANTOM    PRODUCTION USE
                         READS   READS           READS
────────────────────────────────────────────────────────────────────────────
READ UNCOMMITTED         ✅      ✅              ✅         Never use in production
READ COMMITTED (default) ❌      ✅              ✅         Most OLTP operations
REPEATABLE READ          ❌      ❌              ✅         Reports, aggregates
SERIALIZABLE             ❌      ❌              ❌         Financial tx, inventory
```

> **Production Default**: `READ COMMITTED` (Postgres default) for most operations.
> Elevate to `SERIALIZABLE` ONLY for critical financial or inventory transactions.

#### Optimistic Locking — version column (prevents lost updates)
```sql
-- Schema: add version column
ALTER TABLE orders ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- Read:
SELECT id, total_amount, status, version FROM orders WHERE id = $1;

-- Update (check version matches what we read — concurrent update detection):
UPDATE orders
SET status = 'shipped', version = version + 1, updated_at = NOW()
WHERE id = $1
  AND version = $2;   -- Only succeeds if nobody else modified it

-- If rowsAffected = 0 → Concurrent modification → retry or throw ConflictError (409)
```
> **Use when**: Conflicts are RARE (< 5% of operations). E-commerce cart, profile edits.

#### Pessimistic Locking — SELECT FOR UPDATE (prevents concurrent access)
```sql
BEGIN;

-- Lock row exclusively. Other transactions wait until this commits/rolls back.
SELECT * FROM orders WHERE id = $1 FOR UPDATE;
-- FOR UPDATE NOWAIT    → fail immediately if row already locked
-- FOR UPDATE SKIP LOCKED → skip locked rows (queue/job worker pattern)

UPDATE orders SET status = 'processing' WHERE id = $1;

COMMIT;
```
> **Use when**: Conflicts are FREQUENT (> 10% of operations). Payment processing, seat reservation.

#### Deadlock Prevention Rules
```
Rule 1: Always acquire locks in the SAME ORDER across all transactions
  → T1 locks order_items then inventory
  → T2 MUST also lock order_items first — never reverse the order

Rule 2: Keep transactions SHORT
  → Never make external HTTP calls inside a DB transaction
  → Never do slow computation inside a transaction
  → Target: < 100ms per transaction

Rule 3: Set statement_timeout in app DB config
  → Prevents runaway transactions from holding locks indefinitely

Rule 4: Use SKIP LOCKED for worker/job queue patterns
  → Multiple workers pull jobs concurrently without blocking each other
```

#### SKIP LOCKED — Database-Backed Job Queue Pattern
```sql
-- Multiple workers safely pull the next available job without blocking each other
SELECT * FROM scheduled_jobs
WHERE status = 'pending'
  AND scheduled_at <= NOW()
ORDER BY priority DESC, scheduled_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

### Read Replica Routing

#### Connection Strategy
```
Primary (Writer) — Route ALL writes here:
  → INSERT, UPDATE, DELETE operations
  → Transactions spanning multiple reads + writes
  → Reads that must see the latest committed data immediately

Read Replicas — Route read-heavy queries here:
  → Heavy SELECT queries (analytics, reports, listing pages)
  → Operations that tolerate 100–500ms replication lag
  → NEVER: Auth operations (session lookup, token verification)
  → NEVER: Reads immediately after writing the same record
```

#### Read-After-Write Consistency Problem
```
Problem:
  User updates profile → Write routes to PRIMARY
  Immediate GET /profile → Routes to REPLICA
  Replica has 200ms replication lag → User sees OLD data
  → "My change didn't save!" complaint

Solutions:
  Option 1: Route reads to PRIMARY for 2s after any write (per-user sticky routing)
  Option 2: Always read profile/settings from PRIMARY — replica only for listings
  Option 3: Wait for replica WAL LSN to catch up before routing read there
```

#### Replication Lag Monitoring
```
Metric: replication_lag_seconds (per replica)

Alert thresholds:
  WARNING:  lag > 10 seconds
  CRITICAL: lag > 30 seconds → stop routing reads to that replica

Automatic failover:
  Primary fails → replica promoted → app reconnects automatically
  Tools: RDS Multi-AZ (managed automatic), Patroni (self-managed Postgres HA)
```

#### Pool Configuration
```
primaryPool:
  connectionString: process.env.DATABASE_URL           ← Read/Write
  pool: { min: 2, max: 5 }

replicaPool:
  connectionString: process.env.DATABASE_REPLICA_URL   ← Read-Only
  pool: { min: 2, max: 10 }   ← Larger pool, more read concurrency
```

#### Read Replica Checklist
- [ ] Read replica routing configured (writes → primary, heavy reads → replica)
- [ ] `DATABASE_REPLICA_URL` in `.env.example` with descriptive comment
- [ ] Replication lag metric tracked — alert at 10s (WARN) and 30s (CRITICAL)
- [ ] Profile/settings reads hardcoded to primary (avoid read-after-write bugs)
- [ ] Replica removed from rotation automatically when lag threshold exceeded

### Working Checklist
- [ ] Connection pool sizing budgeted against total pod autoscale limit
- [ ] External connection pooler (PgBouncer / RDS Proxy) configured for horizontal workloads
- [ ] Migration files versioned, idempotent, and committed to git
- [ ] Expand-and-Contract protocol enforced for all schema changes
- [ ] DDL scripts set `lock_timeout = '2s'` and use `CREATE INDEX CONCURRENTLY`
- [ ] Rollback migration for every forward migration
- [ ] Audit columns on every table (UUIDv7 recommended)
- [ ] Slow query logging — queries > 200ms logged at WARN level
- [ ] Foreign keys indexed
- [ ] Soft delete pattern (never hard delete user data)

### Gotchas
- ❌ Never: Rename or drop a column in a single migration while older app pods are running
- ❌ Never: Connect 50+ pods directly to Postgres without an intermediate pooler (PgBouncer/RDS Proxy)
- ❌ Never: Run DDL without a short `lock_timeout` — table locks will queue incoming SELECT queries and crash the app

---

## 11. Caching & In-Memory Store

### Caching Layers
```
Layer 1: In-process cache (L1)
  → Inside app process memory (nanoseconds)
  → Lost on restart — static data only
  → MUST set max-size + TTL (prevent memory leak)

Layer 2: Distributed cache (L2) — Redis / Memcached
  → Shared across all app instances (sub-millisecond)
  → Survives app restarts
  → Use for: sessions, rate limiting, expensive query results
```

### Cache Key Convention
```
Pattern:  {service}:{entity}:{identifier}:{version}
Examples:
  user:profile:usr_abc123:v1
  order:list:usr_abc123:page:2:size:20
  rate-limit:ip:192.168.1.1
```

### Cache Invalidation Strategies
```
TTL (Time-To-Live):
  → Automatic expiry after N seconds
  → Risk: stale data for TTL duration
  → Good for: semi-static data (product catalog, config)

Write-Through:
  → Update cache + DB simultaneously on every write
  → Always fresh
  → Good for: user profiles (read-heavy, write-occasional)

Cache-Aside (Lazy Loading):
  → Check cache → miss → load from DB → write to cache
  → Most common pattern
  → Risk: thundering herd on cold start

Event-Driven Invalidation:
  → Data change event → delete/update cache keys
  → Most precise — zero stale data
  → Requires event bus
```

### Cache Stampede Prevention
```
Problem: Hot key expires → 1000 concurrent requests hit DB simultaneously

Solutions:
  1. Mutex / Lock:
     → First request gets lock → fetches from DB → populates cache
     → Others wait → get cached result after lock release

  2. Probabilistic Early Expiration:
     → Re-compute cache slightly before actual TTL expiry
     → Proactively prevents thundering herd
```

### Redis Usage Patterns
```
Sessions:          SETEX session:{id} 3600 {data}
Rate limiting:     INCR + EXPIRE (sliding window counter)
Pub/Sub:           PUBLISH / SUBSCRIBE (real-time notifications)
Job queue:         LPUSH jobs:{name} {payload} / BRPOP (blocking pop)
Distributed lock:  SET lock:{resource} {token} NX EX 30  (Redlock)
Leaderboard:       ZADD / ZREVRANGE (sorted sets)
Feature flags:     HSET / HGET (hash maps)
```

### Working Checklist
- [ ] Cache-aside abstraction (get/set/invalidate interface)
- [ ] Every cached key has a TTL — no zombie keys
- [ ] Cache stampede prevention for high-traffic keys
- [ ] Redis connection with retry + cluster support
- [ ] Cache hit/miss rates tracked as metrics
- [ ] App degrades gracefully if cache is unavailable (fallback to DB)
- [ ] Sensitive data never cached unencrypted
- [ ] Never cache auth tokens

---

## 12. Asynchronous Jobs & Event Processing

### Philosophy
> Heavy operations (email, PDF, notifications, 3rd-party sync) must NEVER run inside HTTP request lifecycle.

### Architecture
```
HTTP Request
  └── Route Handler
        └── Enqueue job → respond 202 Accepted immediately

Message Queue (RabbitMQ / SQS / Kafka / Redis Streams)
  └── Worker / Consumer Process
        ├── Process job
        ├── On success → mark done / publish event
        └── On failure → retry with backoff → Dead Letter Queue (DLQ)
```

### Retry Strategy
```
Attempt 1  → fail → wait 1s
Attempt 2  → fail → wait 2s (exponential)
Attempt 3  → fail → wait 4s
Attempt 4  → fail → wait 8s + random jitter
Attempt N  → all retries exhausted → move to DLQ → alert team
```

### Working Checklist
- [ ] Queue producer abstraction (HTTP handler decoupled from queue implementation)
- [ ] Worker is a separate process (not the HTTP server process)
- [ ] Retries with exponential backoff + random jitter
- [ ] Dead Letter Queue (DLQ) for unrecoverable failures
- [ ] DLQ depth monitored — alert when growing
- [ ] Idempotent consumers — duplicate message delivery must not corrupt state
- [ ] Job schema versioned (consumers handle old + new formats during rolling deploys)
- [ ] Queue depth tracked as a metric

### Gotchas
- ❌ Never send email / generate PDF inside HTTP handler — user timeout risk
- ❌ Consumer without idempotency → duplicate job = double email / double charge
- ✅ Store job status in DB — client can poll for result

---

## 13. Resilience & Fault Tolerance

### Philosophy
> When external dependencies fail, your service must degrade gracefully — not cascade-fail.

### Pattern 1: Strict Timeouts on All I/O
```
Every external call MUST have an explicit timeout:
  DB queries:          5000ms
  Redis calls:         1000ms
  External HTTP APIs:  connectTimeout: 2000ms, readTimeout: 5000ms
  Message broker:      ackTimeout: 10000ms

Without timeout → one slow dependency → threads exhausted → full service down.
```

### Pattern 2: Retry with Exponential Backoff + Jitter
```
function callWithRetry(operation, maxAttempts):
    for attempt in 1..maxAttempts:
        try:
            return operation()
        catch TransientError:
            if attempt == maxAttempts: throw
            delay = min(baseDelay * 2^attempt, maxDelay)
            jitter = random(0, delay * 0.1)    # ±10% prevents thundering herd
            sleep(delay + jitter)
```

### Pattern 3: Circuit Breaker
```
States:
  CLOSED   → Normal. All requests pass through.
  OPEN     → Failure threshold exceeded. All requests FAIL FAST (no calls to downstream).
  HALF-OPEN → After cooldown. Test one request. Success → CLOSED. Fail → OPEN again.

Why: Without circuit breaker → failing downstream gets hammered → delays cascade upstream.
```

### Pattern 4: Idempotency Keys
```
Problem: POST /payments retried by client → double charge!

Solution:
  Client sends:  Idempotency-Key: <client-uuid>
  Server:
    1. Has this key been processed? → return stored response (no re-processing)
    2. If new → process + store response with key (TTL: 24h)
```

### Pattern 5: Request Abort & Cancellation Propagation
```
Problem:
A user navigates away, closes the tab, or the upstream API gateway (Cloudflare/ALB) times out at 15s.
Default backend behavior: The server continues executing heavy SQL queries, parsing payloads, and calling downstream APIs for another 30 seconds.
Result: Zombie execution burns database connection pool slots, thread pools, and CPU on dead sockets.

Solution:
Propagate the incoming HTTP request's cancellation signal down the entire call stack:
  - Node.js: Pass `req.signal` (standard AbortSignal) directly to ORMs, DB drivers, and `fetch()`
  - Go: Pass `r.Context()` to `db.QueryContext(ctx, ...)` and `http.NewRequestWithContext(ctx, ...)`
  - Java / Spring: Utilize reactive cancellations (WebFlux) or async `DeferredResult.onTimeout()`
  - .NET: Pass `HttpContext.RequestAborted` (`CancellationToken`) to EF Core and HttpClient
```

### Working Checklist
- [ ] Strict timeouts on every DB, cache, external HTTP, message broker call
- [ ] Retry with exponential backoff + jitter for transient failures
- [ ] Circuit breaker for all downstream service calls
- [ ] Idempotency keys for all mutating (POST, PUT, DELETE) endpoints
- [ ] Client cancellation signals (`AbortSignal` / `Context`) propagated to DB queries and HTTP calls
- [ ] Fallback behavior defined for each dependency failure (degraded mode)

### Gotchas
- ❌ Never ignore client disconnects: uncancelled queries run as zombies and starve the database pool
- ❌ Never retry non-idempotent operations without an idempotency key (risk of double charging/duplicate records)

---

## 14. Authentication & Authorization

### Authentication Flow (JWT)
```
LOGIN:
  1. Validate email + password (rate limit: 5/min per IP)
  2. Verify password hash (Argon2id / bcrypt — cost ≥ 12)
  3. Generate access_token  (short-lived: 15 minutes)
  4. Generate refresh_token (long-lived: 7 days)
  5. Store refresh_token in DB (hashed) + device metadata
  6. Set refresh_token → HTTP-Only Secure SameSite=Strict cookie
  7. Return access_token in response body

AUTHENTICATED REQUEST:
  1. Extract Bearer token from Authorization header
  2. Verify signature (RS256 preferred — JWKS endpoint for multi-service)
  3. Check expiry
  4. Attach decoded user + tenant context to request

TOKEN REFRESH:
  1. Read refresh_token from HTTP-Only cookie
  2. Verify against hashed value in DB
  3. Rotate: invalidate old → issue new pair
  4. Detect reuse (sign of token theft → invalidate ALL sessions)

LOGOUT:
  1. Invalidate refresh_token in DB
  2. Clear HTTP-Only cookie
  3. Add access_token to blacklist (until natural expiry)
```

### Authorization Models
```
RBAC (Role-Based Access Control):
  User → Roles → Permissions
  Roles: ADMIN, MANAGER, USER, VIEWER
  Good for: most applications

ABAC (Attribute-Based Access Control):
  Policy: user.department == resource.department
  Good for: complex multi-tenant / government systems

Resource Ownership:
  Always verify: resource.ownerId === currentUser.id
```

### Working Checklist
- [ ] Password hash: Argon2id / bcrypt (cost ≥ 12)
- [ ] access_token → response body (15m)
- [ ] refresh_token → HTTP-Only Secure SameSite=Strict cookie only
- [ ] Refresh token rotation on every use
- [ ] Refresh token reuse detection → invalidate all sessions
- [ ] Token blacklist for immediate revocation (Redis with expiry)
- [ ] JWKS endpoint for public key rotation (multi-service)
- [ ] Rate limit auth endpoints (login: 5/min, register: 10/hour, reset: 3/hour)
- [ ] RBAC / ABAC enforced at route level + service level

### Gotchas
- ❌ NEVER store tokens in localStorage → XSS vulnerable
- ❌ NEVER use HS256 in multi-service → shared secret leak risk
- ❌ Long-lived access tokens (hours/days) → can't revoke if compromised

---

## 15. Security Baseline

### HTTP Security Headers
```
Content-Security-Policy      → Prevent XSS, clickjacking
Strict-Transport-Security    → Force HTTPS for 1 year (HSTS)
X-Frame-Options: DENY        → Prevent iframe embedding
X-Content-Type-Options: nosniff → Prevent MIME-type sniffing
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy           → Disable unused browser features
```

### CORS Policy
```
✅ Explicit origin whitelist (never * with credentials: true)
✅ Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
✅ credentials: true only when cookies needed
✅ Preflight cache: 600s
```

### Rate Limiting (Concrete Values)
```
ENDPOINT TYPE               LIMIT         WINDOW     STRATEGY
──────────────────────────────────────────────────────────────────────
Auth / Login                5 requests    1 minute   IP-based (strict)
Auth / Register             10 requests   1 hour     IP-based
Password Reset              3 requests    1 hour     IP-based
API (authenticated users)   1000 requests 1 minute   User ID-based
API (public / anonymous)    100 requests  1 minute   IP-based
File Upload                 10 requests   1 minute   User ID-based
```

### SQL Injection Prevention
```
✅ Parameterized queries / prepared statements
✅ ORM query builders only
❌ NEVER: "SELECT * FROM users WHERE email = '" + email + "'"
```

### XSS Prevention
```
✅ Escape all user-controlled output in HTML context
✅ Content-Security-Policy header
✅ HttpOnly cookies (JS cannot read tokens)
✅ Sanitize rich text with HTML whitelist (DOMPurify equivalent)
```

### CSRF Protection
```
JSON APIs (Authorization header):  → Not vulnerable (SOP protects)
Session-based web apps:            → Required
  ✅ SameSite=Strict cookies (best — modern browsers)
  ✅ Double-submit cookie pattern (fallback)
```

### Password Security
```
Algorithm: Argon2id (preferred) OR bcrypt (cost ≥ 12)
NEVER:     MD5, SHA1, SHA256 (not password hashing algorithms)
NEVER:     Plaintext or reversible encryption
```

### Request Size Limits
```
JSON body:      1MB   (413 Payload Too Large)
File upload:    10MB  (separate dedicated endpoint)
URL length:     2048 chars
Header size:    8KB
```

### Secret Management
```
Development:  .env file (gitignored)
CI/CD:        GitHub Secrets / GitLab CI Variables
Production:   AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager
NEVER:        Hardcoded in source, Dockerfile, or test files
```

### Working Checklist
- [ ] All security headers via middleware
- [ ] CORS origin whitelist enforced (no wildcard with credentials)
- [ ] Rate limiting per endpoint type with concrete limits
- [ ] SQL injection: zero string concatenation in queries
- [ ] XSS: HTML output sanitized, CSP configured
- [ ] CSRF protection for session-based endpoints
- [ ] Password hashing: Argon2id / bcrypt (cost ≥ 12)
- [ ] Request size limits enforced
- [ ] Secrets via Secrets Manager — never hardcoded

---

## 16. API Documentation & Contracts

### OpenAPI / Swagger Standards
```
Format:  OpenAPI 3.x
Approach: Code-first (annotations) OR design-first (spec → generate)

Document per endpoint:
  ✅ Path, method, description, tags
  ✅ Request body schema with working examples
  ✅ All response schemas (success + all error cases)
  ✅ Authentication requirement
  ✅ Rate limit information
  ✅ Deprecation notice

Endpoints:
  GET /docs              → Interactive UI (Swagger UI / Scalar / Redoc)
  GET /docs/openapi.json → Raw OpenAPI spec
  (Disable in production or IP-restrict)
```

### Contract Testing
```
Problem: Backend API silently breaks frontend / mobile / microservice contracts.

Solution: Consumer-Driven Contract Tests (Pact framework)
  → Consumer defines expected API shape
  → Provider verifies it in their test suite
  → CI/CD blocks merge if contract violated
```

### Working Checklist
- [ ] OpenAPI 3.x spec auto-generated from code
- [ ] Interactive sandbox in dev/staging
- [ ] All error response schemas documented
- [ ] Contract tests for all critical API consumers
- [ ] CHANGELOG.md updated every release
- [ ] Postman collection committed to repo

---

## 17. Testing Pyramid Baseline

### Testing Pyramid
```
                    /\
                   /  \
                  / E2E \           → 10% (expensive, slow, flaky risk)
                 /--------\
                / Integration\      → 30% (real DB via Testcontainers, real HTTP)
               /--------------\
              /   Unit Tests    \   → 60% (fast, isolated, mocked)
             /──────────────────\
```

### Unit Tests
```
Target:   Service layer, utilities, validation, data transformations
Rules:
  ✅ Zero external I/O — mock everything (DB, cache, HTTP, queues)
  ✅ One assertion focus per test
  ✅ Deterministic — fixed seeds, no random data
  ✅ < 1ms execution per test
  ✅ Coverage: Lines ≥ 80%, Branches ≥ 75%
```

### Integration / Functional Tests
```
Target: Full HTTP → DB → response cycle
Tools:  Testcontainers (real Postgres + Redis in Docker — no mocks)
Setup:
  ✅ Separate test database
  ✅ Run migrations before test suite
  ✅ Seed minimal deterministic data (fixed IDs)
  ✅ Wrap each test in transaction → rollback after (isolation)
  ✅ Test: auth flows, error shapes, middleware behavior
```

### Smoke Tests
```
Run: After every deployment to staging AND production
  ✅ /health/ready returns 200
  ✅ Critical user journey (login → fetch data → logout)
  ✅ Auth endpoint returns correct error format
```

### Performance Tests
```
Tools: k6 / Locust / Artillery / Gatling

Test Types:
  Load test    → Normal expected traffic (baseline)
  Stress test  → 2-5x peak traffic (find breaking point)
  Spike test   → Sudden traffic burst
  Soak test    → Sustained load over hours (memory leak detection)

SLA Targets (define BEFORE testing):
  p50 latency   < 50ms
  p95 latency   < 200ms
  p99 latency   < 500ms
  Error rate    < 0.1%
```

### Working Checklist
- [ ] Unit test suite (mock all I/O — fast and isolated)
- [ ] Integration tests with Testcontainers (real DB + Redis)
- [ ] Smoke tests for post-deployment verification
- [ ] Performance baseline with k6 / Locust
- [ ] Coverage thresholds enforced in CI (≥ 80% lines, ≥ 75% branches)
- [ ] Tests deterministic — no order-dependent or time-dependent failures

---

## 18. Graceful Shutdown

### The Kubernetes SIGTERM Race Condition
In Kubernetes and modern cloud orchestrators, **pod termination is asynchronous across control planes**:
```
Kubelet sends SIGTERM to Pod ──────────────┐ (Simultaneous)
                                           ▼
Endpoints controller updates iptables ─────┴─► Takes 2–5 seconds across cluster nodes!
```
> **The 502 Outage Pitfall**: If your app immediately stops accepting connections or closes sockets upon receiving `SIGTERM`, clients whose requests were routed by the load balancer during those 2–5 seconds will receive `502 Bad Gateway` or `ECONNRESET`.

#### Zero-Downtime Termination Strategy
1. **K8s `preStop` Hook**: Configure a container lifecycle `preStop` sleep (5–10 seconds) so Kube-proxy can drain iptables BEFORE the app receives SIGTERM:
```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 5"]
```
2. **Application Drain Window**: Maintain active HTTP listening for 5 seconds post-SIGTERM while marking `/ready` as 503, ensuring in-flight and newly arrived packets are cleanly serviced.

### Shutdown Sequence (Zero-Downtime Budget)
```
SIGTERM / SIGINT received:
  1. Mark /ready → 503             (Informs probes; keep HTTP listener OPEN)
  2. Wait 5 seconds (drain delay)  (Allows Ingress / kube-proxy iptables to propagate)
  3. Stop accepting new HTTP connections (server.close())
  4. Wait for in-flight requests to complete (grace timeout: 20s)
  5. Stop consuming from message queues (pause consumer groups)
  6. Flush pending metrics, spans & traces to OpenTelemetry collector
  7. Flush structured logger buffers
  8. Close DB connection pool (drain active pool connections)
  9. Close Redis / cache connections
  10. Log "Shutdown complete. Uptime: {N}s"
  11. process.exit(0)
```
*Budget Check*: `preStop (5s) + Drain (5s) + In-flight (20s) = 30s ≤ terminationGracePeriodSeconds (35s)`.

### Working Checklist
- [ ] SIGTERM + SIGINT both handled with non-zero exit handlers
- [ ] Kubernetes `preStop` hook (`sleep 5`) configured in deployment manifest
- [ ] 5-second drain window observed before closing HTTP listener
- [ ] Load balancer informed (mark `/ready` → 503) immediately upon SIGTERM
- [ ] In-flight requests given explicit grace period (≤ 20s)
- [ ] All connections closed cleanly in order (Queues → HTTP → Traces/Logs → DB/Cache)
- [ ] Logs and OpenTelemetry batches flushed before process termination
- [ ] Exit code 0 on clean shutdown, 1 on uncaught crash

### Gotchas
- ❌ Immediately closing HTTP server on SIGTERM → causes intermittent 502 Bad Gateway errors during deploys
- ❌ App grace period > K8s `terminationGracePeriodSeconds` → Kubelet will brutally SIGKILL the process mid-request
- ❌ Not flushing logger and OpenTelemetry buffers before `process.exit(0)` → lose critical post-mortem crash logs

---

## 19. Code Quality, DevEx & Tooling

### Automated Tools
```
Linting:
  Node.js / TS  → ESLint + typescript-eslint (strict)
  Python        → Ruff / Flake8
  Go            → golangci-lint
  Java          → Checkstyle / SpotBugs
  .NET          → Roslyn Analyzers

Auto-Formatting (zero style debates):
  Node.js / TS  → Prettier
  Python        → Black / Ruff format
  Go            → gofmt (built-in)
  Java          → google-java-format

Type Safety:
  TypeScript    → strict: true (no any, no exceptions)
  Python        → mypy / pyright (strict mode)
  Go / Rust     → statically typed at compile time

Security Scanning:
  Dependencies  → Trivy / Snyk / OWASP Dependency-Check / Dependabot
  Secrets       → GitLeaks / TruffleHog (block commits with secrets)
```

### Pre-commit Hooks (Mandatory)
```
On every commit:
  1. Linter → reject if errors
  2. Formatter check → reject if unformatted
  3. Type checker → reject if type errors
  4. Commit message lint (Conventional Commits format)
  5. Secret scanner → block if secrets detected
```

### Conventional Commit Format
```
<type>(<scope>): <description>

Types: feat | fix | docs | refactor | test | chore | perf | ci

Examples:
  feat(auth): add JWT refresh token rotation
  fix(order): prevent negative quantity in cart
  docs(api): update OpenAPI spec for /users endpoint
```

### Working Checklist
- [ ] One-command local setup: `docker compose up` → DB, Redis, Queue all running
- [ ] Linting + formatting configured and enforced
- [ ] Type checker in strict mode
- [ ] Pre-commit hooks blocking on violations
- [ ] SAST dependency scanning in CI
- [ ] Secret scanning in CI (block PRs with hardcoded secrets)
- [ ] Conventional commits enforced via commit-msg hook

---

## 20. CI/CD & Build Infrastructure

### CI Pipeline (Every Pull Request)
```
Trigger: PR opened / commit pushed

Steps (all must pass — PR blocked if any fail):
  1. Lint check
  2. Format check
  3. Type check
  4. Unit tests + coverage report
  5. Integration tests (Testcontainers)
  6. SAST security scan (dependency audit)
  7. Secret scan
  8. Build Docker image
  9. Image vulnerability scan (Trivy)
  10. Push image to registry (on merge to main only)
```

### Dockerfile — Multi-Stage (Minimal Attack Surface)
```dockerfile
# Stage 1: Build
FROM language-sdk:version AS builder
WORKDIR /app
COPY {lockfile} {manifest} ./
RUN install production dependencies (frozen lockfile)
COPY src/ ./src/
RUN build / compile

# Stage 2: Production runtime (minimal image)
FROM language-runtime:alpine AS production
WORKDIR /app
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER appuser          # NEVER run as root in production
EXPOSE 3000
CMD ["./entrypoint"]
```

### Image Versioning
```
✅ {git-sha}        → Immutable, traceable (prod deploys)
✅ {semver}         → Release tags (e.g., myapp:2.4.1)
❌ latest           → NEVER use in production (unpredictable)
```

### Working Checklist
- [ ] CI pipeline runs on every PR commit
- [ ] All steps must pass before merge allowed
- [ ] Multi-stage Dockerfile (builder + minimal runtime)
- [ ] Non-root user in production container
- [ ] Image vulnerability scanned (Trivy / Snyk)
- [ ] Images tagged with git SHA (immutable)
- [ ] Frozen lockfile installs in CI

---

## 21. Documentation Architecture

### README.md (5-Minute Quick Start — Mandatory)
```markdown
# Project Name
One-sentence description of what this service does.

## Prerequisites
- Runtime version (e.g., Node.js 20+, Python 3.12+, Go 1.22+)
- Docker + Docker Compose
- Package manager (pnpm / pip / go)

## Quick Start
  git clone ...
  cp .env.example .env
  docker compose up -d    # Starts DB, Redis, Queue
  {install dependencies}
  {run migrations}
  {optional: seed dev data}
  {start dev server}

## Running Tests
## Project Structure
## Contributing
## License
```

### docs/ Structure
```
docs/
├── architecture.md      → System design, layer diagram, data flow, decisions
├── development.md       → Local dev setup, debugging tips, useful commands
├── testing.md           → Running tests, coverage targets, test data strategy
├── deployment.md        → Environment topology, deployment steps, rollback
├── database.md          → ER diagram, migration guide, indexing conventions
└── troubleshooting.md   → Common production errors, FAQs, incident runbooks
```

### Working Checklist
- [ ] README enables new developer to run project in < 5 minutes
- [ ] Architecture diagram in `docs/architecture.md` (Mermaid / draw.io)
- [ ] CHANGELOG.md maintained per release
- [ ] API collection (Postman / Insomnia) committed to repo
- [ ] All docs reviewed before first production deployment

---

## 22. Scheduled Jobs & Cron Tasks

### Philosophy
> Scheduled jobs are NOT the same as event-driven queue jobs. Cron fires on time. Queues fire on events. Confusing them leads to missed executions, duplicate runs, and timezone bugs.

### Event-Driven vs Scheduled — Key Difference
```
Event-Driven Jobs (§12):
  Trigger: Something happened (user registered, payment received)
  Pattern: Enqueue → Worker processes → Done
  Tools:   BullMQ, SQS, RabbitMQ, Kafka

Scheduled / Cron Jobs:
  Trigger: Time-based (every day at 2am, every 5 minutes)
  Pattern: Cron expression → Leader acquires lock → Execute
  Tools:   pg-boss, BullMQ cron, Quartz (Java), APScheduler (Python), Hangfire (.NET)
```

### Cron Expression Reference
```
┌──────────── Minute (0–59)
│  ┌─────────── Hour (0–23)
│  │  ┌────────── Day of Month (1–31)
│  │  │  ┌───────── Month (1–12)
│  │  │  │  ┌────── Day of Week (0–7, Sunday=0 or 7)
│  │  │  │  │
*  *  *  *  *

Examples:
  0 2 * * *     → Every day at 2:00 AM
  */5 * * * *   → Every 5 minutes
  0 9 * * 1-5  → 9:00 AM, Monday to Friday
  0 0 1 * *    → First day of every month at midnight
```

### Critical Problem: Duplicate Execution Across Pods
```
Problem:
  3 app pods running → ALL 3 trigger the same cron at 2:00 AM
  → 3x subscription renewal emails to every user!
  → 3x cleanup jobs running simultaneously → race condition + data corruption

Solution — Distributed Lock (Leader Election per execution):
  1. Before executing: acquire distributed lock (Redis SET NX EX)
  2. Only ONE pod gets the lock → executes the job
  3. Others get lock-denied → skip silently (log at DEBUG level)
  4. Lock auto-expires (TTL = job max expected duration + 10s buffer)

Never assume single-instance — always code for distributed execution.
```

### Distributed Cron Lock Pattern (Pseudocode)
```
function runScheduledJob(jobName, jobFn, maxExecutionMs):
    lockKey = "cron-lock:{jobName}"
    lockTtl = maxExecutionMs + 10_000   # 10s buffer

    acquired = redis.SET(lockKey, instanceId, NX, EX, lockTtl / 1000)
    if NOT acquired:
        logger.debug({ jobName, event: 'cron_lock_skipped' })
        return   # Another pod is already running this job

    try:
        logger.info({ jobName, event: 'cron_job_started' })
        startTime = now()
        await jobFn()
        durationMs = now() - startTime
        logger.info({ jobName, event: 'cron_job_completed', durationMs })
        metrics.increment('cron_jobs_completed_total', { jobName })
        db.updateLastRunAt(jobName, now())   # For missed job detection
    catch error:
        logger.error({ jobName, event: 'cron_job_failed', error })
        metrics.increment('cron_jobs_failed_total', { jobName })
        alertOnCallTeam(error, jobName)
    finally:
        redis.DEL(lockKey)   # Release lock early on completion
```

### Cron Job Health Monitoring
```
Track per job:
  last_run_at            → Timestamp of last successful completion
  last_duration_ms       → Execution time of last run
  consecutive_failures   → Count of consecutive failures

Alert conditions:
  🚨 Job not run in > (2 × schedule interval) → MISSED JOB \u2014 page on-call
  🚨 Duration > (3 × historical average)       → SLOW JOB \u2014 Slack alert
  🚨 Consecutive failures > 3                  → CRITICAL \u2014 page on-call
```

### Missed Job Handling
```
Problem: App was down during scheduled execution → job never ran

Strategy by criticality:
  Low:    Accept the miss, wait for next schedule (e.g., analytics aggregation)
  Medium: On startup, check last_run_at → if missed, run immediately (e.g., daily email)
  High:   Use DB-backed scheduler (pg-boss) that persists schedule state
          → Survives pod restarts. Guarantees at-least-once execution.
```

### Timezone Gotchas
```
❌ NEVER use system timezone (varies per host, changes with OS updates)
✅ ALWAYS configure explicit timezone (UTC strongly recommended for cron)
✅ Business-time jobs (e.g., "9am user's time") → store user timezone, convert at runtime
✅ Test DST transitions \u2014 clocks "spring forward/fall back" can cause double-fire or skip
```

### Tools by Language
```
Node.js / TypeScript  → pg-boss (DB-backed, distributed), BullMQ cron, node-cron
Python                → APScheduler, Celery beat, rq-scheduler
Go                    → robfig/cron (v3), gocron
Java                  → Quartz Scheduler + ShedLock, Spring @Scheduled
.NET                  → Hangfire, Quartz.NET
Infrastructure        → Kubernetes CronJob (for heavy standalone tasks)
```

### Working Checklist
- [ ] Distributed lock (Redis NX) preventing duplicate cron execution across pods
- [ ] Every cron job: structured log on start, completion, and failure (with duration)
- [ ] `last_run_at` tracked in DB \u2014 enables missed job detection
- [ ] Cron jobs registered in a central registry (not scattered across codebase)
- [ ] Failed jobs trigger on-call alert after 3 consecutive failures
- [ ] All cron expressions use explicit UTC timezone
- [ ] Long-running cron tasks run as Kubernetes CronJob (not inside HTTP server process)
- [ ] Config-driven schedule \u2014 cron expression from env var, not hardcoded

### Gotchas
- ❌ Never run heavy cron jobs inside the HTTP server process \u2014 blocks request handling
- ❌ No distributed lock → duplicate execution across pods → duplicate emails / double charges
- ❌ Hardcoded schedule string in code → can't override without redeploy
- ❌ DST timezone bugs cause midnight cron to fire at 11pm or 1am in certain months

---

## 23. File Upload & Storage Architecture

### Philosophy
> The backend MUST NOT be the throughput bottleneck for file uploads. Clients upload directly to object storage. Backend only handles metadata validation and pre-signed authorization.

### Architecture: Pre-Signed URL Pattern (Mandatory)
```
❌ WRONG — file bytes flow through your server:
  Client → POST /upload → Backend (buffering file) → S3
  Problem: Memory spike, bandwidth cost, throughput ceiling at your pod count

✅ CORRECT — Pre-Signed URL (client uploads directly to S3):
  Step 1: Client → POST /api/v1/files/upload-url { filename, mimeType, fileSize }
  Step 2: Backend → Validate metadata → Generate pre-signed PUT URL → Return { uploadUrl, fileKey }
  Step 3: Client → PUT {uploadUrl} directly to S3 (bypasses backend entirely)
  Step 4: Client → POST /api/v1/files/confirm { fileKey } → Backend records metadata in DB
  Step 5: S3 event → Lambda/webhook → Virus scan trigger
```

### File Metadata DB Schema
```sql
CREATE TABLE file_uploads (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_key        VARCHAR NOT NULL UNIQUE,     -- S3 object key
  bucket          VARCHAR NOT NULL,
  original_name   VARCHAR NOT NULL,
  mime_type       VARCHAR NOT NULL,
  file_size       BIGINT NOT NULL,             -- bytes
  status          VARCHAR NOT NULL DEFAULT 'pending',
                                               -- pending | confirmed | quarantined | deleted
  uploaded_by     UUID NOT NULL REFERENCES users(id),
  entity_type     VARCHAR,                     -- 'user_avatar' | 'invoice' | 'product_image'
  entity_id       UUID,
  cdn_url         VARCHAR,                     -- populated after CDN distribution
  virus_scan_status VARCHAR DEFAULT 'pending', -- pending | clean | infected
  created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  confirmed_at    TIMESTAMP,
  deleted_at      TIMESTAMP
);
```

### File Type Validation — Magic Bytes (Not Just Extension)
```
❌ WRONG: Check file extension only
  Attacker renames malware.exe → photo.jpg → extension check passes → malware stored!

✅ CORRECT: Validate magic bytes (file signature)
  Read first N bytes of file content → compare against known signatures

Common magic bytes:
  JPEG:  FF D8 FF
  PNG:   89 50 4E 47 0D 0A 1A 0A
  PDF:   25 50 44 46 2D
  GIF:   47 49 46 38
  ZIP:   50 4B 03 04
  EXE:   4D 5A (MZ header) → ALWAYS reject, regardless of extension

Tools: file-type (Node.js), python-magic (Python), Apache Tika (Java)
```

### Virus Scanning Strategy
```
Scan AFTER upload to S3, BEFORE serving to any user.

Options:
  AWS Macie / GCS DLP   → Cloud-native managed, no ops overhead
  ClamAV on Lambda      → Open-source, triggered by S3 event notification
  VirusTotal API        → Multi-engine scan, rate-limited free tier

Flow:
  Upload confirms → S3 triggers Lambda → ClamAV scans
    Clean:    UPDATE status = 'clean', generate CDN URL
    Infected: UPDATE status = 'quarantined', delete from S3, alert security team
    Pending:  User receives "file is processing" until scan completes
```

### CDN Serving Strategy
```
Private files (user documents, invoices, medical records):
  ❌ NEVER expose direct S3 URL — auth check is bypassed entirely
  ✅ Generate time-limited signed CDN URL per request
     Expiry: 1 hour for view, 24 hours for download
     Invalidate signed URL immediately on permission change

Public files (product images, avatars, logos):
  ✅ S3 + CloudFront / Cloudflare CDN (permanent public URL)
  ✅ Cache-Control: public, max-age=31536000, immutable
     (content-hash suffix in filename ensures cache busting on update)
```

### Upload Limits
```
Avatar images:    2MB max
Documents:        20MB max
Video:            500MB max (use S3 multipart API for > 5MB)
Total per user:   Enforce quota in DB (prevent storage abuse)

Multipart upload threshold: > 5MB → use S3 multipart API (resumable)
```

### Working Checklist
- [ ] Pre-signed URL pattern \u2014 file bytes never pass through app server
- [ ] File metadata stored in DB with `status: pending → confirmed` lifecycle
- [ ] Magic byte validation before issuing pre-signed URL
- [ ] Virus scan triggered on every upload (ClamAV / AWS Macie)
- [ ] Users cannot access files until `virus_scan_status = 'clean'`
- [ ] Private files served via time-limited signed CDN URLs (never raw S3 URLs)
- [ ] Public files served via CDN with immutable cache headers
- [ ] Per-user storage quota enforced at upload-url generation step
- [ ] File size limits enforced at app level AND via S3 bucket policy
- [ ] Orphaned file cleanup cron job (pending status > 24h → delete from S3)

### Gotchas
- ❌ Raw S3 URLs for private files = auth bypass \u2014 anyone with the URL can access
- ❌ Extension-only validation = trivially bypassed by renaming malicious files
- ❌ Uploading large files through the backend = memory exhaustion under concurrent load
- ❌ No virus scan = malware stored in your infrastructure, served to other users

---

## 24. Alerting, SLO & On-Call Strategy

### Philosophy
> Metrics without alerts = a dashboard nobody watches. Alerts without runbooks = an on-call engineer guessing at 3am.

### SLI / SLO / SLA — Definitions
```
SLI (Service Level Indicator):
  A measurable metric reflecting service health.
  Example: "HTTP 5xx error rate over 1-hour rolling window"

SLO (Service Level Objective):
  Internal target for an SLI. You own this, customers don't see it.
  Example: "5xx error rate < 0.1% over any rolling 30-day window"

SLA (Service Level Agreement):
  Contractual commitment to customers. Always set BELOW SLO (buffer for recovery).
  Example: "99.9% uptime" (SLA) when internal SLO = 99.95%

Error Budget:
  SLO = 99.9% → Error budget = 0.1% of time = 43.8 minutes/month
  Budget consumed → freeze feature deploys → focus on reliability
```

### Minimum Alert Set (Every Service Must Have These)
```
SEVERITY   CONDITION                                    ACTION
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
CRITICAL   HTTP 5xx rate > 1% for 5 minutes             Page on-call immediately
CRITICAL   0 healthy pods (service completely down)     Page on-call immediately
CRITICAL   DB connection pool > 90% saturated           Page on-call immediately
WARNING    HTTP p99 latency > 1000ms for 10 minutes     Slack alert (no page)
WARNING    HTTP 5xx rate > 0.1% for 15 minutes          Slack alert
WARNING    DLQ depth > 100 messages                     Slack alert
WARNING    Cache hit rate < 60%                         Slack alert
WARNING    Disk / memory usage > 80%                    Slack alert
INFO       Cron job missed (not run in 2× interval)     Slack alert
INFO       Error budget < 20% remaining this month      Slack \u2014 planning action
```

### Alert Quality Rules (Prevent Alert Fatigue)
```
1. Every alert MUST have a runbook link — no runbook = alert not ready to fire
2. Every alert MUST be actionable — if no action needed, it's a metric, not an alert
3. Use "for: 5m" minimum — never alert on single momentary spikes
4. Severity levels: CRITICAL (wake up now) | WARNING (Slack) | INFO (email digest)
5. Suppress child alerts when parent fires (DB down → suppress all query alerts)
6. Quarterly alert audit — remove alerts nobody acts on (noise = ignored = useless)
```

### Alert Body Template
```yaml
alert: HTTP_5xx_SpikeHigh
severity: CRITICAL
summary: "5xx rate {{ $value | humanizePercentage }} on {{ $labels.service }}"
description: |
  Service {{ $labels.service }} is returning 5xx errors above threshold.
  Current: {{ $value | humanizePercentage }} | Threshold: 1%
runbook: https://wiki.company.com/runbooks/http-5xx-spike
dashboard: https://grafana.company.com/d/service-overview
for: 5m
labels:
  service: {{ $labels.service }}
  environment: {{ $labels.env }}
```

### Runbook Template (Mandatory for Every CRITICAL Alert)
```markdown
# Runbook: HTTP 5xx Spike

## Symptoms
Alert fires when HTTP 5xx rate > 1% for 5 continuous minutes.

## Immediate Checks (< 2 minutes)
1. Was there a recent deploy? Check deployment timeline.
2. Check pod logs: `kubectl logs -l app=my-service --tail=100 -f`
3. Check DB health: `kubectl exec -it db-pod -- psql -c "SELECT count(*) FROM pg_stat_activity"`

## Rollback (if deploy-related)
`kubectl rollout undo deployment/my-service`

## Escalation
No resolution in 20 minutes → escalate to Tier 2 (team lead)
```

### Working Checklist
- [ ] SLO defined per service (error rate target + latency p99 target)
- [ ] Error budget tracked and reviewed monthly
- [ ] Minimum alert set configured (5xx rate, p99 latency, DB pool, DLQ depth)
- [ ] Every CRITICAL alert has a Severity + Runbook link + Dashboard link
- [ ] CRITICAL alerts page on-call (PagerDuty / OpsGenie / Grafana OnCall)
- [ ] WARNING alerts route to Slack (not paged)
- [ ] Alert suppression for correlated child alerts
- [ ] Quarterly alert audit scheduled (remove noise)
- [ ] Runbook written for every CRITICAL alert before enabling it

### Gotchas
- ❌ Alerting on every p99 spike without "for: 5m" → alert fatigue → team ignores all alerts
- ❌ Alert with no runbook → engineer spends 20 min guessing at 3am
- ❌ No error budget tracking → deploys continue even when reliability is already degraded

---

## 25. Local Development Environment

### Philosophy
> A new engineer MUST run the full stack locally with ONE command. Every minute of setup friction costs productivity and breeds "works on my machine" bugs.

### docker-compose.yml — Full Local Stack Template
```yaml
name: myapp-local

services:
  # ─────────────────────────────────────────────
  # PostgreSQL \u2014 Primary database
  # ─────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: myapp-postgres
    environment:
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: localpassword
      POSTGRES_DB: myapp_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp -d myapp_dev"]
      interval: 5s
      timeout: 5s
      retries: 10

  # ─────────────────────────────────────────────
  # Redis \u2014 Cache + Rate Limiting + Sessions
  # ─────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  # ─────────────────────────────────────────────
  # RabbitMQ \u2014 Message queue (or swap for Redis Streams)
  # ─────────────────────────────────────────────
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: myapp-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: myapp
      RABBITMQ_DEFAULT_PASS: localpassword
    ports:
      - "5672:5672"     # AMQP protocol
      - "15672:15672"   # Management UI → http://localhost:15672
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10

  # ─────────────────────────────────────────────
  # Mailhog \u2014 Local email catcher (no real emails sent)
  # ─────────────────────────────────────────────
  mailhog:
    image: mailhog/mailhog:latest
    container_name: myapp-mailhog
    ports:
      - "1025:1025"   # SMTP \u2014 configure app to use this
      - "8025:8025"   # Web UI → http://localhost:8025

  # ─────────────────────────────────────────────
  # Adminer \u2014 Lightweight DB browser UI
  # ─────────────────────────────────────────────
  adminer:
    image: adminer:latest
    container_name: myapp-adminer
    ports:
      - "8080:8080"   # → http://localhost:8080
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
  redis_data:
```

### Local Service Port Reference
```
Service       Port    URL / Access
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
App (dev)     3000    http://localhost:3000
API Docs      3000    http://localhost:3000/docs
PostgreSQL    5432    postgresql://myapp:localpassword@localhost:5432/myapp_dev
Redis         6379    redis://localhost:6379
RabbitMQ      5672    amqp://myapp:localpassword@localhost:5672
RabbitMQ UI   15672   http://localhost:15672
Mailhog SMTP  1025    smtp://localhost:1025
Mailhog UI    8025    http://localhost:8025
Adminer UI    8080    http://localhost:8080
```

### One-Command Setup Script (scripts/setup-local.sh)
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up local development environment..."

# 1. Copy env if not exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ .env created from .env.example"
fi

# 2. Start all infrastructure services
docker compose up -d --wait
echo "✅ Infrastructure ready (DB, Redis, Queue, Mail)"

# 3. Install dependencies
pnpm install
echo "✅ Dependencies installed"

# 4. Run database migrations
pnpm db:migrate
echo "✅ Migrations applied"

# 5. Seed development data
pnpm db:seed:dev
echo "✅ Dev seed data loaded"

echo ""
echo "✅ Setup complete! Run: pnpm dev"
echo ""
echo "📋 Local services:"
echo "   App:      http://localhost:3000"
echo "   API Docs: http://localhost:3000/docs"
echo "   Mailhog:  http://localhost:8025"
echo "   Adminer:  http://localhost:8080"
echo "   RabbitMQ: http://localhost:15672"
```

### .env.example — Docker Compose Parity (Critical)
```bash
# Must match docker-compose.yml credentials exactly
DATABASE_URL="postgresql://myapp:localpassword@localhost:5432/myapp_dev"
DATABASE_REPLICA_URL="postgresql://myapp:localpassword@localhost:5432/myapp_dev"
REDIS_URL="redis://localhost:6379"
RABBITMQ_URL="amqp://myapp:localpassword@localhost:5672"

# Email — local dev uses Mailhog SMTP (no real emails sent)
SMTP_HOST=localhost
SMTP_PORT=1025
```

### Hot Reload Configuration by Language
```
Node.js NestJS:   pnpm dev → tsx watch src/main.ts
Node.js Express:  pnpm dev → nodemon with ts-node
Python FastAPI:   uvicorn main:app --reload
Go:               air (live reloader) → go install github.com/air-verse/air
Java Spring:      Spring DevTools dependency → automatic hot restart
```

### Working Checklist
- [ ] `docker-compose.yml` in repo root \u2014 covers DB, Redis, Queue, Mail catcher, DB UI
- [ ] All services use `healthcheck` + `depends_on: condition: service_healthy`
- [ ] `scripts/setup-local.sh` \u2014 one-command full environment setup
- [ ] `.env.example` credentials match `docker-compose.yml` service credentials exactly
- [ ] Mailhog prevents real emails during local development
- [ ] Hot reload configured \u2014 no manual restart needed for code changes
- [ ] README Quick Start verified: < 5 minutes for a new engineer from clone to running

### Gotchas
- ❌ Using `latest` image tag → unexpected breaking changes on next `docker pull`
- ❌ Missing `healthcheck` conditions → app starts before DB is ready → intermittent errors
- ❌ `.env.example` credentials not matching `docker-compose.yml` → setup silently fails
- ❌ No Mail catcher → local dev sends real emails to real users during testing

---

## 26. API Versioning & Deprecation Strategy

### Philosophy
> APIs are contracts. Breaking them silently destroys consumer trust. Versioning strategy MUST be decided before the first public endpoint ships \u2014 retrofitting it later is painful.

### Versioning Approaches
```
Strategy               Example                              Recommendation
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
URL Path (Recommended)  /api/v1/users → /api/v2/users       ✅ Explicit, easy to test, debug, cache
Header Versioning       X-API-Version: 2                    ⚠️  Less visible, can't test in browser
Query Parameter         /api/users?version=2                ❌  Poor caching, non-standard
Content Negotiation     Accept: application/vnd.myapp.v2+json  ⚠️  Over-engineered for most apps
```

### URL Path Versioning — Rules
```
✅ Version only on MAJOR breaking changes (field removed, type changed, auth changed)
✅ Non-breaking additions (new fields, new endpoints) → same version, no bump
✅ Support N (current) and N-1 (previous) versions simultaneously at minimum
✅ Sunset period: minimum 6 months from announcement to shutdown
✅ Version the entire API surface, not individual endpoints
❌ Never version per-endpoint (/api/users/v2/:id) \u2014 creates inconsistent routing chaos
```

### Breaking vs Non-Breaking Changes
```
NON-BREAKING (safe \u2014 no version bump needed):
  ✅ Adding new optional response fields
  ✅ Adding new optional request fields
  ✅ Adding new endpoints entirely
  ✅ Loosening validation rules (previously rejected → now accepted)
  ✅ Adding new enum values (if consumer handles unknown gracefully)

BREAKING (requires new major version):
  ❌ Removing or renaming any response field
  ❌ Changing a field's data type (string → number, object → array)
  ❌ Changing URL structure or HTTP method
  ❌ Adding a REQUIRED request field
  ❌ Changing authentication mechanism
  ❌ Tightening validation (previously valid input → now rejected)
  ❌ Changing error response structure
```

### Deprecation Lifecycle
```
Phase 1: Announce
  → Add Deprecation + Sunset HTTP headers to ALL old-version responses
  → Publish migration guide in docs + changelog
  → Notify API consumers (email / developer portal)

Phase 2: Monitor (6+ months)
  → Track usage of deprecated version per API key / consumer
  → Proactively contact consumers still on old version
  → Track traffic trending toward zero

Phase 3: Sunset
  → After Sunset date → return HTTP 410 Gone (NOT 404)
  → Body: { "error": "API_DEPRECATED",
            "message": "v1 sunset on 2027-01-01. Migrate to /api/v2/",
            "migrationGuide": "https://docs.company.com/v1-to-v2" }

Phase 4: Remove
  → Delete v1 code 30 days after 410 responses confirmed stable
```

### Deprecation HTTP Headers (IETF Standards — RFC 8594)
```
# Set on EVERY response from the deprecated version
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/users>; rel="successor-version"

# Why use standards: API clients / monitoring tools detect these headers automatically
# Consumer can configure automated warnings when they receive Deprecation header
```

### CHANGELOG.md Format
```markdown
## [2.0.0] \u2014 2026-09-01  ⚠️ BREAKING

### Breaking Changes
- `GET /api/v2/users` \u2014 `fullName` split into `firstName` + `lastName`
- `POST /api/v2/auth/login` \u2014 tokens now returned inside `tokens` wrapper object

### Migration Guide
See [v1 to v2 migration guide](docs/migrations/v1-to-v2.md)

### Deprecation Notice
v1 API deprecated as of 2026-09-01. Sunset date: 2027-03-01.
All v1 responses now include `Deprecation: true` and `Sunset` headers.

## [1.4.0] \u2014 2026-08-15  (Non-Breaking)

### Added
- `GET /api/v1/users/:id/preferences` \u2014 new endpoint
- `updatedAt` field added to all user list responses
```

### Working Checklist
- [ ] URL path versioning decided before first public endpoint (`/api/v1/`)
- [ ] CHANGELOG.md maintained per release \u2014 breaking changes clearly marked
- [ ] Deprecation headers (`Deprecation`, `Sunset`, `Link`) on all old-version responses
- [ ] Minimum 6-month sunset period enforced before removal
- [ ] Deprecated version usage tracked per consumer (API key / user agent analytics)
- [ ] HTTP 410 Gone returned after sunset date (not 404)
- [ ] Migration guide published before deprecation announcement

### Gotchas
- ❌ Shipping breaking changes in a minor/patch release → silent breakage for all consumers
- ❌ No sunset date → consumers never migrate → you maintain v1 forever
- ❌ Returning 404 after sunset instead of 410 → consumers think it's a bug, not deprecation
- ❌ No consumer usage tracking → you don't know who still depends on v1

---

## ⚡ Implementation Priority Order

### Sprint 0 — Before First Line of Feature Code
```
  ✅ Folder & clean architecture structure
  ✅ Environment config with boot-time validation
  ✅ Structured logger setup (JSON output)
  ✅ Database connection + pooling
  ✅ Process-level crash handlers
  ✅ Correlation ID middleware
  ✅ Global error handler
  ✅ Standard request / response format
  ✅ Local dev stack (docker-compose.yml \u2014 one-command setup) [§25]
```

### Sprint 1 — Week 1
```
  ✅ Authentication (JWT with refresh token rotation)
  ✅ Authorization (RBAC guards)
  ✅ Security headers (Helmet equivalent)
  ✅ CORS configuration
  ✅ Rate limiting (tiered by endpoint type)
  ✅ Input validation layer
  ✅ Health check endpoints (/live + /ready + /startup)
  ✅ Graceful shutdown handlers
  ✅ API versioning from day 1 (/api/v1/) + deprecation strategy defined [§26]
  ✅ Feature flags (OpenFeature SDK integrated) [§2 expanded]
  ✅ Cron job distributed locking infrastructure (Redis NX lock) [§22]
```

### Sprint 2 — Before First Release
```
  ✅ Metrics endpoint (Prometheus format)
  ✅ Distributed tracing (OpenTelemetry)
  ✅ Caching layer (Redis \u2014 cache-aside + stampede prevention)
  ✅ Async job queue + DLQ
  ✅ Resilience patterns (timeouts, retries, circuit breaker, idempotency)
  ✅ File upload architecture (pre-signed URLs + virus scan) [§23]
  ✅ Alerting & SLO thresholds defined + runbooks written [§24]
  ✅ GDPR compliance (PII inventory, retention policy, erasure flow) [§8 expanded]
  ✅ Read replica routing configured [§10 expanded]
  ✅ Full unit + integration test suite
  ✅ Performance baseline (k6 / Locust \u2014 SLA targets defined)
  ✅ API documentation (OpenAPI 3.x + contract tests)
  ✅ CI/CD pipeline (all steps automated)
  ✅ Docker multi-stage build + image scanning
  ✅ docs/ folder complete
```

---

## 🚫 Anti-Patterns Hall of Shame

| Anti-Pattern | Risk | Correct Approach |
|---|---|---|
| `sync: true` / auto-migrate in prod | Table drop / data loss | Versioned migration files |
| Raw `console.log()` in production | No structure, not searchable | Structured logger (Pino/Zap/Loguru) |
| Secrets hardcoded in source | Credential leak | Secrets Manager / env vars |
| No correlation ID | Bug trace impossible in prod | Middleware assigns UUID per request |
| Immediate socket close on SIGTERM | K8s iptables race causes 502s | K8s `preStop` (sleep 5) + 5s drain window |
| Ignoring client request aborts | Zombie SQL queries starve DB pool | Propagate `AbortSignal` / `Context` to all I/O |
| Direct DB connections from 50+ pods | Postgres connection exhaustion | PgBouncer / RDS Proxy in transaction mode |
| Breaking DDL during rolling deploy | Live v1 pods crash immediately | Expand-and-Contract migration pattern |
| Passing ORM transaction to Domain Service | Violates Clean Architecture | Unit of Work abstraction interface |
| No request timeout | Slow client exhausts threads | Strict I/O timeouts everywhere |
| Storing tokens in localStorage | XSS token theft | HTTP-Only Secure cookies |
| No circuit breaker | Cascading service failure | Circuit breaker + fallback defined |
| No idempotency on mutations | Double charge / duplicate data | Idempotency-Key header handling |
| No DLQ for async jobs | Silent job loss | Dead Letter Queue + alert on depth |
| Over-indexing DB tables | Write performance regression | Index only what EXPLAIN ANALYZE shows |
| Wildcard CORS `*` with credentials | Cross-origin attacks | Explicit origin whitelist |
| No PII redaction in logs | GDPR compliance violation | Sanitize before every log call |
| Cron job without distributed lock | Duplicate execution across pods | Redis NX lock before every cron run |
| Raw S3 URLs for private files | Auth bypass \u2014 anyone with URL can access | Time-limited signed CDN URLs per request |
| Alerts without runbooks | Engineer guesses at 3am | Every CRITICAL alert has runbook link |
| Offset pagination on large tables | O(n) DB scan + page drift at scale | Cursor-based (keyset) pagination |
| No missed cron job detection | Silent data processing gaps | Track `last_run_at`, alert on 2× miss interval |
| Copying prod DB to non-prod | Real PII exposed to all devs | Data masking script before every restore |
| Breaking changes in minor version | Silent consumer breakage | Semantic versioning + Deprecation headers |
| No sunset period on deprecated API | Consumers never migrate | Minimum 6-month sunset with monitoring |
| External HTTP call inside DB transaction | Long-held lock \u2014 cascading slowdown | Keep transactions < 100ms, no I/O inside |
| No optimistic/pessimistic locking | Lost update / double-spend | Version column (optimistic) or SELECT FOR UPDATE |
| File type check via extension only | Malware upload bypasses check | Magic byte validation (file-type library) |
| No virus scan on file uploads | Malware stored and served to users | ClamAV / AWS Macie on every S3 upload event |

---

*Document Version: 3.0 (Production Battle-Tested) | Updated: 2026-09-10 | Language-Agnostic Backend Base Setup Guide*
