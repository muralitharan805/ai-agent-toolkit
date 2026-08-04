---
description: Enforces strict environment separation and proxy usage in Angular projects to prevent hardcoded API URLs.
trigger: always_on
---

# Angular Environment & Proxy Rule

## Description
This rule strictly forbids hardcoding backend API URLs inside Angular components or services and enforces the use of environment variables and proxy configurations for network requests.

## Constraints
- **NO HARDCODED URLS**: Do not write raw URLs like `http://localhost:3000` or `https://api.domain.com` inside `.ts` files, HTTP clients, or services.
- **MANDATORY ENVIRONMENT USAGE**: All API endpoints MUST be referenced using `environment.apiUrl` (or equivalent) imported from `src/environments/environment`.
- **RELATIVE PATHS IN DEV**: For local development, `environment.apiUrl` MUST be a relative path (e.g., `/api`) that resolves via a local proxy (like `proxy.dev.json` or `proxy.conf.json`) to bypass CORS errors.
- **SEPARATE PROXY CONFIGS**: Maintain distinct proxy files for different target environments (e.g., `proxy.dev.json` for local backend, `proxy.staging.json` for cloud dev/staging).
- **ANGULAR.JSON WIRING**: Ensure that `angular.json` is correctly wired to map file replacements for production and proxy configs for serve environments.
- **NPM SCRIPTS**: Rely on dedicated NPM scripts (e.g., `start:dev`, `start:staging`) that explicitly pass the `--configuration` and `--proxy-config` arguments.
