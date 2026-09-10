---
name: caching-and-in-memory-store
description: "Implements and audits enterprise caching architecture, L1/L2 tiered caching, standardized key namespacing, cache stampede mitigation (mutex locking), mandatory TTLs, and graceful DB fallback. Triggered by 'caching:', 'redis:', 'in-memory-store:', or '/caching-and-in-memory-store'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Caching & In-Memory Store Architecture Skill

## Overview

This skill establishes the production engineering protocol for **Multi-Tiered Caching (L1/L2)**, **Hierarchical Key Namespacing**, **Cache Stampede (Thundering Herd) Mitigation**, and **Graceful Persistence Fallbacks** across backend services. It eliminates process memory leaks from unbounded maps, prevents zombie key accumulation in Redis, and protects databases from connection spikes when hot keys expire.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Caching Architecture Pipeline                │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Namespacing Standard]   ──► Format: {service}:{entity}:{id}:{version}
                │
  [Phase 2: Bounded L1 In-Process]  ──► Enforce max capacity + TTL (No raw Maps)
                │
  [Phase 3: L2 Distributed Redis]   ──► Explicit TTL (EX/PX) on every SET command
                │
  [Phase 4: Stampede Protection]    ──► Distributed mutex (NX) or early expiration
                │
  [Phase 5: Conformance Audit]      ──► Run audit_caching_patterns.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Standardized Cache Key Namespacing
1. **Apply Hierarchical Key Format**:
   - Construct all cache keys with the 4-tier pattern:
     `{service}:{entity}:{identifier}:{version}`
   - Example:
     ```typescript
     const key = `${service}:${entity}:${id}:${version}`;
     ```
2. **Schema Versioning**:
   - Embedding `:v1` or `:v2` allows instant schema-breaking migrations without performing dangerous `FLUSHALL` commands on shared Redis clusters.

### Phase 2: Bounded L1 In-Process Caching
1. **Prevent Memory Leaks**:
   - Never use raw JavaScript `new Map()` or empty object literals (`{}`) as unbounded caches.
   - Deploy an LRU cache engine with strict constraints:
     - `max`: Maximum item capacity (e.g. 5,000 items).
     - `ttl`: Maximum lifetime in milliseconds.

### Phase 3: L2 Distributed Caching & Mandatory TTLs
1. **Eliminate Zombie Keys**:
   - Every Redis write MUST include an expiration parameter (`EX` seconds or `PX` milliseconds):
     ```typescript
     await redis.set(cacheKey, JSON.stringify(data), 'EX', 300);
     ```
   - Bare `SET key value` without TTL is strictly forbidden.

### Phase 4: Cache Stampede (Thundering Herd) Mitigation
1. **Serialize Database Misses with Distributed Mutex**:
   - When a hot key expires, acquire a distributed mutex lock before querying the database:
     ```typescript
     const acquired = await redis.set(`lock:${cacheKey}`, '1', 'NX', 'EX', 10);
     if (!acquired) {
       await sleep(50);
       return readCacheAgain();
     }
     try {
       const fresh = await db.load();
       await redis.set(cacheKey, JSON.stringify(fresh), 'EX', ttl);
       return fresh;
     } finally {
       await redis.del(`lock:${cacheKey}`);
     }
     ```

### Phase 5: Resilient Fallback & Conformance Audit
1. **Graceful DB Fallback**:
   - Catch Redis connection errors; never throw unhandled 500 errors to users when the cache layer experiences network hiccups or failover.
2. **Run Conformance Audit**:
   ```bash
   python3 shared/caching-and-in-memory-store/skills/scripts/audit_caching_patterns.py ./src --strict
   ```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [Caching Architecture & Stampede Prevention](references/caching-architecture-and-stampede-prevention.md) for XFetch probabilistic formulas, L1 vs L2 trade-offs, and Redis cluster failover.
- **Production Template**: Review [cache-aside-orchestrator.template.ts](assets/cache-aside-orchestrator.template.ts) for production TypeScript multi-tier cache orchestrator with mutex stampede guards.
- **CLI Auditor**: Execute [audit_caching_patterns.py](scripts/audit_caching_patterns.py) to detect unbounded maps and missing TTLs.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| Unbounded in-memory maps (`const cache = new Map()`) | Bounded LRU cache with strict `max` items and TTL eviction | Inevitable process Out-Of-Memory (OOM) crash under sustained production load. |
| Writing to Redis without TTL (`redis.set(key, val)`) | Mandatory explicit TTL expiration (`'EX', 300`) | Un-expiring zombie keys saturate Redis memory, triggering uncontrolled LRU evictions. |
| Un-namespaced flat keys (`redis.set("user_123", ...)`)| Hierarchical namespacing (`user-svc:profile:123:v1`) | Key collisions across services sharing Redis, corrupting multi-tenant or entity data. |
| Concurrent DB stampede on hot key expiration | Distributed mutex locking (`SET NX EX`) or probabilistic early expiration | Thousands of concurrent requests hit the database simultaneously, crashing connection pools. |
| Crashing HTTP request when Redis is unreachable | Wrap cache calls in try/catch and gracefully fall back to DB | Makes caching layer a catastrophic Single Point of Failure (SPOF) for application availability. |
| Storing unencrypted auth tokens or passwords in cache | Never cache bearer tokens or credentials; store opaque sessions | Exposes critical credentials to compromise if Redis instances are inspected or leaked. |
