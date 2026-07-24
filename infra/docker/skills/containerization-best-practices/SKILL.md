---
name: containerization-best-practices
description: "Universal dynamic containerization guidelines, multi-stage Dockerfile patterns for any tech stack (Node/TypeScript, Python, Go, Java, PHP, Rust), split Docker Compose setups (dev, prod, shared, existing-infra cost saver) for any database/middleware (Postgres, MySQL, MongoDB, Redis, Kafka, RabbitMQ, MinIO), non-root security compliance, healthchecks, and README execution instructions."
---

# Universal Dynamic Containerization & Multi-Environment Docker Suite

## Goal
Guide developers and AI coding agents in dynamically generating production-grade multi-stage Dockerfiles and modular Docker Compose architectures for **ANY programming language, framework, database, or middleware stack** (Node.js/NestJS/Angular/Next.js, Python/FastAPI/Django, Go, Java/Spring Boot, PHP/Laravel, Rust, PostgreSQL, MySQL, MongoDB, Redis, Kafka, RabbitMQ, MinIO, etc.).

---

# Universal Stack Detection & Multi-Stage Dockerfile Engine

The agent MUST dynamically inspect the project repository structure to identify the runtime stack, package manager, and build tool:

| Detected Stack File | Language / Runtime | Build Tool / Package Manager | Base Image Standard | Runner Target |
| :--- | :--- | :--- | :--- | :--- |
| `package.json` | Node.js / TypeScript | `pnpm` / `npm` / `yarn` | `node:20-alpine` | `node dist/main.js` / `nginx:alpine` |
| `requirements.txt` / `pyproject.toml` | Python | `pip` / `poetry` | `python:3.11-slim` | `uvicorn main:app --host 0.0.0.0` |
| `go.mod` | Go | Go Modules | `golang:1.22-alpine` (builder) ➔ `alpine:latest` | `./main` |
| `pom.xml` / `build.gradle` | Java / Kotlin | Maven / Gradle | `eclipse-temurin:21-jdk` ➔ `eclipse-temurin:21-jre-alpine` | `java -jar app.jar` |
| `composer.json` | PHP | Composer | `php:8.3-fpm-alpine` + `nginx:alpine` | `php-fpm` |
| `Cargo.toml` | Rust | Cargo | `rust:1.75-slim` ➔ `debian:bookworm-slim` | `./app` |

---

# Multi-Stage Build Patterns Across Major Stacks

### 1. Node.js / TypeScript (NestJS / Express / Next.js)

```dockerfile
# Stage 1: Dependency Caching
FROM node:20-alpine AS deps
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.cache/pnpm pnpm install --frozen-lockfile

# Stage 2: Compilation
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build
RUN pnpm prune --prod

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package.json ./
COPY docker-entrypoint.sh ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
RUN chmod +x docker-entrypoint.sh
USER node
EXPOSE 3000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["node", "dist/main.js"]
```

### 2. Python (FastAPI / Django / Flask)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Runner
FROM python:3.11-slim AS runner
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Go (Gin / Fiber / Echo)

```dockerfile
# Stage 1: Build
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .

# Stage 2: Minimal Alpine Runner
FROM alpine:3.19 AS runner
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /app/server .
RUN adduser -D -u 10001 appuser
USER appuser
EXPOSE 8080
CMD ["./server"]
```

---

# Universal Dynamic Multi-Environment Docker Compose Architecture

The Compose generator MUST dynamically adapt service blocks based on detected or user-requested infrastructure components:

### Universal Infrastructure Map:

| Infrastructure Service | Docker Image Standard | Default Port | Native Healthcheck Test |
| :--- | :--- | :--- | :--- |
| **PostgreSQL + pgvector** | `ankane/pgvector:v0.5.1` / `postgis/postgis:16-3.5-alpine` | `5432` | `["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]` |
| **MySQL / MariaDB** | `mysql:8.0` / `mariadb:11` | `3306` | `["CMD", "mysqladmin", "ping", "-h", "localhost"]` |
| **MongoDB** | `mongo:7.0` | `27017` | `["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]` |
| **Redis / KeyDB** | `redis:7.2-alpine` | `6379` | `["CMD", "redis-cli", "-a", "$$REDIS_PASSWORD", "ping"]` |
| **RabbitMQ** | `rabbitmq:3.12-management-alpine` | `5672`, `15672` | `["CMD", "rabbitmq-diagnostics", "-q", "ping"]` |
| **Apache Kafka** | `confluentinc/cp-kafka:7.5.0` | `9092` | `["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]` |
| **Meilisearch** | `getmeili/meilisearch:v1.6` | `7700` | `["CMD", "curl", "-f", "http://localhost:7700/health"]` |
| **MinIO (S3 Storage)** | `minio/minio:latest` | `9000`, `9001` | `["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]` |

---

### Deployment Modes:

1. **Mode A: Standalone Infrastructure Mode (Default)**: Creates isolated application and dedicated DB/middleware containers for the project.
2. **Mode B: Shared Infrastructure Cost-Optimization Mode (Low-Resource VPS / POC)**: Connects to existing globally running DB/middleware Docker containers on a shared Docker network (`shared-infra-network`), saving RAM, CPU, and disk storage.

---

### Universal Split Compose File Structure:
```text
project-root/
├── Dockerfile
├── docker-entrypoint.sh
├── .dockerignore
├── docker-compose.yml              # Base service definitions & networks
├── docker-compose.override.yml     # Local Development overrides (hot-reloading, bind mounts)
├── docker-compose.prod.yml         # Production overrides (restart policies, resource limits)
├── docker-compose.shared.yml       # Standalone DB/middleware dependencies
└── docker-compose.existing-infra.yml # Shared DB mode (connects to existing shared containers)
```

---

# README Execution Documentation Standard

Every generated Docker setup MUST include a dedicated section in `README.md` explaining exact commands for local development vs production deployment across both Standalone and Shared Infrastructure modes.

---

# Dynamic User Clarification Protocol

If the tech stack, database type, environment variables, exposed ports, or deployment mode are ambiguous:
1. **STOP** before writing invalid or hardcoded configurations.
2. Prompt the user with specific options:
   - **Stack & Package Manager**: (Node/NestJS, Python, Go, Java, PHP, Rust, etc.)
   - **Database / Middleware**: (PostgreSQL, MySQL, MongoDB, Redis, RabbitMQ, Kafka, MinIO, etc.)
   - **Deployment Mode**: (Standalone dedicated containers vs Shared existing container network)
3. Generate the precise Dockerfile and Compose setup matching the user's answers.
