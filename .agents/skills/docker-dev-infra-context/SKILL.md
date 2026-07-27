---
name: docker-dev-infra-context
description: Architecture, modular directory layout (postgres with pgvector, redis cache), container specifications, environment variable management, healthchecks, initialization scripts, and CLI controls for Murali's docker-dev-infra repository (muralitharan805/docker-dev-infra).
---

# `docker-dev-infra` Product Architecture & Configuration Specification

## Overview

**`docker-dev-infra`** ([`muralitharan805/docker-dev-infra`](https://github.com/muralitharan805/docker-dev-infra)) is Seyalicraft's dedicated DevOps & Infrastructure project. It provides modular, production-ready Docker Compose templates, container configurations, and initialization scripts for local microservice development and production cloud deployment across all Seyalicraft product suites (`seyalicraft-frontend`, `nidhiflow`, `civicpath`).

Instead of bundling all services into a single monolithic Compose file, `docker-dev-infra` organizes infrastructure into **decoupled service modules** (`postgres/`, `redis/`, etc.) that can be started independently or combined.

---

## Infrastructure Module Catalog

```
docker-dev-infra/
├── postgres/                 # PostgreSQL + pgvector Database Service Module
│   ├── Dockerfile            # Custom Postgres build with pgvector extension
│   ├── docker-compose.yml    # Service definition with healthchecks & volume mounts
│   ├── .env.example          # Parameterized DB environment variables
│   ├── init-scripts/         # Auto-executed SQL scripts (01-init-pgvector.sql)
│   └── README.md
│
├── redis/                    # Redis Cache & In-Memory Store Module
│   ├── docker-compose.yml    # Service definition with healthchecks
│   ├── config/redis.conf     # Custom Redis memory limit & persistence config
│   ├── .env.example          # Environment variables
│   └── README.md
│
└── .agents/                  # AI Agent Context & Local Rules
```

---

## Detailed Service Specifications

### 1. PostgreSQL Module (`postgres/`)

- **Primary Image**: `postgres:16-alpine` with `pgvector` compilation/extension.
- **Key Features**:
  - **`pgvector` Support**: Enables vector similarity search (`vector` type, HNSW indexes) for AI embeddings (e.g. NidhiFlow transaction categorization, document search).
  - **Auto Initialization**: Mounts `./init-scripts/*.sql` into `/docker-entrypoint-initdb.d/` for automatic extension creation (`CREATE EXTENSION IF NOT EXISTS vector;`) and schema creation on container first boot.
  - **Healthcheck**: `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}` (interval: 10s, timeout: 5s, retries: 5).
  - **Persistence**: Named volume `postgres_data` mapped to `/var/lib/postgresql/data`.

#### Sample `postgres/docker-compose.yml`:
```yaml
services:
  postgres:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dev-postgres
    restart: unless-stopped
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secretpassword}
      POSTGRES_DB: ${POSTGRES_DB:-devdb}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-admin} -d ${POSTGRES_DB:-devdb}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

---

### 2. Redis Module (`redis/`)

- **Primary Image**: `redis:7-alpine`.
- **Key Features**:
  - **Custom Configuration**: Mounts `./config/redis.conf` for maxmemory limits (`maxmemory 256mb`, `maxmemory-policy allkeys-lru`).
  - **Healthcheck**: `redis-cli ping` (interval: 10s, timeout: 5s, retries: 5).
  - **Persistence**: Mapped to `redis_data` volume for RDB/AOF snapshots.

#### Sample `redis/docker-compose.yml`:
```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: dev-redis
    restart: unless-stopped
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

---

## Operating Procedures & CLI Commands

### 1. Launching Services
```bash
# Spin up PostgreSQL + pgvector
cd postgres && docker compose up -d

# Spin up Redis
cd redis && docker compose up -d
```

### 2. Service Verification & Logs
```bash
# Check PostgreSQL status & health
docker compose -f postgres/docker-compose.yml ps

# View live PostgreSQL logs
docker compose -f postgres/docker-compose.yml logs -f

# Verify pgvector extension
docker exec -it dev-postgres psql -U admin -d devdb -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

---

## Security & Operational Standards

1. **Parameterization**: Never hardcode database credentials or host ports; always use `.env` files backed by `.env.example` templates.
2. **Resource Limits**: Define CPU and memory reservations for production containers.
3. **Volume Isolation**: Use named Docker volumes for database data persistence to prevent unintended data loss on container recreation.
