---
description: "Strict PostgreSQL & ORM query optimization rules (N+1 query prohibition, selective column projection, mandatory pagination, HNSW vector indexing, and composite index alignment)."
trigger: model_decision
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

## Examples

### 1. N+1 Loop Queries vs Eager Loading
```typescript
// ❌ FORBIDDEN: Querying relations inside a loop (N+1 database roundtrips)
const users = await prisma.user.findMany();
for (const user of users) {
  user.posts = await prisma.post.findMany({ where: { authorId: user.id } });
}

// ✅ CORRECT: Eager loading in a single optimized join query
const usersWithPosts = await prisma.user.findMany({
  take: 50,
  include: {
    posts: {
      select: { id: true, title: true, createdAt: true }
    }
  }
});
```

### 2. Selective Projection vs Full Vector Column Retrieval
```typescript
// ❌ FORBIDDEN: Fetching 1536-dim vector embedding arrays into generic list responses
const documents = await prisma.document.findMany({ take: 20 }); // Bloats network and heap memory!

// ✅ CORRECT: Projecting strictly required metadata, excluding heavy vector embeddings
const documentSummaries = await prisma.document.findMany({
  take: 20,
  select: {
    id: true,
    title: true,
    author: true,
    updatedAt: true
    // embedding omitted!
  }
});
```

### 3. HNSW Index Declaration for Similarity Search
```sql
-- ❌ FORBIDDEN: Sequential table scan on unindexed vector column
SELECT id, title, embedding <=> '[0.1, 0.2, ...]' AS distance
FROM documents
ORDER BY distance LIMIT 5;

-- ✅ CORRECT: Fast approximate nearest neighbor search backed by HNSW index
CREATE INDEX idx_documents_embedding_hnsw 
ON documents 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```
