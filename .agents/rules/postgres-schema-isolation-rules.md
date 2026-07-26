---
trigger: always_on
description: "Strict PostgreSQL schema isolation rules for enterprise applications (preventing public schema pollution, domain bounded context schemas, and search_path enforcement)."
---

# PostgreSQL Schema Isolation Rules

## Description
Enforces enterprise PostgreSQL multi-schema architecture principles, preventing `public` schema pollution and ensuring domain bounded context isolation.

## Constraints

### 1. Public Schema Pollution Prohibition
- Enterprise applications with more than 10 tables MUST NOT place all database tables inside the default `public` schema.
- Tables MUST be organized under domain-specific schemas (e.g. `auth`, `finance`, `audit`, `analytics`, `vector_store`).

### 2. Domain Bounded Context Schema Naming
- Schema names MUST be lowercase, singular noun identifiers (e.g., `auth`, `finance`, `audit`).
- Mixed-case or special-character schema names are strictly forbidden.

### 3. ORM Schema Mapping Requirement
- Prisma models MUST declare explicit `@@schema("domain")` directives and enable `previewFeatures = ["multiSchema"]`.
- TypeORM entities MUST specify `{ schema: 'domain' }` in the `@Entity()` decorator.

### 4. Search Path Configuration Rule
- Database connection strings MUST explicitly configure `search_path` (e.g., `search_path=finance,auth,public`) to prevent implicit fallback errors.
