---
name: middleware-pipeline
description: "Architects and audits HTTP server pipelines, deterministic middleware ordering, server timeout tuning, reverse-proxy real IP resolution, and API route design. Triggered by 'middleware:', 'routing-pipeline:', or '/middleware-pipeline'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Server, Routing & Middleware Pipeline Skill

## Overview

This skill establishes the production engineering protocol for **deterministic HTTP middleware execution ordering**, **server timeout hardening**, **reverse-proxy real IP resolution**, and **standardized RESTful API routing** across language-agnostic backend systems. It eliminates security vulnerabilities resulting from misplaced pipeline handlers, prevents cloud load balancer (ALB / Cloudflare) HTTP 502 Bad Gateway race conditions, enforces payload size boundaries, and mandates Day-1 API path versioning.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Timeout Hardening]      ──► Configure keep-alive (65s), read & write (30s)
               │
  [Phase 2: Ingress Identity]       ──► Inject Correlation ID, Real IP, & request logger
               │
  [Phase 3: Security & Parsing]     ──► Helmet, CORS, compression, body parsers, limits
               │
  [Phase 4: Route Mounting]         ──► Mount thin controllers under /api/v1/
               │
  [Phase 5: Terminal Error Handler] ──► Mount RFC-7807 global exception filter LAST
```

---

## 5-Phase Execution Guide

### Phase 1: Server Timeout & Network Configuration Hardening
1. **Tuning Server Keep-Alive**:
   - Set `keepAliveTimeout` to **65,000ms** (must strictly exceed AWS ALB / Nginx 60s idle timeout to prevent TCP RST race conditions and 502 errors).
   - Set `headersTimeout` to **66,000ms** (must strictly exceed keep-alive timeout).
   - Set request read and write timeouts to **30,000ms** to mitigate Slowloris resource exhaustion.

### Phase 2: Ingress Context & Identity Middlewares
1. **Assign or Forward Correlation ID**:
   - Inspect `X-Correlation-ID` header; generate a new UUID if absent.
   - Echo the ID back onto the HTTP response headers.
2. **Resolve Real Client IP**:
   - Enable `trust proxy: true` when operating behind reverse proxies.
   - Extract the client IP from `CF-Connecting-IP` or `X-Forwarded-For` to prevent throttling proxy gateway IPs.
3. **Structured Request Logging**:
   - Log inbound request metadata: method, original path, client IP, user agent, and timestamp.

### Phase 3: Security, Guard & Parsing Middlewares
1. **Security Headers (Helmet)**:
   - Enforce CSP, HSTS, `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY`.
2. **CORS Whitelist**:
   - Restrict allowed origins to explicitly declared domains. Never use wildcard `*` with credentials in production.
3. **Response Compression**:
   - Mount Gzip/Brotli compression (threshold > 1KB) before body parsing.
4. **Body Parsers & Payload Limiters**:
   - Parse JSON and URL-encoded bodies with strict size constraints (`1mb` for standard JSON, `10mb` for multipart uploads).
5. **Rate Limiting**:
   - Throttle abusive traffic using token bucket algorithms keyed by real client IP and authenticated user ID.

### Phase 4: Route Handlers & Thin Controller Mounting
1. **Day-1 API Versioning**:
   - Mount all application routes under explicit version prefixes (e.g. `/api/v1/...`).
   - Restrict resource nesting to a maximum of 2 levels (e.g. `/api/v1/orders/:id/items`).
   - For non-CRUD business actions, suffix the path with an explicit action verb (e.g. `POST /api/v1/orders/:id/cancel`).
2. **Thin Route Handlers**:
   - Keep controllers thin (< 35 lines). Controllers must only extract parameters, call the application use case, and return the response DTO.

### Phase 5: Terminal Egress & Error Filtering
1. **Mount Global Error Handler as the Final Hook**:
   - The catch-all RFC-7807 error middleware MUST be the final registered handler.
   - Any routes or plugins registered after the error handler will escape error interception.

---

## Working Checklist

- [ ] **Server Timeouts Configured**: Keep-alive is 65s (> 60s load balancer idle timeout); read/write timeouts are 30s.
- [ ] **Payload Limits Enforced**: JSON body parser strictly capped at 1MB (10MB for multipart file uploads).
- [ ] **Real IP Resolution**: `trust proxy` enabled; rate limiter keys on actual client IP, not reverse proxy IP.
- [ ] **Deterministic Sequence**: Pipeline strictly follows the 15-step ordering from correlation ID to error filter.
- [ ] **Day-1 API Versioning**: All endpoints mounted under `/api/v1/` prefix.
- [ ] **Thin Route Handlers**: Controllers contain zero inline SQL, ORM calls, or business calculations.
- [ ] **Error Handler Terminal**: Global exception filter registered as the absolute last middleware.

---

## Authoritative References & Bundled Assets

- **Middleware Ordering & Timeout Guide**: [references/middleware-ordering-and-timeouts.md](references/middleware-ordering-and-timeouts.md)
- **Pipeline Auditor CLI Tool**: [scripts/audit_middleware_pipeline.py](scripts/audit_middleware_pipeline.py)
- **Hardened Pipeline Starter Template**: [assets/standard-middleware-pipeline.ts](assets/standard-middleware-pipeline.ts)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Pipeline)

| Legacy Antipattern | Modern Pipeline Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Default Node.js Keep-Alive (5s)** | **Tuned Keep-Alive (65s > ALB 60s)** | Eliminates intermittent HTTP 502 Bad Gateway errors under production load balancers. |
| **Missing Real IP Resolver** | **Proxy Trust + Header Extraction** | Prevents rate limiting the shared proxy IP, which inadvertently blocks all legitimate users. |
| **Error Handler Registered Mid-Pipeline** | **Terminal Error Filter (Final Hook)** | Uncaught exceptions in subsequent routes bypass the filter, leaking raw stack traces to clients. |
| **Unbounded Body Parser Limits** | **Explicit 1MB JSON Cap** | Prevents memory exhaustion and Node.js process Out-of-Memory (OOM) crashes from large payloads. |
| **Unversioned API Endpoints (`/users`)** | **Mandatory Day-1 Path Versioning (`/api/v1/users`)** | Allows seamless breaking schema evolutions without disrupting mobile and third-party consumers. |
| **Fat Controllers with Business Logic** | **Thin Adapters Delegating to Use Cases** | Preserves Clean Architecture boundaries and ensures business logic remains 100% testable. |
