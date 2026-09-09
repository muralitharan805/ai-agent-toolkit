# TypeScript Strict Typing & Type Narrowing Reference

## 1. The Zero-`any` Invariant

In modern production TypeScript, `any` is not a type; it is an escape hatch that silently disables the compiler's type checker for the annotated variable and any expressions derived from it. Writing `any` introduces invisible regressions, breaks IDE auto-completion, and masks fatal runtime bugs.

### Absolute Rule
Explicit `any` type annotations (`: any`, `as any`, `<any>`) are **strictly forbidden** in all source files, utility algorithms, service methods, and test specifications.

---

## 2. Safe Alternatives to `any`

| Use Case | ❌ Forbidden `any` Pattern | ✅ Recommended Production Type Pattern |
| :--- | :--- | :--- |
| **Unknown External Payload** | `function parse(data: any): any` | `function parse(data: unknown): ValidatedUser` with user-defined type guards |
| **Generic Key-Value Dictionary** | `const cache: { [k: string]: any }` | `const cache: Record<string, unknown>` or specific `Record<string, CacheEntry>` |
| **Generic Container Function** | `function wrap(val: any): any` | `function wrap<T>(val: T): Container<T>` with generic constraints (`T extends Base`) |
| **Untyped Third-Party Module** | `const pkg: any = require('pkg')` | Declare custom ambient interface boundary in `types/vendor.d.ts` |
| **Dynamic Form Value Stream** | `formValue: any` | Strongly-typed Angular `FormGroup<UserFormModel>` or Zod inference `z.infer<typeof Schema>` |

---

## 3. Type Narrowing Patterns

### 3.1 User-Defined Type Guards (`value is TargetType`)
When consuming untrusted input (e.g. HTTP request bodies, external webhook payloads, WebSocket messages), validate structure using a custom predicate function:

```typescript
export interface UserProfilePayload {
  readonly id: string;
  readonly email: string;
  readonly role: UserRole;
}

/**
 * Validates whether an unknown value conforms to the UserProfilePayload interface.
 */
export function isUserProfilePayload(value: unknown): value is UserProfilePayload {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate['id'] === 'string' &&
    typeof candidate['email'] === 'string' &&
    typeof candidate['role'] === 'string' &&
    Object.values(UserRole).includes(candidate['role'] as UserRole)
  );
}

// Consuming unknown input with type narrowing
export function processUserWebhook(rawInput: unknown): void {
  if (!isUserProfilePayload(rawInput)) {
    throw new BadRequestException('Malformed user webhook payload structure');
  }

  // Compiler automatically narrows rawInput to UserProfilePayload
  console.log(`Processing verified user: ${rawInput.email}`);
}
```

### 3.2 Discriminated Unions for State Machines
Represent divergent states using tagged unions with a shared literal discriminator property (`kind`, `type`, `status`):

```typescript
export interface IdleState {
  readonly status: 'IDLE';
}

export interface LoadingState {
  readonly status: 'LOADING';
  readonly startedAt: Date;
}

export interface SuccessState<T> {
  readonly status: 'SUCCESS';
  readonly data: T;
  readonly completedAt: Date;
}

export interface FailureState {
  readonly status: 'FAILURE';
  readonly error: Error;
}

export type AsyncOperationState<T> =
  | IdleState
  | LoadingState
  | SuccessState<T>
  | FailureState;

// Exhaustive switch handling
export function renderStateDescription<T>(state: AsyncOperationState<T>): string {
  switch (state.status) {
    case 'IDLE':
      return 'Operation standing by';
    case 'LOADING':
      return `In progress since ${state.startedAt.toISOString()}`;
    case 'SUCCESS':
      return 'Completed successfully';
    case 'FAILURE':
      return `Failed with message: ${state.error.message}`;
    default: {
      const _exhaustiveCheck: never = state;
      return _exhaustiveCheck;
    }
  }
}
```

### 3.3 The `satisfies` Operator
Use TypeScript's `satisfies` operator to enforce that an object satisfies a contract without widening specific literal types:

```typescript
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export interface RouteConfig {
  readonly path: string;
  readonly method: HttpMethod;
}

// Using satisfies preserves literal string paths and methods for autocompletion
export const API_ROUTES = {
  getUsers: { path: '/api/v1/users', method: 'GET' },
  createUser: { path: '/api/v1/users', method: 'POST' }
} satisfies Record<string, RouteConfig>;
```
