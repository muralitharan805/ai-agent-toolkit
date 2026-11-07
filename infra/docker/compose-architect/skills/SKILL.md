---
name: compose-architect
description: "Expert skill for designing multi-container systems, 6-file modular Compose topologies, environment splitting, zero-VPS builds, and healthcheck sequencing."
---

# Docker Compose Architect Skill

## Purpose
Establishes production-grade multi-container orchestration standards using Docker Compose (v2.x+), the mandatory 6-file modular topology, dynamic port mapping, zero-compilation remote registry deployments, and condition-based healthcheck sequencing.

## Architecture & Tooling Matrix
- **Modular Topology Guide**: [references/modular-compose-topology-guide.md](references/modular-compose-topology-guide.md)
- **Healthcheck Sequencing Guide**: [references/container-healthcheck-and-ordering-guide.md](references/container-healthcheck-and-ordering-guide.md)
- **Automated CLI Validator**: [scripts/validate_docker_compose.py](scripts/validate_docker_compose.py)
- **Starter Templates**:
  - Base App: [assets/docker-compose.yml](assets/docker-compose.yml)
  - Local Override: [assets/docker-compose.override.yml](assets/docker-compose.override.yml)
  - Production Hardening: [assets/docker-compose.prod.yml](assets/docker-compose.prod.yml)
  - Backing Infrastructure: [assets/docker-compose.shared.yml](assets/docker-compose.shared.yml)
  - Cost-Saver External Network: [assets/docker-compose.existing-infra.yml](assets/docker-compose.existing-infra.yml)
  - Remote Registry Layer: [assets/docker-compose.repo.yml](assets/docker-compose.repo.yml)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Environment & Dependency Discovery
1. Inspect project root to identify database, cache, and message queue dependencies (PostgreSQL, Redis, RabbitMQ, MongoDB).
2. Determine required environment variables (`PORT`, `JWT_SECRET`, `DATABASE_URL`, `REDIS_PASSWORD`).
3. If database credentials or exposed ports are ambiguous, prompt the user for clarification before scaffolding files.

### Phase 2: Mandatory 6-File Modular Compose Scaffolding
Scaffold the complete 6-file modular topology to support all deployment environments:
1. `docker-compose.yml`: Primary app definition, internal bridge network, and volume declarations.
2. `docker-compose.override.yml`: Local development bind mounts and hot-reloading command (`pnpm run start:dev`).
3. `docker-compose.prod.yml`: Standalone production overrides (resource CPU/memory limits, restart policy, logging driver).
4. `docker-compose.shared.yml`: Standalone backing infrastructure (Postgres + pgvector, Redis) with persistent volumes.
5. `docker-compose.existing-infra.yml`: Cost-saver infrastructure overrides connecting the container to an external network (`db_network`, `redis_network`).
6. `docker-compose.repo.yml`: Pre-built remote image overrides specifying `<username>/<project-name>:latest` to eliminate VPS build load.

### Phase 3: Dynamic Port Mapping & Zero-Hardcoded Secrets
1. Map all exposed ports dynamically using variable interpolation:
   ```yaml
   ports:
     - "${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}"
   ```
2. Bind all sensitive credentials exclusively from `.env` variables (`${DB_PASSWORD}`, `${JWT_SECRET}`).
3. Ensure `.env.example` lists all required parameters with descriptive comments.

### Phase 4: Condition-Based Healthcheck Dependency Sequencing
1. Implement native container healthchecks on all stateful services (`pg_isready` on Postgres, `redis-cli ping` on Redis).
2. Configure application service dependencies using `condition: service_healthy`:
   ```yaml
   depends_on:
     postgres:
       condition: service_healthy
     redis:
       condition: service_healthy
   ```

### Phase 5: Automated CLI Verification & Deployment Testing
1. Execute the automated CLI validator to audit topology and security:
   ```bash
   python3 infra/docker/skills/compose-architect/scripts/validate_docker_compose.py --path . --strict
   ```
2. Test local development startup:
   ```bash
   docker compose up -d
   ```
3. Test remote VPS zero-compilation pull:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always
   ```

---

## Gotchas & Common Pitfalls

| Faulty / Anti-Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Server-Side VPS Builds** (`docker compose up -d --build`) | Pre-built registry image (`-f docker-compose.repo.yml up -d --pull always`) | Building multi-stage images on low-RAM VPS servers causes OOM crashes and server freezes. |
| **Bare `depends_on: [db]`** | `condition: service_healthy` | Containers start before Postgres finishes initializing, causing fatal database connection errors. |
| **Static Port Bindings** (`3000:3000`) | `${HOST_PORT:-${PORT:-3000}}:${PORT:-3000}` | Static port bindings collide when hosting multiple projects or staging environments on one VPS. |
| **Hardcoded Secrets in Compose** | `${DB_PASSWORD}` loaded from `.env` | Exposes plaintext database credentials and API keys in version control history. |
| **Monolithic `docker-compose.yml`** | Mandatory 6-file modular topology | Monolithic compose files force conflicting dev/prod configurations and break deployment flexibility. |
| **Writable Bind Mounts for DB Storage** | Named persistent volumes (`driver: local`) | Host bind mounts for database files cause permission drifts and corruption across container restarts. |
