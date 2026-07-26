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
3. If stack or deployment mode is ambiguous:
   - **STOP** and ask the user for clarification before generating files.

### Step 2: Scaffold Multi-Stage Dockerfile & `.dockerignore`
1. Generate multi-stage `Dockerfile` tailored to the detected language/runtime:
   - Use official slim or alpine base images (`node:20-alpine`, `python:3.11-slim`, `golang:1.22-alpine`, `eclipse-temurin:21-jre-alpine`).
   - Implement package manager cache mounts (`RUN --mount=type=cache`).
   - Enforce non-root execution (`USER node`, `USER appuser`, `USER postgres`).
   - Implement `HEALTHCHECK` directive.
   - Include automated DB migration entrypoint wrapper script (`docker-entrypoint.sh`).
2. Create `.dockerignore` excluding dependencies, local caches, git history, and secrets.

### Step 3: Scaffold Modular Multi-Environment Docker Compose Files
Generate split Compose files based on requested components:
1. `docker-compose.yml`: Shared base service definitions, bridge networks, and volume definitions.
2. `docker-compose.override.yml`: Local Development overrides (bind volume mounts, hot-reloading command).
3. `docker-compose.prod.yml`: Production overrides (`restart: unless-stopped`, resource CPU/memory limits, json-file logging).
4. `docker-compose.shared.yml`: Standalone infrastructure services (Postgres + pgvector, MySQL, MongoDB, Redis + RedisInsight, RabbitMQ, Kafka, MinIO, healthchecks).
5. `docker-compose.existing-infra.yml`: Shared cost-saver overrides connecting application container to existing running infrastructure containers via external Docker network (`shared-infra-network`).

### Step 4: Update Project README.md Documentation
Append a dedicated `## 🐳 Docker Containerization & Execution Guide` section to the project's `README.md` detailing:
- Commands for Mode A: Standalone dev environment (`docker compose -f docker-compose.shared.yml -f docker-compose.yml up -d`).
- Commands for Mode B: Shared cost-saver environment (`docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml up -d`).
- Commands for Production deployment (`docker compose -f docker-compose.shared.yml -f docker-compose.yml -f docker-compose.prod.yml up -d --build`).

### Step 5: Verification & Container Testing
1. Run syntax verification on generated `Dockerfile` and `docker-compose*.yml` files.
2. Verify non-root user execution and healthchecks are correctly configured.
