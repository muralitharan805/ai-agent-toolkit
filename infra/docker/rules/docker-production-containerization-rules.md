---
trigger: always_on
description: "Strict containerization rules for multi-stage Dockerfiles, non-root execution, multi-environment Compose configurations, and container healthchecks."
---

# Enterprise Docker Production Containerization Rules

## Description
Enforces mandatory constraints for authoring production Docker container images, Docker Compose environment splitting, and container security compliance.

## Constraints

### 1. Non-Root Container Execution Rule
- Final production runner images MUST execute under an unprivileged user (e.g. `USER node` or `USER 10001`).
- Running application containers as `root` in production is STRICTLY FORBIDDEN.

```dockerfile
# Correct implementation
FROM node:20-alpine
WORKDIR /app
COPY --chown=node:node . .
USER node
CMD ["node", "server.js"]

# Incorrect implementation (FORBIDDEN: Missing USER instruction defaults to root)
FROM node:20-alpine
WORKDIR /app
COPY . .
CMD ["node", "server.js"]
```

### 2. Mandatory 6-File Compose Topology & Multi-Environment Separation Rule
- All containerized projects MUST scaffold and support the mandatory 6-file Docker Compose topology:
  1. `docker-compose.yml`: Primary application service definition, networks, and named volumes.
  2. `docker-compose.override.yml`: Local development overrides (bind volume mounts, hot-reloading development command).
  3. `docker-compose.prod.yml`: Standalone production environment overrides (`restart: unless-stopped`, resource CPU/memory limits, json-file logging).
  4. `docker-compose.shared.yml`: Dedicated standalone backing infrastructure services (PostgreSQL, Redis, RedisInsight, healthchecks).
  5. `docker-compose.existing-infra.yml`: Cost-saver infrastructure overrides connecting the application container to an existing, external container network (`db_network`, `redis_network`).
  6. `docker-compose.repo.yml`: Pre-built remote image overrides specifying the container registry image tag (`image: <username>/<repository>:<tag>`).

### 3. Remote Image Registry Deployment Rule (No VPS Compilation)
- Production VPS deployments MUST NOT execute image compilation or multi-stage builds (`docker compose up -d --build`) on resource-constrained target servers.
- Images MUST be built locally or in CI (`docker build --target runner -t <username>/<repository>:<tag> .`) and pushed to Docker Hub or Container Registry (`docker push <username>/<repository>:<tag>`).
- VPS deployments MUST pull pre-built images using the `docker-compose.repo.yml` layer (`docker compose -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always`).

### 4. Container Healthcheck Requirement
- Production runner stages and background infrastructure services (PostgreSQL, Redis) MUST declare native `healthcheck` directives.
- Unmonitored containers without health status reporting are forbidden in production suites.

### 5. Layer Caching & Build Optimization
- Manifest files (`package.json`, `pnpm-lock.yaml`) MUST be copied and installed in separate Docker build stages prior to copying source code.
- Host `node_modules` and `.env` files MUST be excluded via `.dockerignore`.

### 6. User Clarification Requirement
- If database credentials, exposed ports, or service dependencies are ambiguous during container setup, agents MUST prompt the user for clarification before generating Compose files.

