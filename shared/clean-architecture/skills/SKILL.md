---
name: clean-architecture
description: "Architects and audits backend applications according to 4-layer Clean Architecture, domain-first modular packaging, dependency inversion, pure domain entities, and decoupled persistence boundaries. Triggered by 'clean-arch:', 'backend-architecture:', or '/clean-architecture'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-09"
---

# Clean Architecture & Domain-First Backend Skill

## Overview

This skill establishes the engineering protocol for architecting, scaffolding, and refactoring backend applications according to **4-Layer Clean Architecture** and **Domain-Driven Design (DDD)** principles. It enforces the inward **Dependency Rule**, mandates vertical domain-first packaging (`src/modules/<feature>/`), guarantees pure business domain entities with zero framework/ORM pollution, implements pluggable infrastructure abstractions via Ports and Adapters, and enforces co-located unit test suites.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Feature Demarcation]    ──► Identify bounded context & isolate domain
               │
  [Phase 2: Pure Domain Modeling]   ──► Create zero-dependency entity & invariants
               │
  [Phase 3: Port & Use Case Spec]   ──► Define interface port & application workflow
               │
  [Phase 4: Adapter Implementation] ──► Implement DB repository with Data Mapper
               │
  [Phase 5: Conformance Audit]      ──► Run audit_clean_architecture.py & co-locate tests
```

---

## 5-Phase Execution Guide

### Phase 1: Feature Demarcation & Directory Packaging
1. **Vertical Slice Organization**:
   - Organize codebase by business capability under `src/modules/<feature>/` (e.g. `src/modules/user/`, `src/modules/order/`).
   - Reject layer-first technical folders at the root (e.g. `src/controllers/`, `src/services/`).
2. **Standard Module Boundary**:
   Each module must isolate its internal concerns:
   ```text
   src/modules/<feature>/
   ├── <feature>.controller.ts    # Adapter (HTTP transport)
   ├── <feature>.service.ts       # Application use case
   ├── <feature>.repository.ts    # Domain Port (Interface)
   ├── <feature>.entity.ts        # Pure Domain Entity
   ├── <feature>.dto.ts           # Request/Response contracts
   └── <feature>.service.test.ts  # Co-located unit tests
   ```

### Phase 2: Pure Domain Modeling (Zero Dependencies)
1. **Zero External Libraries**:
   - The domain entity MUST be a plain language object (TypeScript class, Python dataclass, Go struct).
   - NEVER import ORM decorators (`@Entity()`, `@Column()`, Mongoose schemas, Prisma clients, GORM tags).
2. **Encapsulated Invariants**:
   - Place business validation and state transition logic directly inside the entity methods, not scattered across controllers.
   ```typescript
   export class Order {
     constructor(
       public readonly id: string,
       private status: OrderStatus,
       private readonly items: OrderItem[]
     ) {}

     public cancel(reason: string): void {
       if (this.status === OrderStatus.SHIPPED) {
         throw new DomainRuleViolationException('Shipped orders cannot be cancelled');
       }
       this.status = OrderStatus.CANCELLED;
     }
   }
   ```

### Phase 3: Port Definition & Application Use Case
1. **Define Port Abstractions**:
   - The Domain or Application layer declares what it needs via an interface/protocol:
   ```typescript
   export interface OrderRepositoryPort {
     findById(orderId: string): Promise<Order | null>;
     save(order: Order): Promise<void>;
   }
   ```
2. **Implement Application Use Case**:
   - Orchestrates entities, calls ports, and handles transaction boundaries.
   - Depends strictly on the port interface via constructor dependency injection.

### Phase 4: Infrastructure Adapter Implementation
1. **Data Mapper Pattern**:
   - Create a concrete repository implementing the port interface inside the infrastructure layer (e.g. `postgres-order.repository.ts`).
   - Map raw database rows/ORM persistence records to domain entities upon read, and map domain entities to persistence schemas upon write.
   - Keep persistence tables completely separate from domain entity definitions.

### Phase 5: Conformance Audit & Test Co-location
1. **Automated Structural Audit**:
   - Execute the bundled architecture audit script to detect layer-first antipatterns and leaky domain imports:
   ```bash
   python3 scripts/audit_clean_architecture.py src/ --strict
   ```
2. **Co-locate Behavioral Tests**:
   - Ensure unit test files (`*.service.test.ts`, `*.entity.test.ts`) reside directly alongside the source files they test.
   - Reserve the top-level `tests/` directory strictly for cross-module integration and end-to-end (E2E) suites.

---

## Working Checklist

- [ ] **Strict Dependency Rule**: Dependencies point inward ONLY (Adapters → Use Cases → Domain ← Infrastructure).
- [ ] **Domain-First Packaging**: All features isolated in `src/modules/<feature>/`; zero top-level `controllers/` or `repositories/`.
- [ ] **Zero-Dependency Domain**: Entities contain pure business logic with zero ORM or framework imports.
- [ ] **Inversion via Ports**: Use cases depend on abstract repository interfaces, not concrete database drivers.
- [ ] **Data Mapper Pattern**: Dedicated mappers decouple persistence schemas from business entities.
- [ ] **Common Isolation**: `src/common/` contains only stateless, domain-free cross-cutting utilities.
- [ ] **Co-located Tests**: Unit test suites live directly next to target service and entity source files.

---

## Authoritative References & Bundled Assets

- **Architectural Reference Guide**: [references/four-layer-clean-architecture.md](references/four-layer-clean-architecture.md)
- **Architecture Audit Tool**: [scripts/audit_clean_architecture.py](scripts/audit_clean_architecture.py)
- **Standard Folder Schema**: [assets/standard-backend-folder-tree.json](assets/standard-backend-folder-tree.json)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Clean Architecture)

| Legacy Antipattern | Modern Clean Architecture Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Layer-First Grouping** (`src/controllers/`, `src/services/`, `src/repos/`) | **Domain-First Packaging** (`src/modules/<feature>/`) | Eliminates cross-feature spaghetti; enables microservice extraction. |
| **Active Record Entities** (ORM annotations on business models) | **Data Mapper Pattern** (Separate pure entity from persistence record) | Changes to DB column types no longer break enterprise business rules. |
| **Direct DB Client in Services** (`new PrismaClient().user.find()`) | **Dependency Inversion** (Service depends on `UserRepositoryPort`) | Enables instant in-memory unit testing without spinning up test databases. |
| **Scattered Business Rules** (Validation in controllers or SQL triggers) | **Encapsulated Invariants** (Domain methods guard entity state) | Prevents invalid domain states from ever existing in memory. |
| **Giant `common/` Dumping Ground** (Putting shared business logic in common) | **Shared Kernel Modules** (`src/modules/shared-kernel/`) | Keeps `common/` purely stateless and eliminates hidden inter-feature dependencies. |
| **Distant Test Directories** (`tests/unit/modules/user/user.test.ts`) | **Co-located Tests** (`src/modules/user/user.service.test.ts`) | Immediate visibility of test coverage during code reviews and refactoring. |
