---
name: angular-signal-state-management
description: "Guidelines and protocols for designing reactive state management in Angular 19+ applications using Signals, computed states, linkedSignals, resources, and RxJS interoperability primitives."
---
# Angular Signal State Management Skill

# Goal
Guide the agent in implementing granular, highly performant, type-safe reactive state management using modern Angular Signals (`signal()`, `computed()`, `linkedSignal()`, `resource()`, `rxResource()`) and RxJS bridge utilities (`toSignal()`, `toObservable()`).

# Instructions

1. **Local & Global State Primitive Selection**:
   - Use `signal<T>(initialValue)` for mutable state nodes.
   - Mutate signals using `.set(newValue)` for direct replacements or `.update(fn)` for transformations based on previous value.
   - NEVER call `.set()` or `.update()` inside a `computed()` signal expression or component template getter.

2. **Derived Reactive Computation**:
   - Derive cached dependent state strictly using `computed(() => expression)`.
   - Ensure expressions in `computed()` are pure, synchronous, and side-effect free.
   - Avoid creating manual subscription loops or `effect()` blocks to synchronise two signal values.

3. **Synchronised & Dependent Writable Signals**:
   - Use `linkedSignal({ source: signalA, computation: (val) => derivedVal })` when a signal's writable value needs to automatically reset or re-evaluate whenever a source signal changes (e.g., reset pagination or selected tab when search query updates).

4. **Asynchronous Data Fetching via Resource Primitives**:
   - Use `resource({ request: () => params(), loader: async ({ request, abortSignal }) => fetch(...) })` or `rxResource()` for data fetching linked to reactive input parameters.
   - Leverage built-in resource status signals (`resource.value()`, `resource.isLoading()`, `resource.error()`).

5. **RxJS Interoperability Protocol**:
   - Convert asynchronous observables (e.g., Router events, WebSockets, NgRx streams) into Signals using `toSignal(observable$, { initialValue })` within an injection context.
   - Convert Signals to Observables using `toObservable(signalRef)` when integrating with RxJS operators like `debounceTime` or `switchMap`.

6. **Lightweight Signal Store Pattern**:
   - Structure domain feature state into injectable service classes exposing read-only signals and action methods.

# Examples

## 1. Feature State Store with Signal Primitives
```typescript
// features/products/data-access/product-store.service.ts
import { Injectable, inject, signal, computed, linkedSignal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { rxResource } from '@angular/core/rxjs-interop';

export interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
}

@Injectable({ providedIn: 'root' })
export class ProductStoreService {
  private readonly http = inject(HttpClient);

  // State Primitives
  readonly selectedCategory = signal<string>('all');
  readonly searchQuery = signal<string>('');
  readonly pageIndex = linkedSignal({
    source: this.selectedCategory,
    computation: () => 0 // Reset page to 0 whenever category changes
  });

  // Asynchronous Resource Fetcher
  readonly productsResource = rxResource({
    request: () => ({ category: this.selectedCategory(), query: this.searchQuery() }),
    loader: ({ request }) => 
      this.http.get<Product[]>(`/api/products`, {
        params: { category: request.category, q: request.query }
      })
  });

  // Derived Computed Views
  readonly products = computed(() => this.productsResource.value() ?? []);
  readonly isLoading = computed(() => this.productsResource.isLoading());
  readonly totalProducts = computed(() => this.products().length);

  // Actions
  setCategory(category: string): void {
    this.selectedCategory.set(category);
  }

  setSearchQuery(query: string): void {
    this.searchQuery.set(query);
  }

  nextPage(): void {
    this.pageIndex.update(idx => idx + 1);
  }
}
```

## 2. Converting RxJS Debounced Input to Signal
```typescript
// features/search/search-bar.component.ts
import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <input type="search" (input)="onSearchInput($event)" placeholder="Search items..." />
    @if (searchResults(); as results) {
      <ul>
        @for (item of results; track item.id) {
          <li>{{ item.name }}</li>
        }
      </ul>
    }
  `
})
export class SearchBarComponent {
  private readonly http = inject(HttpClient);
  
  readonly searchTerm = signal<string>('');

  // RxJS pipeline bridged to Signal
  readonly searchResults = toSignal(
    toObservable(this.searchTerm).pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(term => this.http.get<Array<{ id: string; name: string }>>(`/api/search?q=${term}`))
    ),
    { initialValue: [] }
  );

  onSearchInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchTerm.set(input.value);
  }
}
```

# Constraints
- NEVER mutate state inside `computed()` signals.
- MUST supply explicit `initialValue` or handle `undefined` when using `toSignal()`.
- MUST use `linkedSignal()` instead of imperative `effect()` to keep writable dependent state synchronized.
