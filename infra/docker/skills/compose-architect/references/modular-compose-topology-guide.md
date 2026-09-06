# The Mandatory 6-File Docker Compose Topology Guide

## Overview
In production container architectures, a single monolithic `docker-compose.yml` file cannot accommodate local development hot-reloading, standalone production isolation, cost-saving shared database networks, and pre-built registry images without creating fragile merge conflicts or security vulnerabilities.

The **Mandatory 6-File Topology** cleanly splits concerns across dedicated layer files combined deterministically at runtime.

---

## The 6 Modular Compose Files

### 1. `docker-compose.yml` (Base Application Definition)
- **Role**: Defines the core application container, internal private bridge network, volume declarations, and base environment variable fallbacks.
- **Port Mapping**: Always use dynamic variable interpolation:
  ```yaml
  ports:
    - "${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}"
  ```
- **Secrets**: Reference environment variables exclusively:
  ```yaml
  environment:
    - JWT_SECRET=${JWT_SECRET:-dev_jwt_secret}
    - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD}@${DB_HOST:-db}:${DB_PORT:-5432}/${DB_NAME:-app}
  ```

### 2. `docker-compose.override.yml` (Local Development)
- **Role**: Automatically merged by `docker compose up` during local development.
- **Behavior**: Binds local source directories into `/app` for hot-reloading, specifies dev run commands (`pnpm start:dev`), and enables debug ports.
- **Ignored in Production**: Never deploy `docker-compose.override.yml` to remote servers.

### 3. `docker-compose.prod.yml` (Standalone Production Overrides)
- **Role**: Production-hardening parameters for isolated deployments.
- **Configuration**:
  - `restart: unless-stopped`
  - Resource limits:
    ```yaml
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1024M
    ```
  - Structured logging driver (`json-file` with `max-size: 10m` and `max-file: 3`).

### 4. `docker-compose.shared.yml` (Backing Infrastructure)
- **Role**: Standalone backing services (PostgreSQL + pgvector, Redis + RedisInsight) with healthchecks and persistent named volumes.
- **Healthchecks**: Guarantees services are fully initialized before dependent applications connect.

### 5. `docker-compose.existing-infra.yml` (Cost-Saver Shared Network)
- **Role**: Connects the application container to an existing external network on the server (e.g., `db_network`, `redis_network`) instead of launching redundant database containers.
- **Network Declaration**:
  ```yaml
  networks:
    db_network:
      external: true
  ```

### 6. `docker-compose.repo.yml` (Pre-Built Remote Image Layer)
- **Role**: Overrides local build contexts with a pre-built container registry image tag.
- **Zero VPS Compilation**: Prevents memory exhaustion and CPU spikes on target VPS servers:
  ```yaml
  services:
    app:
      image: <username>/<repository>:latest
      build: !reset null
  ```

---

## Deployment Modes

### Mode A: Local Development
```bash
# Automatically combines docker-compose.yml and docker-compose.override.yml
docker compose up
```

### Mode B: Standalone Production on Dedicated Server
```bash
docker compose -f docker-compose.shared.yml -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Mode C: Cost-Saver Shared VPS Mode (Zero VPS Build)
```bash
# Pull pre-built image and attach to existing network
docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always

# Prune dangling image layers
docker image prune -f
```
