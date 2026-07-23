---
description: "Automated workflow to scaffold all 12 core enterprise infrastructure points in a NestJS backend project (Zod env validation, global exception filters, JWT Auth & RBAC, Swagger, Health checks, Prisma/Database layer). Triggered by 'scaffold-nestjs:', 'scaffold-backend:', or '/scaffold-enterprise-nestjs-project'."
trigger: manual
---
# Scaffold Enterprise NestJS Project Workflow

## Objective
Automate the step-by-step setup of the complete 12-point Enterprise NestJS Backend Specification in a new or existing NestJS application.

## Step-by-Step Execution Protocol

When triggered with "scaffold nestjs project", `scaffold-nestjs:`, or `/scaffold-enterprise-nestjs-project`, execute the following steps in sequence:

### Step 1: Directory Tree Setup
Execute directory scaffolding under `src/`:
```bash
mkdir -p src/core/config src/core/decorators src/core/dto src/core/filters src/core/guards src/core/interceptors src/core/logger
mkdir -p src/database src/health
mkdir -p src/features/auth/dto src/features/auth/strategies
mkdir -p src/features/users/dto src/features/users/entities
```

### Step 2: Install Mandatory Dependencies via `pnpm`
```bash
pnpm add @nestjs/config @nestjs/swagger @nestjs/terminus class-validator class-transformer zod helmet @nestjs/throttler
pnpm add @nestjs/jwt @nestjs/passport passport passport-jwt
pnpm add -D @types/passport-jwt @types/express
```

### Step 3: Implement Environment Config & Pagination DTO (Points 2, 14)
Create:
- `src/core/config/env.config.ts` (Zod schema validation).
- `src/core/dto/pagination-query.dto.ts` (Point 14: Default `page = 1`, `limit = 10`, `maxLimit = 100`).

### Step 4: Implement Global Exception Filter, Response Envelope & Logging (Points 3, 4, 13)
Create:
- `src/core/filters/http-exception.filter.ts` (Unified error response format).
- `src/core/interceptors/transform-response.interceptor.ts` (Point 13: Unified `{ success: true, statusCode, message, data, meta, timestamp, path }` envelope).
- `src/core/interceptors/logging.interceptor.ts` (Execution time & `x-correlation-id` logger).

### Step 5: Implement Global Core Module (Point 10)
Create `src/core/core.module.ts` as `@Global()` providing `GlobalHttpExceptionFilter` and `LoggingInterceptor`.

### Step 6: Implement Database ORM Layer & Seeder Architecture (Points 8, 16)
Create:
- `src/database/prisma.service.ts` with `onModuleInit` and `onModuleDestroy` connection hooks.
- `prisma/seed.ts` (Automated DB Seeder script populating initial roles, configuration, and dev mock data).
- Add `"db:migrate": "prisma migrate dev"` and `"db:seed": "ts-node prisma/seed.ts"` to `package.json`.

### Step 7: Implement Health Check Module (Point 9)
Create `src/health/health.controller.ts` utilizing `@nestjs/terminus` to monitor DB and system resources.

### Step 8: Implement Sample Domain Feature CRUD Reference Module (Point 15)
Scaffold reference `UsersModule` under `src/features/users/`:
- `src/features/users/dto/create-user.dto.ts` (With `class-validator` & `@ApiProperty()`).
- `src/features/users/dto/update-user.dto.ts` (`PartialType(CreateUserDto)`).
- `src/features/users/entities/user.entity.ts` (Domain model).
- `src/features/users/users.service.ts` (Paginated `findAll`, `findOne`, `create`, `update`, `remove`).
- `src/features/users/users.controller.ts` (REST endpoints with Swagger annotations).
- `src/features/users/users.module.ts`.

### Step 9: Configure Application Bootstrap, Shutdown Hooks & Swagger (Points 1, 6, 7, 18)
Update `src/main.ts` with Helmet, CORS, Global `ValidationPipe`, global `/api/v1` prefix, `app.enableShutdownHooks()`, and Swagger setup at `/api/docs`.

### Step 10: Generate Production README Documentation (Point 17)
Create/Update `README.md` at project root documenting:
- Tech Stack Matrix (NestJS, pnpm, Zod, Prisma, Swagger, Terminus).
- Environment Variables table (`NODE_ENV`, `PORT`, `DATABASE_URL`, `JWT_SECRET`).
- Migration & Seeder execution commands (`pnpm db:migrate`, `pnpm db:seed`).
- Swagger API Docs URL (`http://localhost:3000/api/docs`).

### Step 11: Scaffold Multi-Stage Dockerfile & CI/CD Pipeline (Points 19, 20)
Create:
- `Dockerfile` (Production multi-stage build using `node:20-alpine`, `pnpm`, non-root user).
- `.dockerignore` (`node_modules`, `dist`, `.env`).
- `.github/workflows/ci.yml` (GitHub Actions automated build & test quality gate).

### Step 12: Build & Type-Check Verification (Point 12)
Verify clean compilation using mandatory `pnpm`:
```bash
pnpm run build
```
Verify zero `any` types and that all 20 enterprise points compile without errors.
