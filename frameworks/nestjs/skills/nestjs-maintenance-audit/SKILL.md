---
name: nestjs-maintenance-audit
description: "Audits and refactors NestJS backend codebases for circular dependencies, memory leaks, unvalidated inputs, missing shutdown hooks, and architectural anti-patterns."
---

# NestJS Codebase Maintenance & Architectural Audit

Audits and refactors existing NestJS backend codebases to detect and eliminate technical debt, circular module references (`forwardRef`), memory leaks, unvalidated payloads, missing graceful shutdown hooks, and architectural anti-patterns.

---

## 5-Pillar Architecture Directory Layout

```text
frameworks/nestjs/skills/nestjs-maintenance-audit/
├── SKILL.md                                                # Core procedural audit instructions (< 500 lines)
├── references/                                             # Authoritative deep-dive runbooks
│   ├── circular-dependencies-and-module-refactoring.md     # Decoupling cycles with events and shared modules
│   └── memory-leaks-and-lifecycle-cleanup.md              # Lifecycle hooks, connection pools, and shutdown
├── scripts/                                                # Standalone automation tools
│   └── audit_nestjs_codebase.py                           # CLI health and compliance scanner
├── assets/                                                 # Reusable reporting assets
│   ├── audit-report-template.md                           # Standardized findings markdown report
│   └── remediation-checklist.json                         # 10-point automated inspection schema
└── evals/                                                  # Verifiable test cases and grading
    ├── evals.json
    └── grading.json
```

---

## Procedural Audit & Refactoring Phases

Follow this 6-phase sequence to audit and remediate a NestJS repository:

### Phase 1: Automated Health Scan
Run the bundled CLI audit tool to inspect the codebase for immediate violations:
```bash
python3 scripts/audit_nestjs_codebase.py --target-dir . --strict
```
For machine-readable output in CI/CD pipelines:
```bash
python3 scripts/audit_nestjs_codebase.py --target-dir . --json
```

### Phase 2: Topology & Circular Dependency Remediation
1. Scan for bidirectional module imports and `forwardRef()` usages:
   ```bash
   grep -rn "forwardRef" src/
   ```
2. If `forwardRef()` connects modules:
   - **Data retrieval cycle**: Extract shared entities or lookup queries into a dedicated `SharedModule` (see `references/circular-dependencies-and-module-refactoring.md`).
   - **Cross-module notification**: Decouple using `@nestjs/event-emitter` (`this.eventEmitter.emit('event.name', payload)`).

### Phase 3: Request Validation & DTO Hardening
1. Inspect `src/main.ts` for global `ValidationPipe`:
   ```typescript
   app.useGlobalPipes(
     new ValidationPipe({
       whitelist: true,
       forbidNonWhitelisted: true,
       transform: true,
     }),
   );
   ```
2. Scan controllers for untyped `@Body()` payloads or `any` parameters. Replace with strongly-typed DTOs decorated with `class-validator` and `@ApiProperty()` annotations.

### Phase 4: Error Handling & Security Headers
1. Ensure `main.ts` registers Helmet security headers and CORS:
   ```typescript
   import helmet from 'helmet';
   app.use(helmet());
   app.enableCors({ origin: process.env.ALLOWED_ORIGINS?.split(',') });
   ```
2. Verify a global exception filter intercepts unhandled exceptions and standardizes API responses to `{ success: false, statusCode, message, timestamp, path }`.

### Phase 5: Resource Management & Graceful Shutdown
1. Verify `app.enableShutdownHooks()` is called in `main.ts`:
   ```typescript
   app.enableShutdownHooks();
   ```
2. Check database and cache service classes (Prisma, TypeORM, Redis) implement `OnModuleDestroy` to close connections cleanly (see `references/memory-leaks-and-lifecycle-cleanup.md`).
3. Audit long-lived services for unsubscribed RxJS observables or dangling interval timers.

### Phase 6: Build Verification & Remediation Report
1. Execute compile check and automated tests:
   ```bash
   pnpm build
   pnpm test
   ```
2. Document all findings, diffs, and verification steps using `assets/audit-report-template.md`.

---

## Gotchas & Architectural Pitfalls

| Legacy / Anti-Pattern | Modern Enterprise Replacement | Why It Matters |
|---|---|---|
| Relying on `forwardRef()` to bridge circular modules | Shared submodules or domain events (`@nestjs/event-emitter`) | `forwardRef()` breaks DI initialization determinism, leaks boundaries, and complicates isolated unit testing. |
| Missing `app.enableShutdownHooks()` in `main.ts` | Explicit `app.enableShutdownHooks()` before `app.listen()` | Kubernetes `SIGTERM` forcibly kills pods, leaving dangling Postgres connection pools and unfinished HTTP requests. |
| `@Body() payload: any` in controllers | Validated DTO classes with `class-validator` annotations | Allows injection of unvalidated properties and potential parameter tampering vulnerabilities. |
| Direct `process.env.VAR` in services | `ConfigService.getOrThrow<string>('VAR')` | Direct `process.env` bypasses startup schema validation, leading to runtime undefined crashes. |
| Raw `console.log()` for debug statements | Structured `Logger` or `Pino` logging service | Console logs leak sensitive PII, lack correlation IDs, and cannot be parsed by log aggregators. |
| Hanging Redis or Prisma client instances | Implementing `OnModuleDestroy` with `$disconnect()` or `quit()` | Prevents container graceful shutdown, exhausting database connection pools during autoscaling. |
