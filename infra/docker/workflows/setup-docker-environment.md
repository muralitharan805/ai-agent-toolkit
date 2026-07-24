---
description: "Workflow to scaffold enterprise multi-stage Dockerfiles, split multi-environment Docker Compose setups (dev, prod, shared, existing-infra cost saver), and README containerization documentation. Triggered by 'docker:', 'compose:', or '/setup-docker-environment'."
trigger: manual
---

# Setup Enterprise Docker & Multi-Environment Compose Workflow

Follow this step-by-step workflow to scaffold enterprise-grade Docker containerization into any application repository.

## Steps

### Step 1: Project Stack & Deployment Mode Selection
1. Inspect the project directory (`package.json`, `NestJS`, `Angular`, `PostgreSQL`, `Redis`).
2. Identify package manager (`pnpm`, `npm`, `yarn`) and Node.js runtime version.
3. Prompt the user or evaluate infrastructure requirements:
   - **Mode A (Standalone)**: Create dedicated Postgres & Redis containers for this project.
   - **Mode B (Shared Cost-Saver)**: Attach application container to existing shared Postgres & Redis container via `external: true` network (`shared-infra-network`) to save RAM & storage on low-cost VPS servers.
4. If database credentials or shared container names are ambiguous:
   - **STOP** and ask the user for clarification before generating Compose files.

### Step 2: Scaffold Production Multi-Stage Dockerfile & `.dockerignore`
1. Create `Dockerfile` using 3-stage architecture (`deps`, `builder`, `runner`):
   - `deps`: Installs dependencies with frozen lockfile.
   - `builder`: Compiles TypeScript / Angular assets.
   - `runner`: Lightweight Alpine production container executing under `USER node` with native `HEALTHCHECK`.
2. Create `.dockerignore` excluding `node_modules`, `.git`, `dist`, `.env`, and build caches.

### Step 3: Scaffold Modular Multi-Environment Docker Compose Files
Create modular Compose configurations:
1. `docker-compose.yml`: Shared base service definitions, bridge networks, and volume definitions.
2. `docker-compose.override.yml`: Local Development overrides (bind volume mounts, hot-reloading command `pnpm start:dev`).
3. `docker-compose.prod.yml`: Production overrides (`restart: unless-stopped`, resource CPU/memory limits, json-file logging).
4. `docker-compose.shared.yml`: Dedicated infrastructure services (`ankane/pgvector` PostgreSQL, Redis 7 Alpine, healthchecks).
5. `docker-compose.existing-infra.yml`: Shared infrastructure overrides connecting application container to existing running Postgres/Redis containers via external Docker network (`shared-infra-network`).

### Step 4: Update Project README.md Documentation
Append a dedicated `## 🐳 Docker Containerization & Execution Guide` section to the project's `README.md` detailing:
- Commands for Mode A: Standalone dev environment with dedicated DB containers (`docker compose -f docker-compose.shared.yml -f docker-compose.yml up -d`).
- Commands for Mode B: Shared cost-saver environment with existing DB containers (`docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml up -d`).
- Commands for Production deployment (`docker compose -f docker-compose.shared.yml -f docker-compose.yml -f docker-compose.prod.yml up -d --build`).

### Step 5: Verification & Container Testing
1. Run lint check on generated `Dockerfile` and `docker-compose*.yml` files.
2. Verify non-root user execution (`USER node`) is configured in the production runner stage.
