---
name: nestjs-module-authoring
description: "Scaffolds enterprise NestJS domain feature modules adhering to Clean Architecture: DTO validation, abstract repository DI, OpenAPI, and unit test isolation."
---

# NestJS Feature Module Authoring Skill

## 1. Overview & 5-Pillar Architecture

This skill provides an enterprise standard for constructing production-ready NestJS domain feature modules adhering to Clean Architecture principles. It enforces strict separation of concerns, request payload validation via `class-validator`, dependency inversion using abstract repository interfaces and Symbol tokens, automated OpenAPI Swagger contracts, and isolated unit testing.

```text
frameworks/nestjs/skills/nestjs-module-authoring/
├── SKILL.md                          # Core procedural instruction (< 500 lines) + Gotchas
├── references/                       # Authoritative architectural runbooks
│   ├── clean-architecture-module-patterns.md # Layer boundaries and repository tokens
│   └── dto-validation-and-openapi.md # class-validator rules and Swagger inheritance
├── scripts/                          # Automated scaffolding & compliance CLI
│   └── scaffold_nestjs_module.py     # Standalone PEP 723 generator and auditor
├── assets/                           # Production-ready drop-in templates
│   ├── feature.controller.ts         # Clean controller router with Swagger decorators
│   ├── feature.service.ts            # Domain business service with exception handling
│   ├── feature-repository.interface.ts # Abstract repository contract & Symbol token
│   ├── feature-prisma.repository.ts  # Concrete Prisma repository adapter
│   ├── create-feature.dto.ts         # Input contract with class-validator
│   ├── update-feature.dto.ts         # Update contract inheriting PartialType
│   ├── feature.module.ts             # Module wiring with custom provider binding
│   └── feature.service.spec.ts       # Isolated unit test specification with mocks
└── evals/                            # Quality verification test suite
    ├── evals.json                    # Automated assertions and evaluation cases
    └── grading.json                  # Net skill lift and benchmark metrics
```

---

## 2. 7-Step Feature Module Scaffolding Protocol

When generating a new domain feature module, execute the following 7 steps in sequence:

### Step 1: Directory Layout & Domain Boundaries
Create the domain feature folder layout under `src/features/[feature-name]/`:
```bash
mkdir -p src/features/[feature-name]/{dto,entities,interfaces,repositories,spec}
```

### Step 2: Request Payload DTOs & Swagger Annotations
1. Create `dto/create-[feature].dto.ts` with `class-validator` rules (`@IsString()`, `@IsNotEmpty()`, `@MaxLength()`) and `@ApiProperty()`.
2. Create `dto/update-[feature].dto.ts` extending `PartialType(Create[Feature]Dto)` from `@nestjs/swagger`.

### Step 3: Abstract Repository Interface & Symbol Token
Define domain interfaces and the injection token in `interfaces/[feature]-repository.interface.ts`:
```typescript
export const FEATURE_REPOSITORY = Symbol('FEATURE_REPOSITORY');

export interface IFeatureRepository {
  findById(id: string): Promise<FeatureEntity | null>;
  findAll(skip: number, limit: number): Promise<[FeatureEntity[], number]>;
  create(data: CreateFeatureInput): Promise<FeatureEntity>;
  update(id: string, data: UpdateFeatureInput): Promise<FeatureEntity>;
  delete(id: string): Promise<void>;
}
```

### Step 4: Concrete Database Repository Adapter
Implement the concrete ORM adapter in `repositories/[feature]-prisma.repository.ts` implementing `IFeatureRepository`.

### Step 5: Domain Service & Business Logic
Create `[feature].service.ts` injecting the repository token:
```typescript
@Injectable()
export class FeatureService {
  constructor(
    @Inject(FEATURE_REPOSITORY)
    private readonly featureRepo: IFeatureRepository,
  ) {}
}
```
Throw standard NestJS exceptions (`NotFoundException`, `ConflictException`, `BadRequestException`) for business rule failures.

### Step 6: HTTP Controller & Routing
Create `[feature].controller.ts` decorated with `@ApiTags('[Feature]')`, `@ApiBearerAuth()`, and `@Controller('[feature]')`. Ensure controllers only delegate to services without business logic or direct database queries.

### Step 7: Module Wiring & DI Registration
In `[feature].module.ts`, bind the repository interface token:
```typescript
@Module({
  controllers: [FeatureController],
  providers: [
    FeatureService,
    {
      provide: FEATURE_REPOSITORY,
      useClass: FeaturePrismaRepository,
    },
  ],
  exports: [FeatureService, FEATURE_REPOSITORY],
})
export class FeatureModule {}
```
Register `[Feature]Module` in `app.module.ts`.

---

## 3. Core Clean Architecture Patterns

### Dependency Inversion Principle (DIP)
- Domain services MUST depend on the abstract repository interface `IFeatureRepository`, NEVER on the concrete ORM adapter (`PrismaService` or `FeaturePrismaRepository`).
- Swapping the database layer (e.g. from Prisma to TypeORM or an in-memory test double) requires zero modifications to service logic.

### Controller Decoupling
- Controllers act purely as protocol adapters. They extract HTTP parameters, invoke domain services, and return responses.
- Controllers MUST NEVER execute raw database queries or direct transaction blocks.

---

## 4. Automated Verification & Scaffolding CLI

Use the bundled CLI tool to audit or scaffold feature modules:
```bash
# Audit an existing module for Clean Architecture compliance
python3 frameworks/nestjs/skills/nestjs-module-authoring/scripts/scaffold_nestjs_module.py --audit src/features/users

# Output machine-readable JSON
python3 frameworks/nestjs/skills/nestjs-module-authoring/scripts/scaffold_nestjs_module.py --audit src/features/users --json

# Run in strict mode for CI/CD pipelines
python3 frameworks/nestjs/skills/nestjs-module-authoring/scripts/scaffold_nestjs_module.py --audit src/features/users --strict
```

---

## 5. Gotchas & Anti-Patterns

| Category | Deprecated / Broken Pattern (❌) | Modern Production Replacement (✅) |
|---|---|---|
| **ORM Coupling** | Injecting PrismaService directly into controllers | Inject domain services; controllers never touch the ORM |
| **Direct Class Injection** | Injecting concrete `FeaturePrismaRepository` in service | Inject abstract interface via `@Inject(FEATURE_REPOSITORY)` |
| **DTO Duplication** | Manually duplicating fields in `UpdateFeatureDto` | Inherit validated fields using `PartialType(CreateFeatureDto)` |
| **Untyped Payloads** | Using `@Body() body: any` in controllers | Validate all request payloads with explicit `class-validator` DTOs |
| **Cross-Module Leak** | Importing ORM entities directly across module boundaries | Export domain interfaces or DTOs from the host module |
| **Unit Test Isolation** | Running unit tests against live database connections | Mock `IFeatureRepository` methods using `jest.fn()` |
| **Type Safety** | Using explicit `any` in service return signatures | Explicitly declare `Promise<FeatureEntity>` or `Promise<void>` |
