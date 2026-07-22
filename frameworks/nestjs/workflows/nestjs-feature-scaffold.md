---
description: "Sequential workflow for scaffolding a production-ready NestJS feature module with Clean Architecture, DTOs, Guards, Services, Repositories, and Unit Tests."
trigger: manual
---
# NestJS Feature Module Scaffolding Workflow

## Objective
Scaffold a fully compliant, production-ready NestJS feature module adhering to enterprise Clean Architecture, type safety, DTO validation, custom exceptions, OpenAPI documentation, and isolated unit test specifications.

## Prerequisites
- Working NestJS v10+ project environment.
- Required packages installed: `@nestjs/common`, `@nestjs/core`, `class-validator`, `class-transformer`, `@nestjs/swagger`.

## Execution Steps
1. **Domain & Boundaries Definition**:
   - Analyze the feature requirements and identify domain entities, state mutations, and external dependencies.
   - Create feature directory structure:
     `src/modules/[feature-name]/{controllers,services,repositories,dto,entities,interfaces,spec}`.

2. **DTO & Schema Creation**:
   - Create `dto/create-[feature].dto.ts` and `dto/update-[feature].dto.ts`.
   - Add strict `class-validator` decorators (`@IsString()`, `@IsNumber()`, `@IsUUID()`, `@ValidateNested()`) and `@ApiProperty()` annotations.

3. **Repository Abstraction Layer**:
   - Define interface `interfaces/[feature]-repository.interface.ts` with explicit async method signatures.
   - Implement database repository `repositories/[feature]-[orm].repository.ts` implementing the interface.

4. **Business Service Implementation**:
   - Create `services/[feature].service.ts` annotated with `@Injectable()`.
   - Inject repository via provider symbol.
   - Implement business logic, standardizing error handling via NestJS exceptions (`NotFoundException`, `ConflictException`).

5. **Controller Layer & Security Rules**:
   - Create `controllers/[feature].controller.ts`.
   - Apply routing decorators, OpenAPI annotations (`@ApiTags()`, `@ApiResponse()`), and security guards (`@UseGuards(JwtAuthGuard)`).

6. **Module Wiring & DI Registration**:
   - Create `[feature].module.ts`.
   - Register controllers and providers with interface token binding. Export service if needed by external modules.
   - Register `[Feature]Module` into `app.module.ts`.

7. **Automated Verification**:
   - Scaffold `spec/[feature].service.spec.ts` using `@nestjs/testing`.
   - Execute test suite via `npm run test` or `jest` to ensure 100% build and spec passage.

## Expected Output
- Complete feature module directory with clean component separation.
- Zero TypeScript compiler errors (`tsc --noEmit`).
- Passing unit test suite for service and controller classes.
