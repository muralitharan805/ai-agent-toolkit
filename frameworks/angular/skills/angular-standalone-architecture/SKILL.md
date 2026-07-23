---
name: angular-standalone-architecture
description: "Guidelines and protocols for scaffolding Angular 19+ applications using Standalone Components, functional router config, functional HTTP interceptors, and domain-driven folder architecture."
---
# Angular Standalone Architecture Skill

# Goal
Guide the agent in structuring, scaffolding, and configuring modern Standalone Angular applications with zero `NgModule` dependencies, clean functional providers, modular routing, and strict layer boundaries.

# Instructions

1. **Bootstrap & Provider Configuration**:
   - Bootstrap applications strictly using `bootstrapApplication(AppComponent, appConfig)` in `main.ts`.
   - Configure global providers in `app.config.ts` using functional providers:
     - `provideRouter(routes, withComponentInputBinding(), withViewTransitions())`
     - `provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]))`
     - `provideExperimentalZonelessChangeDetection()` or standard zone configuration.

2. **Domain-Driven Directory Layout & Master Scaffolding**:
   - Organise code into strict architectural boundaries following the 14-Point Master Scaffolding Specification:
     ```text
     src/
     ├── app/
     │   ├── core/                        # 🛡️ Core Infrastructure & Application Singletons
     │   │   ├── guards/                  # Security Route Guards (auth.guard, guest.guard, role.guard)
     │   │   ├── interceptors/            # Functional HTTP Interceptors (auth, error, loading, api-prefix, cache)
     │   │   ├── services/                # Core Singletons (api.service, auth.service, notification.service, storage.service, loading.service)
     │   │   ├── strategies/              # Route & SEO Strategies (page-title.strategy, preload.strategy)
     │   │   └── handlers/                # Uncaught Exception Handlers (global-error.handler)
     │   │
     │   ├── shared/                      # 🎨 Reusable UI Components, Directives, Pipes & Layouts
     │   │   ├── components/              # Reusable UI Widgets (toast-notification, confirm-dialog, loading-spinner, skeleton-loader, empty-state, pagination)
     │   │   ├── layouts/                 # Base App Page Shells (main-layout, auth-layout)
     │   │   ├── directives/              # Custom Utility Directives (has-permission.directive, autofocus.directive)
     │   │   ├── pipes/                   # Custom Utility Pipes (truncate.pipe, relative-time.pipe, currency-format.pipe)
     │   │   └── validators/              # Typed Reactive Form Custom Validators (password-match, no-whitespace)
     │   │
     │   ├── features/                    # 📦 Bounded Domain Feature Modules (Modular 4-Subfolder Pattern)
     │   │   └── [feature-name]/          # Domain Features (e.g., 'users', 'products', 'orders')
     │   │       ├── data-access/         # Signal Store & Feature Services (user-store.service.ts, user-api.service.ts)
     │   │       ├── feature-shell/       # Container Smart Page Components & Feature Routes (user-list-page, users.routes.ts)
     │   │       ├── ui/                  # Presentational Dumb Components (user-card, user-table, user-form-modal)
     │   │       └── models/              # TypeScript Interfaces, DTOs & Enums (user.model.ts)
     │   │
     │   ├── testing/                     # 🧪 Testing Harnesses & Mocks (mock-api.service, mock-auth.service)
     │   ├── app.config.ts                # ⚙️ Application Bootstrap Config (Zoneless, Router, HttpClient, TitleStrategy)
     │   ├── app.routes.ts                # 🛣️ Top-level App Routes (Lazy-loaded Features)
     │   └── app.component.ts             # 🚀 Root Standalone Shell Component (`<router-outlet />`)
     │
     └── styles/                          # 🎨 Global Styling & Theme System Tokens
         ├── _variables.scss              # CSS Tokens / Material 3 System Variables (`--mat-sys-*`)
         ├── _typography.scss             # Font scale, headings & body text styles
         ├── _utilities.scss              # Global helper CSS classes (`.flex-between`, `.skeleton-box`)
         └── styles.scss                  # Main global SCSS entry point
     ```

3. **Functional Router Routing & Lazy Loading**:
   - Define feature routes using `loadComponent` or `loadChildren` with standalone components and route files.
   - Use `withComponentInputBinding()` so route params and query params automatically bind to signal inputs (`input()`).

4. **Functional Security Guards & Resolvers**:
   - Implement route guards as `CanActivateFn` functions using `inject()` for dependency retrieval.
   - Implement route resolvers as `ResolveFn<T>` functions.

5. **Functional HTTP Interceptors**:
   - Write HTTP interceptors as `HttpInterceptorFn` pure functions manipulating `HttpRequest` and calling `next(req)`.

# Examples

## 1. Application Configuration (`app.config.ts`)
```typescript
// app/app.config.ts
import { ApplicationConfig, provideExperimentalZonelessChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { loggingInterceptor } from './core/interceptors/logging.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
    provideRouter(
      routes,
      withComponentInputBinding(),
      withViewTransitions()
    ),
    provideHttpClient(
      withFetch(),
      withInterceptors([authInterceptor, loggingInterceptor])
    )
  ]
};
```

## 2. Functional Auth Guard & HTTP Interceptor
```typescript
// app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

// app/core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  if (token) {
    const clonedReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
    return next(clonedReq);
  }

  return next(req);
};
```

## 3. Modular Standalone Feature Routes (`features/orders/orders.routes.ts`)
```typescript
// app/features/orders/orders.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from '../../core/guards/auth.guard';

export const ORDER_ROUTES: Routes = [
  {
    path: '',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./feature-shell/order-list.component').then(m => m.OrderListComponent)
      },
      {
        path: ':orderId',
        loadComponent: () => import('./feature-shell/order-detail.component').then(m => m.OrderDetailComponent)
      }
    ]
  }
];
```

# Constraints
- NEVER import `NgModule` or use `@NgModule()` in modern Angular applications.
- MUST use functional `CanActivateFn` and `HttpInterceptorFn` constructs.
- MUST leverage `withComponentInputBinding()` for route parameter injection into components.
