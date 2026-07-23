---
trigger: manual
description: "Execution workflow for initializing or converting an Angular application to modern Angular 19+ architecture (Standalone, Signals, Functional Providers, Zoneless Change Detection)."
---
# Setup Modern Angular Project Workflow

## Purpose
This workflow provides step-by-step instructions to configure a newly generated or existing Angular application with production-grade Standalone Component architecture, Signal-driven state patterns, functional dependency injection, and optimized change detection.

## Execution Steps

### Step 1: Verify Dependencies & Angular Version
1. Ensure the workspace is running Angular 19 or higher in `package.json`.
2. Verify TypeScript is configured with strict mode enabled in `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "strict": true,
       "noImplicitOverride": true,
       "noPropertyAccessFromIndexSignature": true,
       "noImplicitReturns": true,
       "noFallthroughCasesInSwitch": true
     }
   }
   ```

### Step 2: Configure Functional App Bootstrap (`main.ts` & `app.config.ts`)
1. Create or update `src/app/app.config.ts` with functional providers:
   ```typescript
   import { ApplicationConfig, provideExperimentalZonelessChangeDetection } from '@angular/core';
   import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';
   import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
   import { routes } from './app.routes';
   import { authInterceptor } from './core/interceptors/auth.interceptor';

   export const appConfig: ApplicationConfig = {
     providers: [
       provideExperimentalZonelessChangeDetection(),
       provideRouter(routes, withComponentInputBinding(), withViewTransitions()),
       provideHttpClient(withFetch(), withInterceptors([authInterceptor]))
     ]
   };
   ```
2. Verify `src/main.ts` bootstraps the `AppComponent` using `bootstrapApplication`:
   ```typescript
   import { bootstrapApplication } from '@angular/platform-browser';
   import { AppComponent } from './app/app.component';
   import { appConfig } from './app/app.config';

   bootstrapApplication(AppComponent, appConfig)
     .catch((err) => console.error(err));
   ```

### Step 3: Scaffold Enterprise Master Directory Architecture
Scaffold the complete 14-point Master Directory layout under `src/`:
```bash
# Core Layer
mkdir -p src/app/core/guards src/app/core/interceptors src/app/core/services src/app/core/strategies src/app/core/handlers

# Shared UI & Utilities Layer
mkdir -p src/app/shared/components/toast-notification src/app/shared/components/confirm-dialog
mkdir -p src/app/shared/components/loading-spinner src/app/shared/components/skeleton-loader
mkdir -p src/app/shared/components/empty-state src/app/shared/components/pagination
mkdir -p src/app/shared/layouts/main-layout src/app/shared/layouts/auth-layout
mkdir -p src/app/shared/directives src/app/shared/pipes src/app/shared/validators

# Domain Features & Testing Layer
mkdir -p src/app/features src/app/testing

# Global Styling & Tokens Layer
mkdir -p src/styles
```

### Step 4: Configure Global Root Component
Update `src/app/app.component.ts` as a Standalone component:
```typescript
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<router-outlet />`,
  styleUrl: './app.component.scss'
})
export class AppComponent {}
```

### Step 5: Validate Application Setup
1. Run `npm run build` or `ng build` to verify clean compilation.
2. Confirm zero `NgModule` imports exist in the project directory.
