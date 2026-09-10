# 🏗️ Production Backend Project — Language-Agnostic Base Setup Guide

> **Scope**: Every section here applies to **any language or framework** — Node.js, Python, Go, Java, .NET, Rust, etc.
> Examples use pseudocode or multi-language snippets. Pick what fits your stack.

---

## 1. Standard Folder Architecture

### Philosophy
> **Domain-first, not layer-first.** Feature grow aana folder explode aagathe.

```
project-root/
├── src/
│   ├── modules/              # Feature domains (user, order, payment...)
│   │   └── user/
│   │       ├── user.controller
│   │       ├── user.service
│   │       ├── user.repository
│   │       ├── user.dto
│   │       ├── user.entity
│   │       └── user.test
│   ├── common/               # Shared across all modules
│   │   ├── decorators/
│   │   ├── filters/          # Global error handlers
│   │   ├── guards/           # Auth guards
│   │   ├── interceptors/     # Logging, transform interceptors
│   │   ├── middlewares/      # Correlation ID, request logger
│   │   ├── pipes/            # Validation pipes
│   │   └── utils/            # Pure utility functions
│   ├── config/               # All environment config in one place
│   ├── database/
│   │   ├── migrations/
│   │   ├── seeders/
│   │   └── connection.ts
│   ├── observability/        # Logging, metrics, tracing setup
│   └── main.ts               # Bootstrap entry point
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
├── scripts/                  # DB migration scripts, seed scripts, CI helpers
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example              # Every variable with descriptive comments
├── .env                      # NEVER commit — gitignore mandatory
├── README.md
└── package.json / pyproject.toml / go.mod / pom.xml
```

### Rules
- ❌ Never mix `controllers/`, `services/`, `repositories/` as top-level folders
- ✅ One domain = one folder = co-located files (controller + service + test together)
- ✅ `common/` only for truly shared cross-cutting concerns

---

## 2. Central Environment Configuration

### Philosophy
> Single source of truth for all config. Never scatter `process.env.X` / `os.environ['X']` across business logic.

### Pattern (Pseudocode)
```
ConfigService:
  - Load .env file on startup
  - Validate ALL required variables exist → if missing, CRASH with clear error message
  - Expose typed getters (never raw strings where possible)
  - Support per-environment overrides (dev / staging / prod)
```

### Validation at Boot
```
REQUIRED VARIABLES          TYPE        EXAMPLE
─────────────────────────────────────────────────
DATABASE_URL                string      postgresql://...
JWT_SECRET                  string      min 32 chars
JWT_EXPIRES_IN              string      15m
REDIS_URL                   string      redis://...
PORT                        number      3000
NODE_ENV / APP_ENV          enum        development|production
LOG_LEVEL                   enum        debug|info|warn|error
```

### .env.example Template (mandatory, with comments)
```bash
# ==============================================================
# Server Port — The HTTP port the application listens on
# ==============================================================
PORT=3000

# ==============================================================
# Database Connection URI
# Format: <dialect>://<user>:<pass>@<host>:<port>/<db>
# ==============================================================
DATABASE_URL="postgresql://postgres:password@localhost:5432/myapp"

# ==============================================================
# JWT Secret — Minimum 32-character high-entropy string
# Generate: openssl rand -base64 32
# ==============================================================
JWT_SECRET="replace_with_32_char_cryptographic_secret"

# ==============================================================
# JWT Access Token TTL — Short-lived (15m recommended)
# ==============================================================
JWT_EXPIRES_IN="15m"

# ==============================================================
# Redis URL — Used for caching, rate limiting, session store
# ==============================================================
REDIS_URL="redis://localhost:6379"
```

---

## 3. Application Bootstrap

### Philosophy
> App boot = infrastructure wiring. Business logic should NOT run here.

### Boot Sequence (Universal Order)
```
1. Load & validate environment config
2. Initialize logger (first thing — before anything else can fail silently)
3. Connect to database (with retry logic)
4. Connect to cache/Redis
5. Register middlewares (order matters!)
6. Register routes / controllers
7. Register global error handler (LAST middleware)
8. Register graceful shutdown hooks
9. Start HTTP server
10. Log: "Server ready at http://0.0.0.0:{PORT}" with correlationId
```

### Anti-patterns
- ❌ Never `process.exit(1)` without logging WHY
- ❌ Never start server if DB connection fails
- ❌ Never hardcode port — always from config

---

## 4. Server Configuration

### Mandatory Settings
```
HTTP server configuration checklist:
  ✅ Request timeout          → 30s default (prevent slow client attacks)
  ✅ Keep-alive timeout       → slightly > load balancer timeout
  ✅ Max request body size    → 1MB default (override per endpoint if needed)
  ✅ Max URL length           → 2048 chars
  ✅ Compression (gzip/brotli)→ enabled for responses > 1kb
  ✅ Trust proxy              → enabled if behind reverse proxy (Nginx/ALB)
  ✅ HTTP/2 support           → if TLS terminated at app layer
```

### Recommended Defaults
```
Body limit:        1mb
Timeout:           30_000ms
Max headers:       100
Keep-alive:        65_000ms  (ALB timeout is 60s, so must be higher)
```

---

## 5. Routing

### Philosophy
> Routes = contract. Treat them as public API from day 1.

### Conventions
```
# Versioning — mandatory
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/:id
PUT    /api/v1/users/:id
DELETE /api/v1/users/:id

# Nested resources — max 2 levels
GET    /api/v1/orders/:id/items

# Actions (non-CRUD)
POST   /api/v1/orders/:id/cancel
POST   /api/v1/users/:id/deactivate
```

### Rules
- ✅ Always version your API (`/v1/`, `/v2/`)
- ✅ Plural nouns for resources (`/users` not `/user`)
- ✅ HTTP verbs correctly (GET=read, POST=create, PUT=replace, PATCH=partial, DELETE=remove)
- ❌ Never: `/getUser`, `/createOrder`, `/deleteItem` in URL path
- ✅ Route handler = thin layer → delegates to service immediately

---

## 6. Middleware

### Execution Order (Critical!)
```
Request →
  [1] Correlation ID           (assign/propagate X-Correlation-ID)
  [2] Request Logger           (log method, path, timestamp)
  [3] Security Headers         (Helmet equivalent)
  [4] CORS
  [5] Compression
  [6] Body Parser              (JSON, form-data)
  [7] Rate Limiter
  [8] Authentication           (JWT verification)
  [9] Authorization            (role/permission check)
  [10] Validation              (DTO/schema validation)
  [11] Route Handler           (business logic)
  [12] Response Transformer    (standard response wrapper)
  [13] Error Handler           (LAST — catches everything above)
→ Response
```

### Correlation ID Middleware (Universal Pattern)
```
function correlationIdMiddleware(request, response, next):
    id = request.headers['x-correlation-id'] OR generate_uuid()
    request.correlationId = id
    response.setHeader('X-Correlation-ID', id)
    store_in_async_context(id)   # AsyncLocalStorage / context var
    next()
```

### Request Logger Middleware
```
ON REQUEST:
    log { correlationId, method, path, userAgent, ip, timestamp }

ON RESPONSE:
    log { correlationId, method, path, statusCode, durationMs }
```

---

## 7. Global Error Handling

### Philosophy
> Every unhandled error MUST be caught here. Client should NEVER see stack traces.

### Standard Error Response Shape
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email address is invalid",
    "details": [
      { "field": "emailAddress", "message": "Must be a valid email" }
    ]
  },
  "meta": {
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-09-09T09:18:00Z",
    "path": "/api/v1/users"
  }
}
```

### Error Code Catalog (Define upfront)
```
VALIDATION_ERROR          → 400
UNAUTHORIZED              → 401
FORBIDDEN                 → 403
NOT_FOUND                 → 404
CONFLICT                  → 409
RATE_LIMIT_EXCEEDED       → 429
INTERNAL_SERVER_ERROR     → 500
SERVICE_UNAVAILABLE       → 503
```

### Rules
- ✅ Log full error (with stack) on server side
- ✅ Return sanitized message to client
- ✅ Include correlationId in every error response
- ❌ Never expose database errors / stack traces to client
- ✅ Separate operational errors (expected) vs programmer errors (bugs)

---

## 8. Validation

### Philosophy
> Trust nobody. Validate at the boundary — before business logic touches data.

### Validation Layers
```
Layer 1: Schema/Type validation     → Is shape correct? (string, number, email...)
Layer 2: Business rule validation   → Is value valid? (user exists? stock available?)
Layer 3: Authorization validation   → Is caller allowed? (checked in middleware)
```

### What to Validate (Checklist)
```
Every request body:
  ✅ Required fields present
  ✅ Correct data types
  ✅ String lengths (min/max)
  ✅ Enum values in allowed set
  ✅ Email format
  ✅ Phone number format
  ✅ Date format and range
  ✅ Numeric ranges (no negative prices)
  ✅ UUID format for IDs
  ✅ No unexpected extra fields (strip or reject)
```

### Tools by Language
```
Node.js (TypeScript)  → class-validator + class-transformer / Zod
Python                → Pydantic v2
Go                    → go-playground/validator
Java                  → Jakarta Validation (Bean Validation)
.NET                  → FluentValidation / DataAnnotations
Rust                  → validator crate
```

---

## 9. Observability — The Three Pillars

### Overview
```
Logs    → WHAT happened (events, errors, state changes)
Metrics → HOW MUCH / HOW FAST (counters, gauges, histograms)
Traces  → WHERE time was spent (distributed request flow)

Together → Full picture of system health in production
```

---

### 9a. Logs

#### Log Levels
```
TRACE  → Ultra-verbose (DB queries, internal loops) — dev only
DEBUG  → Debugging info — dev/staging only
INFO   → Normal business events (user created, order placed)
WARN   → Unexpected but handled (retry attempt, deprecated API used)
ERROR  → Handled failure (payment failed, external API timeout)
FATAL  → Unrecoverable — app may crash (DB unreachable at boot)
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
level          → log level
service        → service name
correlationId  → request trace ID
message        → human readable description
```

#### What MUST be Redacted
```
❌ passwords          → "[REDACTED]"
❌ tokens/secrets     → "[REDACTED]"
❌ credit card numbers→ "[REDACTED]"
❌ auth headers       → "[REDACTED]"
❌ PII (DOB, SSN)     → "[REDACTED]" or hash
```

#### Tools by Language
```
Node.js  → Pino (fastest) / Winston
Python   → structlog / loguru
Go       → zerolog / zap
Java     → Logback + SLF4J
.NET     → Serilog / NLog
```

---

### 9b. Metrics

#### Metric Types
```
Counter    → Always increases (total requests, total errors)
Gauge      → Can go up/down (active connections, memory usage)
Histogram  → Distribution of values (request duration, response size)
Summary    → Pre-calculated percentiles (p50, p95, p99 latency)
```

#### Mandatory Metrics to Expose
```
http_requests_total{method, path, status}          → Counter
http_request_duration_seconds{method, path}        → Histogram
http_active_connections                            → Gauge
db_query_duration_seconds{operation, table}        → Histogram
db_connection_pool_size{state}                     → Gauge
cache_hits_total / cache_misses_total              → Counter
errors_total{type, code}                           → Counter
```

#### Exposure Format
```
GET /metrics   → Prometheus text format (standard)
               → Scrape interval: 15s
```

---

### 9c. Traces (Distributed Tracing)

#### Concept
```
One user request → multiple services / DB calls / cache calls
Trace = full journey of one request across all hops
Span  = one unit of work within a trace

User Request
  └── [Span] HTTP Handler (50ms total)
        ├── [Span] Auth verification (5ms)
        ├── [Span] DB query: SELECT user (20ms)
        ├── [Span] Redis cache GET (2ms)
        └── [Span] External API call (23ms)
```

#### Standard: OpenTelemetry (language-agnostic)
```
Use OpenTelemetry SDK for your language
Export to: Jaeger / Zipkin / Tempo / Datadog / AWS X-Ray

Mandatory context propagation headers:
  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
  tracestate:  (optional vendor-specific)
```

---

## 10. Database Foundation

### Connection Configuration
```
Settings (tune per workload):
  pool.min             → 2   (always keep warm connections)
  pool.max             → 10  (prevent DB overload)
  pool.acquireTimeout  → 30s (fail fast if pool exhausted)
  pool.idleTimeout     → 10m (release idle connections)
  connectionTimeout    → 5s
  queryTimeout         → 30s (prevent runaway queries)
  ssl                  → true in production (always)
```

### Migration Strategy
```
✅ ALWAYS use migration files (never auto-sync/auto-migrate in production)
✅ Migrations are versioned and committed to git
✅ Up migration + Down migration (rollback capability)
✅ CI/CD runs migrations before deploying new code
✅ Migrations must be idempotent (safe to run twice)
✅ Test migration on staging before production

Migration naming convention:
  YYYYMMDDHHMMSS_descriptive_name.sql
  20260909091800_add_refresh_token_to_users.sql
```

### Audit Columns (Every Table)
```sql
created_at    TIMESTAMP NOT NULL DEFAULT NOW()
updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
deleted_at    TIMESTAMP NULL      -- soft delete
created_by    UUID / VARCHAR      -- who created
updated_by    UUID / VARCHAR      -- who last modified
```

### Indexes Checklist
```
✅ Primary key (auto)
✅ Foreign keys (always index)
✅ Columns used in WHERE clauses frequently
✅ Columns used in ORDER BY
✅ Unique constraints (email, username, slug)
✅ Composite indexes for multi-column queries
✅ Partial indexes for filtered queries (WHERE deleted_at IS NULL)

❌ Don't over-index — write performance degrades
❌ Analyze slow queries before adding indexes (use EXPLAIN ANALYZE)
```

### Transaction Pattern
```
BEGIN TRANSACTION
  step 1: debit account A
  step 2: credit account B
  step 3: create transaction record
  if any step fails → ROLLBACK (all or nothing)
COMMIT
```

### Seeder Strategy
```
dev-seed.sql   → Large fake dataset for local development
test-seed.sql  → Minimal deterministic data for integration tests
prod-seed.sql  → Only reference/master data (countries, roles, enums)
                 NEVER user data in prod seeders
```

---

## 11. Authentication

### Flow (JWT Recommended Pattern)
```
LOGIN:
  1. Validate credentials (email + password)
  2. Check password hash (bcrypt/argon2 — min cost 10)
  3. Generate access_token (short-lived: 15 minutes)
  4. Generate refresh_token (long-lived: 7 days)
  5. Store refresh_token in DB (hashed) + HTTP-Only cookie
  6. Return access_token in response body

AUTHENTICATED REQUEST:
  1. Extract Bearer token from Authorization header
  2. Verify signature + expiry
  3. Attach decoded user to request context

TOKEN REFRESH:
  1. Read refresh_token from HTTP-Only cookie
  2. Verify against stored hash in DB
  3. Rotate: invalidate old → issue new pair
  4. Return new access_token

LOGOUT:
  1. Invalidate refresh_token in DB
  2. Clear HTTP-Only cookie
```

### Rules
```
✅ access_token   → response body (short-lived)
✅ refresh_token  → HTTP-Only Secure SameSite=Strict cookie
❌ NEVER store tokens in localStorage (XSS vulnerable)
✅ Rotate refresh tokens on every use (detect token theft)
✅ Maintain token blacklist for immediate revocation
✅ JWT algorithm: RS256 (asymmetric) preferred for microservices
```

---

## 12. Authorization

### Models
```
RBAC (Role-Based Access Control):
  User → has Role(s) → Role has Permission(s)
  Roles: ADMIN, MANAGER, USER, VIEWER

ABAC (Attribute-Based Access Control):
  More granular: user.department == resource.department
  Use when RBAC becomes too complex

Resource Ownership:
  "Can user X modify resource Y?"
  Always check: resource.ownerId === currentUser.id
```

### Pattern (Middleware/Guard)
```
Every protected route:
  1. Authenticate (who are you?)
  2. Authorize  (are you allowed to do THIS on THIS resource?)
  3. Ownership check (if needed — is this YOUR resource?)
```

---

## 13. Security

### Security Checklist

#### HTTP Security Headers
```
Content-Security-Policy      → Prevent XSS, clickjacking
Strict-Transport-Security    → Force HTTPS (HSTS)
X-Frame-Options: DENY        → Prevent iframe embedding
X-Content-Type-Options: nosniff → Prevent MIME sniffing
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy           → Disable unused browser features
```

#### CORS
```
✅ Whitelist specific origins (not *)
✅ Specify allowed methods
✅ Specify allowed headers
✅ credentials: true only when needed
✅ preflight cache: 600s
```

#### Rate Limiting Strategy
```
Endpoint Type          Limit          Window
─────────────────────────────────────────────
Auth/Login             5 requests     1 minute   (strict — brute force)
Auth/Register          10 requests    1 hour
Password Reset         3 requests     1 hour
API (authenticated)    1000 requests  1 minute
API (public)           100 requests   1 minute
File Upload            10 requests    1 minute
```

#### Input Validation
```
✅ Validate type, format, length on every input
✅ Parameterized queries ONLY (never string concatenation in SQL)
✅ Sanitize HTML output (DOMPurify equivalent)
✅ Validate Content-Type header
✅ Reject unexpected fields (whitelist approach)
```

#### Request Size Limits
```
JSON body:     1mb  default
File upload:   10mb (tune per use case)
URL length:    2048 chars
Header size:   8kb
```

#### Password Hashing
```
Algorithm: bcrypt (cost: 12) OR argon2id
NEVER: MD5, SHA1, SHA256 alone (not for passwords)
NEVER: Store plain text
NEVER: Store reversible encryption
```

#### SQL Injection Prevention
```
✅ Use ORM parameterized queries
✅ Use prepared statements for raw SQL
❌ NEVER: "SELECT * FROM users WHERE email = '" + email + "'"
✅ Escape special characters if raw input required
```

#### XSS Prevention
```
✅ Escape all user-controlled output in HTML context
✅ Content-Security-Policy header
✅ HttpOnly cookies (JS cannot access)
✅ Sanitize rich text content (HTML whitelist)
```

#### CSRF Protection
```
APIs (JSON + Authorization header):  Not needed (SOP protects)
Session-based web apps:              Required
  → Double-submit cookie pattern
  → Synchronizer token pattern
  → SameSite=Strict cookies (modern approach)
```

#### Secret Management
```
Development:   .env file (gitignored)
CI/CD:         GitHub Secrets / GitLab CI Variables
Production:    AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager
NEVER:         Hardcoded in source code, config files, or Dockerfile
```

---

## 14. API Documentation

### OpenAPI / Swagger
```
Format: OpenAPI 3.x
Auto-generate from code annotations where possible
Include:
  ✅ All endpoints with path, method, description
  ✅ Request body schema with examples
  ✅ Response schemas (success + error cases)
  ✅ Authentication requirements
  ✅ Rate limit information
  ✅ Deprecation notices

Endpoints:
  GET /docs            → Swagger UI (dev/staging only)
  GET /docs/openapi.json → Raw OpenAPI spec
```

### Additional Docs
```
CHANGELOG.md       → Version history and breaking changes
API versioning     → /v1/ → /v2/ with deprecation timeline
Postman Collection → Export and commit to repo for team
```

---

## 15. Testing

### Testing Pyramid
```
                    /\
                   /  \
                  / E2E \         → 10% (expensive, slow)
                 /--------\
                / Integration\    → 30% (test DB, real HTTP)
               /--------------\
              /   Unit Tests    \  → 60% (fast, isolated, mocked)
             /──────────────────\
```

### Unit Tests
```
What to test:
  ✅ Service layer business logic
  ✅ Utility functions / helpers
  ✅ Data transformation functions
  ✅ Validation rules
  ✅ Edge cases and error paths

Rules:
  ✅ No DB connections — mock everything external
  ✅ Test one thing per test
  ✅ Deterministic (no random data — use fixed seeds)
  ✅ Fast < 1ms per test
  ✅ Coverage targets: Lines > 80%, Branches > 75%
```

### Integration / Functional Tests
```
What to test:
  ✅ Full HTTP request → response cycle
  ✅ Real database operations (test DB, rolled back after)
  ✅ Auth flows (login, refresh, logout)
  ✅ Error response shapes
  ✅ Middleware behavior (rate limiting, CORS)

Setup:
  ✅ Separate test database
  ✅ Run migrations before test suite
  ✅ Seed minimal required data
  ✅ Wrap each test in transaction → rollback after
```

### Performance Testing
```
Tool options: k6 / Locust / Artillery / Gatling / JMeter

Test types:
  Load test     → Normal expected traffic
  Stress test   → 2-5x peak traffic
  Spike test    → Sudden traffic burst
  Soak test     → Sustained load over hours (memory leak detection)

SLA Targets (define before testing):
  p50 latency   < 50ms
  p95 latency   < 200ms
  p99 latency   < 500ms
  Error rate    < 0.1%
  Throughput    > X req/s (define per endpoint)
```

---

## 16. Health Checks

### Endpoints
```
GET /health
  → Liveness: Is the app process alive?
  → Response: 200 OK immediately (no external checks)
  → Used by: Kubernetes liveness probe

GET /health/ready
  → Readiness: Can the app serve traffic?
  → Checks: DB connected? Redis connected? External deps up?
  → Response: 200 if all healthy, 503 if any failing
  → Used by: Kubernetes readiness probe / Load balancer

GET /health/details  (internal/admin only)
  → Full system status with details
```

### Standard Health Response
```json
{
  "status": "healthy",
  "timestamp": "2026-09-09T09:18:00Z",
  "version": "2.4.1",
  "uptime": 86400,
  "checks": {
    "database": { "status": "healthy", "responseTimeMs": 5 },
    "redis":    { "status": "healthy", "responseTimeMs": 1 },
    "externalApi": { "status": "degraded", "responseTimeMs": 2500 }
  }
}
```

---

## 17. Graceful Shutdown

### Why It Matters
```
Without graceful shutdown:
  → In-flight requests dropped (users see errors)
  → DB connections not closed (connection pool exhausted)
  → Background jobs aborted mid-way (data corruption risk)

With graceful shutdown:
  → Stop accepting new requests
  → Finish in-flight requests (with timeout)
  → Flush logs and metrics
  → Close DB and cache connections cleanly
  → Exit with code 0 (success)
```

### Shutdown Sequence
```
SIGTERM / SIGINT received:
  1. Mark health/ready → 503 (load balancer stops routing)
  2. Wait for in-flight requests to complete (max 30s)
  3. Stop consuming from message queues
  4. Flush metrics and traces
  5. Close DB connection pool
  6. Close Redis connections
  7. Close HTTP server
  8. Log "shutdown complete"
  9. process.exit(0)
```

---

## 18. Global Standard Request & Response Format

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

### Request ID / Correlation Headers
```
Request headers (accepted):
  X-Correlation-ID: <uuid>   → pass through if provided

Response headers (always set):
  X-Correlation-ID: <uuid>
  X-Response-Time: 45ms
  X-API-Version: v1
```

---

## 19. Code Quality

### Automated Tools
```
Linting:
  Node.js   → ESLint + typescript-eslint
  Python    → Ruff / Flake8
  Go        → golangci-lint
  Java      → Checkstyle / SpotBugs
  .NET      → Roslyn Analyzers

Formatting (auto-format on save):
  Node.js   → Prettier
  Python    → Black
  Go        → gofmt (built-in)
  Java      → google-java-format
  .NET      → dotnet-format

Type Safety:
  TypeScript → strict: true (no exceptions)
  Python    → mypy or pyright (strict mode)
  Go        → statically typed by default

Pre-commit hooks:
  → Run linter
  → Run formatter check
  → Run unit tests
  → Reject commit if any fail
```

### Code Review Standards
```
PR requirements:
  ✅ Linked to a GitHub Issue
  ✅ Passes CI/CD pipeline
  ✅ Test coverage not decreased
  ✅ No new lint warnings
  ✅ Reviewed by minimum 1 senior engineer
  ✅ Conventional commit message
```

---

## 20. Documentation

### README.md (Minimum Required Sections)
```markdown
# Project Name
Brief description (1-2 sentences)

## Quick Start (< 5 minutes to run locally)
## Prerequisites
## Installation
## Environment Setup
## Running the Application
## Running Tests
## Project Structure
## Contributing
## License
```

### docs/ Structure
```
docs/
├── architecture.md     → System design, component diagram, data flow
├── development.md      → Local setup, debugging tips, useful commands
├── testing.md          → How to run tests, coverage, test data setup
├── deployment.md       → Staging / prod deployment steps, env vars
├── database.md         → Schema overview, migration guide, seeding
└── troubleshooting.md  → Common errors, FAQs, runbook for incidents
```

---

## 21. Caching & In-Memory Store

### Caching Layers
```
Layer 1: In-process cache (L1)
  → Memory inside the app process
  → Fastest (nanoseconds)
  → Lost on restart — use only for truly static data
  → Max size limit mandatory (prevent memory leak)
  → Libraries: LRU cache, TTL cache

Layer 2: Distributed cache (L2) — Redis/Memcached
  → Shared across all app instances
  → Fast (< 1ms on same network)
  → Survives app restarts
  → Use for: sessions, rate limiting, expensive query results
```

### Cache Key Convention
```
Pattern:  {service}:{entity}:{identifier}:{version}
Examples:
  user:profile:usr_abc123:v1
  order:list:usr_abc123:page:1
  product:detail:prod_xyz:v1
  rate-limit:ip:192.168.1.1
```

### Cache Invalidation Strategies
```
TTL (Time-To-Live):
  → Simple, automatic expiry
  → Risk: stale data for TTL duration
  → Good for: semi-static data (product catalog, config)

Write-Through:
  → Update cache + DB at same time
  → Always fresh
  → Good for: user profiles, frequently read & written data

Cache-Aside (Lazy loading):
  → Check cache first
  → If miss → load from DB → write to cache
  → Most common pattern
  → Risk: thundering herd on cold start

Event-Driven Invalidation:
  → On data change event → delete/update relevant cache keys
  → Most precise but most complex
  → Good for: microservices with event bus
```

### Redis Usage Patterns
```
Sessions:         SET session:{id} {data} EX 3600
Rate limiting:    INCR + EXPIRE (sliding window)
Pub/Sub:          Real-time notifications
Queues:           LPUSH / BRPOP (simple job queue)
Distributed lock: SET key value NX EX 30 (Redlock pattern)
Leaderboard:      ZADD / ZREVRANGE (sorted sets)
```

### Cache Rules
```
✅ Always set TTL — never cache without expiry
✅ Cache read-heavy, update-light data
✅ Cache expensive computations
✅ Log cache hit/miss rates as metrics
✅ Plan for cache failure — app must work without cache (degraded)
❌ Never cache sensitive data unencrypted
❌ Never cache auth tokens
❌ Don't cache data that must be real-time (bank balance, stock price)
```

---

## ⚡ Implementation Priority Order

```
Sprint 0 (Before First Line of Feature Code):
  ✅ Folder structure
  ✅ Environment config + validation
  ✅ Logger setup (structured JSON)
  ✅ Database connection + pooling
  ✅ Correlation ID middleware
  ✅ Global error handler
  ✅ Standard response format

Sprint 1 (Week 1):
  ✅ Authentication (JWT)
  ✅ Security headers (Helmet/CORS)
  ✅ Rate limiting
  ✅ Input validation layer
  ✅ Health check endpoints
  ✅ Graceful shutdown
  ✅ API versioning

Sprint 2 (Before First Release):
  ✅ Metrics endpoint (Prometheus)
  ✅ Distributed tracing (OpenTelemetry)
  ✅ Caching layer (Redis)
  ✅ Full test suite (unit + integration)
  ✅ Performance baseline test
  ✅ API documentation (OpenAPI)
  ✅ CI/CD pipeline
  ✅ Docker multi-stage build
```

---

*Document Version: 1.0 | Last Updated: 2026-09-09 | Language-Agnostic Backend Base Setup Guide*
