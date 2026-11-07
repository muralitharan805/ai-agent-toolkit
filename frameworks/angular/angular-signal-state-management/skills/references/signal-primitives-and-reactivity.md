# Angular Signal Primitives & Reactivity Technical Guide

This guide provides deep technical specifications, internal mechanisms, and architectural best practices for Angular's core reactive primitives: `signal()`, `computed()`, `linkedSignal()`, and `effect()`.

---

## 1. Writable Signals (`signal`)

Writable signals represent reactive state nodes that can be read and imperatively modified.

### 1.1 Signature & Configuration

```typescript
import { signal, CreateSignalOptions } from '@angular/core';

export interface UserPreferences {
  readonly theme: 'light' | 'dark' | 'system';
  readonly fontSize: number;
  readonly notificationsEnabled: boolean;
}

// Custom equality check to prevent downstream propagation when values are deeply identical
const equalityCheck = (a: UserPreferences, b: UserPreferences): boolean =>
  a.theme === b.theme &&
  a.fontSize === b.fontSize &&
  a.notificationsEnabled === b.notificationsEnabled;

const preferences = signal<UserPreferences>(
  { theme: 'system', fontSize: 14, notificationsEnabled: true },
  { equal: equalityCheck }
);
```

### 1.2 State Mutation Protocols

1. **Direct Value Replacement (`.set(value)`):**
   Use when the new value is independent of the existing state.
   ```typescript
   preferences.set({ theme: 'dark', fontSize: 16, notificationsEnabled: true });
   ```

2. **Functional Transformation (`.update(fn)`):**
   Use when the new state derives from the previous state. The updater function must be pure and return an immutable copy.
   ```typescript
   // Correct: Immutable copy with object spread
   preferences.update(current => ({ ...current, fontSize: current.fontSize + 2 }));

   // STRICTLY FORBIDDEN: In-place mutation
   // preferences.update(current => { current.fontSize += 2; return current; });
   ```

3. **Readonly Projection (`.asReadonly()`):**
   Always protect internal writable state before exposing it from injectable services.
   ```typescript
   readonly userPreferences = preferences.asReadonly();
   ```

---

## 2. Derived Reactive Computations (`computed`)

`computed()` creates a read-only memoized signal that derives its value from other signals using Angular's push-pull glitch-free reactivity graph.

### 2.1 Mechanical Invariants

- **Memoization & Lazy Evaluation**: The derivation computation only executes when the signal is read (`pull`), provided at least one dependency notified a change (`push`).
- **Dynamic Dependency Tracking**: Dependencies are tracked dynamically per evaluation pass. If a branch is bypassed by a conditional check (`if/else`), inactive signals are automatically unobserved.
- **Glitch-Free Guarantee**: Angular guarantees that intermediate transient states are never observed, eliminating "diamond problem" graph anomalies.

### 2.2 Strict Constraints

```typescript
// Correct: Pure, side-effect-free derivation
const activeTheme = computed<'light' | 'dark'>(() => {
  const pref = preferences();
  if (pref.theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return pref.theme;
});

// STRICTLY FORBIDDEN: Mutating another signal inside computed()
// const broken = computed(() => {
//   someSignal.set('oops'); // Throws runtime error in Angular!
//   return 42;
// });
```

---

## 3. Synchronized Dependent State (`linkedSignal`)

Introduced to solve the pattern where a writable signal must automatically update or reset when a dependent source changes, while still allowing manual user overrides.

### 3.1 Form Factor Comparison

#### Shorthand Form (Default Derivation)
Automatically resets its value to the computation result whenever any signal read inside the function changes:

```typescript
import { signal, linkedSignal } from '@angular/core';

const selectedCategoryId = signal<string>('cat-101');
const selectedProductId = linkedSignal(() => {
  const categoryId = selectedCategoryId();
  return getDefaultProductForCategory(categoryId);
});

// User can override the selection:
selectedProductId.set('prod-999');

// If selectedCategoryId changes, selectedProductId automatically resets!
selectedCategoryId.set('cat-102');
// selectedProductId() is now getDefaultProductForCategory('cat-102')
```

#### Advanced Options Form (`source` + `computation`)
Exposes both the source and the previous state, allowing preservation of user edits or differential updates:

```typescript
export interface FilterCriteria {
  readonly query: string;
  readonly page: number;
}

const activeQuery = signal<string>('');

const paginationState = linkedSignal<string, number>({
  source: () => activeQuery(),
  computation: (currentQuery, previous) => {
    // Only reset page to 0 if the search term actually changed
    if (previous && previous.source !== currentQuery) {
      return 0;
    }
    return previous?.value ?? 0;
  }
});
```

### 3.2 Anti-Pattern Replacement

| Legacy Anti-Pattern (Zone/RxJS/Effect) | Modern Recommended Angular Primitive |
| :--- | :--- |
| Using `effect()` to call `.set()` on a writable signal when another signal updates | `linkedSignal()` |
| Subscribing to an Observable only to assign an internal variable | `toSignal()` or `linkedSignal()` |
| Manually resetting form or page indices in change handlers | `linkedSignal({ source: triggerSignal, computation: () => 0 })` |

---

## 4. Side Effects & External Synchronization (`effect`)

`effect()` registers an operation that executes in response to signal changes. It is intended strictly for operations that leave the reactive graph (DOM mutations, canvas rendering, analytic beacons, logging).

### 4.1 Invariants & Safety Rules

1. **Injection Context**: Must be instantiated inside an injection context (constructor, factory function, or property initializer), or provided an explicit `Injector`.
2. **Side-Effect Boundary**: Do NOT call `.set()` or `.update()` inside an `effect()` without explicit architectural justification (`allowSignalWrites: true` is an escape hatch and considered an architectural code smell in 95% of use cases).
3. **Untracked Reads (`untracked`)**: Wrap signals whose changes should NOT trigger the effect in `untracked()`.
4. **Teardown Cleanup (`onCleanup`)**: Always register resource release routines.

```typescript
import { Component, effect, inject, signal, untracked } from '@angular/core';
import { AnalyticsTrackerService } from './analytics-tracker.service';

@Component({ ... })
export class ProductViewComponent {
  private readonly analytics = inject(AnalyticsTrackerService);

  readonly currentProductId = signal<string>('prod-001');
  readonly userRole = signal<'admin' | 'guest'>('guest');

  constructor() {
    effect((onCleanup) => {
      const productId = this.currentProductId();
      // Read userRole WITHOUT creating a dependency trigger
      const role = untracked(() => this.userRole());

      const timerId = setTimeout(() => {
        this.analytics.trackView(productId, role);
      }, 500);

      // Register cleanup handler to cancel stale timers on next emission or destruction
      onCleanup(() => {
        clearTimeout(timerId);
      });
    });
  }
}
```

---

## 5. Zoneless Change Detection Mechanics

In Zoneless Angular (`provideExperimentalZonelessChangeDetection()` or `provideZonelessChangeDetection()`), Angular does not monkey-patch browser APIs via `zone.js`.

Instead:
1. Signal reads inside templates register reactive consumer bindings directly.
2. When a signal value is updated, Angular's scheduler queues a microtask to traverse only the invalidated component views.
3. DOM updates happen with microsecond-level latency and zero overhead from unneeded tree-wide checks.
