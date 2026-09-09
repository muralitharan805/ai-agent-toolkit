---
description: "Mandates minimum 80% line and 75% branch test coverage, mock isolation for external dependencies, deterministic test setup, and forbidden production test mocks."
trigger: model_decision
---

# Automated Testing & Coverage Quality Rules

## Description
Enforces mandatory test coverage thresholds, unit and integration test isolation, E2E testing protocols, and deterministic mock management across frontend and backend projects.

## Constraints

### 1. Mandatory Minimum Test Coverage Thresholds
- Applications MUST achieve a minimum of **80% line coverage** and **75% branch coverage** across core business logic services and components.
- CI/CD build scripts MUST fail if code coverage drops below threshold boundaries (`pnpm test:cov`).

### 2. Dependency Mocking & Test Isolation Rule
- Unit tests (`*.spec.ts`) MUST mock all external network adapters, database connections, and third-party API services using mock providers or spy functions (`vi.fn()`, `jest.fn()`).
- Tests MUST NOT make real outbound HTTP network calls or modify external production database records.

### 3. Test File Colocation & Naming Standard
- Component and service test spec files MUST be colocated in the exact same directory as the source file:
  - Component: `user-profile.component.ts` $\rightarrow$ `user-profile.component.spec.ts`
  - Service: `user.service.ts` $\rightarrow$ `user.service.spec.ts`

### 4. Deterministic Test Setup & Tear-Down
- Every test suite MUST reset mock calls and state in `beforeEach()` / `afterEach()` hooks (`vi.clearAllMocks()` or `jest.clearAllMocks()`).
- Tests MUST NOT depend on execution order or shared mutable global state.

## Examples

### 1. Isolated Service Unit Test with Mock Repository
```typescript
// src/modules/users/user.service.spec.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserService } from './user.service';
import { IUserRepository, USER_REPOSITORY } from './user-repository.interface';

describe('UserService', () => {
  let service: UserService;
  let mockRepo: IUserRepository;

  beforeEach(() => {
    vi.clearAllMocks();
    mockRepo = {
      findById: vi.fn(),
      create: vi.fn(),
    };
    service = new UserService(mockRepo);
  });

  it('should return user when found', async () => {
    const fakeUser = { id: 'usr_1', email: 'test@example.com' };
    vi.mocked(mockRepo.findById).mockResolvedValue(fakeUser);

    const result = await service.getUserById('usr_1');

    expect(mockRepo.findById).toHaveBeenCalledWith('usr_1');
    expect(result).toEqual(fakeUser);
  });
});
```

### 2. Angular Signal Component Testing with TestBed
```typescript
// src/app/features/counter/counter.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { CounterComponent } from './counter.component';

describe('CounterComponent', () => {
  let component: CounterComponent;
  let fixture: ComponentFixture<CounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CounterComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(CounterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should increment signal value upon action', () => {
    expect(component.count()).toBe(0);
    component.increment();
    expect(component.count()).toBe(1);
  });
});
```

### 3. Coverage Threshold Configuration in Vitest
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      thresholds: {
        lines: 80,
        branches: 75,
        functions: 80,
        statements: 80,
      },
    },
  },
});
```
