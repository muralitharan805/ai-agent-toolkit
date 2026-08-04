---
name: angular-environment-proxy-setup
description: Instructions for implementing production-ready environment separation and proxy setups in Angular applications.
---

# Angular Environment & Proxy Setup

This skill provides the standard operating procedure for configuring enterprise-grade environment separation and local dev proxies in Angular.

## 1. Environment Configurations

Always use environment files to manage API URLs and environment-specific flags. Never hardcode API domains in services or components.

### Development (`src/environments/environment.ts`)
```typescript
export const environment = {
  production: false,
  apiUrl: '/api' // Proxied locally to avoid CORS
};
```

### Production (`src/environments/environment.prod.ts`)
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://api.yourdomain.com/api/v1' // Actual production API
};
```

## 2. Proxy Setup (Local Development Server)

Create proxy configuration files at the root of the workspace to bypass CORS during local development.

### Dev Proxy (`proxy.dev.json`)
```json
{
  "/api": {
    "target": "http://localhost:3000",
    "secure": false,
    "changeOrigin": true,
    "pathRewrite": {
      "^/api": "/api/v1"
    }
  }
}
```

### Staging Proxy (`proxy.staging.json`)
```json
{
  "/api": {
    "target": "https://staging-api.yourdomain.com",
    "secure": true,
    "changeOrigin": true,
    "pathRewrite": {
      "^/api": "/api/v1"
    }
  }
}
```

## 3. Angular CLI Configuration (`angular.json`)

Wire the environments and proxies in `angular.json`:

1. **File Replacements (Build):** Under `architect.build.configurations.production`, ensure file replacements are configured:
```json
"fileReplacements": [
  {
    "replace": "src/environments/environment.ts",
    "with": "src/environments/environment.prod.ts"
  }
]
```

2. **Proxy Config (Serve):** Map the proxy configuration under `architect.serve.configurations`:
```json
"development": {
  "buildTarget": "your-app:build:development",
  "proxyConfig": "proxy.dev.json"
},
"staging": {
  "buildTarget": "your-app:build:development",
  "proxyConfig": "proxy.staging.json"
}
```

## 4. NPM Scripts (`package.json`)

Add standard scripts for consistent execution across team members and CI/CD pipelines:

```json
"scripts": {
  "start:dev": "ng serve --configuration=development --proxy-config proxy.dev.json",
  "start:staging": "ng serve --configuration=development --proxy-config proxy.staging.json",
  "build:dev": "ng build --configuration=development",
  "build:live": "ng build --configuration=production"
}
```
