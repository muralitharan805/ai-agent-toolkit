---
name: angular-enterprise-scaffolding
description: "Blueprints, automated audits, and architectural protocols for scaffolding enterprise-grade Angular 19+ applications. Enforces the 14-point infrastructure specification, Standalone architecture, Zoneless change detection, functional guards/interceptors, and domain-driven directory layout."
compatibility: "Requires Angular 19+ and Node.js 20+"
---

# Angular Enterprise Scaffolding Skill (`angular-enterprise-scaffolding`)

## Persona & Architectural Mandate
Act as a Principal Frontend Architect specializing in mission-critical, enterprise Angular (v19+) application architecture. Your mandate is to enforce the canonical **14-Point Enterprise Scaffolding Specification** across all projects, ensuring 100% Standalone architecture, Zoneless or OnPush change detection, clean layer isolation, functional dependency injection (`inject()`), functional guards/interceptors, and zero legacy `NgModule` declarations.

---

## 5-Pillar Directory Map

```text
frameworks/angular/skills/angular-enterprise-scaffolding/
├── SKILL.md                                        # Tier 2 Core Scaffolding Guidance (< 500 lines)
├── references/
│   ├── fourteen-point-scaffolding-guide.md         # In-depth architectural specification
│   └── standalone-bootstrap-and-routing.md         # Bootstrap, functional providers & routing
├── scripts/
│   └── audit_enterprise_scaffolding.py             # CLI compliance audit tool (PEP 723)
├── assets/
│   ├── api.service.ts                              # Generic typed HTTP client wrapper
│   ├── app.config.ts                               # Zoneless bootstrap application config
│   └── page-title.strategy.ts                      # Route-synchronized title strategy
└── evals/
    ├── evals.json                                  # Empirical verification test suite
    └── grading.json                                # Quality benchmark scorecard (100%)
```

---

## Authoritative Reference Grounding & Bundled Assets
Consult the specialized guides and assets bundled directly inside this skill:
- **14-Point Scaffolding Guide**: [references/fourteen-point-scaffolding-guide.md](references/fourteen-point-scaffolding-guide.md)
- **Standalone Bootstrap & Routing**: [references/standalone-bootstrap-and-routing.md](references/standalone-bootstrap-and-routing.md)
- **Generic API Service Asset**: [assets/api.service.ts](assets/api.service.ts)
- **Bootstrap Config Asset**: [assets/app.config.ts](assets/app.config.ts)
- **Page Title Strategy Asset**: [assets/page-title.strategy.ts](assets/page-title.strategy.ts)
- **Automated Compliance Audit Tool**: `python3 scripts/audit_enterprise_scaffolding.py <path>`
- **Empirical Test Suite**: [evals/evals.json](evals/evals.json)

---

## 1. Domain-Driven Directory Layout & Architecture Tree

```text
src/
├── app/
│   ├── core/                        # 🛡️ Core Infrastructure & Application Singletons
│   │   ├── guards/                  # Security Route Guards (auth.guard, guest.guard, role.guard)
│   │   ├── interceptors/            # Functional HTTP Interceptors (auth, error, loading, api-prefix)
│   │   ├── services/                # Core Singletons (api.service, auth.service, notification.service, loading.service)
│   │   ├── strategies/              # Route & SEO Strategies (page-title.strategy, preload.strategy)
│   │   └── handlers/                # Uncaught Exception Handlers (global-error.handler)
│   │
│   ├── shared/                      # 🎨 Reusable UI Components, Directives, Pipes & Layouts
│   │   ├── components/              # Reusable UI Widgets (toast, confirm-dialog, loading-spinner, skeleton-loader)
│   │   ├── layouts/                 # Base App Page Shells (main-layout, auth-layout)
│   │   ├── directives/              # Custom Directives (has-permission, autofocus)
│   │   ├── pipes/                   # Custom Pure Pipes (truncate, relative-time, currency-format)
│   │   └── validators/              # Custom Form Validators (password-match, no-whitespace)
│   │
│   ├── features/                    # 📦 Bounded Domain Feature Modules (4-Subfolder Pattern)
│   │   └── [domain-feature]/        # Domain Features (e.g., 'dashboard', 'orders', 'users')
│   │       ├── data-access/         # Signal Store & Feature Services (order-store.service.ts)
│   │       ├── feature-shell/       # Container Smart Page Components & Routes (order-list-page, orders.routes.ts)
│   │       ├── ui/                  # Presentational Dumb Components (order-card, order-table)
│   │       └── models/              # TypeScript Interfaces, DTOs & Enums (order.model.ts)
│   │
│   ├── testing/                     # 🧪 Testing Harnesses & Mocks (mock-api.service, mock-auth.service)
│   ├── app.config.ts                # ⚙️ Application Bootstrap Config (Zoneless, Router, HttpClient, TitleStrategy)
│   ├── app.routes.ts                # 🛣️ Top-level App Routes (Lazy-loaded Features)
│   └── app.component.ts             # 🚀 Root Standalone Shell Component (<router-outlet />)
│
└── styles/                          # 🎨 Global Styling & Theme System Tokens
    ├── _variables.scss              # CSS Tokens / Material 3 System Variables (--mat-sys-*)
    ├── _typography.scss             # Typography scale & headings
    ├── _utilities.scss              # Global helper CSS classes (.flex-between, .skeleton-box)
    └── styles.scss                  # Main global SCSS entry point
```

---

## 2. Step-by-Step Scaffolding Protocol

### Step 1: Execute Directory Tree Creation
```bash
mkdir -p src/app/core/guards src/app/core/interceptors src/app/core/services src/app/core/strategies src/app/core/handlers
mkdir -p src/app/shared/components/toast-notification src/app/shared/components/confirm-dialog
mkdir -p src/app/shared/components/loading-spinner src/app/shared/components/skeleton-loader
mkdir -p src/app/shared/components/empty-state src/app/shared/components/pagination
mkdir -p src/app/shared/layouts/main-layout src/app/shared/layouts/auth-layout
mkdir -p src/app/shared/directives src/app/shared/pipes src/app/shared/validators
mkdir -p src/app/features src/app/testing src/styles
```

### Step 2: Establish Application Bootstrap & Providers (`app.config.ts`)
Deploy [assets/app.config.ts](assets/app.config.ts) configuring Zoneless change detection and functional interceptors:
```typescript
import { ApplicationConfig, provideExperimentalZonelessChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding, withViewTransitions, TitleStrategy } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { loadingInterceptor } from './core/interceptors/loading.interceptor';
import { AppTitleStrategy } from './core/strategies/page-title.strategy';

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
    provideRouter(routes, withComponentInputBinding(), withViewTransitions()),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor, errorInterceptor, loadingInterceptor])),
    { provide: TitleStrategy, useClass: AppTitleStrategy }
  ]
};
```

### Step 3: Implement Core Infrastructure Singletons
1. **Generic ApiService**: Deploy [assets/api.service.ts](assets/api.service.ts) into `src/app/core/services/api.service.ts`.
2. **Dynamic Title Strategy**: Deploy [assets/page-title.strategy.ts](assets/page-title.strategy.ts) into `src/app/core/strategies/page-title.strategy.ts`.
3. **Session AuthService**: Implement Signals-based session store (`currentUser = signal<User | null>(null)`, `isAuthenticated = computed(() => !!this.currentUser())`).
4. **GlobalErrorHandler**: Implement `ErrorHandler` to catch uncaught exceptions and prevent silent app crashes.

### Step 4: Implement Functional Security Guards & Interceptors
Implement functional `CanActivateFn` and `HttpInterceptorFn`:
```typescript
// src/app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (_route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  return authService.isAuthenticated()
    ? true
    : router.createUrlTree(['/auth/login'], { queryParams: { returnUrl: state.url } });
};
```

### Step 5: Implement Modular Lazy-Loaded Feature Routing
```typescript
// src/app/features/orders/orders.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from '../../core/guards/auth.guard';

export const ORDER_ROUTES: Routes = [
  {
    path: '',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./feature-shell/order-list.component').then(m => m.OrderListComponent),
        data: { title: 'Order History' }
      },
      {
        path: ':orderId',
        loadComponent: () => import('./feature-shell/order-detail.component').then(m => m.OrderDetailComponent),
        data: { title: 'Order Details' }
      }
    ]
  }
];
```

---

## 3. Automated Scaffolding Compliance Audit
Run the bundled CLI verification tool to audit any Angular project directory against the 14-point specification:

```bash
# Standard console audit report:
python3 frameworks/angular/skills/angular-enterprise-scaffolding/scripts/audit_enterprise_scaffolding.py src/app

# Machine-readable JSON output for CI pipelines:
python3 frameworks/angular/skills/angular-enterprise-scaffolding/scripts/audit_enterprise_scaffolding.py src/app --json

# Strict enforcement (fails with code 1 if any checkpoint fails):
python3 frameworks/angular/skills/angular-enterprise-scaffolding/scripts/audit_enterprise_scaffolding.py src/app --strict
```

---

## Gotchas & Anti-Patterns

| Legacy / Deprecated Anti-Pattern | Why It Fails | Modern Recommended Replacement |
| :--- | :--- | :--- |
| **`NgModule` Feature Modules** | Bloats bundle sizes, creates hidden DI scoping bugs, and obstructs tree-shaking. | **100% Standalone Components** with `loadComponent` and `loadChildren`. |
| **Class-Based Guards (`CanActivate`)** | Requires class instantiation, `@Injectable()` boilerplate, and complex test harnesses. | **Functional Guards (`CanActivateFn`)** using functional `inject(Router)`. |
| **Class-Based Interceptors (`HttpInterceptor`)** | Interceptor registration order is fragile and requires verbose multi-provider DI arrays. | **Functional Interceptors (`HttpInterceptorFn`)** with `withInterceptors([...])`. |
| **Constructor Dependency Injection** | Clutters constructors, breaks inheritance without tedious `super()`, and prevents composable functions. | **Functional `inject(Service)`** assigned to `readonly` class properties. |
| **Zone.js Change Detection** | Over-checks the entire component DOM tree on every microtask, degrading high-frequency UI performance. | **`provideExperimentalZonelessChangeDetection()`** or `ChangeDetectionStrategy.OnPush` with Signals. |
| **Untyped HTTP Client Calls** | Calls like `http.get('/api/users')` without explicit generics leak implicit `any` across the entire codebase. | **`ApiService.get<T>(...)`** enforcing strict TypeScript interfaces. |
