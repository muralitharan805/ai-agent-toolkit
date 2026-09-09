# Resolving Circular Dependencies & NestJS Module Refactoring

## Overview

Circular dependencies in NestJS occur when two or more modules or services depend on each other directly or indirectly (e.g., `AuthModule` imports `UsersModule`, while `UsersModule` imports `AuthModule`). While NestJS provides `forwardRef()` as an escape hatch, widespread usage of `forwardRef()` is an architectural code smell indicating leaky domain boundaries, high coupling, and runtime initialization order fragility.

This guide details definitive strategies to eliminate circular dependencies cleanly.

---

## 1. Root Causes of Circular Dependencies

| Cause | Typical Scenario | Architectural Anti-Pattern |
|---|---|---|
| **Feature Co-dependence** | `UsersService` verifies tokens via `AuthService`; `AuthService` fetches user entities via `UsersService`. | Mixed responsibilities; lack of a dedicated authentication credential lookup boundary. |
| **Bidirectional Entity Relations** | `UserEntity` has many `OrderEntity`; `OrderEntity` references `UserEntity`. | Domain model entanglement leaking into service orchestration. |
| **Notification / Event Loops** | `OrderService` triggers `NotificationService`; `NotificationService` queries `OrderService` for status updates. | Synchronous point-to-point service coupling instead of asynchronous domain events. |

---

## 2. Decoupling Pattern 1: Shared Submodule Extraction

When two modules need common entities, interfaces, or repository methods, extract the shared logic into an independent upstream module that both feature modules import.

```text
❌ Bad (Cyclic Coupling):
UsersModule <======== forwardRef() ========> AuthModule

✅ Good (Hierarchical Shared Dependency):
       UsersSharedModule (UserRepository, UserEntity)
            ▲                        ▲
            │                        │
       UsersModule              AuthModule
```

### Implementation:
```typescript
// src/modules/users-shared/users-shared.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from '../../prisma/prisma.module';
import { UserCredentialRepository } from './user-credential.repository';

/**
 * Shared module exposing only essential user lookup operations
 * for authentication and authorization without importing full UsersModule.
 */
@Module({
  imports: [PrismaModule],
  providers: [UserCredentialRepository],
  exports: [UserCredentialRepository],
})
export class UsersSharedModule {}
```

---

## 3. Decoupling Pattern 2: Domain Events (`@nestjs/event-emitter`)

Instead of calling dependent services directly across domain boundaries, publish domain events. This converts synchronous cyclic dependency graphs into decoupled publish-subscribe flows.

### Example: Order Created Notification

#### Anti-Pattern (`forwardRef` coupling):
```typescript
// ❌ OrdersService calls NotificationsService, which calls OrdersService
@Injectable()
export class OrdersService {
  constructor(
    @Inject(forwardRef(() => NotificationsService))
    private readonly notificationsService: NotificationsService,
  ) {}
}
```

#### Production-Grade Event Decoupling:
```typescript
// 1. Define Typed Domain Event
export class OrderCreatedEvent {
  constructor(
    public readonly orderId: string,
    public readonly userId: string,
    public readonly totalAmount: number,
  ) {}
}

// 2. Publish from Domain Service
import { Injectable } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';

@Injectable()
export class OrdersService {
  constructor(
    private readonly eventEmitter: EventEmitter2,
    private readonly orderRepo: OrderRepository,
  ) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    const order = await this.orderRepo.create(dto);
    this.eventEmitter.emit(
      'order.created',
      new OrderCreatedEvent(order.id, order.userId, order.total),
    );
    return order;
  }
}

// 3. Subscribe in Independent Feature Listener
import { Injectable } from '@nestjs/common';
import { OnEvent } from '@nestjs/event-emitter';

@Injectable()
export class OrderNotificationsListener {
  constructor(private readonly emailService: EmailService) {}

  @OnEvent('order.created', { async: true })
  async handleOrderCreated(event: OrderCreatedEvent): Promise<void> {
    await this.emailService.sendOrderConfirmation(event.userId, event.orderId);
  }
}
```

---

## 4. Decoupling Pattern 3: Interface Segregation with Symbol Tokens

If a service only requires a subset of operations from another service, define an abstract interface token in the consumer's module.

```typescript
// 1. Consumer defines interface and token (src/auth/interfaces/user-lookup.interface.ts)
export const USER_LOOKUP_SERVICE = Symbol('USER_LOOKUP_SERVICE');

export interface IUserLookupService {
  findForAuth(email: string): Promise<AuthUserRecord | null>;
}

// 2. AuthModule injects token
@Injectable()
export class AuthService {
  constructor(
    @Inject(USER_LOOKUP_SERVICE)
    private readonly userLookup: IUserLookupService,
  ) {}
}

// 3. Parent / AppModule wires provider
@Module({
  imports: [UsersModule, AuthModule],
  providers: [
    {
      provide: USER_LOOKUP_SERVICE,
      useExisting: UsersService,
    },
  ],
})
export class AppModule {}
```

---

## 5. Circular Dependency Detection Runbook

### Detection Commands:
```bash
# 1. Search for forwardRef in codebase
grep -rn "forwardRef" src/

# 2. Use madge for visual dependency graph cycle detection
pnpm dlx madge --circular --extensions ts ./src

# 3. Automated audit script
python3 frameworks/nestjs/skills/nestjs-maintenance-audit/scripts/audit_nestjs_codebase.py --target-dir .
```

### Remediation Checklist:
1. Identify the cycle: `Module A -> Module B -> Module A`.
2. Determine which method call crosses the boundary.
3. If it is data retrieval: extract to a `SharedModule` or Repository token.
4. If it is a side effect (email, log, sync): convert to `@OnEvent()`.
5. Remove `forwardRef()` from `@Inject()` and `@Module({ imports: [...] })`.
6. Run `pnpm test` and `pnpm build` to verify clean compilation.
