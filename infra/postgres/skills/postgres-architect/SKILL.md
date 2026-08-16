# PostgreSQL & pgvector Architect Skill

## Metadata
* **Name:** postgres_orchestration
* **Description:** Expert skill for configuring, deploying, tuning, and maintaining high-performance enterprise PostgreSQL instances, vector databases, and multi-database orchestrations.
* **Scope:** Custom compilation of C extensions (like `pgvector` v0.8.2), dynamic Multi-DB provisioning, named volume persistence, and performance-tuned indexing.

## Technical Architectures & Best Practices

### 1. pgvector Custom Compilation & Alpine Integration
To keep vector database images small, build on top of PostGIS Alpine base environments and compile extensions inside multi-stage containers.
* **JIT Compiler Bypass:** When building the `pgvector` extension, compile with `with_llvm=no` to bypass heavy dependencies on the full LLVM-19 clang runtime in modern Alpine environments:
```dockerfile
RUN git clone --depth 1 --branch v0.8.2 https://github.com/pgvector/pgvector.git . \
    && make with_llvm=no \
    && make install with_llvm=no
```
* **Binary Extraction:** Copy *only* `vector.so` and `vector.control` / `vector--*.sql` files to the target runtime.

### 2. Dynamic Multi-Database Provisioning Pattern
Enable developers to spin up multiple isolated databases pre-seeded with extensions (e.g. `vector`, `postgis`, `postgis_topology`) dynamically via environment variables without requiring manual SQL commands.
* **Dynamic Script Mount:** Mount a bash script to the `/docker-entrypoint-initdb.d/` directory inside the container (e.g., `01-init-multiple-databases.sh`).
* **Environment Variable:** Define `POSTGRES_MULTIPLE_DATABASES` as a comma-separated list of database names in the `.env` file (e.g., `POSTGRES_MULTIPLE_DATABASES=civicpath,analytics_db`).
* **The Provisioning Loop:**
```bash
#!/bin/bash
set -e
set -u

function setup_database() {
    local db_name=$1
    # Create DB if missing
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        SELECT 'CREATE DATABASE $db_name'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\gexec
EOSQL

    # Pre-register extensions
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db_name" <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS postgis;
        CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOSQL
}

setup_database "$POSTGRES_DB"
if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
        setup_database "$db"
    done
fi
```

### 3. Named Storage Persistence & Volume Safety
* **Always use Named Volumes:** Writable bind mounts (`./data:/var/lib/postgresql/data`) lead to host ownership conflicts (UID 70 postgres vs host user) and storage lock-ups. Use named volumes like `pgvector_data:/var/lib/postgresql/data`.
* **Disaster Recovery / Command Rules:**
  * **Safe Stopping:** Use `docker compose down` to stop container runtime. This preserves the stateful volume.
  * **Database Wipe:** Use `docker compose down -v` to delete both container interfaces and the named volume permanently.

### 4. Vector Query Operators (pgvector Cheat-sheet)
When querying vector columns, leverage exact semantic search operations:
* **Cosine Distance (`<=>`):** Use for normalized embeddings (e.g. OpenAI ada-002).
  * `SELECT * FROM items ORDER BY embedding <=> '[1,2,3]' LIMIT 5;`
* **L2 Distance / Euclidean (`<->`):** Use for absolute spatial distances.
  * `SELECT * FROM items ORDER BY embedding <-> '[1,2,3]' LIMIT 5;`
* **Inner Product (`<#>`):** Use for dot product operations.
  * `SELECT * FROM items ORDER BY (embedding <#> '[1,2,3]') ASC LIMIT 5;` *(Note: negative inner product is ordered ASC to find highest dot product).*

### 5. High-Performance Index Tuning
For high-dimensional vectors, optimize execution performance directly via command startup configs in `docker-compose.yml`:
```yaml
services:
  pgvector-db:
    command: postgres -c shared_buffers=512MB -c work_mem=64MB -c maintenance_work_mem=256MB
```
* **`shared_buffers`**: Recommended to be 25% of available host memory to load active database tables and indexes in RAM.
* **`maintenance_work_mem`**: Significantly speeds up HNSW index creation.
* **`work_mem`**: Speeds up filtered query sorts.
