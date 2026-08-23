---
description: "Workflow to scaffold enterprise multi-stage Dockerfiles and split multi-environment Docker Compose setups for ANY tech stack (Node/TypeScript, Python, Go, Java, PHP, Rust) and ANY database/middleware (PostgreSQL, MySQL, MongoDB, Redis, Kafka, RabbitMQ, MinIO). Triggered by 'docker:', 'compose:', or '/setup-docker-environment'."
trigger: manual
---

# Universal Dynamic Setup Docker & Multi-Environment Compose Workflow

Follow this step-by-step workflow to scaffold enterprise-grade Docker containerization into any application repository regardless of tech stack or infrastructure components.

## Steps

### Step 1: Dynamic Project Stack & Middleware Detection
1. Inspect project root files:
   - `package.json` -> Node.js / TypeScript (NestJS, Angular, Express, Next.js)
   - `requirements.txt` / `pyproject.toml` -> Python (FastAPI, Django, Flask)
   - `go.mod` -> Go (Gin, Fiber, Echo)
   - `pom.xml` / `build.gradle` -> Java / Kotlin (Spring Boot, Micronaut)
   - `composer.json` -> PHP (Laravel, Symfony)
   - `Cargo.toml` -> Rust (Actix, Axum)
2. Detect database / middleware dependencies (PostgreSQL, MySQL, MongoDB, Redis, RabbitMQ, Kafka, MinIO).
3. Determine image registry namespace:
   - Always format image tags as `<username>/<project-name>:latest`
4. If stack or deployment mode is ambiguous:
   - **STOP** and ask the user for clarification before generating files.

### Step 2: Scaffold Multi-Stage Dockerfile & `.dockerignore`
1. Generate multi-stage `Dockerfile` tailored to the detected language/runtime:
   - Use official slim or alpine base images (`node:22-alpine`, `python:3.11-slim`, `golang:1.22-alpine`, `eclipse-temurin:21-jre-alpine`).
   - Implement package manager cache mounts (`RUN --mount=type=cache`).
   - Enforce non-root execution (`USER node`, `USER appuser`, `USER postgres`).
   -  always set values from .env variable name not hardcode. 
   - Set `ENV PORT=3000` default and `EXPOSE ${PORT}` dynamically. always set port by .env variable name not hardcode.
   - Implement `HEALTHCHECK` directive targeting IPv4 and API global prefix:
     `CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:${PORT:-3000}/api/v1 || exit 1`
   - Include automated DB migration entrypoint wrapper script (`scripts/docker-entrypoint.sh`) using local `./node_modules/.bin/prisma migrate deploy` for offline-capable execution.
2. Create `.dockerignore` excluding dependencies, local caches, git history, and secrets.

### Step 3: Scaffold Mandatory 6-File Modular Docker Compose Topology
Generate all 6 split Compose files to support all execution modes:
- always set values from .env variable name not hardcode. Ex: ${JWT_SECRET:-dev_jwt_secret}
1. `docker-compose.yml`: Primary application service definition, networks, named volumes, `${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}` port mapping, and `${JWT_SECRET:-dev_jwt_secret}` default fallbacks.
2. `docker-compose.override.yml`: Local Development overrides (bind volume mounts, hot-reloading command).
3. `docker-compose.prod.yml`: Standalone production overrides (`restart: unless-stopped`, resource CPU/memory limits, json-file logging).
4. `docker-compose.shared.yml`: Dedicated standalone backing infrastructure services (Postgres + pgvector, MySQL, MongoDB, Redis + RedisInsight, healthchecks).
5. `docker-compose.existing-infra.yml`: Cost-saver infrastructure overrides connecting the application container to an existing external network (`db_network`, `redis_network`), specifying `target: runner`, `env_file: - .env`, and dynamic `${DB_HOST:-pgvector-db}` fallbacks.
6. `docker-compose.repo.yml`: Pre-built remote image overrides referencing `<username>/<project-name>:latest` instead of a local build context.

> [!CRITICAL]
> **ZERO-HARDCODED SECRETS & DYNAMIC PORT POLICY**
> - NEVER hardcode passwords, API keys, JWT secrets, or port numbers inside any Docker Compose file or Dockerfile.
> - All ports MUST be mapped dynamically via `${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}`.
> - All credentials MUST be interpolated dynamically from `.env` (e.g., `${DB_PASSWORD}`, `${POSTGRES_PASSWORD}`, `${REDIS_PASSWORD}`, `${JWT_SECRET}`).
> - Ensure `.env.example` contains clear placeholder values (`DB_PASSWORD=your_db_password_here`, `JWT_SECRET=your_jwt_secret_here`) accompanied by descriptive comments.

### Step 4: Update Project README.md Documentation
Append a dedicated `## 🐳 Docker Containerization & Execution Guide` section to the project's `README.md` detailing:

#### 1. Local Machine Build & Registry Push
```bash
# Build lightweight production runner stage locally
docker build --target runner -t <username>/<repository>:latest .

# Authenticate and push image to Container Registry (Docker Hub)
docker push <username>/<project-name>:latest
```

#### 2. Remote VPS Server Deployment Modes
- **Mode A: Standalone Infrastructure Mode** (Dedicated Postgres + Redis containers):
  ```bash
  docker compose -f docker-compose.shared.yml -f docker-compose.yml -f docker-compose.prod.yml up -d --build
  ```
- **Mode B: Shared Infrastructure Cost-Saver Mode** (Connecting to existing database network with server-side build):
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml up -d --build
  ```
- **Mode C: Recommended Remote Registry Mode** (Zero VPS CPU build load using pre-built image):
  ```bash
  # First time deployment or ongoing code updates
  docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always
  
  # Clean up dangling image layers to save disk space
  docker image prune -f
  ```

### Step 5: Verification & Container Testing
1. Run syntax verification on generated `Dockerfile` and all 6 `docker-compose*.yml` files.
2. Verify non-root user execution, healthchecks, and registry image tags are correctly configured.
