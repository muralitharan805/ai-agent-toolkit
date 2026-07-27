---
description: "Workflow to launch, verify, or add new infrastructure modules (Postgres pgvector, Redis, MinIO, RabbitMQ) into docker-dev-infra repository. Triggered by 'dev-infra:', 'docker-infra:', or '/setup-docker-dev-infra'."
trigger: manual
---

# Setup & Manage `docker-dev-infra` Workflow

This workflow guides the AI agent and DevOps engineer through launching existing infrastructure services (Postgres + pgvector, Redis) or scaffolding new service modules (MinIO, RabbitMQ, Kafka) within `docker-dev-infra`.

## Step 1: Select Infrastructure Action

1. **Launch Existing Module**: Spin up `postgres` (with pgvector) or `redis`.
2. **Scaffold New Module**: Add a new service module (e.g. `minio/`, `rabbitmq/`).
3. **Audit Health & Logs**: Check health status and active container connections.

---

## Step 2: Launch & Verify Services

### 1. Launch PostgreSQL with pgvector
```bash
cd postgres
cp .env.example .env
docker compose up -d
```

### 2. Launch Redis Cache Service
```bash
cd redis
cp .env.example .env
docker compose up -d
```

---

## Step 3: Verify Health & Extension Status

1. **Check Container Health**:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```
2. **Verify Postgres pgvector Extension**:
   ```bash
   docker exec -it dev-postgres psql -U admin -d devdb -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
   ```
3. **Verify Redis Response**:
   ```bash
   docker exec -it dev-redis redis-cli ping
   # Expected output: PONG
   ```

---

## Step 4: Scaffold New Service Module Pattern

When creating a new service module (e.g. `minio/`):
1. Create directory `minio/`.
2. Create `minio/docker-compose.yml` with healthcheck directive and named volume.
3. Create `minio/.env.example`.
4. Create `minio/README.md` with startup & credentials documentation.
