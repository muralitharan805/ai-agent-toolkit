---
trigger: model_decision
description: "Enforces strict Angular environment separation, proxy configurations, and zero-hardcoding rules for backend API URLs across development, staging, and production builds."
---

# Angular Environment & Proxy Configuration Rule

## Description
This rule strictly forbids hardcoding backend API URLs, hostnames, ports, or protocol prefixes inside Angular components, services, interceptors, or templates. It mandates the use of strictly typed environment files (`environment.ts`, `environment.prod.ts`), relative endpoint paths (`/api`) for local development, distinct proxy configurations (`proxy.dev.json`, `proxy.staging.json`) to bypass Cross-Origin Resource Sharing (CORS) restrictions, and deterministic build-time file replacements in `angular.json`.

## Constraints

### 1. Zero Hardcoded URLs Invariant
- Developers and AI agents MUST NEVER write raw URLs (e.g. `http://localhost:3000`, `http://127.0.0.1:8080`, `https://api.example.com`) inside `.ts` files, templates, or inline strings.
- All HTTP requests and WebSocket connections MUST resolve base URLs dynamically from `environment.apiUrl` or `environment.wsUrl` imported from the canonical environment path (`src/environments/environment`).
- Code reviews and automated linters MUST treat raw protocol strings (`http://`, `https://`, `ws://`, `wss://`) inside service logic as critical build failures.

### 2. Relative Endpoint Paths in Local Development
- In development mode (`src/environments/environment.ts`), `environment.apiUrl` MUST be defined as a relative root path (e.g. `/api` or `/api/v1`).
- The Angular CLI development server (`ng serve`) MUST forward these relative requests to the appropriate target backend via a local reverse proxy configuration file.
- Direct browser calls to disparate ports on `localhost` without proxy forwarding are STRICTLY FORBIDDEN to eliminate CORS preflight failures and browser security warnings.

### 3. Dedicated Multi-Environment Proxy Files
- Angular workspaces MUST maintain dedicated proxy configuration files at the root of the project:
  - `proxy.dev.json`: For routing traffic to local development backend instances (e.g. NestJS running on port 3000).
  - `proxy.staging.json`: For routing local frontend sessions to cloud-hosted staging or test environments.
- Every proxy configuration MUST specify:
  - `target`: The fully qualified backend origin.
  - `secure`: Set to `false` for local dev or self-signed SSL; `true` for valid remote TLS certificates.
  - `changeOrigin`: Set to `true` to ensure the Host header matches the target origin.
  - `pathRewrite`: Optional path rewriting dictionary when frontend path prefixes differ from backend route structures.

### 4. WebSocket & Microservice Gateway Proxying
- When real-time WebSocket communication is utilized (e.g. Socket.io, NestJS Gateways), proxy configurations MUST include `"ws": true` on the target route definition to prevent connection dropouts and socket polling fallbacks.
- Multi-service applications communicating with multiple backend microservices MUST declare distinct route keys in the proxy configuration (e.g. `"/api/auth"`, `"/api/billing"`, `"/api/notifications"`).

### 5. Deterministic `angular.json` Build & Serve Wiring
- `angular.json` build targets MUST declare production file replacements under `architect.build.configurations.production.fileReplacements`:
  ```json
  "fileReplacements": [
    {
      "replace": "src/environments/environment.ts",
      "with": "src/environments/environment.prod.ts"
    }
  ]
  ```
- The serve target (`architect.serve.configurations`) MUST bind proxy configuration files to their respective target configurations (`"proxyConfig": "proxy.dev.json"`).

### 6. Standardized Execution Scripts (`package.json`)
- `package.json` MUST provide explicit scripts that pass configuration and proxy flags, ensuring reproducibility across developer environments:
  - `"start:dev"`: `ng serve --configuration=development --proxy-config proxy.dev.json`
  - `"start:staging"`: `ng serve --configuration=development --proxy-config proxy.staging.json`
  - `"build:dev"`: `ng build --configuration=development`
  - `"build:live"`: `ng build --configuration=production`

## Examples

### Correct Implementation

```typescript
// src/environments/environment.ts (Development - Uses Relative Proxy Path)
export interface EnvironmentConfig {
  readonly production: boolean;
  readonly apiUrl: string;
  readonly wsUrl: string;
  readonly appName: string;
}

export const environment: EnvironmentConfig = {
  production: false,
  apiUrl: '/api',
  wsUrl: '/socket.io',
  appName: 'Enterprise Application (Dev)'
};
```

```typescript
// src/environments/environment.prod.ts (Production - Fully Qualified Gateway)
import { EnvironmentConfig } from './environment';

export const environment: EnvironmentConfig = {
  production: true,
  apiUrl: 'https://api.yourdomain.com/v1',
  wsUrl: 'wss://api.yourdomain.com/socket.io',
  appName: 'Enterprise Application'
};
```

```json
// proxy.dev.json (Root directory)
{
  "/api": {
    "target": "http://localhost:3000",
    "secure": false,
    "changeOrigin": true,
    "pathRewrite": {
      "^/api": "/v1"
    }
  },
  "/socket.io": {
    "target": "http://localhost:3000",
    "secure": false,
    "changeOrigin": true,
    "ws": true
  }
}
```

```typescript
// src/app/core/services/user-api.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface UserProfileDto {
  readonly id: string;
  readonly email: string;
  readonly displayName: string;
}

@Injectable({ providedIn: 'root' })
export class UserApiService {
  private readonly http = inject(HttpClient);
  // Resolves to '/api/users' in dev (proxied to localhost:3000/v1/users)
  // Resolves to 'https://api.yourdomain.com/v1/users' in production
  private readonly endpoint = `${environment.apiUrl}/users`;

  fetchUserProfile(userId: string): Observable<UserProfileDto> {
    return this.http.get<UserProfileDto>(`${this.endpoint}/${encodeURIComponent(userId)}`);
  }
}
```

### Incorrect Implementation (STRICTLY FORBIDDEN)

```typescript
// ❌ CRITICAL VIOLATIONS: Hardcoded hostnames, unmanaged CORS, and un-typed environments
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class BrokenApiService {
  constructor(private http: HttpClient) {}

  // FORBIDDEN: Raw localhost URL creates immediate CORS errors in dev and breaks in production!
  getUsers() {
    return this.http.get('http://localhost:3000/api/users');
  }

  // FORBIDDEN: Hardcoded production domain bypasses dev proxy and leaks environment secrets!
  getOrders() {
    return this.http.get('https://api.staging.internal-corp.com/orders');
  }
}
```
