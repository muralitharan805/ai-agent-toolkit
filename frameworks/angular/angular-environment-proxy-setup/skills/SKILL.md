---
name: angular-environment-proxy-setup
description: "Protocols and blueprints for configuring production-ready Angular multi-environment separation, local reverse proxies, CORS elimination, and deterministic build wiring. Activate when establishing environment files, dev proxies, or auditing hardcoded URLs."
compatibility: "Requires Angular 19+ and Node.js 20+"
---

# Angular Environment & Proxy Setup Skill (`angular-environment-proxy-setup`)

## Persona & Architectural Mandate
Act as a Principal Frontend Architect specializing in secure, enterprise-grade Angular (v19+) application infrastructure. Your mandate is to enforce strict zero-hardcoding standards for API URLs, ensure seamless local reverse proxy routing that eliminates Cross-Origin Resource Sharing (CORS) friction, configure typed multi-environment separation, and establish deterministic build-time file replacements.

---

## 5-Pillar Directory Map

```text
frameworks/angular/skills/angular-environment-proxy-setup/
├── SKILL.md                                        # Tier 2 Core Protocol (< 500 lines)
├── references/
│   ├── proxy-configuration-and-cors.md             # Reverse proxy, CORS, and WebSocket guide
│   └── multi-environment-build-wiring.md           # angular.json fileReplacements & serve config
├── scripts/
│   └── audit_angular_environment.py                # Standalone CLI validation tool (PEP 723)
├── assets/
│   ├── environment.ts                              # Dev environment with relative /api path
│   ├── environment.prod.ts                         # Production environment template
│   ├── proxy.dev.json                              # Local dev proxy with path rewriting
│   └── proxy.staging.json                          # Staging proxy with remote TLS target
└── evals/
    ├── evals.json                                  # Empirical verification test suite
    └── grading.json                                # Quality benchmark scorecard (100%)
```

---

## Authoritative Reference Grounding & Bundled Assets
Consult the specialized guides and assets bundled directly inside this skill:
- **Proxy Configuration & CORS Guide**: [references/proxy-configuration-and-cors.md](references/proxy-configuration-and-cors.md)
- **Multi-Environment Build Wiring**: [references/multi-environment-build-wiring.md](references/multi-environment-build-wiring.md)
- **Development Environment Asset**: [assets/environment.ts](assets/environment.ts)
- **Production Environment Asset**: [assets/environment.prod.ts](assets/environment.prod.ts)
- **Development Proxy Asset**: [assets/proxy.dev.json](assets/proxy.dev.json)
- **Staging Proxy Asset**: [assets/proxy.staging.json](assets/proxy.staging.json)
- **Automated Environment Audit CLI Tool**: `python3 scripts/audit_angular_environment.py <path>`
- **Empirical Test Suite**: [evals/evals.json](evals/evals.json)

---

## 1. Architectural Strategy: Relative Dev Path vs. Absolute Prod Gateway

| Environment | Endpoint Strategy | `environment.apiUrl` | Routing Mechanism |
| :--- | :--- | :--- | :--- |
| **Local Development** | Relative Root Path | `'/api'` | Forwarded by dev server (`proxy.dev.json`) to `http://localhost:3000` without browser CORS. |
| **Local Staging** | Relative Root Path | `'/api'` | Forwarded by dev server (`proxy.staging.json`) to `https://staging-api.yourdomain.com`. |
| **Production Build** | Fully Qualified URL | `'https://api.yourdomain.com/v1'` | Direct HTTPS browser call to CDN / API Gateway with production CORS headers. |

---

## 2. Step-by-Step Implementation Protocol

### Step 1: Deploy Typed Environment Files
Deploy [assets/environment.ts](assets/environment.ts) and [assets/environment.prod.ts](assets/environment.prod.ts) under `src/environments/`:

```typescript
// src/environments/environment.ts (Development)
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
// src/environments/environment.prod.ts (Production)
import { EnvironmentConfig } from './environment';

export const environment: EnvironmentConfig = {
  production: true,
  apiUrl: 'https://api.yourdomain.com/v1',
  wsUrl: 'wss://api.yourdomain.com/socket.io',
  appName: 'Enterprise Application'
};
```

### Step 2: Deploy Reverse Proxy Configurations
Deploy [assets/proxy.dev.json](assets/proxy.dev.json) and [assets/proxy.staging.json](assets/proxy.staging.json) to the repository root:

```json
// proxy.dev.json
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

### Step 3: Configure `angular.json` Build & Serve Targets
Wire file replacements and proxy configs in `angular.json`:

1. **Build Configuration (`fileReplacements`)**:
```json
"configurations": {
  "production": {
    "fileReplacements": [
      {
        "replace": "src/environments/environment.ts",
        "with": "src/environments/environment.prod.ts"
      }
    ]
  }
}
```

2. **Serve Configuration (`proxyConfig`)**:
```json
"configurations": {
  "development": {
    "buildTarget": "my-app:build:development",
    "proxyConfig": "proxy.dev.json"
  },
  "staging": {
    "buildTarget": "my-app:build:development",
    "proxyConfig": "proxy.staging.json"
  }
}
```

### Step 4: Configure `package.json` NPM Scripts
```json
"scripts": {
  "start:dev": "ng serve --configuration=development --proxy-config proxy.dev.json",
  "start:staging": "ng serve --configuration=development --proxy-config proxy.staging.json",
  "build:dev": "ng build --configuration=development",
  "build:prod": "ng build --configuration=production"
}
```

### Step 5: Consume Environment Symbol in Core Services
Always import from base `src/environments/environment`, never importing `.prod` directly:

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class UserApiService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/users`;

  getUsers(): Observable<unknown[]> {
    return this.http.get<unknown[]>(this.endpoint);
  }
}
```

---

## 3. Automated Environment & Hardcoded URL Audit Tool
Scan an entire Angular repository for raw hardcoded URLs (`http://localhost`, raw IPs) and verify configuration files:

```bash
# Standard console audit:
python3 frameworks/angular/skills/angular-environment-proxy-setup/scripts/audit_angular_environment.py src/app

# Machine-readable JSON output:
python3 frameworks/angular/skills/angular-environment-proxy-setup/scripts/audit_angular_environment.py src/app --json

# Strict mode for CI pipelines:
python3 frameworks/angular/skills/angular-environment-proxy-setup/scripts/audit_angular_environment.py src/app --strict
```

---

## Gotchas & Anti-Patterns

| Anti-Pattern / Mistake | Root Cause & Failure Mode | Modern Recommended Replacement |
| :--- | :--- | :--- |
| **Hardcoding `http://localhost:3000`** | Triggers browser CORS preflight failures; breaks immediately when deployed to cloud. | **Relative `apiUrl: '/api'`** routed via `proxy.dev.json`. |
| **Direct Import of `environment.prod`** | Bypasses Angular CLI build-time file replacements, hardcoding prod settings into dev. | **Always import base `src/environments/environment`**. |
| **Missing `changeOrigin: true`** | Backend virtual hosts or reverse proxies reject requests because the HTTP `Host` header remains `localhost:4200`. | **Always set `"changeOrigin": true`** in proxy configurations. |
| **Missing `secure: false` in Dev** | Dev server fails to proxy to HTTPS endpoints with self-signed certificates. | **Set `"secure": false`** in `proxy.dev.json` for local backend development. |
| **Dropping WebSocket Connections** | Socket.io or NestJS WebSocket gateways disconnect or fall back to slow HTTP long-polling. | **Include `"ws": true`** on the WebSocket proxy route entry. |
| **Path Rewriting Collision** | `pathRewrite: { "^/api": "" }` accidentally strips valid URL segments if backend routes expect `/api`. | **Verify backend route prefixes** before configuring `pathRewrite`. |
