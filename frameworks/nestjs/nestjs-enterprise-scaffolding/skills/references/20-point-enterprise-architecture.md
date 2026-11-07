# 20-Point Enterprise NestJS Backend Architecture Specification

This reference documents the definitive, battle-tested 20-point enterprise blueprint for scaffolding and maintaining production-grade NestJS backend applications.

---

## The 20 Enterprise Architecture Invariants

### 1. Standardized Directory Tree Layout
Applications must organize source files into clean bounded domains under `src/`:
- `src/core/`: Global singleton infrastructure (config, filters, guards, interceptors, logger).
- `src/database/`: Database connectivity, ORM lifecycle handlers, and migration hooks.
- `src/features/`: Domain feature modules (`auth`, `users`, `billing`) encapsulating domain logic.
- `src/health/`: System health, readiness, and liveness probes using `@nestjs/terminus`.

### 2. Main Bootstrap Hardening (`src/main.ts`)
The application entrypoint must enforce:
- Security headers via `helmet()`.
- Explicit CORS credentials and allowed origin boundaries.
- Global route prefix (e.g. `/api/v1`).
- Port resolution defaulting to `3000`.

### 3. Strict Payload Validation Pipeline
All incoming HTTP requests must pass through a global `ValidationPipe`:
```typescript
new ValidationPipe({
  whitelist: true,
  forbidNonWhitelisted: true,
  transform: true,
  transformOptions: { enableImplicitConversion: true },
})
```

### 4. Deterministic Environment Configuration (`env.config.ts`)
Environment variables must not be read directly from `process.env`. They must be parsed, validated, and coerced using a Zod schema at application bootstrap.

### 5. Standardized Global Exception Filter
All uncaught exceptions must be transformed into a predictable error envelope (`{ success: false, statusCode, path, timestamp, error }`), preventing raw database connection strings or stack traces from reaching clients.

### 6. Standardized Response Envelope Interceptor
All successful HTTP responses must be wrapped in a uniform envelope (`{ success: true, statusCode, message, data, meta?, timestamp, path }`).

### 7. Observability & Correlation ID Tracing
Every request lifecycle must propagate a unique `X-Correlation-ID` header and log execution latency in milliseconds (`[correlationId] GET /api/v1/users 200 - 18ms`).

### 8. Interactive OpenAPI Documentation
Interactive Swagger documentation must be generated at `/api/docs` using `@nestjs/swagger` with Bearer Auth security definitions.

### 9. Database Connection Lifecycle Hooks
The ORM service (`PrismaService`) must implement `OnModuleInit` and `OnModuleDestroy` to ensure database pools connect reliably on startup and drain cleanly on shutdown.

### 10. System Health & Readiness Probes
Endpoints under `/api/v1/health` must monitor database connectivity, memory heap thresholds, and disk storage using `@nestjs/terminus`.

### 11. Global Core Encapsulation (`CoreModule`)
Cross-cutting providers (`GlobalHttpExceptionFilter`, `TransformResponseInterceptor`, `LoggingInterceptor`) must be bound inside an `@Global()` `CoreModule`.

### 12. Mandatory `pnpm` Package Management
Package management must strictly use `pnpm` with Corepack engine pins to prevent phantom dependency leakage and lockfile mutations.

### 13. Controller Layer Decoupling
Controllers must act strictly as HTTP routers. Business logic, database queries, and third-party API calls must reside in domain services or repository abstractions.

### 14. Mandatory Collection GET Pagination
ALL list or collection endpoints must enforce pagination using `PaginationQueryDto` (`page = 1`, `limit = 10`, `maxLimit = 100`). Unbounded `SELECT *` queries are strictly forbidden.

### 15. Complete Reference CRUD Domain Module
Scaffolding must generate a fully functional reference feature (`UsersModule`) implementing DTO validation, Swagger annotations, pagination, and service unit tests.

### 16. Declarative Database Migrations & Automated Seeder
Database changes must strictly run through version-controlled migrations (`pnpm db:migrate`). Projects must provide an idempotent seeding script (`prisma/seed.ts`).

### 17. Automated Production README Documentation
Every project must contain a complete `README.md` documenting environment variables, quick-start commands, database workflows, and Swagger endpoints.

### 18. Graceful Container Termination Hooks
Bootstrap must call `app.enableShutdownHooks()` to allow container orchestrators (Kubernetes / Docker) to terminate pods without dropping active HTTP traffic.

### 19. Production Multi-Stage Containerization
Projects must provide a BuildKit-optimized multi-stage `Dockerfile` executing as a non-root `node` user with production-only dependencies.

### 20. Automated CI/CD Quality Pipeline
A GitHub Actions workflow (`.github/workflows/ci.yml`) must enforce automated dependency installation, TypeScript compilation, and test suite execution on every PR.
