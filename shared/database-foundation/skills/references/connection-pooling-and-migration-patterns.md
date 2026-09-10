# Database Connection Pooling, Migrations & Indexing Patterns

## Overview

A robust database foundation requires resilient connection management, disciplined migration workflows, standardized table audit columns, and strategic indexing. Neglecting these areas leads to pool exhaustion, production deadlocks, index bloat, and unrecoverable schema drift.

---

## 1. Connection Pool Engineering & Sizing Formula

A connection pool maintains a set of reusable, pre-established database TCP connections to avoid the high latency of establishing a new TLS handshake on every request.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Connection Pool Sizing Formula                       │
└──────────────────────────────────────────────────────────────────────────────┘
  Total Max Connections = (Application Replicas × pool.max)
  
  Invariant:
    Total Max Connections ≤ Database max_connections × 0.8
```

Leaving a 20% buffer guarantees that administrative tools, migrations, and database monitoring agents can always connect even during maximum traffic load.

### Recommended Settings & Justifications

| Configuration Key | Production Value | Architectural Rationale |
| :--- | :--- | :--- |
| `pool.min` | `2` | Keeps warm connections active; prevents handshake latency on initial requests. |
| `pool.max` | `10` | Caps concurrent DB threads per pod; prevents connection exhaustion on the primary database. |
| `acquireTimeout` | `30000ms` (30s) | Fails fast when all pool connections are saturated instead of queueing requests indefinitely. |
| `idleTimeout` | `600000ms` (10m) | Reaps and closes surplus idle connections, releasing memory back to the database engine. |
| `connectionTimeout` | `5000ms` (5s) | Fails fast during initial network or host unreachable errors. |
| `queryTimeout` | `30000ms` (30s) | Prevents runaway, unindexed queries from holding connection locks indefinitely. |
| `ssl` | `true` | Enforces TLS encryption for all data in transit. Mandatory in production. |

---

## 2. Migration Governance & CI/CD Sequence

### Invariants
1. **Never Auto-Migrate in Production**:
   Setting `synchronize: true` in TypeORM or executing `prisma db push` in production can drop columns, recreate tables, and cause irreversible data loss.
2. **Deterministic Versioning**:
   Use timestamped SQL files: `YYYYMMDDHHMMSS_action_target.sql`.
3. **Dual Directional (Up & Down)**:
   Every migration must supply both an `up` statement and a verified `down` rollback statement.
4. **Idempotency**:
   Use `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, and `DROP TABLE IF EXISTS`.
5. **Pre-Deployment Execution**:
   In CI/CD, run database migrations as a dedicated one-off step BEFORE deploying new application replicas:

```
[Git Push to main]
        │
        ▼
[CI Build & Test Pass]
        │
        ▼
[Execute Migrations: pnpm run db:migrate:prod] ──► (Fails? Abort deployment)
        │
        ▼
[Deploy Application Pods with rolling update]
```

---

## 3. Schema Design & Mandatory Audit Columns

Every table storing business entities MUST include standard audit columns:

```sql
CREATE TABLE IF NOT EXISTS accounts (
  -- UUIDv7: 48-bit timestamp prefix + cryptographically random suffix
  -- Guarantees monotonic time ordering, preventing B-tree index fragmentation
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  name VARCHAR(255) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  
  -- Mandatory Audit Columns
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL, -- Soft delete: NULL = active, timestamp = deleted
  created_by UUID NULL,
  updated_by UUID NULL
);
```

### Why UUIDv7 is Recommended
- Standard `UUIDv4` generates purely random numbers. Inserting random keys into a B-tree index causes frequent page splits, high disk I/O, and severe performance degradation on tables with millions of rows.
- `UUIDv7` embeds a 48-bit millisecond timestamp in the leading bits, making keys naturally K-sortable while preserving global uniqueness.

---

## 4. Strategic Indexing & Foreign Keys

### Mandatory Foreign Key Indexes
In PostgreSQL and MySQL, creating a foreign key constraint does NOT automatically create an index on the child table's column:

```sql
-- ❌ DANGEROUS: Unindexed foreign key
ALTER TABLE orders ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(id);
-- Running DELETE FROM customers WHERE id = ... will lock the entire orders table or scan all rows!

-- ✅ CORRECT: Always pair foreign keys with an explicit index
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders (customer_id);
```

### Partial Indexes for Soft-Deleted Tables
Most application queries filter out soft-deleted records (`WHERE deleted_at IS NULL`). Using a partial index significantly reduces index footprint and speeds up lookups:

```sql
CREATE INDEX IF NOT EXISTS idx_orders_customer_active
  ON orders (customer_id)
  WHERE deleted_at IS NULL;
```

---

## 5. Slow Query Telemetry

Configure your ORM or database driver to intercept query completion and evaluate duration:
- Threshold: Any query taking $> 200\text{ms}$ must log a `WARN` event.
- Log attributes: `durationMs`, `sql` (parameterized), `correlationId`.
- Never log raw substituted values (prevents leaking passwords, credit cards, or PII into log sinks).
