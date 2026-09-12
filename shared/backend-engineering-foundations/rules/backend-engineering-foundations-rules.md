---
description: "Enforces production-grade, language-agnostic backend engineering foundation baselines, architectural boundaries, and operational constraints across all backend services."
trigger: model_decision
---

# Production Backend Engineering Foundations & Architectural Invariants

## Description
This rule enforces the universal, language-agnostic engineering baselines that MUST exist in a backend service before business domain feature development begins. It applies across all backend runtimes (Node.js/NestJS, Java Spring Boot, Go, Python FastAPI, .NET, Rust), ensuring that architecture boundaries, error handling, database reliability, lifecycle management, and security baselines are strictly standardized.

## Constraints & Invariants

### 1. Architectural Strategy & Boundary Inversion
- Domain entities and core business use cases MUST NOT import, depend on, or reference transport layers (HTTP/gRPC/CLI) or infrastructure drivers (ORMs, SQL drivers, cache clients, cloud SDKs).
- All external dependencies MUST be inverted through abstract Interfaces or Ports defined inside the Domain/Application layer.
- Cross-domain use case to use case invocations are STRICTLY FORBIDDEN. Cross-boundary workflows MUST coordinate via Domain Events, Application Mediators, or Unit of Work orchestrators.
- Domain Use Cases MUST NEVER receive or manipulate raw database/ORM transaction objects. Multi-repository atomic operations MUST use an abstract `UnitOfWork` interface.

### 2. Central Configuration & Fail-Fast Boot Schema
- Application runtime configuration MUST NOT read raw environment variables (`process.env`, `System.getenv()`, `os.environ`) outside of a single central Configuration Service.
- Startup MUST fail fast (`EXIT 1`) immediately during bootstrap if any mandatory configuration variable is missing or violates the strongly typed schema.
- Every environment variable MUST be mirrored in `.env.example` with human-readable comments explaining purpose, expected format, and default fallback. Real secrets in `.env.example` are STRICTLY FORBIDDEN.
- Containerized runtimes MUST enforce cgroup memory ceilings (preventing Linux Exit 137 OOM-Kills) and set explicit OS file descriptor limits (`ulimit -n 65535`).

### 3. Application Lifecycle & Zero-Downtime Socket Draining
- Runtimes MUST execute a deterministic bootstrap sequence, pre-warming database connection pools before opening HTTP/gRPC listening sockets.
- The service MUST trap OS termination signals (`SIGTERM`, `SIGINT`) and execute an asynchronous graceful shutdown sequence.
- Under Kubernetes or container orchestrators, the pod MUST configure a 5-second `preStop` sleep hook to allow external load balancers to deregister the pod before the application socket drains.
- In-flight HTTP requests and background worker transactions MUST be granted a bounded grace period (15–30 seconds) to complete before hard process termination.

### 4. Universal 7-Stage Middleware Pipeline
All inbound transport requests MUST traverse an ordered 7-stage middleware pipeline:
1. **Stage 1 (Context & Tracking)**: Assign or propagate `X-Correlation-ID` and start high-resolution execution timers.
2. **Stage 2 (Perimeter Security)**: Inject standard security headers (`CSP`, `HSTS`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`).
3. **Stage 3 (Abuse Defense)**: Enforce IP and tenant token-bucket sliding-window rate limiting before CPU-heavy parsing.
4. **Stage 4 (Payload & Network)**: Enforce strict body size limits (1MB JSON default) and verify trusted proxy headers.
5. **Stage 5 (Authentication)**: Validate short-lived stateless JWTs and extract authenticated tenant/user identity.
6. **Stage 6 (Boundary Validation)**: Execute strict DTO schema validation, stripping all unknown parameters to prevent mass-assignment attacks.
7. **Stage 7 (Response & Error Adapter)**: Wrap payloads in standard response envelopes or RFC 9457 Problem Details error schemas.

### 5. Database Pooling, Concurrency & Safe Migrations
- Database connection pools MUST be sized according to hardware limits: `PoolSize = (CPU_Cores * 2) + Effective_Spindles`. Arbitrary uncalculated pool sizes are FORBIDDEN.
- Multi-pod deployments connecting to a shared relational database MUST interpose a connection pooling proxy (PgBouncer, AWS RDS Proxy).
- All DDL database migrations MUST follow the Expand-and-Contract zero-downtime pattern. Destructive operations (dropping columns, changing data types) MUST occur in separate, phased releases.
- Schema migrations MUST execute with strict statement and lock timeouts (`lock_timeout = 2s`) to prevent table-level lock escalation and connection pool exhaustion.
- High-concurrency mutable resources (inventories, balances, seats) MUST use atomic conditional mutations (`UPDATE ... WHERE quantity >= :req`) or Optimistic Concurrency Control (OCC) with monotonic version numbers.
- Identifiers for transactional tables MUST use time-ordered 128-bit identifiers (UUIDv7, RFC 9562) to prevent B-Tree index fragmentation and insert degradation.

### 6. Asynchronous Processing & The Outbox Invariant
- Direct dual-writing across a database and message queue within a single business transaction is STRICTLY FORBIDDEN.
- State-changing events destined for external workers or messaging brokers MUST be persisted in an append-only `Transactional Outbox` table within the same ACID database transaction as the business mutation.
- Asynchronous consumers MUST be idempotent, maintaining deduplication tables keyed by unique event IDs with deterministic processing windows.
- Background queues MUST maintain Dead Letter Queues (DLQs) with bounded retry policies and exponential backoff with full jitter.

### 7. Unified Observability & Telemetry Standards
- Raw `console.log` or unformatted standard out logging is STRICTLY FORBIDDEN. All logs MUST be emitted as single-line serialized JSON containing `timestamp`, `level`, `correlationId`, `serviceName`, and `message`.
- All payload logs MUST pass through recursive PII and credential sanitization redacting passwords, tokens, and payment card numbers.
- Prometheus metrics MUST strictly track the RED method (Rate, Errors, Duration) for request traffic and the USE method (Utilization, Saturation, Errors) for resources. Unbounded metric labels (e.g. User IDs, Emails, GUIDs) are STRICTLY FORBIDDEN.
- Health checks MUST decouple `/live` (shallow ping verifying runtime event-loop liveliness) from `/ready` (deep probe verifying critical database and dependency readiness).

### 8. Resilience, Fault Tolerance & Isolation
- All outbound network calls (HTTP, RPC, external APIs) MUST configure explicit connect timeouts ($\le 2\text{s}$) and read/request timeouts ($\le 10\text{s}$).
- Retries on transient errors MUST use Exponential Backoff with Full Jitter: $T_{\text{sleep}} = \text{random}(0, \min(T_{\text{max}}, T_{\text{base}} \times 2^{\text{attempt}}))$.
- Downstream external dependencies MUST be shielded by Circuit Breakers transitioning across Closed, Open, and Half-Open states with graceful degradation fallbacks.
- Tenant data MUST enforce strict multi-tenant isolation policies (Row-Level Security or schema separation) verified by automated isolation test suites.

## Examples

### 1. Language-Agnostic Transactional Outbox Pattern
```text
// ✅ CORRECT: Atomically persist business state and message outbox in single ACID transaction
BEGIN TRANSACTION;
  INSERT INTO orders (id, tenant_id, customer_id, total_amount, status)
  VALUES ('018e3f2a-bc91-7890-a123-456789abcdef', 't_123', 'c_456', 9950, 'CREATED');

  INSERT INTO transactional_outbox (id, aggregate_type, aggregate_id, event_type, payload, status)
  VALUES (
    '018e3f2a-bc92-7890-a123-456789abcdef',
    'ORDER',
    '018e3f2a-bc91-7890-a123-456789abcdef',
    'ORDER_CREATED',
    '{"orderId":"018e3f2a-bc91-7890-a123-456789abcdef","amount":9950}',
    'PENDING'
  );
COMMIT;
// Asynchronous background poller/CDC publisher picks up outbox records and delivers to queue.
```

### 2. Forbidden Dual-Write Hazard
```text
// ❌ FORBIDDEN: Dual-write hazard causes data corruption if queue publish fails
BEGIN TRANSACTION;
  INSERT INTO orders ...;
COMMIT;

// CRITICAL RISK: If process crashes here or broker is down, DB has order but queue never gets event!
MessageQueue.publish("order.created", orderPayload);
```
