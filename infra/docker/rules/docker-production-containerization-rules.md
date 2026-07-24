---
trigger: always_on
description: "Strict containerization rules for multi-stage Dockerfiles, non-root execution, multi-environment Compose configurations, and container healthchecks."
---

# Enterprise Docker Production Containerization Rules

## Description
Enforces mandatory constraints for authoring production Docker container images, Docker Compose environment splitting, and container security compliance.

## Constraints

### 1. Non-Root Container Execution Rule
- Final production runner images MUST execute under an unprivileged user (e.g. `USER node`).
- Running application containers as `root` in production is STRICTLY FORBIDDEN.

### 2. Multi-Environment Compose Separation Rule
- Local development configs (bind volume mounts, hot-reloading watchers) MUST reside exclusively in `docker-compose.override.yml`.
- Production deployment configs (built runner images, restart policies `unless-stopped`, resource limits) MUST reside in `docker-compose.prod.yml`.
- Production deployments MUST NOT use host bind mounts (`./:/app`) or development hot-reloading commands.

### 3. Container Healthcheck Requirement
- Production runner stages and background infrastructure services (PostgreSQL, Redis) MUST declare native `healthcheck` directives.
- Unmonitored containers without health status reporting are forbidden in production suites.

### 4. Layer Caching & Build Optimization
- Manifest files (`package.json`, `pnpm-lock.yaml`) MUST be copied and installed in separate Docker build stages prior to copying source code.
- Host `node_modules` and `.env` files MUST be excluded via `.dockerignore`.

### 5. User Clarification Requirement
- If database credentials, exposed ports, or service dependencies are ambiguous during container setup, agents MUST prompt the user for clarification before generating Compose files.
