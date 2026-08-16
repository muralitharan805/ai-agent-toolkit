# Docker Compose Architect Skill

## Metadata
* **Name:** compose_orchestration
* **Description:** Expert skill for designing multi-container systems, orchestrating networks, defining persistent volumes, and handling container dependency topologies.
* **Scope:** Standardizing Compose (v2.x+) configurations to guarantee environmental isolation, clean startup order, and robust container health monitoring.

## Core Rules & Best Practices

### 1. Environment Isolation & Variable Interpolation
* **External `.env` Enforced:** Never hardcode sensitive passwords, database credentials, API tokens, or dynamic configuration values (such as host ports) in the `docker-compose.yml` file.
* **Fallback Defaults:** Use variable interpolation with safe fallbacks for non-sensitive values (e.g. `${POSTGRES_PORT:-5432}`).
* **Template Separation:** Maintain a `.env.example` file that lists all configurable parameters with detailed comments, making onboarding deterministic.

### 2. Precise Dependency & Health Sequencing
* **No Network Discovery Assumptions:** Do not rely on mere container existence or network DNS. Databases, brokers, and cache systems must be completely active before application containers attempt connections.
* **Health Checks Required:** Implement robust, fast healthchecks for every stateful or core backing service.
  * *Example (PostgreSQL):* `test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]`
* **Condition-based Startup:** Define `depends_on` using the strict `condition: service_healthy` rule in downstream services:
```yaml
services:
  app-service:
    # ...
    depends_on:
      pgvector-db:
        condition: service_healthy
```

### 3. Volume and Storage Strategy
* **Persistent Stateful Storage:** Always use **named persistent volumes** mapped via a dedicated backend driver (e.g., `driver: local`) for data directories (e.g. database directories, log storage).
* **Config Bind-Mounts:** Use strict, read-only (`:ro`) bind mounts for initialization scripts, custom configuration files, or certificates. Never use writable bind mounts for stateful database storage to avoid ownership/permission drift.
* **Wiping Storage Safely:** Educate developers to use `docker compose down -v` only when they explicitly intend to wipe named volumes and reset database schemas.

### 4. Network Isolation
* **Explicit Custom Bridges:** Avoid using the default implicit docker network. Create named, isolated private bridge networks for service groupings to limit attack surface and avoid subnet collisions.
* **DNS Resolution:** Use container names or service names for internal communication (e.g. `postgresql://admin:pwd@pgvector-db:5432/db`).

## Reference Compose Template
```yaml
services:
  pgvector-db:
    build:
      context: .
      dockerfile: Dockerfile
    image: local/postgres-pgvector-postgis:16-alpine
    container_name: pgvector-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - pgvector_data:/var/lib/postgresql/data
      - ./init-scripts/init-multiple-databases.sh:/docker-entrypoint-initdb.d/01-init-multiple-databases.sh:ro
    networks:
      - pgvector_network
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1500M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: ${HEALTHCHECK_INTERVAL:-10s}
      timeout: ${HEALTHCHECK_TIMEOUT:-5s}
      retries: ${HEALTHCHECK_RETRIES:-5}
      start_period: ${HEALTHCHECK_START_PERIOD:-5s}

volumes:
  pgvector_data:
    name: pgvector_data_volume
    driver: local

networks:
  pgvector_network:
    name: pgvector_network
    driver: bridge
```
