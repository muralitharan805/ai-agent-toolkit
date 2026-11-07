---
trigger: model_decision
description: "Enforces 4-layer Clean Architecture, domain-first modular boundaries, dependency inversion (outer to inner only), pure domain entities without ORM coupling, and co-located tests in backend systems."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-09"
---

# Clean Architecture & Domain-First Backend Standards

## Description
Enforces strict 4-layer Clean Architecture, Domain-Driven Design (DDD) module boundaries, and dependency inversion across all backend projects. Eliminates layer-first technical grouping (`controllers/`, `services/`, `repositories/` at root), guarantees pure business domain entities with zero external framework/ORM coupling, requires pluggable infrastructure abstractions via ports/interfaces, and mandates co-located unit and integration testing.

## Constraints

### 1. Mandatory 4-Layer Dependency Inversion (Outer → Inner Only)
- Software components MUST strictly adhere to the 4 concentric architectural layers:
  1. **Adapters / Transport Layer** (Outer): HTTP controllers, gRPC handlers, CLI commands, WebSocket gateways.
  2. **Application / Use Cases Layer**: Workflow orchestrators, business command/query handlers, application DTOs.
  3. **Domain / Entities Layer** (Core): Enterprise business rules, entity models, value objects, domain events.
  4. **Infrastructure Layer** (Outer Boundary): Database repositories, caching drivers, external API clients, message brokers.
- Dependency arrows MUST point inwards ONLY (`Adapters` → `Use Cases` → `Domain` ← `Infrastructure`). Inner layers MUST NEVER import, reference, or depend upon outer layers.

### 2. Domain-First Feature Modularization
- Source code MUST be organized by business domain features (`src/modules/<domain>/` or `src/features/<domain>/`), NOT by technical layer.
- Having top-level technical directories such as `src/controllers/`, `src/services/`, or `src/repositories/` containing multiple unrelated business features is STRICTLY FORBIDDEN.
- Every domain module MUST encapsulate its own controller/handler, application use case, repository interface, DTO contracts, domain entities, and co-located test suites.

### 3. Pure Business Domain (Zero Framework & ORM Coupling)
- Core domain entities and value objects MUST be pure language objects (POCO / POJO / Plain TypeScript Classes / Python dataclasses / Go structs) with ZERO external dependencies.
- Domain entities MUST NOT contain database ORM decorators, entity manager metadata, schema annotations (e.g. TypeORM `@Entity()`, Prisma generated client imports, Mongoose Schemas, SQLAlchemy declarative models, or GORM tags), or HTTP framework decorators.
- Persistence data models MUST live exclusively in the Infrastructure layer and map to/from domain entities using the Data Mapper pattern.

### 4. Pluggable Infrastructure Abstractions (Ports & Adapters)
- Use cases and domain logic MUST interact with infrastructure (databases, caches, third-party mailers, payment gateways) exclusively through abstract interfaces/protocols (Ports).
- Concrete infrastructure implementations (Adapters) MUST implement these domain interfaces and be injected at runtime via Dependency Injection or factory composition.
- Direct instantiation of database clients or external SDKs inside domain use cases is STRICTLY FORBIDDEN.

### 5. Co-Located Testing Discipline
- Unit and behavioral tests MUST be co-located next to the target source file (e.g. `order.service.test.ts` or `order_service_test.go` directly alongside `order.service.ts`).
- Root-level `tests/` directory is reserved strictly for cross-cutting integration, end-to-end (E2E), and performance benchmarks.

### 6. Cross-Cutting `common/` Boundary Invariant
- The `src/common/` directory is strictly restricted to stateless, domain-free primitives (e.g. global HTTP filters, correlation ID middlewares, validation pipes, cryptographic hashing utilities).
- Reusable business logic, shared entities, or multi-domain helper methods MUST NOT be placed into `src/common/`. Shared domain concepts MUST be modeled as dedicated shared kernel modules (`src/modules/shared-kernel/`).

## Examples

### 1. Domain-First Module Layout vs. Forbidden Layer-First Monolith

```text
// ❌ FORBIDDEN: Layer-First Antipattern (Technical silos)
src/
├── controllers/
│   ├── user.controller.ts
│   ├── payment.controller.ts
│   └── order.controller.ts
├── services/
│   ├── user.service.ts
│   └── order.service.ts
└── repositories/
    ├── user.repo.ts
    └── order.repo.ts

// ✅ CORRECT: Domain-First Clean Architecture (Vertical feature encapsulation)
src/
└── modules/
    ├── user/
    │   ├── user.controller.ts     # Adapter: HTTP transport handling
    │   ├── user.service.ts        # Use Case: Application business orchestration
    │   ├── user.repository.ts     # Port: Abstract repository interface
    │   ├── user.entity.ts         # Domain: Pure entity model (Zero deps)
    │   ├── user.dto.ts            # Contract: Request/Response DTOs
    │   └── user.service.test.ts   # Co-located unit tests
    └── order/
        ├── order.controller.ts
        ├── order.service.ts
        ├── order.repository.ts
        └── order.entity.ts
```

### 2. Pure Domain Entity vs. Forbidden ORM-Polluted Entity

```typescript
// ❌ FORBIDDEN: ORM annotations leaking into core domain model
import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 100 })
  fullName: string;
}

// ✅ CORRECT: Pure domain entity decoupled from persistence
export class User {
  constructor(
    public readonly id: string,
    public readonly fullName: string,
    public readonly emailAddress: string,
    private isActive: boolean
  ) {}

  public deactivate(): void {
    this.isActive = false;
  }

  public get active(): boolean {
    return this.isActive;
  }
}
```

### 3. Pluggable Port & Adapter Dependency Inversion

```typescript
// ✅ CORRECT: Domain defines Port; Infrastructure implements Adapter

// 1. Domain Port (src/modules/user/user.repository.ts)
export interface UserRepositoryPort {
  findById(userId: string): Promise<User | null>;
  save(user: User): Promise<void>;
}

// 2. Application Use Case (src/modules/user/user.service.ts)
export class DeactivateUserUseCase {
  constructor(private readonly userRepo: UserRepositoryPort) {}

  async execute(userId: string): Promise<void> {
    const user = await this.userRepo.findById(userId);
    if (!user) throw new EntityNotFoundException('User not found');
    user.deactivate();
    await this.userRepo.save(user);
  }
}

// 3. Infrastructure Adapter (src/modules/user/infrastructure/postgres-user.repository.ts)
export class PostgresUserRepository implements UserRepositoryPort {
  constructor(private readonly dbPool: DatabasePool) {}

  async findById(userId: string): Promise<User | null> {
    const row = await this.dbPool.query('SELECT * FROM users WHERE id = $1', [userId]);
    return row ? UserMapper.toDomain(row) : null;
  }

  async save(user: User): Promise<void> {
    await this.dbPool.query(
      'UPDATE users SET is_active = $1 WHERE id = $2',
      [user.active, user.id]
    );
  }
}
```
