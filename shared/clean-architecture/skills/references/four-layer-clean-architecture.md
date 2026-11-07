# 4-Layer Clean Architecture & Domain-First Engineering Reference

## 1. Architectural Philosophy

The fundamental premise of Clean Architecture (Robert C. Martin / Alistair Cockburn's Hexagonal Architecture) is **Separation of Concerns** achieved through the **Dependency Rule**:

> **The Dependency Rule**: Source code dependencies MUST only point inward, toward higher-level policies. Nothing in an inner circle can know anything at all about something in an outer circle.

```
┌────────────────────────────────────────────────────────┐
│  Layer 1: Adapters / Transport (Outer Ring)            │
│  - HTTP Controllers, gRPC Handlers, CLI, WebSockets    │
├────────────────────────────────────────────────────────┤
│  Layer 2: Application / Use Cases                      │
│  - Command/Query Handlers, Orchestration, App DTOs     │
├────────────────────────────────────────────────────────┤
│  Layer 3: Core Domain / Entities (Center Core)         │
│  - Pure Domain Entities, Value Objects, Domain Events  │
├────────────────────────────────────────────────────────┤
│  Layer 4: Infrastructure / Persistence (Outer Ring)    │
│  - SQL/NoSQL DB, Redis, Message Queues, 3rd Party APIs │
└────────────────────────────────────────────────────────┘

Data Flow:        Request -> Adapter -> Use Case -> Domain -> Infrastructure (via Port)
Dependency Flow:  Adapter -> Use Case -> Domain <- Infrastructure (Inversion of Control)
```

---

## 2. The 4 Layers Explained

### Layer 1: Adapters / Transport
- **Purpose**: Translates wire protocols (HTTP JSON, gRPC Protobuf, AMQP Messages, CLI flags) into application requests and returns formatted responses.
- **Responsibilities**:
  - Request deserialization, status codes, route definitions.
  - Calling application use cases with typed request DTOs.
  - Zero business decision making.
- **Naming Conventions**: `*.controller.ts`, `*_handler.go`, `*_router.py`.

### Layer 2: Application / Use Cases
- **Purpose**: Orchestrates the execution flow for a specific business feature.
- **Responsibilities**:
  - Fetches domain entities through Ports (repository interfaces).
  - Executes domain entity behavior/methods.
  - Coordinates transactions and side-effects (publishing domain events, logging audit trails).
  - Converts domain models into Response DTOs.
- **Naming Conventions**: `*.service.ts`, `*_use_case.go`, `*_usecase.py`.

### Layer 3: Domain / Entities (The Sacred Core)
- **Purpose**: Encapsulates enterprise business rules and state invariants.
- **Constraints**:
  - **ZERO external framework imports** (`express`, `nestjs`, `fastapi`, `typeorm`, `sqlalchemy`, `prisma`).
  - Contains entity classes, immutable value objects, domain exceptions, and domain event definitions.
  - High cohesion: business validation (e.g. `order.canBeCancelled()`) lives directly inside the entity.
- **Naming Conventions**: `*.entity.ts`, `*_entity.go`, `*_entity.py`.

### Layer 4: Infrastructure / Persistence
- **Purpose**: Implements the technical details required by inner layers.
- **Responsibilities**:
  - Database schema definitions (ORM models, migrations, SQL queries).
  - External API clients (Stripe, SendGrid, Twilio).
  - Cache drivers (Redis, Memcached) and queue publishers (RabbitMQ, Kafka).
- **Naming Conventions**: `*.repository.ts`, `*_repo.go`, `*_client.py`.

---

## 3. Ports and Adapters (Dependency Inversion Principle)

Instead of the Application layer depending on the Database, the **Application/Domain layer defines an Interface (Port)**, and the **Infrastructure layer provides the Concrete Implementation (Adapter)**.

### TypeScript / Node.js Implementation
```typescript
// 1. Port defined in Domain Layer (src/modules/order/order.repository.port.ts)
export interface OrderRepositoryPort {
  findById(id: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

// 2. Application Use Case depends ONLY on the Port (src/modules/order/order.service.ts)
export class CancelOrderUseCase {
  constructor(private readonly orderRepo: OrderRepositoryPort) {}

  async execute(orderId: string, reason: string): Promise<void> {
    const order = await this.orderRepo.findById(orderId);
    if (!order) {
      throw new DomainNotFoundException(`Order ${orderId} not found`);
    }
    order.cancel(reason); // Pure business method
    await this.orderRepo.save(order);
  }
}

// 3. Adapter defined in Infrastructure Layer (src/modules/order/infrastructure/postgres-order.repository.ts)
export class PostgresOrderRepository implements OrderRepositoryPort {
  constructor(private readonly pool: DbPool) {}

  async findById(id: string): Promise<Order | null> {
    const row = await this.pool.query('SELECT * FROM orders WHERE id = $1', [id]);
    return row ? OrderDataMapper.toDomain(row) : null;
  }

  async save(order: Order): Promise<void> {
    const persistenceModel = OrderDataMapper.toPersistence(order);
    await this.pool.query(
      'UPDATE orders SET status = $1, cancelled_reason = $2 WHERE id = $3',
      [persistenceModel.status, persistenceModel.cancelledReason, persistenceModel.id]
    );
  }
}
```

---

## 4. Data Mapper Pattern: Decoupling Domain from Persistence

A critical mistake in naive implementations is placing database ORM annotations (e.g. `@Column()`, `@Table()`) directly on domain entities.

```
┌─────────────────────────┐          ┌─────────────────────────┐
│     Domain Entity       │          │   Persistence Record    │
│  (Pure Business Model)  │ ◄──────► │  (Table Schema / ORM)   │
│  - Encapsulated logic   │  Mapper  │  - Primary keys         │
│  - Invariants           │          │  - Foreign keys         │
│  - Private fields       │          │  - Database types       │
└─────────────────────────┘          └─────────────────────────┘
```

### Why Active Record Fails in Enterprise Applications
1. **Schema Coupling**: Changes to DB column types force alterations to business logic.
2. **Untestable State**: Entities cannot be unit-tested without initializing an in-memory database or mocking ORM connection pools.
3. **Leaky Invariants**: Public getters/setters required by ORMs allow external callers to bypass domain validation rules.

---

## 5. `common/` vs. Domain Feature Modules

| Directory | What Belongs Here | What is FORBIDDEN Here |
| :--- | :--- | :--- |
| **`src/common/`** | - Request ID / Correlation ID middlewares<br>- Global RFC-7807 Exception Filters<br>- Pure utility functions (UUID, DateTime, Hash)<br>- Global Validation Pipes | - Business logic or feature workflows<br>- Database models or feature DTOs<br>- Domain-specific services (e.g., `user.common.ts`) |
| **`src/modules/<feature>/`** | - Feature HTTP controllers<br>- Feature Use Cases / Services<br>- Feature Domain Entities & Ports<br>- Co-located unit tests | - Cross-cutting server setup logic<br>- Generic non-business helper functions |
