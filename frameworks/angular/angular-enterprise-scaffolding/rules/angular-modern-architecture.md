---
trigger: always_on
description: "Enforces modern Angular (v19+) architectural standards including Standalone components, Signals reactivity (signal, computed, input, output, resource), modern control flow (@if, @for), functional dependency injection (inject), OnPush change detection, and the 14-point enterprise scaffolding architecture."
---
# Angular Modern Architecture & Scaffolding Rule

## Description
This rule enforces enterprise-grade Angular standards based on modern Angular framework paradigms (v19+). It mandates full adoption of Standalone components, fine-grained Signal reactivity, built-in control flow syntax, functional dependency injection, and OnPush/Zoneless change detection while strictly prohibiting legacy patterns such as `NgModule` declarations, class-based router guards, decorator-based inputs/outputs, and RxJS `BehaviorSubject` for local component state. Furthermore, it mandates that any new Angular project setup MUST fulfill the 14-point enterprise infrastructure specification.

## Constraints

### 1. Modern Angular Core Architecture (v19+)
- **Standalone Architecture**: ALL components, directives, and pipes MUST be standalone. `NgModule` declarations MUST NOT be used for feature module encapsulation.
- **Signal Inputs & Outputs**: MUST use `input()`, `input.required()`, `output()`, and `model()` signal primitives instead of `@Input()` and `@Output()` property decorators.
- **Signal State & Reactivity**: Local component state MUST be managed using `signal()`, `computed()`, `linkedSignal()`, and asynchronous `resource()` / `rxResource()`. RxJS `BehaviorSubject` or `Subject` MUST NOT be used for component-local reactivity.
- **Control Flow Syntax**: MUST use built-in block syntax (`@if`, `@else`, `@for (item of items; track item.id)`, `@switch`) instead of legacy directive syntax (`*ngIf`, `*ngFor`, `*ngSwitch`).
- **Functional Dependency Injection**: Services, router tokens, and dependencies MUST be injected using the `inject(Token)` function instead of constructor parameter injection.
- **Change Detection**: Components MUST explicitly configure `changeDetection: ChangeDetectionStrategy.OnPush` or run within a zoneless change detection environment (`provideExperimentalZonelessChangeDetection()`).
- **Functional Interceptors & Guards**: Route guards, resolvers, and HTTP interceptors MUST be declared as functional constructs (`CanActivateFn`, `HttpInterceptorFn`) rather than injectable classes.

### 2. 14-Point Enterprise Infrastructure Mandate
When scaffolding or configuring an Angular project, the agent MUST establish all 14 infrastructure components:
1. `app.config.ts` (Zoneless change detection, Router, HttpClient with Interceptors, TitleStrategy).
2. `ApiService` (`src/app/core/services/api.service.ts`) with generic `get`, `post`, `put`, `patch`, `delete`, `uploadFile`, and `buildHttpParams`.
3. `AuthService` (`src/app/core/services/auth.service.ts`) with Signals reactive state (`currentUser`, `isAuthenticated`).
4. `NotificationService` & Toast UI component (`src/app/shared/components/toast-notification/`).
5. `LoadingService` & `loadingInterceptor` (`src/app/core/services/loading.service.ts`).
6. Functional Interceptors (`auth`, `error`, `loading`, `cache`, `api-prefix`).
7. Functional Security Guards (`authGuard`, `guestGuard`, `roleGuard`).
8. `AppTitleStrategy` (`src/app/core/strategies/page-title.strategy.ts`) for route `<title>` synchronization.
9. `GlobalErrorHandler` (`src/app/core/handlers/global-error.handler.ts`) for uncaught exception logging.
10. Base Page Shell Layouts (`MainLayoutComponent` with Header/Sidebar, `AuthLayoutComponent`).
11. Theme Tokens & Global SCSS (`src/styles/_variables.scss`, `_typography.scss`, `_utilities.scss`).
12. Domain Feature 4-Subfolder Pattern (`data-access/`, `feature-shell/`, `ui/`, `models/`).
13. Complete Enterprise Directory Layout (`core/`, `shared/`, `features/`, `testing/`, `styles/`).
14. Automated Scaffolding Verification & Build Checks.

## Examples

- **Correct implementation:**
```typescript
// user-profile.component.ts
import { Component, ChangeDetectionStrategy, inject, input, output, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserService, User } from './user.service';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="user-card">
      @if (isLoading()) {
        <div class="skeleton-loader">Loading profile...</div>
      } @else if (user(); as currentUser) {
        <header class="card-header">
          <h2>{{ displayName() }}</h2>
          <span class="badge">{{ currentUser.role }}</span>
        </header>
        <p>{{ currentUser.email }}</p>
        <button type="button" (click)="onSelectUser()">Select Profile</button>
      } @else {
        <p class="empty-state">No profile selected.</p>
      }
    </section>
  `,
  styleUrl: './user-profile.component.scss'
})
export class UserProfileComponent {
  private readonly userService = inject(UserService);

  // Signal Inputs & Outputs
  readonly userId = input.required<string>();
  readonly profileSelected = output<string>();

  // Reactive State & Computed Signals
  readonly isLoading = signal<boolean>(false);
  readonly user = signal<User | null>(null);
  readonly displayName = computed(() => {
    const current = this.user();
    return current ? `${current.firstName} ${current.lastName}` : 'Guest';
  });

  onSelectUser(): void {
    const current = this.user();
    if (current) {
      this.profileSelected.emit(current.id);
    }
  }
}
```
