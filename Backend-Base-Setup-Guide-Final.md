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

### Working Checklist
- [ ] Strict dependency rule: outer → inner only (no domain importing infrastructure)
- [ ] Pluggable abstractions: Interface/Trait/Protocol for DB, Cache, Mailers
- [ ] Core business logic zero coupling to framework internals
- [ ] `common/` only for truly cross-cutting concerns

### Gotchas
- ❌ Never: `controllers/`, `services/`, `repositories/` as top-level folders
- ❌ Never: Mix domain model with ORM entity annotations directly
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

### Working Checklist
- [ ] Schema validation on startup — all required vars present + correct type
- [ ] Zero hardcoding: ports, URLs, timeouts, retry counts — all config-driven
- [ ] Hierarchical config: defaults → env-specific → secrets injection
- [ ] Secret sanitization: passwords and API keys auto-mask (`***`) in logs
- [ ] `.env` in `.gitignore` — verified in CI pipeline
- [ ] `.env.example` has 1:1 parity with all required vars + descriptive comments

### Gotchas
- ❌ Never scatter `process.env.DB_URL` / `os.environ['DB']` across business logic files
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

### Paginated List Response
```json
{
  "success": true,
  "data": [ ],
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

### Connection Pool Configuration
```
SETTING              VALUE      REASON
──────────────────────────────────────────────────────────────
pool.min             2          Keep warm connections
pool.max             10         Prevent DB overload
pool.acquireTimeout  30s        Fail fast if pool exhausted
pool.idleTimeout     10m        Release idle connections
connectionTimeout    5s         Initial connect fail fast
queryTimeout         30s        Kill runaway queries
ssl                  true       Always in production
```

### Migration Strategy
```
✅ Versioned migration files only (never auto-sync/auto-migrate in prod)
✅ Forward (up) + rollback (down) migrations — both required
✅ CI/CD runs migrations BEFORE deploying new app code
✅ Idempotent migrations (IF NOT EXISTS guards)
✅ Test on staging before running on production
✅ Naming: YYYYMMDDHHMMSS_descriptive_name.sql
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

### Working Checklist
- [ ] Connection pooling configured with correct min/max/timeout values
- [ ] Migration files versioned and committed to git
- [ ] Rollback migration for every forward migration
- [ ] Audit columns on every table
- [ ] Slow query logging — queries > 200ms logged at WARN level
- [ ] Foreign keys indexed
- [ ] Soft delete pattern (never hard delete user data)

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

### Working Checklist
- [ ] Strict timeouts on every DB, cache, external HTTP, message broker call
- [ ] Retry with exponential backoff + jitter for transient failures
- [ ] Circuit breaker for all downstream service calls
- [ ] Idempotency keys for all mutating (POST, PUT, DELETE) endpoints
- [ ] Fallback behavior defined for each dependency failure (degraded mode)

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

### Shutdown Sequence
```
SIGTERM / SIGINT received:
  1. Mark /ready → 503             (load balancer stops routing new traffic)
  2. Stop accepting new connections
  3. Wait for in-flight requests to complete (grace timeout: 30s)
  4. Stop consuming from message queues
  5. Flush pending metrics + traces
  6. Flush log buffers
  7. Close DB connection pool
  8. Close Redis / cache connections
  9. Close HTTP server
  10. Log "Shutdown complete. Uptime: {N}s"
  11. process.exit(0)
```

### Working Checklist
- [ ] SIGTERM + SIGINT both handled
- [ ] Load balancer informed (mark ready → 503) before closing
- [ ] In-flight requests given grace period (30s max)
- [ ] All connections closed cleanly (DB, Redis, message broker)
- [ ] Logs flushed before exit
- [ ] Exit code 0 on clean shutdown, 1 on crash

### Gotchas
- ❌ Kubernetes SIGKILL after 30s — grace period must be < 30s
- ❌ Not flushing logs → last seconds of logs lost
- ✅ In-flight request timeout < grace period (avoid SIGKILL mid-request)

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
  ✅ API versioning (/api/v1/)
```

### Sprint 2 — Before First Release
```
  ✅ Metrics endpoint (Prometheus format)
  ✅ Distributed tracing (OpenTelemetry)
  ✅ Caching layer (Redis — cache-aside + stampede prevention)
  ✅ Async job queue + DLQ
  ✅ Resilience patterns (timeouts, retries, circuit breaker, idempotency)
  ✅ Full unit + integration test suite
  ✅ Performance baseline (k6 / Locust — SLA targets defined)
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
| No graceful shutdown | Dropped requests on deploy | SIGTERM handler + grace period |
| No request timeout | Slow client exhausts threads | Strict I/O timeouts everywhere |
| Storing tokens in localStorage | XSS token theft | HTTP-Only Secure cookies |
| No circuit breaker | Cascading service failure | Circuit breaker + fallback defined |
| No idempotency on mutations | Double charge / duplicate data | Idempotency-Key header handling |
| No DLQ for async jobs | Silent job loss | Dead Letter Queue + alert on depth |
| Over-indexing DB tables | Write performance regression | Index only what EXPLAIN ANALYZE shows |
| Wildcard CORS `*` with credentials | Cross-origin attacks | Explicit origin whitelist |
| No PII redaction in logs | Compliance violation (GDPR) | Sanitize before every log call |

---

*Document Version: 2.0 (Final Merged) | Updated: 2026-09-09 | Language-Agnostic Backend Base Setup Guide*
