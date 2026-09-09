# 1. Standard Folder & Clean Architecture
Any language-la project expand aagum podhu spaghetti aagama irukka:
* **Separation of Concerns:** 
  * `Domain / Entities`: Pure business models (Zero external dependencies).
  * `Use Cases / Services`: Application business logic.
  * `Adapters / Controllers`: HTTP, gRPC, CLI, WebSockets (Protocol handling).
  * `Repositories / Infrastructure`: DB access, external APIs, Cache, Message Broker.
* **Working Items:**
  - [ ] Strict dependency rule enforce pannanum (Inner layers outer layers pathi theriya koodadhu).
  - [ ] Pluggable abstractions (Interface/Traits/Protocols for DB, Cache, Mailers).
  - [ ] Core business logic-kum framework code-kum coupling irukka koodadhu.

---

# 2. Central Environment Configuration & Secrets
* **Golden Rule:** **Fail-Fast on Boot.** Missing environment variables prod runtime-la crash aaga koodadhu.
* **Working Items:**
  - [ ] **Strict Schema Validation:** Env variables parse panni type-cast pannanum (string, number, boolean) with strict defaults & required rules.
  - [ ] **Zero Hardcoding:** Ports, URLs, timeouts, retry counts ellame config driven.
  - [ ] **Hierarchical Config:** Default config $\rightarrow$ Environment specific (`local`, `test`, `prod`) $\rightarrow$ Secrets injection.
  - [ ] **Secret Sanitization:** App start aagum podhu log panra configs-la passwords, API keys automatically mask (`***`) aaganum.

---

# 3. Application Bootstrap & Server Lifecycle
* **Working Items:**
  - [ ] **Explicit Dependency Injection (DI) / Wiring:** Components (DB pool, logger, redis client) startup-la wire aaganum.
  - [ ] **Graceful Shutdown Hook:** 
    - `SIGTERM` / `SIGINT` signals listen pannanum.
    - Stop accepting new traffic from Load Balancer.
    - Ongoing requests finish aaga grace period time (e.g., 15s).
    - Database connection pools, Redis clients, Message consumers-a flush panni clean-a close pannanum.
  - [ ] **Process Level Handlers:** Unhandled Promise Rejections / Uncaught Exceptions / Panics catch panni crash-to-log trigger pannanum.

---

# 4. Server, Routing & Middleware Pipeline
* **Working Items:**
  - [ ] **Server Timeouts:** Request read timeout, write timeout, idle timeout compulsory (Slowloris attacks prevent panna).
  - [ ] **Payload Limits:** Maximum request body size restrict pannanum (e.g., max 1MB for JSON, 10MB for multipart).
  - [ ] **Standard Middleware Execution Order:**
    1. Request ID Injection (`X-Request-ID`)
    2. Real IP resolver (reverse proxy / Cloudflare header handling)
    3. CORS & Security Headers
    4. Rate Limiting
    5. Access Logging & Tracing start
    6. Body Parser & Size Limiter
    7. Authentication & Context Binding
    8. Route Handler Execution
    9. Error Handling & Response Serialization

---

# 5. Global Standard Request & Response Contract
Client apps (Frontend, Mobile, Microservices) predictable-a irukkanum:
* **Working Items:**
  - [ ] **Standard Success Format:**
    ```json
    {
      "success": true,
      "data": { ... },
      "meta": { "page": 1, "total": 100, "requestId": "req-xyz" }
    }
    ```
  - [ ] **Standard Error Format:**
    ```json
    {
      "success": false,
      "error": {
        "code": "VALIDATION_FAILED",
        "message": "Human readable error",
        "details": [ ... ],
        "requestId": "req-xyz"
      }
    }
    ```
  - [ ] **Zero Leakage Policy:** Internal DB errors, stack traces client-kku eppovume poga koodadhu.

---

# 6. Global Error Handling Strategy
* **Working Items:**
  - [ ] **Domain Error Hierarchy:** Base App Error $\rightarrow$ NotFoundError, UnauthorizedError, ValidationError, ConflictError.
  - [ ] **HTTP Status Code Mapping:** App domain error-kku accurate HTTP status map pannanum (400, 401, 403, 404, 409, 422, 500).
  - [ ] **Panic / Unhandled Crash Recovery:** Server crash aagama 500 internal error return panni, alert trigger aaganum.

---

# 7. Input Validation & Data Sanitization
* **Working Items:**
  - [ ] **Fail at the Gate:** Request controller business logic-kku pogum munne validate aaganum.
  - [ ] **Schema Definition:** Query params, route params, request body, headers ellathukum strict schema validation.
  - [ ] **Strip Unknown Fields:** Schema-la illadha extra payload keys-a automatically reject or strip pannanum (Mass assignment attack prevent panna).
  - [ ] **Sanitization:** String trimming, HTML tag stripping, XSS prevention.

---

# 8. Observability & Telemetry (The 3 Pillars)
Production-la visibility illana blind-a irukkuradhukku samam:
* **Logs:**
  - [ ] Structured JSON output (timestamp, level, service, trace_id, user_id, message).
  - [ ] Contextual logging (Log statements should carry `requestId`).
  - [ ] PII Masking (Passwords, Credit Cards, SSN logs-la vilama iruka regex scrubbers).
* **Metrics:**
  - [ ] RED Metrics (Rate, Errors, Duration/Latency - p50, p95, p99).
  - [ ] System metrics (Memory, CPU, Goroutines/Threads, DB Pool saturation).
  - [ ] Standard `/metrics` exporter (Prometheus format).
* **Traces:**
  - [ ] OpenTelemetry distributed tracing integration.
  - [ ] Trace Context Propagation (HTTP headers via W3C `traceparent`).

---

# 9. Health Checks & Probes
* **Working Items:**
  - [ ] **Liveness Probe (`/live`):** App process running-a irukka? (Fails $\rightarrow$ K8s/Docker restarts container).
  - [ ] **Readiness Probe (`/ready`):** App traffic accept panna ready-a irukka? (DB ping, Redis ping check pannanum. Fails $\rightarrow$ Load balancer traffic stop pannum).
  - [ ] **Startup Probe (`/startup`):** Heavy warmup/cache loading mudiyura varaikkum traffic block panna.

---

# 10. Database Foundation
* **Working Items:**
  - [ ] **Connection Pooling:** Min connections, max connections, idle timeout, max lifetime correctly tuned.
  - [ ] **Automated Migrations:** Code-versioned schema changes (Forward & Rollback).
  - [ ] **Seeders / Fixtures:** Dev environment setup-kku fake data seeders.
  - [ ] **Transaction Management:** Unit-of-Work pattern or clean programmatic transaction boundaries (Commit & Rollback guarantees).
  - [ ] **Audit Trail Columns:** `id` (UUIDv7 or BigInt), `created_at`, `updated_at`, `deleted_at` (Soft delete), `created_by`.
  - [ ] **Index Strategy:** Foreign keys, frequently queried filters, unique constraints-ku compulsory indexes.
  - [ ] **Slow Query Logging:** Exceeding threshold queries-a (e.g. >200ms) warn-level-la log pannanum.

---

# 11. Caching & In-Memory Store *(New Enterprise Pillar)*
Without caching, DB collapse aagidum:
* **Working Items:**
  - [ ] **Cache-Aside Pattern:** Standard abstraction for get/set/invalidate.
  - [ ] **TTL (Time to Live):** Any cached key must have an expiration (No zombie keys).
  - [ ] **Cache Stampede Prevention:** Mutex/Locking or Probabilistic early expiration for hot keys.
  - [ ] **Connection & Serialization:** Resilient connection, Redis/Memcached cluster support, compact serialization.

---

# 12. Asynchronous Jobs & Event Processing *(New Enterprise Pillar)*
Heavy operations HTTP request lifecycle-la nadakka koodadhu (e.g. Email, PDF generation, Push notifications, 3rd party sync):
* **Working Items:**
  - [ ] **Queue Producer & Consumer Abstraction:** Decoupled job submission.
  - [ ] **Job Retries & Exponential Backoff:** Network glitches handle panna.
  - [ ] **Dead Letter Queue (DLQ):** Unrecoverable failed jobs poison pill aagama store panni alert panna.
  - [ ] **Idempotent Consumers:** Duplicate messages vandhalum system corrupt aaga koodadhu.

---

# 13. Resilience & Fault Tolerance *(FAANG Critical)*
When external dependencies fail, your service shouldn't die:
* **Working Items:**
  - [ ] **Strict Timeouts on All I/O:** Every external HTTP call, DB query, Redis call MUST have a strict timeout (e.g., 2000ms max).
  - [ ] **Retries with Jitter:** Exponential backoff + random jitter for transient errors.
  - [ ] **Circuit Breaker:** Downstream service down aana continuous calls panni resource exhaust aagama fail-fast panna.
  - [ ] **Idempotency Keys:** Mutating operations (`POST /payments`, `POST /orders`) duplicate execution aagama `Idempotency-Key` header handling.

---

# 14. Authentication & Authorization
* **Working Items:**
  - [ ] **Auth Token Verification:** JWT / Session state validation, public key rotation support (JWKS).
  - [ ] **Context Injection:** Token decode aana udane current user / tenant info request context-la attach aaganum.
  - [ ] **Authorization (RBAC / ABAC):** Granular permission checks at route level & service level.
  - [ ] **Token Revocation / Blacklist:** Compromised tokens-a blacklist panra mechanism.

---

# 15. Security Baseline
* **Working Items:**
  - [ ] **Security Headers:** HSTS, X-Content-Type-Options, X-Frame-Options, CSP.
  - [ ] **CORS Policy:** Strict whitelist of allowed origins (No wildcard `*` in production with credentials).
  - [ ] **Rate Limiting:** IP-based & User-based throttling (Tiered limits: Public vs Auth endpoints).
  - [ ] **SQL Injection Protection:** Parameterized queries / ORM query builders only (Zero string concatenation).
  - [ ] **Password Security:** Salted modern hashing (Argon2id or Bcrypt).
  - [ ] **CSRF Protection:** SameSite cookies or Anti-CSRF tokens for session-based cookies.

---

# 16. API Documentation & Contracts
* **Working Items:**
  - [ ] **Single Source of Truth:** OpenAPI (Swagger) specs or code-first generated schema.
  - [ ] **Interactive Sandbox:** Swagger UI / Scalar / Redoc for testing endpoints.
  - [ ] **Contract Testing:** Client-server API contract drift aagama test suites.

---

# 17. Testing Pyramid Baseline
* **Working Items:**
  - [ ] **Unit Tests:** Fast, in-memory, mocking external dependencies.
  - [ ] **Integration Tests:** Testcontainers (Real Postgres, Real Redis in Docker) vachu actual DB queries & repositories test panradhu.
  - [ ] **E2E API Tests:** Entire request pipeline (Route $\rightarrow$ DB $\rightarrow$ Response) test panradhu.
  - [ ] **Smoke Tests:** Post-deployment health verification in staging/prod.
  - [ ] **Load / Stress Testing:** Baseline performance scripts (k6, Locust) to verify concurrency & latency.

---

# 18. Code Quality, DevEx & Tooling
* **Working Items:**
  - [ ] **One-Command Local Setup:** `docker compose up` spins up DB, Redis, Queue, Mocks.
  - [ ] **Deterministic Linting & Formatting:** Zero debates on code style.
  - [ ] **Pre-commit Hooks (Husky / Git hooks):** Linting, formatting, git commit message linting before push.
  - [ ] **Static Analysis & Security Scanning (SAST):** Dependency vulnerability scanner (e.g. Trivy, Snyk, Dependabot).

---

# 19. CI/CD & Build Infrastructure
* **Working Items:**
  - [ ] **Multi-stage Dockerfile:** Ultra-small, minimal attack-surface production image (distroless/alpine, non-root user).
  - [ ] **Automated CI Pipeline:** PR create aana Lint $\rightarrow$ Unit Tests $\rightarrow$ Integration Tests $\rightarrow$ Build run aaganum.
  - [ ] **Artifact Generation:** Semantic versioning + Immutable container images tagged with git SHA.

---

# 20. Documentation Architecture
* **Working Items:**
  - [ ] `README.md`: 5-minute quick start for any new developer.
  - [ ] `docs/architecture.md`: High-level architecture, layer diagram, design principles.
  - [ ] `docs/development.md`: Local dev setup, running tests, debug guide.
  - [ ] `docs/database.md`: ER diagram, migration guide, indexing conventions.
  - [ ] `docs/deployment.md`: Environment topology, deployment procedure, rollback steps.
  - [ ] `docs/troubleshooting.md`: Common production issues, runbooks, log querying.

---
