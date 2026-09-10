# Middleware Pipeline Ordering, Timeouts & Routing Reference

## 1. Architectural Philosophy

> **Middleware Order is Security Order**: Middlewares form a sequential onion. If a rate limiter is placed before the real IP resolver, an attacker can spoof headers or exhaust the quota of every user behind Cloudflare. If an error handler is placed before routes, runtime exceptions bypass global filters.

```
Incoming HTTP Request
        │
  [1] Correlation ID Injection     (X-Correlation-ID assigned or forwarded)
        │
  [2] Real IP Resolution           (Trust proxy + X-Forwarded-For extraction)
        │
  [3] Structured Request Logger    (Log ingress timestamp, method, path, IP)
        │
  [4] Security Headers             (Helmet CSP, HSTS, X-Content-Type-Options)
        │
  [5] CORS Guard                   (Validate origin against whitelist)
        │
  [6] Compression                  (Gzip/Brotli response compression > 1KB)
        │
  [7] Body Parsers                 (JSON & URL-encoded parsing)
        │
  [8] Body Size Limiter            (Reject > 1MB JSON early before worker allocation)
        │
  [9] Rate Limiter                 (Token bucket per real client IP + User ID)
        │
  [10] Authentication              (Verify JWT signature & expiry)
        │
  [11] Authorization               (Verify RBAC roles / permissions)
        │
  [12] Input Validation Pipe       (Zod / class-validator schema assertion)
        │
  [13] Route Handler (Controller)  (Thin handler delegating to Application Use Case)
        │
  [14] Response Envelope Wrapper   (Format output: { success: true, data, meta })
        │
  [15] Global Error Handler        (LAST: catch all unhandled errors as RFC-7807)
        │
Outgoing HTTP Response
```

---

## 2. The Cloud Load Balancer Keep-Alive Race Condition

A common cause of sporadic **HTTP 502 Bad Gateway** errors in cloud environments (AWS Application Load Balancer, Google Cloud Load Balancer, Nginx) is mismatched keep-alive timeouts:

- **The Problem**: 
  1. Default Node.js `keepAliveTimeout` is **5 seconds**.
  2. Default AWS ALB connection idle timeout is **60 seconds**.
  3. When an ALB sends an incoming client request over an existing TCP connection that Node.js decides to close at that exact millisecond, Node sends a TCP `RST`.
  4. The ALB interprets this as an ungraceful backend termination and immediately returns **502 Bad Gateway** to the end user.

- **The Solution**:
  ```typescript
  // The server's keep-alive timeout MUST be strictly greater than the upstream load balancer's timeout:
  const server = http.createServer(app);
  server.keepAliveTimeout = 65000; // 65 seconds (> ALB 60s)
  server.headersTimeout = 66000;   // Must be strictly greater than keepAliveTimeout
  server.requestTimeout = 30000;   // 30 seconds against Slowloris
  ```

---

## 3. Real IP Resolution Behind Reverse Proxies & Cloudflare

When an application sits behind Cloudflare, AWS ALB, or Nginx:
1. `req.socket.remoteAddress` is the **internal IP of the proxy**, not the end user.
2. If rate limiting uses `req.ip` without proxy trust, all millions of users behind the proxy share a single rate-limit bucket.
3. Enabling proxy trust:
   - **Express / Fastify**: `app.set('trust proxy', true)` (or provide CIDR subnet list).
   - Priority IP header check:
     1. `CF-Connecting-IP` (Cloudflare)
     2. `True-Client-IP` (Akamai / Cloudflare Enterprise)
     3. `X-Forwarded-For` (First leftmost client IP in chain)

---

## 4. Multi-Language Pipeline Implementations

### Node.js / Express
```typescript
app.use(correlationIdMiddleware());
app.set('trust proxy', true);
app.use(realIpMiddleware());
app.use(requestLoggerMiddleware());
app.use(helmet());
app.use(cors({ origin: allowedOrigins }));
app.use(compression({ threshold: 1024 }));
app.use(express.json({ limit: '1mb' }));
app.use(rateLimiter());

// Mount versioned API routes
app.use('/api/v1', apiV1Router);

// Global Error Handler MUST be the last middleware
app.use(globalErrorHandler());
```

### Python / FastAPI
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# 1. Middlewares execute in reverse order of addition in Starlette/FastAPI!
app.add_middleware(GlobalErrorMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# 2. Versioned Router
app.include_router(v1_router, prefix="/api/v1")
```
