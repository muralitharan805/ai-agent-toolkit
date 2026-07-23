---
trigger: always_on
description: "Mandates that any Angular project scaffolding operation MUST construct all 14 enterprise infrastructure points including generic ApiService, Auth Signals store, functional interceptors, guards, title strategy, layout shells, and SCSS theme tokens."
---
# Angular Enterprise Scaffolding Rule

## Description
This rule enforces that whenever an agent is instructed to initialize or scaffold an Angular application, it MUST implement all 14 core enterprise infrastructure layers. Scaffolding MUST NOT stop at a blank Angular CLI skeleton; it must establish production-ready core services, security guards, HTTP interceptors, layout shells, theme tokens, and feature domain conventions.

## Constraints
- **14-Point Mandate**: The agent MUST generate all 14 core scaffolding components during project setup:
  1. `app.config.ts` (Zoneless, Router, HttpClient with Interceptors, TitleStrategy).
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
  14. Automated Scaffolding Documentation & Verification.
- **Zero Legacy Patterns**: MUST NOT generate `NgModule` declarations or class-based route guards.
- **Type Safety**: MUST NOT use `any` types in generic HTTP methods or store state primitives.

## Examples

- **Correct implementation:**
```typescript
// src/app/core/services/api.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  get<T>(endpoint: string, params?: Record<string, unknown>): Observable<T> {
    const httpParams = this.buildHttpParams(params);
    return this.http.get<T>(endpoint, { params: httpParams });
  }

  private buildHttpParams(paramsObj?: Record<string, unknown>): HttpParams {
    let httpParams = new HttpParams();
    if (!paramsObj) return httpParams;
    Object.entries(paramsObj).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        httpParams = httpParams.set(key, String(value));
      }
    });
    return httpParams;
  }
}
```
