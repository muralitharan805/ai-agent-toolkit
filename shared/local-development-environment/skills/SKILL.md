---
name: local-development-environment
description: "Enforces one-command local stack setup (docker-compose.yml with healthchecks), service credential parity between .env.example and docker-compose.yml, mail catcher integration (Mailhog), hot reload configuration per language, and sub-5-minute new engineer onboarding. Triggered by 'local-dev:', 'docker-compose:', 'local-setup:', 'onboarding:', or '/local-development-environment'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Local Development Environment Skill

## Overview

This skill establishes production engineering standards for **One-Command Local Stack Initialization** (`docker compose up`), **Docker Compose Service Healthchecks** (prevents app starting before DB is ready), **`.env.example` ↔ `docker-compose.yml` Credential Parity**, **Mailhog Email Catcher** (prevents real emails during development), **Hot Reload per Language/Framework**, and **`scripts/setup-local.sh` Single Setup Script**. It guarantees a new engineer goes from `git clone` to a fully running local stack in under 5 minutes.

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Local Development Stack Architecture                │
│                                                                        │
│  docker-compose.yml                                                    │
│  ├── postgres:16-alpine        ← Primary DB (port 5432)               │
│  ├── redis:7-alpine            ← Cache + Sessions + Rate Limit (6379) │
│  ├── rabbitmq:3-management     ← Message Queue (5672 + UI 15672)       │
│  ├── mailhog                   ← Email catcher (SMTP 1025, UI 8025)    │
│  └── adminer                   ← DB browser UI (8080)                 │
│                                                                        │
│  scripts/setup-local.sh                                                │
│  └── cp .env.example → .env → docker compose up → install → migrate   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3-Phase Execution Guide

### Phase 1: Docker Compose Stack Definition
1. **Pin image tags** — never use `latest` (use `postgres:16-alpine`, `redis:7-alpine`):
   - Prevents unexpected breaking changes on `docker pull`.
2. **Healthchecks on every service**:
   - Postgres: `pg_isready -U {user} -d {db}` every 5s, 10 retries.
   - Redis: `redis-cli ping` every 5s, 10 retries.
   - RabbitMQ: `rabbitmq-diagnostics ping` every 10s.
3. **`depends_on: condition: service_healthy`** on every service that needs the above:
   - Without this → app starts before DB is ready → intermittent "connection refused" errors.
4. **Named volumes** for persistent data across `docker compose down` / `up` cycles.
5. **Include Mailhog** — configures app's SMTP settings to `localhost:1025`.
   - All emails are caught locally — zero risk of sending real emails to real users.

### Phase 2: `.env.example` Parity & Credential Matching
1. **Every credential in `docker-compose.yml` MUST have a matching var in `.env.example`**:
   - `POSTGRES_USER: myapp` → `DATABASE_URL="postgresql://myapp:..."`
   - `RABBITMQ_DEFAULT_USER: myapp` → `RABBITMQ_URL="amqp://myapp:..."`
2. **Mismatched credentials** = silent setup failure — app connects with wrong password.
3. **Every `.env.example` variable** MUST have a descriptive comment explaining what it does and where to find the value.

### Phase 3: Setup Script & Hot Reload
1. **`scripts/setup-local.sh`** — one-command idempotent setup:
   - Check if `.env` exists → if not, copy from `.env.example`.
   - `docker compose up -d --wait` (waits for all healthchecks to pass).
   - Install dependencies (`pnpm install`).
   - Run migrations (`pnpm db:migrate`).
   - Seed dev data (`pnpm db:seed:dev`).
   - Print local service URL table.
2. **Hot reload** — no manual restart needed for code changes:
   - Node.js NestJS: `tsx watch src/main.ts`.
   - Python FastAPI: `uvicorn main:app --reload`.
   - Go: `air` (github.com/air-verse/air).
   - Java Spring: Spring DevTools dependency.

---

## Local Service Port Reference
```
Service       Port    URL / Access
──────────────────────────────────────────────────────────────────────
App (dev)     3000    http://localhost:3000
API Docs      3000    http://localhost:3000/docs
PostgreSQL    5432    postgresql://myapp:localpassword@localhost:5432/myapp_dev
Redis         6379    redis://localhost:6379
RabbitMQ      5672    amqp://myapp:localpassword@localhost:5672
RabbitMQ UI   15672   http://localhost:15672 (user: myapp / localpassword)
Mailhog SMTP  1025    smtp://localhost:1025 (no auth needed locally)
Mailhog UI    8025    http://localhost:8025
Adminer UI    8080    http://localhost:8080
```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/docker-compose-and-local-stack-guide.md](references/docker-compose-and-local-stack-guide.md) for complete docker-compose.yml templates, healthcheck configurations, and per-language hot reload setup.
- **Production Asset**: Inspect [assets/docker-compose.local.yml](assets/docker-compose.local.yml) for a complete ready-to-use local development stack template.
- **CLI Auditor Tool**: Execute [scripts/audit_local_dev_setup.py](scripts/audit_local_dev_setup.py) to verify healthchecks, credential parity, and `.env.example` completeness.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Risk |
| :--- | :--- | :--- | :--- |
| **Image Tags** | `image: postgres:latest` | `image: postgres:16-alpine` (pinned) | Breaking changes on next `docker pull` |
| **Healthchecks** | No `healthcheck` + `depends_on` | All services define healthcheck conditions | App starts before DB ready → crash loops |
| **Email** | No mail catcher | Mailhog on SMTP port 1025 | Local dev sends real emails to real users |
| **Credential Parity** | `.env.example` doesn't match docker-compose | 1:1 credential match between both files | Silent auth failure on `docker compose up` |
| **Setup Friction** | 15-step manual README | `./scripts/setup-local.sh` one command | New engineer spends hours setting up |
| **Hot Reload** | Manual restart on code change | Language-specific hot reload configured | Developer flow broken — productivity loss |
| **No README Test** | README never verified by fresh eyes | Verify: clone → setup → running in < 5 min | Onboarding fails silently for months |
