---
trigger: model_decision
description: "Enforces production database connection pooling, versioned idempotent migrations with rollbacks, mandatory audit columns (UUIDv7, created_at, updated_at, deleted_at soft deletes), index optimization, and slow query logging."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Database Foundation & Persistence Standards

## Description
Enforces production-grade relational database architecture, connection pool sizing, migration governance, schema design invariants, and performance telemetry across all backend services. Mandates deterministic connection pool configuration (min, max, acquireTimeout, queryTimeout, SSL), strictly prohibits automatic schema synchronization in production, requires versioned forward/rollback migration scripts with idempotent guards, enforces mandatory audit and soft-delete columns across all business tables, mandates foreign key indexing, and enforces slow query logging for queries exceeding 200ms.

## Constraints

### 1. Mandatory Connection Pool Configuration
- Production database clients and ORMs (Prisma, TypeORM, Kysely, pg, SQLAlchemy, GORM) MUST explicitly define connection pool limits:
  - `pool.min`: Minimum 2 connections (maintains warm connections to eliminate cold-handshake latency).
  - `pool.max`: Maximum 10 connections per application instance (prevents connection exhaustion and database thread thrashing under traffic spikes). Total connections across all replicas must never exceed database `max_connections * 0.8`.
  - `pool.acquireTimeout`: Maximum 30s (fails fast if pool is exhausted rather than hanging indefinitely).
  - `pool.idleTimeout`: Maximum 10m (releases idle connections back to the OS/database).
  - `connectionTimeout`: Maximum 5s (aborts unreachable database hosts immediately).
  - `queryTimeout`: Maximum 30s (terminates runaway or unindexed blocking queries).
  - `ssl`: MUST be enabled in staging and production environments (`ssl: { rejectUnauthorized: true }`).

### 2. Versioned Migrations & Zero Auto-Migration in Production
- Automatic schema synchronization (e.g. TypeORM `synchronize: true`, Prisma `db push` in production, Hibernate `hbm2ddl.auto = update`) is STRICTLY FORBIDDEN in production.
- Every schema modification MUST be encapsulated in a versioned migration file:
  - Forward (`up`) and rollback (`down`) operations are both mandatory.
  - Migrations MUST be idempotent using defensive guards (`IF NOT EXISTS`, `IF EXISTS`).
  - Migration file naming convention: `YYYYMMDDHHMMSS_descriptive_action.sql` (e.g. `20260910083000_create_orders_table.sql`).
- In CI/CD pipelines, database migrations MUST execute as a distinct pre-deployment gate BEFORE deploying new application containers.

### 3. Mandatory Audit & Soft-Delete Columns on Every Table
- Every business table in the schema MUST declare standard audit and lifecycle columns:
  - `id`: Primary key using `UUIDv7` (time-ordered, K-sortable) or `BIGINT`. Random UUIDv4 is discouraged for high-write tables due to B-tree index fragmentation.
  - `created_at`: `TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`.
  - `updated_at`: `TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`.
  - `deleted_at`: `TIMESTAMP WITH TIME ZONE NULL` (Soft delete: `NULL` indicates an active record; non-`NULL` indicates soft deletion. Hard deletion of customer/order data is strictly forbidden).
  - `created_by`: `UUID / VARCHAR NULL` (identifier of the user or system worker).
  - `updated_by`: `UUID / VARCHAR NULL` (identifier of the last modifier).

### 4. Index Optimization & Foreign Key Invariants
- **Mandatory Foreign Key Indexing**: Every foreign key column MUST have a corresponding index. Unindexed foreign keys trigger full-table locks or sequential scans during `JOIN`, `CASCADE`, or delete operations.
- **Selective Indexing**:
  - Add indexes for columns frequently queried in `WHERE`, `ORDER BY`, or `JOIN` conditions.
  - Add unique indexes for business natural keys (e.g., `email`, `slug`, `sku`).
  - Use partial indexes for soft-deleted tables to minimize index size:
    `CREATE INDEX idx_orders_customer_id ON orders (customer_id) WHERE deleted_at IS NULL;`
- **Zero Blind Over-Indexing**: Do not create speculative indexes. Every index adds overhead to `INSERT`, `UPDATE`, and `DELETE` transactions. Validate index effectiveness using `EXPLAIN ANALYZE`.

### 5. Slow Query Logging & Telemetry
- All database queries taking longer than `200ms` MUST be intercepted and logged at `WARN` level.
- Slow query log entries MUST include:
  - Query execution duration in milliseconds (`durationMs`).
  - Parameterized SQL query template (raw parameters MUST NOT be logged to prevent credential and PII leakage).
  - Active request `correlationId`.

### 6. Seeder Strategy Isolation
- Seed scripts MUST be partitioned by environment lifecycle:
  - `dev-seed`: Generates voluminous, realistic mock datasets for local development.
  - `test-seed`: Generates minimal, deterministic fixtures with hardcoded IDs for CI integration tests.
  - `prod-seed`: Contains REFERENCE data ONLY (countries, currencies, tax rates, standard roles). Seeding test users or mock transactions in production is STRICTLY FORBIDDEN.

## Examples

### 1. Connection Pool Configuration (Node.js / pg / TypeORM)

```typescript
// ✅ CORRECT: Production-hardened connection pool configuration
export const databaseConfig = {
  type: 'postgres' as const,
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME,
  username: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: true } : false,
  synchronize: false, // STRICTLY FORBIDDEN in production!
  migrationsRun: false, // Managed via separate pre-deploy CI task
  extra: {
    min: 2,                  // Minimum warm connections
    max: 10,                 // Maximum pool ceiling
    idleTimeoutMillis: 600000, // 10 minutes
    connectionTimeoutMillis: 5000, // 5s connect timeout
    statement_timeout: 30000, // 30s query timeout
  },
};
```

### 2. Standard Idempotent SQL Migration with Audit Columns & Partial Index

```sql
-- Up Migration: 20260910083000_create_orders_table.sql
CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL,
  total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
  status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL,
  created_by UUID NULL,
  updated_by UUID NULL
);

-- Foreign key index with soft-delete partial filter
CREATE INDEX IF NOT EXISTS idx_orders_customer_id_active
  ON orders (customer_id)
  WHERE deleted_at IS NULL;

-- Down Migration
DROP INDEX IF EXISTS idx_orders_customer_id_active;
DROP TABLE IF EXISTS orders;
```

### 3. Slow Query Logger Middleware

```typescript
// ✅ CORRECT: Intercepting and logging slow queries (> 200ms)
export function logSlowQuery(query: string, durationMs: number, correlationId?: string): void {
  const SLOW_QUERY_THRESHOLD_MS = 200;
  if (durationMs >= SLOW_QUERY_THRESHOLD_MS) {
    logger.warn({
      event: 'database.slow_query',
      correlationId,
      durationMs,
      thresholdMs: SLOW_QUERY_THRESHOLD_MS,
      query, // Parameterized SQL template
      message: `Database query exceeded slow query threshold: ${durationMs}ms`,
    });
  }
}
```
