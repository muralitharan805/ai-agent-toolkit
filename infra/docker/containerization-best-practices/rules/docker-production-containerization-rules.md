---
description: "Strict containerization rules for multi-stage Dockerfiles, non-root execution, multi-environment Compose configurations, and container healthchecks."
trigger: model_decision
---

# Enterprise Docker Production Containerization Rules

## Description
Enforces mandatory constraints for authoring production Docker container images, Docker Compose environment splitting, non-root user execution, and container security compliance across all deployment environments.

## Constraints

### 1. Non-Root Container Execution Rule
- Final production runner images MUST execute under an unprivileged user (e.g. `USER node`, `USER appuser`, or `USER 10001`).
- Running application containers as `root` in production is STRICTLY FORBIDDEN.

### 2. Mandatory 6-File Compose Topology & Multi-Environment Separation Rule
- All containerized projects MUST scaffold and support the mandatory 6-file Docker Compose topology:
  1. `docker-compose.yml`: Primary application service definition, bridge networks, and named persistent volumes.
  2. `docker-compose.override.yml`: Local development overrides (bind volume mounts, hot-reloading development command).
  3. `docker-compose.prod.yml`: Standalone production environment overrides (`restart: unless-stopped`, resource CPU/memory limits, json-file logging).
  4. `docker-compose.shared.yml`: Dedicated standalone backing infrastructure services (PostgreSQL + pgvector, Redis + RedisInsight, healthchecks).
  5. `docker-compose.existing-infra.yml`: Cost-saver infrastructure overrides connecting the application container to an existing external network (`db_network`, `redis_network`).
  6. `docker-compose.repo.yml`: Pre-built remote image overrides specifying the container registry image tag (`image: <username>/<repository>:<tag>`).

### 3. Remote Image Registry Deployment Rule (No VPS Compilation)
- Production VPS deployments MUST NOT execute image compilation or multi-stage builds (`docker compose up -d --build`) on resource-constrained target servers.
- Images MUST be built locally or in CI (`docker build --target runner -t <username>/<repository>:<tag> .`) and pushed to Docker Hub or Container Registry (`docker push <username>/<repository>:<tag>`).
- VPS deployments MUST pull pre-built images using the `docker-compose.repo.yml` layer (`docker compose -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always`).

### 4. Zero Hardcoded Secrets & Dynamic Port Policy
- NEVER hardcode passwords, API keys, JWT secrets, or port numbers inside any Docker Compose file or Dockerfile.
- All ports MUST be mapped dynamically via `${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}`.
- All credentials MUST be interpolated dynamically from `.env` (e.g., `${DB_PASSWORD}`, `${JWT_SECRET}`).

### 5. Container Healthcheck Requirement
- Production runner stages and background infrastructure services (PostgreSQL, Redis) MUST declare native `healthcheck` directives.
- Dependent services in Compose MUST use `condition: service_healthy` rather than bare network dependency.

### 6. Layer Caching & Build Optimization
- Manifest files (`package.json`, `pnpm-lock.yaml`) MUST be copied and installed in separate Docker build stages prior to copying source code.
- Host `node_modules` and `.env` files MUST be excluded via `.dockerignore`.

## Examples

### 1. Non-Root Execution vs Root Execution
```dockerfile
# ❌ FORBIDDEN: Missing USER instruction leaves container running as root
FROM node:22-alpine
WORKDIR /app
COPY . .
CMD ["node", "dist/main.js"]

# ✅ CORRECT: Explicit unprivileged user execution with pre-assigned permissions
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder --chown=node:node /app/dist ./dist
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 2. Compose Zero-Hardcoding & Dynamic Port Mapping
```yaml
# ❌ FORBIDDEN: Hardcoded credentials and static port bindings
services:
  app:
    image: my-app:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://admin:secret123@localhost:5432/db

# ✅ CORRECT: Interpolated environment variables with safe fallbacks and dynamic port mapping
services:
  app:
    image: ${IMAGE_NAME:-my-app:latest}
    ports:
      - "${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}"
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD}@${DB_HOST:-postgres}:${DB_PORT:-5432}/${DB_NAME:-app}
      - JWT_SECRET=${JWT_SECRET:-dev_jwt_secret}
```

### 3. Condition-Based Service Health Sequencing
```yaml
# ❌ FORBIDDEN: Bare depends_on without healthcheck validation
services:
  app:
    depends_on:
      - postgres-db # Container may start before database is ready to accept connections!

# ✅ CORRECT: Precise condition-based dependency sequencing
services:
  app:
    depends_on:
      postgres-db:
        condition: service_healthy
```
