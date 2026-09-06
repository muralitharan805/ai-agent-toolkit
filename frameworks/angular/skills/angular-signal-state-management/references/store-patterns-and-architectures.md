# Angular Store Patterns & Architecture Technical Guide

This guide details enterprise state management patterns in modern Angular (v19+), contrasting lightweight injectable service stores with `@ngrx/signals`, and explaining their integration with Zoneless change detection.

---

## 1. Architectural Selection Matrix

Choose the simplest state abstraction that satisfies requirements:

```text
┌─────────────────────────────────────────────────────────────┐
│ Does state outlive a single component or route lifecycle?   │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼ NO                            ▼ YES
     ┌───────────────────┐       ┌───────────────────────────────┐
     │ Component-Local   │       │ Does it require shared        │
     │ Signals (inline)  │       │ caching, async orchestration, │
     └───────────────────┘       │ or multi-feature coordination?│
                                 └───────────────┬───────────────┘
                                                 │
                                 ┌───────────────┴───────────────┐
                                 ▼ NO                            ▼ YES
                       ┌───────────────────┐       ┌───────────────────────────┐
                       │ Lightweight       │       │ Feature Complexity Check: │
                       │ Injectable Store  │       │ Entity management, RxJS   │
                       │ (Service Pattern) │       │ side-effects, plugins?    │
                       └───────────────────┘       └─────────────┬─────────────┘
                                                                 │
                                                 ┌───────────────┴───────────────┐
                                                 ▼ Standard                      ▼ Highly Complex
                                       ┌───────────────────┐       ┌───────────────────────────┐
                                       │ Lightweight Store │       │ NgRx SignalStore          │
                                       │ + rxResource      │       │ (@ngrx/signals)           │
                                       └───────────────────┘       └───────────────────────────┘
```

---

## 2. Pattern 1: Lightweight Injectable Signal Store

For 85% of enterprise business modules, a clean injectable service exposing read-only signals provides sufficient encapsulation, minimal bundle overhead, and zero third-party dependencies.

### 2.1 Core Architectural Tenets

1. **Private Writable State**: Internal state signals are private and never exposed directly to components.
2. **Public Readonly & Computed Views**: Components consume state strictly through read-only signals and computed selectors.
3. **Action Methods**: State transitions occur exclusively through explicit public methods containing input validation and business rules.

### 2.2 Complete Implementation Example

```typescript
// features/inventory/data-access/inventory-store.service.ts
import { Injectable, inject, signal, computed, linkedSignal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { rxResource } from '@angular/core/rxjs-interop';

export interface InventoryItem {
  readonly id: string;
  readonly sku: string;
  readonly stockQuantity: number;
  readonly unitPrice: number;
}

export interface InventoryFilters {
  readonly search: string;
  readonly inStockOnly: boolean;
  readonly pageIndex: number;
}

/**
 * Enterprise state store managing inventory catalog and filter projections.
 */
@Injectable({ providedIn: 'root' })
export class InventoryStoreService {
  private readonly http = inject(HttpClient);

  // 1. Private Writable State
  private readonly filterState = signal<InventoryFilters>({
    search: '',
    inStockOnly: false,
    pageIndex: 0
  });

  // 2. Synchronized Writable Signal (Resets pagination when search updates)
  readonly activePageIndex = linkedSignal<string, number>({
    source: () => this.filterState().search,
    computation: (_search, prev) => (prev ? 0 : 0)
  });

  // 3. Asynchronous Data Resource
  readonly catalogResource = rxResource<readonly InventoryItem[], InventoryFilters>({
    request: () => ({
      ...this.filterState(),
      pageIndex: this.activePageIndex()
    }),
    loader: ({ request }) =>
      this.http.get<readonly InventoryItem[]>('/api/v1/inventory', {
        params: {
          q: request.search,
          inStock: String(request.inStockOnly),
          page: String(request.pageIndex)
        }
      })
  });

  // 4. Public Derived Computed Projections
  readonly items = computed(() => this.catalogResource.value() ?? []);
  readonly isLoading = computed(() => this.catalogResource.isLoading());
  readonly error = computed(() => this.catalogResource.error());
  readonly filters = this.filterState.asReadonly();

  readonly totalInventoryValue = computed<number>(() => {
    return this.items().reduce((total, item) => total + item.stockQuantity * item.unitPrice, 0);
  });

  // 5. Explicit Action Methods
  /**
   * Updates search query keyword and triggers catalog refetch.
   * @param keyword User query string
   */
  setSearchKeyword(keyword: string): void {
    const trimmed = keyword.trim();
    this.filterState.update(prev => ({ ...prev, search: trimmed }));
  }

  /**
   * Toggles whether out-of-stock items should be hidden.
   */
  toggleInStockOnly(): void {
    this.filterState.update(prev => ({ ...prev, inStockOnly: !prev.inStockOnly }));
  }

  /**
   * Navigates to a specific pagination index.
   * @param page Target page zero-indexed
   */
  goToPage(page: number): void {
    if (page < 0) {
      return;
    }
    this.activePageIndex.set(page);
  }

  /**
   * Reloads inventory data from the backend.
   */
  reload(): void {
    this.catalogResource.reload();
  }
}
```

---

## 3. Pattern 2: NgRx SignalStore (`@ngrx/signals`)

When applications require modular plugin composition, reusable entity management, or advanced reactive method orchestration, `@ngrx/signals` provides a standardized functional architecture.

### 3.1 Anatomy of a SignalStore

```typescript
// features/customers/data-access/customer.store.ts
import { computed, inject } from '@angular/core';
import { signalStore, withState, withComputed, withMethods, withHooks, patchState } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe } from 'rxjs';
import { tap, switchMap, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';

export interface Customer {
  readonly id: string;
  readonly name: string;
  readonly balance: number;
}

export interface CustomerState {
  readonly customers: readonly Customer[];
  readonly isLoading: boolean;
  readonly filterQuery: string;
}

const initialCustomerState: CustomerState = {
  customers: [],
  isLoading: false,
  filterQuery: ''
};

export const CustomerStore = signalStore(
  { providedIn: 'root' },
  withState(initialCustomerState),

  withComputed(({ customers, filterQuery }) => ({
    filteredCustomers: computed(() => {
      const query = filterQuery().toLowerCase();
      return customers().filter(c => c.name.toLowerCase().includes(query));
    }),
    totalBalance: computed(() => {
      return customers().reduce((acc, curr) => acc + curr.balance, 0);
    })
  })),

  withMethods((store, http = inject(HttpClient)) => ({
    setFilterQuery(filterQuery: string): void {
      patchState(store, { filterQuery });
    },

    loadCustomers: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoading: true })),
        switchMap(() =>
          http.get<readonly Customer[]>('/api/v1/customers').pipe(
            tap({
              next: customers => patchState(store, { customers, isLoading: false }),
              error: () => patchState(store, { isLoading: false })
            })
          )
        )
      )
    )
  })),

  withHooks({
    onInit(store) {
      store.loadCustomers();
    }
  })
);
```

---

## 4. Zoneless Change Detection Integration

Modern Angular supports complete Zone.js omission via `provideExperimentalZonelessChangeDetection()` in `app.config.ts`.

### 4.1 How Signals Drive Zoneless Rendering

1. **No Polling or Monkey Patching**: In Zone.js, asynchronous tasks (timers, microtasks, DOM events) triggered a top-down dirty check of the component hierarchy.
2. **Push-Based Notifications**: With Signals, calling `.set()` or `.update()` notifies the consumer view directly.
3. **Template Reactivity**: When templates read `store.items()`, Angular links that node directly to DOM rendering passes.
4. **Zero Overhead**: Inactive tabs or views without active signal modifications perform zero CPU cycles during browser event loops.
