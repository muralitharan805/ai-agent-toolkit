---
trigger: model_decision
description: "Enforces deterministic 15-step HTTP middleware execution order, server timeout hardening (keep-alive, read, write), reverse-proxy real IP extraction, payload limits, and Day-1 API versioning."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Server, Routing & Middleware Pipeline Standards

## Description
Enforces production-grade server configuration, strict deterministic middleware execution ordering, reverse-proxy real IP resolution, network timeout hardening, and standardized API routing conventions across all backend services. Eliminates security vulnerabilities caused by misplaced middlewares (e.g. rate limiters throttling load balancer IPs, uncaught exceptions bypassing error handlers), prevents Slowloris and connection dropouts by hardening timeouts, and mandates Day-1 RESTful API versioning.

## Constraints

### 1. Mandatory 15-Step Middleware Execution Order
HTTP server middleware pipelines MUST be registered in a strict, non-negotiable sequence. Any deviations that compromise security or error handling are STRICTLY FORBIDDEN:
1. **Correlation ID Injector**: Assign or propagate `X-Correlation-ID` header (UUID) for tracing.
2. **Real IP Resolver**: Extract true client IP (`X-Forwarded-For` / `CF-Connecting-IP`); configure `trust proxy: true` behind load balancers.
3. **Structured Request Logger**: Log HTTP method, path, IP, user-agent, and incoming timestamp.
4. **Security Headers (Helmet)**: Enforce CSP, HSTS, `X-Content-Type-Options`, and `X-Frame-Options`.
5. **CORS Guard**: Validate request origin against an explicit domain whitelist (never `*` in production).
6. **Response Compression**: Gzip/Brotli compression for payloads exceeding 1KB (placed BEFORE body parsing).
7. **Body Parser**: Deserialize JSON and URL-encoded payloads into typed request objects.
8. **Request Body Size Limiter**: Enforce strict payload limits (1MB for JSON, 10MB for multipart uploads).
9. **Rate Limiter**: Token-bucket or sliding-window rate limiting keyed by real client IP + authenticated user ID.
10. **Authentication Guard**: Verify bearer JWT tokens or session cookies.
11. **Authorization Guard**: Check RBAC roles and permissions against the authenticated principal.
12. **Input Validation Pipe**: Validate DTO schemas (Zod / class-validator); strip unknown fields before handler execution.
13. **Route Handler**: Thin controller that immediately delegates execution to application use case services.
14. **Response Envelope Transformer**: Wrap successful payloads in standard contract (`{ success: true, data, meta }`).
15. **Global Error Handler**: Terminal catch-all RFC-7807 error filter (MUST be the final middleware in the pipeline).

### 2. Strict Error Handler Terminal Position
- The global error handling middleware MUST be registered as the absolute LAST handler in the server pipeline.
- Registering route handlers, static files, or plugins after the global error handler is STRICTLY FORBIDDEN, as uncaught exceptions in downstream handlers will escape the filter and crash the process or leak raw stack traces to clients.

### 3. Real IP Resolution Behind Reverse Proxies
- Backend services deployed behind reverse proxies, Cloudflare, or cloud load balancers (AWS ALB, GCP Cloud Load Balancing) MUST enable proxy trust (e.g. `app.set('trust proxy', true)`).
- Rate limiters and audit logs MUST extract the client IP using verified proxy headers (`X-Forwarded-For`, `CF-Connecting-IP`).
- Applying rate limiting to the proxy's internal IP address is STRICTLY FORBIDDEN (causes denial-of-service for all users sharing the proxy).

### 4. Server Network Timeout Hardening
- Server HTTP timeouts MUST be explicitly configured to prevent connection starvation:
  - **Request Read Timeout**: 30s (prevents Slowloris attacks where clients transmit headers at 1 byte/sec).
  - **Request Write Timeout**: 30s (prevents slow clients from holding server worker threads indefinitely).
  - **Keep-Alive Timeout**: Minimum 65s (MUST strictly exceed upstream load balancer idle timeout, e.g. AWS ALB 60s default, to eliminate HTTP 502 connection dropouts).
  - **Max URL Length**: 2048 characters.

### 5. Mandatory Day-1 API Versioning
- All public API routes MUST be versioned at the path level starting from Day 1 (`/api/v1/...`).
- Unversioned API routes (e.g. `/users`, `/api/orders`) are forbidden.
- Resource nesting MUST NOT exceed 2 levels deep (`/api/v1/orders/:id/items` is valid; `/api/v1/users/:id/orders/:oid/items/:iid` is forbidden).
- Non-CRUD business actions MUST be expressed using a verb as the final path segment (e.g. `POST /api/v1/orders/:id/cancel`).

### 6. Thin Route Handler Invariant
- Route controllers MUST remain thin adapters (< 35 lines of code).
- Controllers are responsible exclusively for extracting HTTP params/body, invoking the application use case service, and returning the formatted response.
- Writing database queries, business calculations, or multi-step entity logic inside route handlers is STRICTLY FORBIDDEN.

## Examples

### 1. Deterministic Middleware Pipeline Registration

```typescript
// ✅ CORRECT: Strict sequential registration in Express / Fastify / Koa
export function configureMiddlewarePipeline(app: Express, config: AppConfig): void {
  // [1] Correlation ID
  app.use(correlationIdMiddleware());
  // [2] Real IP & Proxy Trust
  app.set('trust proxy', config.TRUST_PROXY);
  app.use(realIpResolverMiddleware());
  // [3] Request Logger
  app.use(structuredRequestLogger());
  // [4] Security Headers
  app.use(helmet(config.SECURITY_HEADERS));
  // [5] CORS Whitelist
  app.use(cors({ origin: config.CORS_ALLOWED_ORIGINS, credentials: true }));
  // [6] Compression
  app.use(compression({ threshold: 1024 }));
  // [7 & 8] Body Parser & Size Limiter
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true, limit: '1mb' }));
  // [9] Rate Limiter
  app.use(rateLimiterMiddleware(config.RATE_LIMIT));
  
  // [10 - 13] Routes with Auth & Validation mounted at /api/v1
  app.use('/api/v1', apiV1Router);

  // [14 & 15] Global RFC-7807 Error Handler — MUST BE LAST
  app.use(globalErrorHandlerMiddleware());
}
```

### 2. Keep-Alive Timeout Hardening for Cloud Load Balancers

```typescript
// ❌ FORBIDDEN: Default Node.js keep-alive (5s) causes 502 errors behind AWS ALB (60s)
const server = app.listen(3000);

// ✅ CORRECT: Keep-alive timeout tuned higher than upstream proxy
const server = http.createServer(app);
server.keepAliveTimeout = 65000;  // 65s > ALB 60s
server.headersTimeout = 66000;    // Must be greater than keepAliveTimeout
server.requestTimeout = 30000;    // 30s read timeout against Slowloris

server.listen(config.PORT);
```

### 3. RESTful URL Conventions & Day-1 Versioning

```text
// ❌ FORBIDDEN: Unversioned, deeply nested, or unstandardized RPC endpoints
GET    /users
POST   /cancel_order_by_id?id=123
GET    /api/stores/1/departments/2/categories/3/products/4/reviews

// ✅ CORRECT: Day-1 versioning, shallow nesting, verb-terminated actions
GET    /api/v1/users
GET    /api/v1/users/:id
GET    /api/v1/orders/:id/items            # Max 2 levels nesting
POST   /api/v1/orders/:id/cancel           # Non-CRUD action verb
POST   /api/v1/auth/refresh                # Authentication action
```
