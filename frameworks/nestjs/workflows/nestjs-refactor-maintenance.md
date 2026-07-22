---
description: "End-to-end workflow to audit, refactor, and modernize NestJS backend codebases for long-term stability and maintainability."
trigger: manual
---
# NestJS Codebase Maintenance & Refactoring Workflow

## Objective
Audit an existing NestJS backend codebase, remove technical debt, resolve circular dependencies, harden request validation, standardize error logging, and optimize code for long-term maintainability.

## Prerequisites
- Accessible NestJS repository with build scripts configured (`npm run build`, `npm run test`).

## Execution Steps
1. **Repository Topology & Dependency Scan**:
   - Analyze module relationships across `src/`. Check for circular module references or excessive `forwardRef()` usages.
   - Run dependency check to identify deprecated or vulnerable npm packages.

2. **Validation & Exception Pipeline Hardening**:
   - Inspect `main.ts` for global `ValidationPipe` configuration (`whitelist: true`, `forbidNonWhitelisted: true`, `transform: true`).
   - Ensure global `HttpExceptionFilter` is bound to standardize output error payloads (`{ statusCode, message, timestamp, path }`).

3. **Controller & Service Layer Decoupling**:
   - Scan controllers for direct ORM model manipulation, inline business logic, or untyped `@Body()` payloads.
   - Extract business logic into injectable domain services and move database logic into repository abstractions.

4. **Configuration & Environment Validation**:
   - Verify environment configuration uses `ConfigModule` with schema validation (Joi or Zod).
   - Ensure database connection strings and JWT secrets are injected via `ConfigService` rather than `process.env` directly.

5. **Resource Management & Shutdown Hooks**:
   - Enable `app.enableShutdownHooks()` in `main.ts`.
   - Verify database connections, Redis clients, and background queues close cleanly in `onModuleDestroy()` handlers.

6. **Validation & CI Build Check**:
   - Run type checking: `npm run build` or `npx tsc --noEmit`.
   - Run test suite: `npm run test` and `npm run test:e2e`.

## Expected Output
- Refactored NestJS architecture free of circular dependencies and unvalidated payloads.
- Verified test suite and zero build errors.
- Clean maintainability report confirming long-term stability.
