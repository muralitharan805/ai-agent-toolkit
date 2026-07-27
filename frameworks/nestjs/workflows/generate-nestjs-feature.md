---
description: "Sequential workflow to scaffold a production-ready NestJS feature module with Clean Architecture, DTOs, Guards, Services, Repositories, and Unit Tests. Triggered by 'nestjs-feature:', 'generate-nestjs-feature:', or '/generate-nestjs-feature'."
trigger: manual
---

# Generate NestJS Feature Module Workflow

## Objective
Scaffold a fully compliant, production-ready NestJS domain feature module adhering to enterprise Clean Architecture, strict type safety, `class-validator` DTO validation, custom exceptions, OpenAPI documentation, and isolated unit test specifications.

## Execution Steps

### 1. Domain & Boundaries Definition
Analyze feature requirements and create feature directory structure:
`src/modules/[feature-name]/{controllers,services,repositories,dto,entities,interfaces,spec}`

### 2. DTO & Schema Creation
Create `dto/create-[feature].dto.ts` and `dto/update-[feature].dto.ts` with strict `class-validator` decorators (`@IsString()`, `@IsNumber()`, `@IsUUID()`, `@ValidateNested()`) and `@ApiProperty()` annotations.

### 3. Repository Abstraction Layer
Define interface `interfaces/[feature]-repository.interface.ts` with explicit async method signatures, and implement database repository `repositories/[feature]-[orm].repository.ts`.

### 4. Business Service Implementation
Create `services/[feature].service.ts` annotated with `@Injectable()`. Implement business logic, standardizing error handling via NestJS exceptions (`NotFoundException`, `ConflictException`, `BadRequestException`).

### 5. Controller Layer & Security Guards
Create `controllers/[feature].controller.ts`. Apply routing decorators, OpenAPI annotations (`@ApiTags()`, `@ApiResponse()`), and security guards (`@UseGuards(JwtAuthGuard)`).

### 6. Module Wiring & DI Registration
Create `[feature].module.ts`. Register controllers and providers with interface token binding. Register `[Feature]Module` into `app.module.ts`.

### 7. Automated Verification
Scaffold `spec/[feature].service.spec.ts` using `@nestjs/testing` and run tests (`pnpm test`).
