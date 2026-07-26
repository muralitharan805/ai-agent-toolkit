---
name: postgres-multi-schema-architecture
description: "Enterprise guidelines, schema isolation strategies, domain-driven Bounded Context schemas (auth, finance, audit, analytics), schema-per-tenant multi-tenancy, Prisma/TypeORM multi-schema configuration, search_path management, and PostgreSQL RBAC security permissions."
---

# PostgreSQL Multi-Schema Architecture & Domain Isolation

## Goal
Guide developers and AI coding agents in designing, configuring, and maintaining enterprise-grade PostgreSQL multi-schema database architectures. Prevents `public` schema pollution, enforces Domain-Driven Bounded Context isolation, enables B2B SaaS multi-tenancy (`schema-per-tenant`), and secures schema permissions.

---

# Why Multi-Schema Architecture in Enterprise PostgreSQL?

In production enterprise systems, storing 50–100+ tables in the default `public` schema is considered a major architectural antipattern.

### Key Benefits:
1. **Domain Bounded Context Isolation**: Grouping tables into logical schemas (`auth`, `finance`, `audit`, `analytics`, `vector_store`) matching software domain boundaries.
2. **Security & Role-Based Access Control (RBAC)**: Service roles are granted permissions ONLY on their required schemas (e.g. `auth_service` cannot access `finance` tables).
3. **Multi-Tenancy (Schema-per-Tenant)**: B2B SaaS applications isolate client data in dedicated schemas (`tenant_acme`, `tenant_globex`), guaranteeing zero cross-tenant data leaks.
4. **Zero-Downtime Migration Management**: Managing zero-downtime Blue/Green migrations using PostgreSQL `search_path`.

---

# Domain Schema Breakdown Specification

```sql
-- 1. Create Core Domain Schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS vector_store;

-- 2. Domain Bounded Table Allocations

-- Auth Domain Schema
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE auth.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

-- Finance Domain Schema
CREATE TABLE finance.accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    type VARCHAR(32) NOT NULL,
    balance NUMERIC(15, 2) DEFAULT 0.00
);

CREATE TABLE finance.journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_date DATE NOT NULL,
    description TEXT NOT NULL
);

-- Audit Domain Schema
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES auth.users(id),
    action VARCHAR(64) NOT NULL,
    target_resource VARCHAR(128),
    ip_address VARCHAR(45),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

---

# PostgreSQL `search_path` & Connection URL Configuration

PostgreSQL uses `search_path` to resolve table names in SQL queries.

### Setting `search_path` in PostgreSQL Connection String:
```text
postgresql://user:password@localhost:5432/nidhiflow_db?schema=finance&search_path=finance,auth,public
```

### Dynamic `search_path` SQL Commands:
```sql
-- Set search path for current database session
SET search_path TO finance, auth, public;

-- Set default search path for a specific service role
ALTER ROLE finance_service_role SET search_path TO finance, public;
```

---

# ORM Integration (Prisma & TypeORM)

### 1. Prisma ORM Multi-Schema Configuration

#### `prisma/schema.prisma`:
```prisma
datasource db {
  provider     = "postgresql"
  url          = env("DATABASE_URL")
  schemas      = ["auth", "finance", "audit"]
}

generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["multiSchema"]
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  sessions  Session[]

  @@map("users")
  @@schema("auth")
}

model Session {
  id        String   @id @default(uuid())
  userId    String   @map("user_id")
  user      User     @relation(fields: [userId], references: [id])

  @@map("sessions")
  @@schema("auth")
}

model Account {
  id      String @id @default(uuid())
  code    String @unique
  name    String
  balance Decimal

  @@map("accounts")
  @@schema("finance")
}
```

### 2. TypeORM Multi-Schema Configuration

```typescript
// user.entity.ts
import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity({ name: 'users', schema: 'auth' })
export class UserEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;
}

// account.entity.ts
import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity({ name: 'accounts', schema: 'finance' })
export class AccountEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  code: string;
}
```

---

# Multi-Tenancy (Schema-per-Tenant Pattern)

For B2B SaaS applications requiring strict tenant isolation:

```sql
-- Function to dynamically provision isolated tenant schema
CREATE OR REPLACE FUNCTION provision_tenant_schema(tenant_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', tenant_name);
    
    -- Clone base schema tables into tenant schema
    EXECUTE format('CREATE TABLE %I.accounts (LIKE finance.accounts INCLUDING ALL)', tenant_name);
    EXECUTE format('CREATE TABLE %I.journal_entries (LIKE finance.journal_entries INCLUDING ALL)', tenant_name);
    
    RAISE NOTICE 'Successfully provisioned tenant schema: %', tenant_name;
END;
$$ LANGUAGE plpgsql;

-- Execute tenant provisioning
SELECT provision_tenant_schema('tenant_acme');
SELECT provision_tenant_schema('tenant_globex');
```

---

# Security & RBAC Permission Hardening

Restrict service account access strictly to authorized schemas:

```sql
-- 1. Revoke public access
REVOKE ALL ON DATABASE nidhiflow_db FROM PUBLIC;

-- 2. Create service roles
CREATE ROLE auth_service_role LOGIN PASSWORD 'SecureAuthPass123';
CREATE ROLE finance_service_role LOGIN PASSWORD 'SecureFinancePass123';

-- 3. Grant schema permissions
GRANT USAGE ON SCHEMA auth TO auth_service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO auth_service_role;

GRANT USAGE ON SCHEMA finance TO finance_service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA finance TO finance_service_role;

-- 4. Set default future table permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO auth_service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA finance GRANT ALL ON TABLES TO finance_service_role;
```

---

# Verification Protocols

1. **Schema Check**: Query `SELECT schema_name FROM information_schema.schemata;` to verify domain schemas (`auth`, `finance`, `audit`) exist.
2. **Prisma Multi-Schema Sync**: Run `pnpm prisma db push` or `pnpm prisma migrate dev` and verify tables are created under respective Postgres schemas.
3. **Role Permission Test**: Connect as `finance_service_role` and verify `SELECT * FROM auth.users` returns `permission denied for schema auth`.
