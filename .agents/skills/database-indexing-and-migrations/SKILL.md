---
name: database-indexing-and-migrations
description: "Enterprise guidelines for zero-downtime PostgreSQL migrations, ORM query optimization (Prisma, TypeORM), N+1 prevention, HNSW vector index tuning (pgvector), composite B-tree index alignment, and schema safety."
---

# PostgreSQL Database Indexing, Zero-Downtime Migrations & ORM Query Optimization

## Goal
Guide developers and AI coding agents in executing safe, high-performance database schema migrations, composite index optimizations, and ORM query tuning for PostgreSQL (Prisma, TypeORM, raw SQL).

---

# ORM Query Optimization & Performance Best Practices

### 1. N+1 Query Elimination
- **Antipattern**: Issuing ORM query calls inside `for`, `map`, or `forEach` loops (e.g. 1 query to fetch 100 journal entries, then 100 queries inside a loop to fetch postings).
- **Solution**: Use eager relation loading (`include` in Prisma, `relations:` or `relationLoadStrategy: 'join'` in TypeORM) or batch fetching via `$transaction([])`:

```typescript
// Prisma N+1 Prevention (Correct)
const entries = await prisma.journalEntry.findMany({
  take: 10,
  include: {
    postings: {
      include: { account: true }
    }
  }
});
```

### 2. Selective Column Projection (`select:`)
- **Antipattern**: Unbound `SELECT *` queries fetching 40+ columns (including heavy text, JSON, or 1536-dimensional vector embedding arrays) when only basic fields are needed.
- **Solution**: Project strictly required columns:

```typescript
// Prisma Selective Projection (Correct)
const accounts = await prisma.account.findMany({
  select: {
    id: true,
    code: true,
    name: true,
    type: true
  }
});
```

### 3. Composite B-Tree Index Alignment for Filters & Sorting
Whenever queries filter on multiple columns (e.g., `WHERE status = 'POSTED' AND entry_date >= '2026-01-01' ORDER BY entry_date DESC`), a matching composite B-tree index MUST be created in the database migration:

```sql
-- Migration: Create composite index for filtered & sorted queries
CREATE INDEX CONCURRENTLY idx_journal_entries_status_date 
ON finance.journal_entries (is_posted, entry_date DESC);
```

### 4. HNSW Index Optimization for `pgvector` Distance Queries
For vector similarity searches (`ORDER BY embedding <=> '[...]' LIMIT 5`), running un-indexed table scans will freeze host CPUs as table size grows. Create an **HNSW** (Hierarchical Navigable Small World) index:

```sql
-- Migration: Create HNSW index for OpenAI 1536-dim vector similarity search
CREATE INDEX CONCURRENTLY idx_accounts_description_embedding_hnsw 
ON finance.accounts 
USING hnsw (description_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 5. Bulk Write Transaction Batching
- **Antipattern**: Inserting 500 records by awaiting 500 individual `prisma.posting.create()` calls in separate DB network roundtrips.
- **Solution**: Use `createMany()` or `$transaction([])`:

```typescript
// Prisma Bulk Insert (Correct)
await prisma.journalPosting.createMany({
  data: postingsList
});
```

---

# Migration Protocols & Schema Safety

1. **Zero-Downtime Migration**: Write version-controlled migration files with explicit `up` and `down` rollback procedures.
2. **Concurrent Indexing**: Use `CREATE INDEX CONCURRENTLY` on production tables to prevent locking reads/writes.
3. **Foreign Key Action**: Add foreign key constraints with explicit ON DELETE actions (`CASCADE`, `SET NULL`, `RESTRICT`).
4. **Multi-Step Deprecation**: Avoid column type changes or column deletions in a single step; use multi-step deprecation patterns for zero-downtime releases.

---

# Verification Protocols

1. **Explain Analyze**: Run `EXPLAIN ANALYZE SELECT ...` on complex queries to verify index scans (`Index Scan` / `HNSW Index Scan`) instead of `Seq Scan` (Sequential Table Scan).
2. **N+1 Inspection**: Enable query logging in Prisma (`log: ['query']`) to verify only 1 query is executed per endpoint call.
