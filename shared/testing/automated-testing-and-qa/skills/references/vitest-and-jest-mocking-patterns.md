# Vitest & Jest Dependency Mocking Patterns

## Overview

Reliable, deterministic unit tests depend on strict mock isolation. Tests that make real network calls, connect to live databases, or share global mutable state produce flaky builds and slow CI/CD pipelines. This guide defines standard mocking patterns for TypeScript applications using Vitest and Jest.

---

## 1. Mocking Injected Dependencies in NestJS

When testing NestJS services that inject abstract repository tokens or external HTTP adapters, provide mock implementations using `useValue`:

```typescript
// src/modules/orders/orders.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { OrdersService } from './orders.service';
import { ORDER_REPOSITORY, IOrderRepository } from './order-repository.interface';
import { NotFoundException } from '@nestjs/common';

describe('OrdersService', () => {
  let service: OrdersService;
  let mockOrderRepo: Partial<Record<keyof IOrderRepository, ReturnType<typeof vi.fn>>>;

  beforeEach(async () => {
    mockOrderRepo = {
      findById: vi.fn(),
      create: vi.fn(),
      updateStatus: vi.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OrdersService,
        {
          provide: ORDER_REPOSITORY,
          useValue: mockOrderRepo,
        },
      ],
    }).compile();

    service = module.get<OrdersService>(OrdersService);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should throw NotFoundException when order does not exist', async () => {
    mockOrderRepo.findById?.mockResolvedValue(null);

    await expect(service.getOrderById('ord_999')).rejects.toThrow(
      NotFoundException,
    );
    expect(mockOrderRepo.findById).toHaveBeenCalledWith('ord_999');
  });
});
```

---

## 2. Spying on Methods with `vi.spyOn()` / `jest.spyOn()`

When you need to verify that an existing service or module method is called without replacing the entire object:

```typescript
// Spying on a logger or event emitter
const emitSpy = vi.spyOn(eventEmitter, 'emit');

await service.completeTask('task_123');

expect(emitSpy).toHaveBeenCalledWith('task.completed', expect.objectContaining({
  taskId: 'task_123',
}));
```

---

## 3. Controlling Time with Fake Timers

Never use `setTimeout` or arbitrary sleeps in unit tests. Use fake timers to advance time deterministically:

```typescript
describe('PollingService', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should execute retry after backoff interval', async () => {
    const callback = vi.fn();
    service.scheduleRetry(callback, 5000);

    expect(callback).not.toHaveBeenCalled();

    // Fast-forward time by 5000ms
    vi.advanceTimersByTime(5000);

    expect(callback).toHaveBeenCalledTimes(1);
  });
});
```

---

## 4. Resetting Mocks & Preventing Cross-Test Pollution

| Method | Behavior | When to Use |
|---|---|---|
| `mockClear()` / `clearAllMocks()` | Clears `mock.calls` and `mock.instances`. Retains mock implementation. | **Default in `beforeEach()` / `afterEach()`**. |
| `mockReset()` / `resetAllMocks()` | Clears calls and resets mock implementation to `undefined`. | When tests define different return values. |
| `mockRestore()` / `restoreAllMocks()` | Restores original unmocked method (only works on `spyOn`). | When temporarily spying on built-in prototypes. |

---

## 5. Testing Asynchronous Rejections & Error Boundaries

Always assert specific error types and error messages rather than generic error catching:

```typescript
// ✅ Good: Verifies error type and message
await expect(service.processPayment(-50)).rejects.toThrowError(
  'Payment amount must be greater than zero',
);

// ❌ Bad: Silently swallowing exceptions in try/catch without failing test
try {
  await service.processPayment(-50);
} catch (e) {
  // Test passes even if service didn't throw!
}
```
