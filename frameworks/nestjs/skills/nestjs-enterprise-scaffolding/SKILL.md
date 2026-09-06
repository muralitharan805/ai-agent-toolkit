---
name: nestjs-enterprise-scaffolding
description: "Scaffolds enterprise NestJS architecture adhering to the 20-Point Specification: Zod validation, global filters, response envelope, pagination, Prisma lifecycle, and Docker."
---

# NestJS Enterprise Scaffolding Skill

## 1. Overview & 5-Pillar Architecture

This skill provides the definitive blueprint for bootstrapping production-grade NestJS backend applications adhering to the **20-Point Enterprise Architecture Specification** (executed through a 12-step automated pipeline). It enforces clean architecture boundaries, Zod runtime environment parsing, uniform exception filtering, standardized response envelopes, mandatory collection pagination, Prisma connection lifecycle management, and non-root containerization.

```text
frameworks/nestjs/skills/nestjs-enterprise-scaffolding/
├── SKILL.md                          # Core procedural instruction (< 500 lines) + Gotchas
├── references/                       # Authoritative architectural runbooks
│   ├── 20-point-enterprise-architecture.md # Full specification of all 20 invariants
│   └── prisma-migrations-and-seeding.md # Database migrations, seeders, and lifecycle
├── scripts/                          # Automated compliance audit CLI
│   └── verify_nestjs_scaffolding.py  # Standalone PEP 723 compliance checker
├── assets/                           # Production-ready drop-in templates
│   ├── main.ts                       # Hardened bootstrap entry point
│   ├── env.config.ts                 # Zod schema environment validator
│   ├── pagination-query.dto.ts       # Standard collection pagination DTO
│   ├── http-exception.filter.ts      # Standardized exception filter
│   ├── transform-response.interceptor.ts # Standardized API response envelope
│   ├── logging.interceptor.ts        # Correlation ID and latency logger
│   ├── prisma.service.ts             # Lifecycle-managed Prisma client
│   ├── seed.ts                       # Idempotent database seeder
│   ├── Dockerfile                    # Multi-stage production containerfile
│   └── ci.yml                        # GitHub Actions CI quality workflow
└── evals/                            # Quality verification test suite
    ├── evals.json                    # Automated assertions and evaluation cases
    └── grading.json                  # Net skill lift and benchmark metrics
```

---

## 2. 12-Step Scaffolding Protocol

When bootstrapping or auditing an enterprise NestJS backend, execute the following 12 steps in sequence:

### Step 1: Directory Tree Scaffolding
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

### Step 3: Configure Environment & Pagination DTO
Copy `assets/env.config.ts` into `src/core/config/env.config.ts` and `assets/pagination-query.dto.ts` into `src/core/dto/pagination-query.dto.ts`.

### Step 4: Configure Global Filters, Response Envelope & Logging
Copy `assets/http-exception.filter.ts` into `src/core/filters/`, `assets/transform-response.interceptor.ts` into `src/core/interceptors/`, and `assets/logging.interceptor.ts` into `src/core/interceptors/`.

### Step 5: Encapsulate Global Core Module
Bind filters and interceptors inside an `@Global()` `CoreModule` (`src/core/core.module.ts`).

### Step 6: Configure Prisma Service & Database Seeder
1. Copy `assets/prisma.service.ts` into `src/database/prisma.service.ts`.
2. Copy `assets/seed.ts` into `prisma/seed.ts`.
3. Add seeding scripts to `package.json`:
   ```json
   {
     "scripts": {
       "db:migrate": "prisma migrate dev",
       "db:seed": "ts-node prisma/seed.ts"
     },
     "prisma": {
       "seed": "ts-node prisma/seed.ts"
     }
   }
   ```
4. Run initial declarative migration: `pnpm prisma migrate dev --name init`.

### Step 7: Configure Terminus Health Probes
Create `src/health/health.controller.ts` monitoring database connectivity and memory heaps via `@nestjs/terminus`.

### Step 8: Scaffold Reference Domain Feature (`UsersModule`)
Create full reference CRUD feature under `src/features/users/` (DTOs, entity, paginated `findAll`, `findOne`, `create`, `update`, `remove`).

### Step 9: Configure Main Bootstrap Entrypoint
Copy `assets/main.ts` into `src/main.ts`. Verify Helmet, CORS, global `/api/v1` prefix, `app.enableShutdownHooks()`, and Swagger setup at `/api/docs`.

### Step 10: Generate Production README Documentation
Create a root `README.md` documenting tech stack, environment variables, migration/seeder commands, and Swagger URLs.

### Step 11: Scaffold Multi-Stage Container & CI Pipeline
Copy `assets/Dockerfile` and `assets/ci.yml` into `.github/workflows/ci.yml`.

### Step 12: Verify Build & Clean Compilation
```bash
pnpm run build
pnpm test
```

---

## 3. Core Architecture Highlights

### Bootstrap Hardening (`src/main.ts`)
See `assets/main.ts`:
- Enables `app.enableShutdownHooks()` to gracefully terminate connections on container shutdown.
- Configures global `ValidationPipe` with `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`.
- Sets up interactive OpenAPI documentation at `/api/docs`.

### Response Envelope Interceptor
See `assets/transform-response.interceptor.ts`:
Wraps all controller responses in the uniform structure:
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Operation completed successfully",
  "data": [...],
  "meta": { "page": 1, "limit": 10, "total": 45 },
  "timestamp": "2026-09-06T21:00:00.000Z",
  "path": "/api/v1/users"
}
```

---

## 4. Automated Compliance Verification

Verify codebase compliance using the bundled audit CLI:
```bash
# Audit project src directory
python3 frameworks/nestjs/skills/nestjs-enterprise-scaffolding/scripts/verify_nestjs_scaffolding.py src

# Run in strict mode for CI/CD gates
python3 frameworks/nestjs/skills/nestjs-enterprise-scaffolding/scripts/verify_nestjs_scaffolding.py --strict

# Output machine-readable JSON
python3 frameworks/nestjs/skills/nestjs-enterprise-scaffolding/scripts/verify_nestjs_scaffolding.py --json
```

---

## 5. Gotchas & Anti-Patterns

| Category | Deprecated / Broken Pattern (❌) | Modern Production Replacement (✅) |
|---|---|---|
| **Shutdown Hooks** | Omitting `enableShutdownHooks()`, causing hung database pools | Invoke `app.enableShutdownHooks()` in `main.ts` |
| **Response Formats** | Returning unwrapped primitives or inconsistent controller objects | Use global `TransformResponseInterceptor` API envelope |
| **Pagination** | Unbounded `SELECT *` queries (`findAll()` returning raw arrays) | Mandate `PaginationQueryDto` with hard ceiling (`maxLimit: 100`) |
| **Environment Vars** | Direct unvalidated `process.env.VAR` access in services | Validate with Zod schema via `envSchema.safeParse()` |
| **Database Changes** | Direct manual SQL table modifications (`ALTER TABLE`) | Strictly version-controlled declarative migrations (`prisma migrate dev`) |
| **Container Security** | Single-stage Dockerfiles running as root user | Multi-stage BuildKit Dockerfile running as non-root `node` |
| **Package Manager** | Using `npm` or `yarn` (phantom dependencies, slow installs) | Mandate `pnpm` with Corepack engine definition |
| **Type Safety** | Using `any` in DTOs, controllers, or service method signatures | Strict interfaces with DTO validation and generic types |
