---
trigger: always_on
description: "Strict PostgreSQL & ORM query optimization rules (N+1 query prohibition, selective column projection, mandatory pagination, HNSW vector indexing, and composite index alignment)."
---

# PostgreSQL & ORM Query Optimization Rules

## Description
Enforces strict performance rules for Prisma, TypeORM, and raw PostgreSQL queries, preventing N+1 query leaks, unindexed sequential table scans, and memory bloat.

## Constraints

### 1. N+1 Query Prohibition Rule
- Agents and developers MUST NOT execute database query calls inside `for`, `map`, or `forEach` loops.
- All relation fetching MUST use eager loading (`include` / `relations`) or `$transaction([])` batching.

### 2. Selective Column Projection Rule
- Queries returning entities with large fields (text, JSONB, or vector embeddings) MUST project required fields explicitly (`select: { id: true, code: true }`).
- Fetching full 1536-dimensional vector embedding columns in generic list queries is STRICTLY FORBIDDEN.

### 3. HNSW Vector Index Requirement (`pgvector`)
- Any vector column used in similarity search operations (`<=>`, `<->`, `<#>`) MUST have a corresponding **HNSW** or **IVFFlat** index defined in database migrations.

### 4. Filter & Sort Composite Index Rule
- Columns referenced in `where:` or `orderBy:` query clauses MUST be backed by a B-tree or composite index.
- Un-indexed multi-column filtering on production tables is forbidden.

### 5. Mandatory Collection Query Pagination Rule
- All queries returning arrays/collections MUST enforce `skip` and `take` (maximum 100).
- Executing unpaginated bulk `findMany()` queries without hard limits is strictly forbidden.
