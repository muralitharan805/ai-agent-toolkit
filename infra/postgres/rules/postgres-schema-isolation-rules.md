---
description: "Strict PostgreSQL schema isolation rules for enterprise applications (preventing public schema pollution, domain bounded context schemas, and search_path enforcement)."
trigger: model_decision
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

## Examples

### 1. Prisma Multi-Schema Isolation vs Public Pollution
```prisma
// ❌ FORBIDDEN: Default public schema with unisolated domain tables
model User {
  id    String @id @default(uuid())
  email String @unique
}

model AccountTransaction {
  id     String @id @default(uuid())
  amount Decimal
}

// ✅ CORRECT: Explicit domain bounded context schema mapping
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["multiSchema"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  schemas  = ["auth", "finance", "audit"]
}

model User {
  id    String @id @default(uuid())
  email String @unique

  @@schema("auth")
}

model AccountTransaction {
  id     String  @id @default(uuid())
  amount Decimal

  @@schema("finance")
}
```

### 2. TypeORM Entity Schema Declaration
```typescript
// ✅ CORRECT: Explicit schema isolation in TypeORM entity decorator
@Entity({ name: 'users', schema: 'auth' })
export class UserEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;
}
```

### 3. Connection String Search Path Configuration
```bash
# ✅ CORRECT: Explicit search_path mapping in environment connection URI
DATABASE_URL="postgresql://postgres:password@localhost:5432/app_db?schema=public&search_path=auth,finance,audit,public"
```
