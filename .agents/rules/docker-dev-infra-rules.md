# `docker-dev-infra` Operational Constraints & Rules

## Description
Enforces mandatory standards for `docker-dev-infra` project management, including modular Compose folder structuring (`postgres/`, `redis/`), mandatory healthcheck directives, environment variable parameterization, pgvector extension initialization, and volume isolation across Seyalicraft projects.

## Constraints

### 1. Modular Directory Structure Requirement
- Each infrastructure service MUST reside in its own dedicated directory (e.g. `postgres/`, `redis/`, `minio/`).
- Each module directory MUST contain a standalone `docker-compose.yml`, `.env.example`, and `README.md`.

### 2. Mandatory Healthcheck Directive
- Every production and dev service container MUST declare a native `healthcheck` block in its `docker-compose.yml`:
  - PostgreSQL: `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}`
  - Redis: `redis-cli ping`
- Unmonitored containers without health reporting are strictly forbidden.

### 3. PostgreSQL `pgvector` Initialization Rule
- PostgreSQL module MUST compile/include `pgvector` extension and mount `./init-scripts/01-init-pgvector.sql` to execute `CREATE EXTENSION IF NOT EXISTS vector;` on boot.

### 4. No Hardcoded Ports or Credentials
- Port bindings, database passwords, and usernames MUST NOT be hardcoded in `docker-compose.yml`.
- All variables MUST use shell fallback syntax (e.g. `${POSTGRES_PORT:-5432}`).

### 5. Git Safety & `.env` Rules
- Active `.env` files containing local secrets MUST be listed in `.gitignore`.
- Every service directory MUST commit a clean `.env.example` template with dummy default values.
