---
name: containerization-best-practices
description: "Enterprise guidelines, multi-stage Dockerfile patterns, multi-environment Docker Compose setups (dev, prod, shared, existing-infra cost saver), non-root security compliance, container healthchecks, and README execution instructions."
---

# Enterprise Containerization & Multi-Environment Docker Suite

## Goal
Guide developers and AI coding agents in authoring production-grade multi-stage Dockerfiles, modular multi-environment Docker Compose architectures (`docker-compose.yml`, `docker-compose.override.yml`, `docker-compose.prod.yml`, `docker-compose.shared.yml`, `docker-compose.existing-infra.yml`), and container execution documentation.

---

# Multi-Stage Dockerfile Architecture

### Principles:
1. **Layer Caching**: Copy lockfiles (`package.json`, `pnpm-lock.yaml`) and run dependency installation before copying source code.
2. **Minimal Runtime Footprint**: Use multi-stage builds so build tools, TypeScript compilers, and dev dependencies are omitted from the final runner image.
3. **Non-Root Execution Compliance**: Execute application processes under an unprivileged user (`USER node`).
4. **Health Check & Signal Handling**: Implement `HEALTHCHECK` instructions and handle OS signals (`SIGTERM`/`SIGINT`) gracefully.

### Enterprise NestJS Multi-Stage Dockerfile Pattern (`Dockerfile`):

```dockerfile
# Stage 1: Dependency Caching
FROM node:20-alpine AS deps
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Stage 2: Compilation & Asset Build
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build
RUN pnpm prune --prod

# Stage 3: Production Lightweight Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy production artifacts
COPY package.json pnpm-lock.yaml ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma

# Security Hardening
USER node
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/v1/health || exit 1

CMD ["node", "dist/main.js"]
```

---

# Deployment Modes & Docker Compose Architecture

Support two deployment modes depending on resource availability and infrastructure budget:

1. **Mode A: Standalone Infrastructure Mode (Default)**: Creates isolated application and dedicated Postgres/Redis containers for the project.
2. **Mode B: Shared Infrastructure Cost-Optimization Mode (Low-Resource VPS / POC)**: Connects to existing globally running PostgreSQL/Redis Docker containers on a shared Docker network (`shared-infra-network`), saving RAM, CPU, and disk storage.

---

### File Structure Overview:
```
project-root/
├── Dockerfile
├── .dockerignore
├── docker-compose.yml              # Base shared service definitions & networks
├── docker-compose.override.yml     # Development overrides (hot-reloading, bind mounts)
├── docker-compose.prod.yml         # Production overrides (restart policies, limits)
├── docker-compose.shared.yml       # Standalone DB dependencies (Postgres + pgvector, Redis)
└── docker-compose.existing-infra.yml # Shared DB mode (connects to existing Postgres/Redis container)
```

---

### Mode A: Standalone Database Compose (`docker-compose.shared.yml`)
Spawns dedicated PostgreSQL (`ankane/pgvector`) and Redis containers for this project:

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:v0.5.1
    container_name: nidhi-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres123}
      POSTGRES_DB: ${DB_NAME:-nidhiflow}
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - nidhi-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: nidhi-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    networks:
      - nidhi-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

### Mode B: Shared Infrastructure Cost-Optimization Compose (`docker-compose.existing-infra.yml`)
Connects application container to an existing running PostgreSQL/Redis container via an external Docker network:

```yaml
version: '3.8'

# Connects to existing running shared infrastructure container
services:
  app:
    environment:
      # Connects to shared Postgres DB host via external network
      - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres123}@shared-postgres:5432/${DB_NAME:-nidhiflow_db}?schema=public
      - REDIS_HOST=shared-redis
      - REDIS_PORT=6379
    networks:
      - shared-infra-network

networks:
  # External Docker network shared across multiple projects on the same server
  shared-infra-network:
    external: true
```

---

# README Execution Documentation Standard

Every project containerized with Docker MUST contain a dedicated section in `README.md` explaining exact commands for local development vs production deployment across both Standalone and Shared Infrastructure modes.

### README Template Section:

```markdown
## 🐳 Docker Containerization & Execution Guide

### 1. Mode A: Standalone Local Development (Dedicated DBs)
Starts application container with dedicated local PostgreSQL & Redis containers:

```bash
# Start standalone dev environment with hot-reloading & DB dependencies
docker compose -f docker-compose.shared.yml -f docker-compose.yml up -d

# View application logs
docker compose logs -f app

# Stop dev environment
docker compose down
```

### 2. Mode B: Shared Infrastructure Cost-Saver Mode (Existing Postgres/Redis)
Connects to an existing shared PostgreSQL & Redis container on a shared server to save RAM & storage:

```bash
# 1. Ensure shared external network exists
docker network create shared-infra-network || true

# 2. Launch application attached to existing shared DB container
docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml up -d

# 3. Execute database migrations for the new project DB
docker compose exec app pnpm db:migrate
```

### 3. Production Deployment Mode
Run production containers using the production override (`docker-compose.prod.yml`):

```bash
# Build & launch production containers in detached mode
docker compose -f docker-compose.shared.yml -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
```

---

# User Clarification Protocol

If environment variables, database credentials, exposed ports, or service dependencies are ambiguous during Docker setup:
1. **STOP** before writing invalid configurations.
2. Ask the user two specific questions:
   - **Q1**: Do you want **Standalone Mode** (new dedicated Postgres/Redis containers) or **Shared Infrastructure Mode** (attach to existing Postgres/Redis container)?
   - **Q2**: What is the target database name and port mapping?
3. Generate the precise Dockerfile and Compose setup based on user inputs.
