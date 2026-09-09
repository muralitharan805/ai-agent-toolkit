---
name: angular-signal-state-management
description: "Guidelines, architectural patterns, and diagnostic tools for designing reactive state management in modern Angular (v19+) using Signals, computed states, linkedSignals, async resources (resource, rxResource), and RxJS interop. Activate when implementing feature state, debugging reactivity bugs, or migrating to Zoneless change detection."
compatibility: "Requires Angular 19+ and Node.js 20+"
---

# Angular Signal State Management Skill

This skill guides the design, implementation, and automated auditing of granular, type-safe, and high-performance reactive state management in modern Angular applications. It leverages native Signal primitives (`signal()`, `computed()`, `linkedSignal()`, `resource()`, `rxResource()`) and RxJS interoperability bridges (`toSignal()`, `toObservable()`) to support Zoneless and OnPush architectures.

---

## 1. Reactive Primitive Decision Matrix

Select the most restrictive reactive primitive suited for the task:

| Requirement / Scenario | Recommended Primitive | Primary Mechanism |
| :--- | :--- | :--- |
| **Local mutable state** (form input, toggle, counter) | `signal<T>(initialValue)` | Direct `.set()` or immutable `.update(fn)` |
| **Derived read-only calculation** (filtered list, totals) | `computed<T>(() => fn)` | Pure synchronous memoization; lazy push-pull evaluation |
| **Dependent writable state that resets on source update** | `linkedSignal<S, D>(options)` | Automatically resets or synchronizes when dependency emits |
| **Asynchronous data fetching with Angular HttpClient** | `rxResource<T, R>(options)` | Directly bridges Observable streams with loading/error signals |
| **Native asynchronous fetch / SDK calls** | `resource<T, R>(options)` | Promise-based loader with native `AbortSignal` cancellation |
| **External side effects** (logging, DOM/Canvas, analytics) | `effect((onCleanup) => ...)` | Runs outside reactive graph; requires cleanup registration |
| **Debounced search inputs or stream operators** | `toObservable()` $\rightarrow$ pipe $\rightarrow$ `toSignal()` | Bi-directional interop via `@angular/core/rxjs-interop` |

---

## 2. Core Implementation Workflow

Follow this 5-stage protocol when architecting domain feature state:

### Stage 1: Isolate Mutable State Nodes
Declare discrete, fine-grained writable signals. Keep state structures normalized:

```typescript
// Private internal state
private readonly selectedCategoryId = signal<string>('all');
private readonly searchQuery = signal<string>('');
```

### Stage 2: Establish Dependent State via `linkedSignal`
When a secondary writable signal depends on a primary source (e.g. resetting page index to `0` when search query or filter changes), use `linkedSignal()` instead of imperative effects:

```typescript
readonly pageIndex = linkedSignal<string, number>({
  source: () => `${this.selectedCategoryId()}_${this.searchQuery()}`,
  computation: (_source, previous) => (previous ? 0 : 0)
});
```

### Stage 3: Wire Asynchronous Data Fetching via `rxResource`
Bind the parameter signals to the data loader:

```typescript
readonly catalogResource = rxResource({
  request: () => ({
    category: this.selectedCategoryId(),
    query: this.searchQuery(),
    page: this.pageIndex()
  }),
  loader: ({ request }) =>
    this.http.get<readonly Product[]>('/api/v1/products', {
      params: { category: request.category, q: request.query, page: request.page }
    })
});
```

### Stage 4: Derive Cached Projections via `computed`
Expose read-only computed selectors to components:

```typescript
readonly products = computed(() => this.catalogResource.value() ?? []);
readonly isLoading = computed(() => this.catalogResource.isLoading());
readonly hasError = computed(() => !!this.catalogResource.error());
```

### Stage 5: Encapsulate into an Injectable Service Store
Expose state strictly via read-only signals and explicit action methods:

```typescript
setCategory(category: string): void {
  if (category !== this.selectedCategoryId()) {
    this.selectedCategoryId.set(category);
  }
}
```

---

## 3. Progressive Disclosure Pointers

For granular implementation guides, low-level mechanics, automation scripts, and validation schemas, consult the following resources:

- **Signal Primitives Deep Dive**: [references/signal-primitives-and-reactivity.md](references/signal-primitives-and-reactivity.md)
  *Detailed specifications for `signal`, `computed`, `linkedSignal`, custom equality checkers, and Zoneless reactivity mechanics.*
- **Async Resources & RxJS Interop**: [references/async-resources-and-rxjs-interop.md](references/async-resources-and-rxjs-interop.md)
  *Full guide to `resource()`, `rxResource()`, cancellation via `AbortSignal`, `toSignal()` options, and stream debouncing.*
- **Store Patterns & Architectural Blueprints**: [references/store-patterns-and-architectures.md](references/store-patterns-and-architectures.md)
  *Comparative architecture between Lightweight Injectable Service Stores and `@ngrx/signals`, with Zoneless performance profiling.*
- **Automated Anti-Pattern Auditing Script**: [scripts/audit_signal_antipatterns.py](scripts/audit_signal_antipatterns.py)
  *Self-contained Python CLI tool to detect mutations in `computed()`, unmanaged effects, and deprecated methods.*
- **Production Store Template**: [assets/signal-store-template.ts](assets/signal-store-template.ts)
  *Ready-to-use TypeScript boilerplate with Clean Code annotations and zero `any` types.*
- **Signal Store Contract Schema**: [assets/signal-store-schema.json](assets/signal-store-schema.json)
  *JSON schema for validating signal store architectural contracts.*
- **Quality Verification Suite**: [evals/evals.json](evals/evals.json)
  *Evaluation test cases and objective assertions for prompt execution.*

---

## 4. Gotchas

- **State Mutation in `computed()`**: Calling `.set()` or `.update()` on any signal within a `computed()` expression throws a runtime error. Derivations must remain strictly pure and synchronous.
- **In-Place Mutation in `.update()`**: Modifying array elements in-place (`list.push(item)`) inside `.update()` preserves the object identity, causing Angular to bypass equality checks and miss change notifications. Always return a new reference (`[...list, item]`).
- **Missing Options in `toSignal()`**: Calling `toSignal(observable$)` without `{ initialValue: ... }` causes the signal type to widen to `T | undefined`. Always provide an initial value unless `requireSync: true` is verified.
- **Overusing `effect()` for State Synchronization**: Avoid using `effect()` to listen to Signal A and write to Signal B. Use `linkedSignal()` or `computed()` instead. `effect()` is strictly for operations outside Angular's reactive graph.
- **Untracked Signal Reads in `effect()`**: If an `effect()` reads multiple signals but should only trigger when one specific signal changes, wrap the secondary reads in `untracked(() => secondarySignal())`.
- **Injection Context Lifetime**: `effect()`, `toSignal()`, and `toObservable()` must be called in an active injection context (field initializers or constructors). If invoked elsewhere, pass `{ injector }` explicitly.
- **`resource` vs `rxResource` Reload Behavior**: Calling `.reload()` triggers an immediate refetch regardless of whether the `request` signal values changed.
- **Zoneless Signal Binding**: In Zoneless mode (`provideZonelessChangeDetection()`), template rendering depends directly on signal notifications. Components consuming non-signal properties or mutable class fields will NOT re-render without explicit `ChangeDetectorRef.markForCheck()`.
