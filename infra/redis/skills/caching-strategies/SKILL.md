---
name: caching-strategies
description: "Best practices for Redis caching patterns, key namespace conventions, TTL expiry settings, cache invalidation, and data serialization."
---
# Goal
Guide the agent in implementing high-performance, fault-tolerant Redis caching strategies for API query results and session stores.

# Instructions
1. Use consistent, colon-delimited key namespacing: `<environment>:<service>:<entity>:<id>` (e.g. `prod:user-service:user:1024`).
2. Always set explicit Time-To-Live (TTL) expiration on cached keys to prevent stale data accumulation.
3. Implement Cache-Aside (Lazy Loading) or Write-Through pattern systematically.
4. Handle Redis connection failures gracefully by falling back to primary database queries without crashing the service.
5. Use JSON serialization or MessagePack for complex object payloads.

# Constraints
- Do NOT set keys without a TTL unless explicitly required for persistent configuration.
- Do NOT allow Redis downtime to break critical application request handlers.
