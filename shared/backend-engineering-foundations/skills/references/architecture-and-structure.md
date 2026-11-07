# Clean Architecture & Domain-First Folder Layout

## 1. Core Philosophy
Clean Architecture establishes a strict boundary between business domain rules and infrastructure mechanisms (database ORMs, HTTP frameworks, third-party cloud SDKs).

---

## 2. The 4-Layer Dependency Rule

```text
┌─────────────────────────────────────────────────────────┐
│ Adapters / Controllers (Outer Layer)                   │  ← HTTP, gRPC, CLI, WebSocket handlers
├─────────────────────────────────────────────────────────┤
│ Application / Use Cases Layer                          │  ← Orchestrates domain workflows
├─────────────────────────────────────────────────────────┤
│ Domain Layer (Core Entities & Invariants)              │  ← Pure business models (ZERO deps)
├─────────────────────────────────────────────────────────┤
│ Infrastructure / Drivers Layer                         │  ← DB Repositories, Caches, Queues
└─────────────────────────────────────────────────────────┘
Dependency Inversion Principle: Outer layers depend on inner interfaces. 
Inner layers know nothing of outer layers.
```

---

## 3. Recommended Production Directory Taxonomy

```text
project-root/
├── src/
│   ├── modules/                         # Feature domain modules
│   │   └── order/
│   │       ├── order.controller         # Adapter: Unpacks transport protocol
│   │       ├── order.service            # Application: Use case orchestration
│   │       ├── order.repository.port    # Domain Port: Abstract interface
│   │       ├── order.repository.adapter # Infrastructure: Concrete DB implementation
│   │       ├── order.entity             # Pure Domain Entity
│   │       ├── order.dto                # Input/Output validation schemas
│   │       └── order.service.test       # Co-located unit/integration tests
│   ├── common/                          # Cross-cutting concerns only
│   │   ├── decorators/
│   │   ├── filters/                     # Global exception adapters
│   │   ├── guards/                      # Authentication & RBAC guards
│   │   ├── interceptors/                # Correlation ID & execution logging
│   │   ├── middlewares/                 # Security headers & rate limiting
│   │   └── utils/                       # Pure stateless utility functions
│   ├── config/                          # Central environment configuration service
│   ├── database/
│   │   ├── migrations/                  # Versioned DDL migrations
│   │   ├── seeders/                     # Test data seeders
│   │   └── connection                   # Connection pool initialization
│   ├── observability/                   # Logger, RED metrics, OpenTelemetry tracer
│   └── main                             # Technical application entry point
├── tests/
│   ├── integration/                     # Testcontainers integration tests
│   └── performance/                     # k6 SLA performance scripts
├── docs/                                # Living documentation & ADR catalog
└── docker/
    ├── Dockerfile                       # Multi-stage non-root container build
    └── docker-compose.yml               # Local dependencies (Postgres, Redis, RabbitMQ)
```

---

## 4. Unit of Work & Transaction Boundaries

### The Dependency Invariant
Domain use cases must NEVER import or receive raw database/ORM transaction objects (`EntityManager`, `PrismaClient`, `java.sql.Connection`). Doing so leaks persistence implementation details into domain logic.

```text
// Clean Architecture Unit of Work Interface (Defined in Application/Domain layer)
INTERFACE TransactionalContext:
    PROPERTY orderRepo: OrderRepositoryPort
    PROPERTY inventoryRepo: InventoryRepositoryPort

INTERFACE UnitOfWork:
    METHOD executeInTransaction(work: Function(TransactionalContext) -> T) -> T
```

### Use Case Execution Example
```text
FUNCTION PlaceOrderUseCase(UnitOfWork, Command):
    RETURN UnitOfWork.executeInTransaction(FUNCTION(ctx):
        Order = OrderEntity.create(Command.items, Command.customerId)
        
        ctx.inventoryRepo.decrementStock(Command.items)
        ctx.orderRepo.save(Order)
        
        RETURN Order.id
    )
```
