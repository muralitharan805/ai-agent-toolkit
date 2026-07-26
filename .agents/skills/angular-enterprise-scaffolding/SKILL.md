---
name: angular-enterprise-scaffolding
description: "Guidelines and code blueprints for scaffolding complete 14-point enterprise Angular applications including ApiService, Auth Signals, functional interceptors, guards, page title strategy, and layout shells."
---
# Angular Enterprise Scaffolding Skill

# Goal
Guide the agent in executing complete 14-point enterprise Angular scaffolding. When prompted to scaffold an Angular project, the agent must generate the complete core infrastructure, shared UI utilities, theme tokens, and feature domain layout.

# Instructions

1. **Scaffold Directory Tree**:
   Create the complete enterprise directory structure:
   ```bash
   mkdir -p src/app/core/guards src/app/core/interceptors src/app/core/services src/app/core/strategies src/app/core/handlers
   mkdir -p src/app/shared/components/toast-notification src/app/shared/components/confirm-dialog
   mkdir -p src/app/shared/components/loading-spinner src/app/shared/components/skeleton-loader
   mkdir -p src/app/shared/components/empty-state src/app/shared/components/pagination
   mkdir -p src/app/shared/layouts/main-layout src/app/shared/layouts/auth-layout
   mkdir -p src/app/shared/directives src/app/shared/pipes src/app/shared/validators
   mkdir -p src/app/features src/app/testing src/styles
   ```

2. **Implement Core Infrastructure**:
   - `src/app/core/services/api.service.ts`: Generic HTTP API wrapper (`get`, `post`, `put`, `patch`, `delete`, `uploadFile`, `buildHttpParams`).
   - `src/app/core/services/auth.service.ts`: Signals-based session store (`currentUser`, `isAuthenticated`, login/logout).
   - `src/app/core/services/notification.service.ts`: Toast dispatcher.
   - `src/app/core/services/loading.service.ts`: HTTP loading state signal (`isLoading`).
   - `src/app/core/interceptors/auth.interceptor.ts`: Attaches Bearer JWT header.
   - `src/app/core/interceptors/error.interceptor.ts`: Handles 401, 403, 500 API errors.
   - `src/app/core/interceptors/loading.interceptor.ts`: Triggers progress bar on requests.
   - `src/app/core/guards/auth.guard.ts`: Functional `CanActivateFn` checking auth status.
   - `src/app/core/strategies/page-title.strategy.ts`: Synchronizes route `data.title` with browser `<title>`.
   - `src/app/core/handlers/global-error.handler.ts`: Uncaught TS runtime error handler.

3. **Implement Shared UI Shells & Tokens**:
   - `src/app/shared/layouts/main-layout/main-layout.component.ts`: Shell with Header, Sidebar, and RouterOutlet.
   - `src/styles/_variables.scss`: Global Material 3 / CSS Tokens (`--mat-sys-primary`, `--mat-sys-surface`).

# Code Blueprints

## 1. Generic API Service (`src/app/core/services/api.service.ts`)
```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export type HttpOptions = {
  params?: Record<string, string | number | boolean | readonly (string | number | boolean)[] | undefined>;
  headers?: Record<string, string>;
};

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  get<T>(endpoint: string, options?: HttpOptions): Observable<T> {
    return this.http.get<T>(endpoint, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  post<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    return this.http.post<T>(endpoint, body, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  put<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    return this.http.put<T>(endpoint, body, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  delete<T>(endpoint: string, options?: HttpOptions): Observable<T> {
    return this.http.delete<T>(endpoint, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  uploadFile<T>(endpoint: string, file: File, extraData?: Record<string, string>): Observable<T> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    if (extraData) {
      Object.entries(extraData).forEach(([k, v]) => formData.append(k, v));
    }
    return this.http.post<T>(endpoint, formData);
  }

  private buildHttpParams(paramsObj?: HttpOptions['params']): HttpParams {
    let httpParams = new HttpParams();
    if (!paramsObj) return httpParams;
    Object.entries(paramsObj).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => { httpParams = httpParams.append(key, String(item)); });
        } else {
          httpParams = httpParams.set(key, String(value));
        }
      }
    });
    return httpParams;
  }
}
```

## 2. Dynamic Title Strategy (`src/app/core/strategies/page-title.strategy.ts`)
```typescript
import { Injectable, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AppTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);

  override updateTitle(routerState: RouterStateSnapshot): void {
    const pageTitle = this.buildTitle(routerState);
    this.title.setTitle(pageTitle ? `${pageTitle} | Application` : 'Application');
  }
}
```

## 3. Bootstrap Config (`src/app/app.config.ts`)
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
