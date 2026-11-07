# Angular Async Resources & RxJS Interoperability Technical Guide

This guide provides architectural specifications and production patterns for managing asynchronous operations using Angular's Resource primitives (`resource`, `rxResource`) and RxJS bridge functions (`toSignal`, `toObservable`).

---

## 1. Asynchronous Resource Primitives

Angular provides native primitives to bind asynchronous fetch lifecycles directly into the reactive signal graph without boilerplate BehaviorSubjects.

### 1.1 `resource()` vs `rxResource()`

| Capability | `resource()` (Native Promise) | `rxResource()` (RxJS Observable) |
| :--- | :--- | :--- |
| **Import Path** | `@angular/core` | `@angular/core/rxjs-interop` |
| **Loader Return** | `Promise<T>` | `Observable<T>` |
| **HttpClient Integration** | Requires wrapping with `firstValueFrom` | Direct Observable pipe (Idiomatic) |
| **Cancellation** | Native `AbortSignal` parameter | Handled via RxJS Observable unsubscription / `AbortSignal` |
| **Best For** | Browser `fetch()`, async SDKs, native APIs | Angular `HttpClient`, RxJS pipelines |

### 1.2 `rxResource` Architecture & Lifecycle

```typescript
import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { rxResource } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';

export interface UserProfile {
  readonly id: string;
  readonly username: string;
  readonly email: string;
}

@Injectable({ providedIn: 'root' })
export class UserProfileService {
  private readonly http = inject(HttpClient);

  readonly targetUserId = signal<string>('usr_1001');

  readonly profileResource = rxResource<UserProfile, { userId: string }>({
    // Request signal: Whenever targetUserId() changes, the loader automatically re-executes
    request: () => ({ userId: this.targetUserId() }),
    loader: ({ request, abortSignal }) => {
      // Return typed Observable. Passing abortSignal ensures HTTP cancellation
      return this.http.get<UserProfile>(`/api/v1/users/${request.userId}`);
    }
  });

  // Resource State Projections
  readonly profile = this.profileResource.value.asReadonly();
  readonly isLoading = this.profileResource.isLoading.asReadonly();
  readonly error = this.profileResource.error.asReadonly();
  readonly status = this.profileResource.status.asReadonly();

  // Manual Refresh
  refreshProfile(): void {
    this.profileResource.reload();
  }

  // Optimistic Local State Update
  updateLocalName(newUsername: string): void {
    this.profileResource.update(current => {
      if (!current) {
        return undefined;
      }
      return { ...current, username: newUsername };
    });
  }
}
```

### 1.3 Resource Status Enum & Handling

A resource exhibits one of several discrete states:
- `ResourceStatus.Idle`: No request dispatched yet.
- `ResourceStatus.Loading`: Active in-flight network request.
- `ResourceStatus.Resolved`: Data successfully loaded and available in `.value()`.
- `ResourceStatus.Error`: Request failed; error object accessible via `.error()`.
- `ResourceStatus.Local`: Resource value was locally overridden via `.set()` or `.update()`.

---

## 2. RxJS Interoperability Primitives

When integrating with reactive browser events, web sockets, or complex debounce operators, use `@angular/core/rxjs-interop`.

### 2.1 `toSignal(observable$, options)`

Converts an Observable into a Signal.

#### Options Matrix

```typescript
import { toSignal } from '@angular/core/rxjs-interop';
import { inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs/operators';

// 1. Safe default with explicit initialValue (Recommended)
readonly queryParam = toSignal(
  this.route.queryParamMap.pipe(map(params => params.get('tab') ?? 'overview')),
  { initialValue: 'overview' }
);

// 2. Synchronous observable requirement (e.g., BehaviorSubject)
readonly cachedToken = toSignal(this.authService.token$, { requireSync: true });

// 3. Rejecting errors instead of storing them as undefined
readonly liveUpdates = toSignal(this.webSocketService.stream$, {
  initialValue: null,
  rejectErrors: true // Throws unhandled exceptions to global error handler
});
```

> [!WARNING]
> If neither `initialValue` nor `requireSync: true` is supplied, TypeScript infers the signal return type as `Signal<T | undefined>`. Always provide `initialValue` to guarantee strict non-null typing.

### 2.2 `toObservable(signalRef, options)`

Converts a Signal into an RxJS Observable to leverage operators like `debounceTime`, `distinctUntilChanged`, `switchMap`, or `bufferTime`.

```typescript
import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { HttpClient } from '@angular/common/http';
import { debounceTime, distinctUntilChanged, filter, switchMap } from 'rxjs/operators';

export interface SearchMatch {
  readonly id: string;
  readonly title: string;
}

@Component({
  selector: 'app-global-search',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <input
      type="search"
      [value]="searchTerm()"
      (input)="onSearchChange($event)"
      placeholder="Type to search..."
    />
    @if (searchResults(); as results) {
      <ul role="listbox">
        @for (item of results; track item.id) {
          <li role="option">{{ item.title }}</li>
        }
      </ul>
    }
  `
})
export class GlobalSearchComponent {
  private readonly http = inject(HttpClient);

  readonly searchTerm = signal<string>('');

  // Pipe signal through debounce and switchMap, then bridge back to Signal
  readonly searchResults = toSignal(
    toObservable(this.searchTerm).pipe(
      map(term => term.trim()),
      filter(term => term.length >= 3),
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(term =>
        this.http.get<readonly SearchMatch[]>('/api/v1/search', {
          params: { query: term }
        })
      )
    ),
    { initialValue: [] }
  );

  onSearchChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchTerm.set(input.value);
  }
}
```

### 2.3 Injection Context Rules

Both `toSignal()` and `toObservable()` rely on an active `EnvironmentInjector` to manage lifecycle subscriptions and teardown automatically.

- If called outside a constructor or property initializer (e.g. inside an event callback or method), you MUST explicitly pass an `Injector`:
  ```typescript
  import { Injector, inject } from '@angular/core';

  const injector = inject(Injector);
  const customSignal = toSignal(observable$, { injector });
  ```
