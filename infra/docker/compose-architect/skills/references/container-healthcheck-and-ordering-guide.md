# Container Healthchecks & Precise Dependency Sequencing

## Overview
Relying solely on network DNS resolution or bare container presence (`depends_on: [postgres]`) causes race conditions during system startup. Databases and message queues typically register their network ports before they finish running internal migrations or accepting incoming queries.

---

## 1. Backing Service Healthchecks

### PostgreSQL / PostGIS / pgvector
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-app_db}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
```

### Redis Cache
```yaml
services:
  redis:
    image: redis:7-alpine
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}"]
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
```

### Application HTTP Healthcheck
```yaml
services:
  app:
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://127.0.0.1:${PORT:-3000}/api/v1/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 20s
```

---

## 2. Condition-Based Dependency Startup
Downstream application containers MUST declare dependencies using `condition: service_healthy`:

```yaml
services:
  api:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

This ensures Docker delays starting the application container until all backing services have passed their operational healthchecks.
