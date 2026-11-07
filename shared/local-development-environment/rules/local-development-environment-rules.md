---
trigger: model_decision
description: "Enforces one-command local stack setup (docker-compose.yml with healthchecks on all services), .env.example credential parity with docker-compose.yml, Mailhog email catcher preventing real email sends, pinned Docker image tags, and scripts/setup-local.sh single-command onboarding."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Local Development Environment Standards

## Description
Enforces production engineering standards for local development environment setup. Mandates a `docker-compose.yml` in the repository root covering all required infrastructure services (PostgreSQL, Redis, message broker, mail catcher, database admin UI) with explicit `healthcheck` definitions and `depends_on: condition: service_healthy` dependency ordering (preventing the application from starting before its dependencies are ready), pinned Docker image tags (never `latest`), exact credential parity between `docker-compose.yml` environment variables and `.env.example` values, a Mailhog mail catcher preventing real email delivery during local development, and an idempotent `scripts/setup-local.sh` one-command setup script enabling new engineers to go from `git clone` to a running local stack in under 5 minutes.

## Constraints

### 1. Docker Compose — Healthchecks on All Services
- Every infrastructure service in `docker-compose.yml` MUST define a `healthcheck` block.
- Postgres healthcheck: `pg_isready -U {user} -d {db}`, interval 5s, retries 10.
- Redis healthcheck: `redis-cli ping`, interval 5s, retries 10.
- Services depending on Postgres or Redis MUST declare `depends_on: {service}: condition: service_healthy`.
- Docker image tags MUST be pinned to specific versions — `latest` tag is STRICTLY FORBIDDEN.

### 2. Credential Parity Between docker-compose.yml and .env.example
- Every username, password, and connection parameter defined in `docker-compose.yml` environment variables MUST have a corresponding variable in `.env.example`.
- The `.env.example` connection string values MUST exactly match the `docker-compose.yml` credentials.
- Credential mismatch between these two files is STRICTLY FORBIDDEN — it causes silent connection failures.
- Every variable in `.env.example` MUST include a descriptive comment explaining what it does and its expected format.

### 3. Mail Catcher Mandatory
- `docker-compose.yml` MUST include a Mailhog (or equivalent mail catcher) service.
- Application SMTP configuration in `.env.example` MUST default to `SMTP_HOST=localhost` and `SMTP_PORT=1025`.
- This prevents real emails from being sent to real users during local development and testing.

### 4. One-Command Setup Script
- A `scripts/setup-local.sh` script MUST exist in the repository.
- The script MUST be idempotent: safe to run multiple times without side effects.
- Script MUST: copy `.env.example` to `.env` if not present, run `docker compose up -d --wait`, install dependencies, run migrations, seed development data, and print a local service URL table.
- The README Quick Start section MUST be verified: a new engineer MUST be able to complete setup in under 5 minutes from `git clone`.

## Examples

### 1. Correct Docker Compose with Healthchecks
```yaml
# ✅ CORRECT: Pinned tags, healthchecks, credential parity
services:
  postgres:
    image: postgres:16-alpine          # ← pinned, not 'latest'
    environment:
      POSTGRES_USER: myapp             # ← matches DATABASE_URL in .env.example
      POSTGRES_PASSWORD: localpassword
      POSTGRES_DB: myapp_dev
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp -d myapp_dev"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine              # ← pinned
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10

  mailhog:
    image: mailhog/mailhog:v1.0.1     # ← pinned
    ports:
      - "1025:1025"   # SMTP
      - "8025:8025"   # Web UI
```

### 2. Forbidden — Missing Healthchecks
```yaml
# ❌ FORBIDDEN: No healthcheck — app starts before DB is ready
services:
  postgres:
    image: postgres:latest             # ← unpinned: breaking changes on pull
    environment:
      POSTGRES_USER: root              # ← different from .env.example (parity violation)
  app:
    depends_on:
      - postgres                       # ← no 'condition: service_healthy' — race condition
```
