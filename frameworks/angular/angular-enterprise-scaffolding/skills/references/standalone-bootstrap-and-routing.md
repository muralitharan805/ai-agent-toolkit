# Standalone Bootstrap, Functional Providers & Routing Guide

## 1. Application Entry Point (`main.ts`)
Angular (v19+) applications must bootstrap strictly using `bootstrapApplication` with an `ApplicationConfig` object. Never wrap bootstrap calls in `platformBrowserDynamic().bootstrapModule(AppModule)`.

```typescript
// src/main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';

bootstrapApplication(AppComponent, appConfig).catch((err: unknown) => {
  console.error('Fatal application bootstrap failure:', err);
});
```

---

## 2. Functional Router Setup & Lazy Loading
Modern Angular routing delegates feature trees to lazy-loaded standalone components or standalone route configurations:

```typescript
// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { MainLayoutComponent } from './shared/layouts/main-layout/main-layout.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/feature-shell/dashboard-page.component')
            .then(m => m.DashboardPageComponent),
        data: { title: 'Executive Dashboard' }
      },
      {
        path: 'orders',
        loadChildren: () =>
          import('./features/orders/orders.routes')
            .then(m => m.ORDER_ROUTES)
      }
    ]
  },
  {
    path: 'auth',
    loadChildren: () =>
      import('./features/auth/auth.routes')
        .then(m => m.AUTH_ROUTES)
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
```

---

## 3. Functional Route Guards (`CanActivateFn`)
Route guards are pure functions using `inject()` for dependency resolution. Class-based guards implementing `CanActivate` are deprecated.

```typescript
// src/app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (_route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl: state.url }
  });
};
```

---

## 4. Functional HTTP Interceptors (`HttpInterceptorFn`)
Functional interceptors eliminate class boilerplate and provide predictable asynchronous request/response manipulation:

```typescript
// src/app/core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  if (token) {
    const authorizedRequest = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
    return next(authorizedRequest);
  }

  return next(req);
};
```

---

## 5. Modern Component Input Binding
When `withComponentInputBinding()` is configured in `provideRouter()`, route URL parameters, query parameters, and route `data` values automatically bind to component Signal inputs:

```typescript
@Component({
  selector: 'app-order-detail',
  standalone: true,
  template: `<h1>Order #{{ orderId() }}</h1>`
})
export class OrderDetailComponent {
  // Automatically bound from route /orders/:orderId
  readonly orderId = input.required<string>();
}
```
