---
name: nestjs-maintenance-audit
description: "Audits existing NestJS backend repositories for architectural anti-patterns, circular dependencies, memory leaks, unvalidated inputs, missing error handling, and performance bottlenecks."
---
# Goal
Execute a comprehensive technical audit of a NestJS backend codebase to detect tech debt, security vulnerabilities, circular module dependencies, memory leaks, missing DTO validations, and architectural anti-patterns, providing actionable remediation steps for long-term code health.

# Instructions
1. **Module & Circular Dependency Audit**:
   - Inspect module imports across `app.module.ts` and feature modules.
   - Scan for explicit `forwardRef()` usages, which indicate tight coupling or invalid domain boundaries.
   - Recommend extracting shared entities into a separate sub-module or using domain events (`@nestjs/event-emitter`) to decouple cyclic relationships.
2. **Type Safety & Payload Validation Audit**:
   - Verify that `main.ts` configures global `ValidationPipe` with `whitelist: true` and `forbidNonWhitelisted: true`.
   - Grep for `any`, `Record<string, any>`, or direct `@Req()` / `@Res()` access without type interfaces in controllers.
   - Audit all DTO classes to ensure every property has a `class-validator` decorator.
3. **Error Handling & Resiliency Audit**:
   - Verify existence of a global `@Catch()` exception filter intercepting unhandled rejections and standardizing API error responses.
   - Check if database errors (e.g. Prisma `P2002`, TypeORM `QueryFailedError`) are translated to appropriate HTTP status codes (e.g. 409 Conflict, 400 Bad Request).
   - Audit `main.ts` shutdown hooks (`app.enableShutdownHooks()`) for graceful container termination in K8s / Docker environments.
4. **Database & Resource Management Audit**:
   - Audit database access patterns in service classes for N+1 query problems.
   - Check ORM connection pooling and transaction lifecycle handling. Ensure connections are closed or released in `onModuleDestroy()`.
   - Scan for unhandled RxJS subscriptions or un-closed event listeners causing memory leaks.
5. **Configuration & Security Audit**:
   - Confirm `ConfigModule` validates schema using `Joi` or `Zod` on startup.
   - Verify implementation of security middleware (`helmet`, `cors` rate limiting with `@nestjs/throttler`).
   - Ensure secrets, API keys, and database URIs are never hardcoded in repository files.

# Examples
Input: Run maintenance audit on legacy NestJS repository.
Output Audit Findings Report:
```markdown
# NestJS Maintainability Audit Findings

## Critical Issues
1. **Unvalidated DTO Payload**: `OrderController` accepts untyped `@Body() payload: any` without `ValidationPipe` enforcement.
2. **Circular Dependency**: `UserModule` <-> `AuthModule` using `forwardRef()`. Refactor authentication lookup to `AuthService`.
3. **Missing Shutdown Hooks**: `main.ts` lacks `app.enableShutdownHooks()`, leading to dangling database pool connections during deployment restarts.

## Remediation Plan
- Add `ValidationPipe` globally in `main.ts`.
- Refactor `forwardRef()` by creating a shared `UserAuthModule`.
- Enable shutdown hooks in `main.ts`.
```

# Constraints
- Do NOT auto-delete code without validating test suite coverage.
- Do NOT replace standard HTTP exceptions with generic internal server errors (500).
- Always verify NestJS framework version compatibility before introducing new core decorators or modules.
