# Multi-Environment Build Wiring in Modern Angular (v19+)

## 1. Overview
Modern Angular applications leverage build-time file replacements to swap configuration files between local development, staging, and production builds without polluting runtime code with dynamic conditionals (`if (env === 'production')`).

---

## 2. Modern `angular.json` Schema Alignment

In Angular 19+, applications are compiled using `@angular/build:application` (the modern Vite/esbuild application builder).

### Production Build Configuration (`fileReplacements`)
Under `projects.<project-name>.architect.build.configurations.production`:

```json
{
  "configurations": {
    "production": {
      "fileReplacements": [
        {
          "replace": "src/environments/environment.ts",
          "with": "src/environments/environment.prod.ts"
        }
      ],
      "outputHashing": "all",
      "optimization": true,
      "sourceMap": false
    },
    "development": {
      "optimization": false,
      "extractLicenses": false,
      "sourceMap": true
    }
  }
}
```

### Development Server Configuration (`proxyConfig`)
Under `projects.<project-name>.architect.serve.configurations`:

```json
{
  "configurations": {
    "production": {
      "buildTarget": "my-app:build:production"
    },
    "development": {
      "buildTarget": "my-app:build:development",
      "proxyConfig": "proxy.dev.json"
    },
    "staging": {
      "buildTarget": "my-app:build:development",
      "proxyConfig": "proxy.staging.json"
    }
  },
  "defaultConfiguration": "development"
}
```

---

## 3. Canonical Service Consumption Pattern
Components and services must ALWAYS import from the base `src/environments/environment` path, NEVER directly importing `environment.prod.ts`:

```typescript
// ✅ CORRECT: Always import base environment symbol
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class CatalogService {
  private readonly http = inject(HttpClient);
  // Replaced automatically at build-time with environment.prod.ts when building for production
  private readonly apiUrl = `${environment.apiUrl}/catalog`;
}
```

---

## 4. Standard NPM Execution Scripts (`package.json`)
Ensure standard npm scripts are configured in `package.json` for deterministic CI/CD and developer workflows:

```json
{
  "scripts": {
    "start:dev": "ng serve --configuration=development --proxy-config proxy.dev.json",
    "start:staging": "ng serve --configuration=development --proxy-config proxy.staging.json",
    "build:dev": "ng build --configuration=development",
    "build:prod": "ng build --configuration=production"
  }
}
```
