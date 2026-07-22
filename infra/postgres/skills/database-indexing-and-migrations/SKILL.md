---
name: database-indexing-and-migrations
description: "Guidelines for writing zero-downtime PostgreSQL migrations, index optimization (B-tree, GIN), foreign key constraints, and schema safety."
---
# Goal
Guide the agent in executing safe, performance-optimized database schema migrations and indexing strategies for PostgreSQL.

# Instructions
1. Write version-controlled migration files with explicit `up` and `down` rollback procedures.
2. Use `CREATE INDEX CONCURRENTLY` when creating indexes on production tables to prevent table locking.
3. Add foreign key constraints with explicit ON DELETE actions (`CASCADE`, `SET NULL`, `RESTRICT`).
4. Avoid column type changes or column deletions in single-step migrations; use multi-step deprecation patterns for zero-downtime deployments.
5. Choose appropriate index types: B-Tree for equality/range, GIN for JSONB/array columns, GiST for geometric/text search.

# Constraints
- Do NOT run blocking schema changes without evaluating table size and lock impact.
- Do NOT write migrations without defining a corresponding rollback script.
