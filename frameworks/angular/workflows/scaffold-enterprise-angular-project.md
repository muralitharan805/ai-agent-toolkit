---
description: "Automated workflow to scaffold all 14 core enterprise infrastructure layers in a new or existing Angular 19+ project (ApiService, Auth Signals, functional interceptors, guards, title strategy, layout shells, SCSS theme tokens). Triggered by 'scaffold-angular:', 'scaffold:', or '/scaffold-enterprise-angular-project'."
trigger: manual
---
# Scaffold Enterprise Angular Project Workflow

## Purpose
Automate the end-to-end generation of the complete 14-point Enterprise Angular Architecture Specification in any targeted Angular project.

## Step-by-Step Execution Protocol

When triggered with "scaffold this project" or `/scaffold-enterprise-angular-project`, execute the following steps in sequence:

### Step 1: Directory Tree Scaffolding
Execute directory creation under `src/`:
```bash
mkdir -p src/app/core/guards src/app/core/interceptors src/app/core/services src/app/core/strategies src/app/core/handlers
mkdir -p src/app/shared/components/toast-notification src/app/shared/components/confirm-dialog
mkdir -p src/app/shared/components/loading-spinner src/app/shared/components/skeleton-loader
mkdir -p src/app/shared/components/empty-state src/app/shared/components/pagination
mkdir -p src/app/shared/layouts/main-layout src/app/shared/layouts/auth-layout
mkdir -p src/app/shared/directives src/app/shared/pipes src/app/shared/validators
mkdir -p src/app/features src/app/testing src/styles
```

### Step 2: Implement Core Services (Points 2, 3, 4, 5)
Create:
- `src/app/core/services/api.service.ts` (Generic `get`, `post`, `put`, `patch`, `delete`, `uploadFile`, `buildHttpParams`).
- `src/app/core/services/auth.service.ts` (`currentUser` signal, `isAuthenticated` computed, login/logout).
- `src/app/core/services/notification.service.ts` (Toast alert dispatcher).
- `src/app/core/services/loading.service.ts` (`isLoading` signal).

### Step 3: Implement Functional Interceptors (Point 6)
Create:
- `src/app/core/interceptors/auth.interceptor.ts` (Bearer token header).
- `src/app/core/interceptors/error.interceptor.ts` (401/403/500 catch and notification).
- `src/app/core/interceptors/loading.interceptor.ts` (Auto-triggers `LoadingService`).

### Step 4: Implement Functional Guards & Strategies (Points 7, 8, 9)
Create:
- `src/app/core/guards/auth.guard.ts` (`CanActivateFn`).
- `src/app/core/guards/guest.guard.ts` (`CanActivateFn`).
- `src/app/core/strategies/page-title.strategy.ts` (`AppTitleStrategy` extending `TitleStrategy`).
- `src/app/core/handlers/global-error.handler.ts` (Custom `ErrorHandler`).

### Step 5: Implement App Bootstrap & Routes (Point 1)
Create/Update:
- `src/app/app.config.ts` (Zoneless, `provideRouter`, `provideHttpClient`, `TitleStrategy`).
- `src/app/app.routes.ts` (MainLayout Shell & Auth routes).
- `src/app/app.component.ts` (`<router-outlet />`).

### Step 6: Implement Shared UI Layouts & Theme Tokens (Points 10, 11)
Create:
- `src/app/shared/layouts/main-layout/main-layout.component.ts` (Header, Sidebar, RouterOutlet).
- `src/styles/_variables.scss` (Material 3 CSS Tokens `--mat-sys-primary`, `--mat-sys-surface`).
- `src/styles/styles.scss` (SCSS Imports).

### Step 7: Scaffold Sample Domain Feature (Point 12)
Scaffold initial dashboard feature:
- `src/app/features/dashboard/models/dashboard.model.ts`
- `src/app/features/dashboard/data-access/dashboard-store.service.ts`
- `src/app/features/dashboard/feature-shell/dashboard-page.component.ts`
- `src/app/features/dashboard/dashboard.routes.ts`

### Step 8: Build Verification (Points 13, 14)
Run compilation check:
```bash
npm run build
```
Verify zero `NgModule` declarations exist and all 14 points compile cleanly without TypeScript errors.
