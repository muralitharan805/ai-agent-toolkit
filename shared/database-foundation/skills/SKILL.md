---
name: database-foundation
description: "Implements and audits production database connection pooling, versioned idempotent SQL migrations, mandatory audit columns (UUIDv7, created_at, updated_at, deleted_at), foreign key indexing, and slow query logging. Triggered by 'database:', 'migration:', 'connection-pool:', or '/database-foundation'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Database Foundation & Persistence Standards Skill

## Overview

This skill establishes the production engineering protocol for **Database Connection Pooling**, **Deterministic Schema Migrations**, **Entity Audit Columns**, and **Index Optimization** across relational databases (PostgreSQL, MySQL). It prevents production connection exhaustion, avoids unrecoverable schema drift, guarantees data auditability with soft deletion, and identifies slow queries exceeding 200ms.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         5-Phase Database Foundation Pipeline                   │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Connection Pool Hardening] ──► Configure min=2, max=10, timeouts, SSL
                │
  [Phase 2: Versioned Migrations]      ──► Idempotent SQL (up/down), zero auto-sync
                │
  [Phase 3: Mandatory Audit Columns]   ──► UUIDv7 PK, created_at, updated_at, deleted_at
                │
  [Phase 4: Strategic Indexing]        ──► Index foreign keys, partial soft-delete index
                │
  [Phase 5: Conformance Audit]         ──► Run audit_database_foundation.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Connection Pool Hardening
1. **Configure Sizing & Timeouts**:
   - Explicitly define connection pool boundaries in the database configuration:
     - `pool.min: 2` (keeps warm connections; eliminates initial TLS latency).
     - `pool.max: 10` (caps max connections per replica; avoids server exhaustion).
     - `acquireTimeout: 30s` (fails fast on pool exhaustion instead of hanging).
     - `idleTimeout: 10m` (reclaims idle connections).
     - `connectionTimeout: 5s` (aborts unreachable hosts quickly).
     - `queryTimeout: 30s` (terminates runaway queries).
     - `ssl: true` (mandatory TLS in production).
2. **Cluster Sizing Formula**:
   - Assert: `(replicas × pool.max) <= (database max_connections × 0.8)`.

### Phase 2: Versioned Migrations & CI/CD Gate
1. **Zero Auto-Sync in Production**:
   - Strictly prohibit TypeORM `synchronize: true` or Prisma `db push` in production.
2. **Author Idempotent Up/Down Migrations**:
   - Write timestamped migration files: `YYYYMMDDHHMMSS_action_description.sql`.
   - Ensure every migration includes an `up` block and a verified `down` rollback.
   - Use defensive guards: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`.
3. **CI/CD Sequence**:
   - Execute migrations as a pre-deployment step BEFORE rolling out new application code.

### Phase 3: Mandatory Audit Columns & Soft Deletes
1. **Apply Audit Columns to Every Table**:
   - `id`: Primary key using `UUIDv7` or `BIGINT`.
   - `created_at`: `TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
   - `updated_at`: `TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
   - `deleted_at`: `TIMESTAMPTZ NULL` (Soft delete; `NULL` = active record; hard delete of user data is forbidden).
   - `created_by`: `UUID / VARCHAR NULL`.
   - `updated_by`: `UUID / VARCHAR NULL`.

### Phase 4: Strategic Indexing & Foreign Keys
1. **Index All Foreign Keys**:
   - Always create an explicit index on foreign key columns (`CREATE INDEX idx_orders_customer ON orders(customer_id)`).
2. **Partial Indexes for Soft Deletes**:
   - Accelerate active-record queries:
     `CREATE INDEX idx_orders_customer_active ON orders(customer_id) WHERE deleted_at IS NULL;`
3. **Zero Blind Over-Indexing**:
   - Use `EXPLAIN ANALYZE` before adding composite indexes.

### Phase 5: Conformance Audit
1. Run the database foundation audit tool against the codebase and migrations:
   ```bash
   python3 shared/database-foundation/skills/scripts/audit_database_foundation.py ./src --strict
   ```
2. Verify zero `synchronize: true` risks, presence of pool limits, and audit column compliance.

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [Connection Pooling & Migration Patterns](references/connection-pooling-and-migration-patterns.md) for pool sizing formulas, UUIDv7 vs UUIDv4 B-tree analysis, and CI/CD deployment gates.
- **Production Template**: Review [database-connection-pool.template.ts](assets/database-connection-pool.template.ts) for production pool configuration, entity schema types, and slow query telemetry.
- **CLI Auditor**: Execute [audit_database_foundation.py](scripts/audit_database_foundation.py) to audit repository compliance.

---

## Gotchas & Pitfalls

| Anti-Pattern / Legacy | Modern Recommended Production Standard | Architectural Risk |
| :--- | :--- | :--- |
| `synchronize: true` or auto-migration in production | Explicit versioned SQL migration scripts with up and down rollbacks | Auto-sync can drop tables or columns on startup, causing catastrophic data loss. |
| Unbounded connection pool (`max: 100` per pod) | Capped connection pool (`max: 10`) adhering to `replicas × pool.max <= DB max_conn × 0.8` | Traffic spikes cause pods to open thousands of connections, crashing the DB with OOM. |
| Unindexed foreign key columns | Explicit index created for every foreign key | Deleting a parent row triggers full table scans and row locks across child tables. |
| UUIDv4 random primary keys on high-write tables | UUIDv7 (time-ordered prefix) or sequential BIGINT | Random keys cause continuous B-tree index fragmentation and massive disk write amplification. |
| Hard deleting user or financial transaction records | Soft deletion pattern via `deleted_at TIMESTAMPTZ NULL` | Violates financial compliance, destroys historical audit trails, breaks foreign key integrity. |
| Missing query statement timeout | Strict `queryTimeout` (e.g. 30s) configured on connection pool | A single runaway unindexed query can hold connection locks indefinitely, blocking all traffic. |
