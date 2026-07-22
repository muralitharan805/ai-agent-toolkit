---
name: nestjs-module-authoring
description: "Guides the creation of scalable, maintainable NestJS feature modules adhering to Clean Architecture, robust DTO validation, dependency injection, and comprehensive unit testing."
---
# Goal
Standardize the construction of production-ready NestJS feature modules to guarantee long-term maintainability, isolation, microservices compatibility, and high unit test coverage.

# Instructions
1. **Module Architecture Planning**:
   - Define domain boundaries for the feature. Create a directory layout under `src/modules/[feature-name]/` containing `dto/`, `entities/` (or `domain/`), `interfaces/`, `controllers/`, `services/`, `repositories/`, and `spec/`.
2. **DTO & Schema Definition**:
   - Create explicit DTOs for request payloads (`create-[feature].dto.ts`, `update-[feature].dto.ts`, `query-[feature].dto.ts`).
   - Annotate all DTO properties with `class-validator` rules (`@IsString()`, `@IsOptional()`, `@Nested()`, etc.) and OpenAPI Swagger metadata (`@ApiProperty()`).
3. **Repository Abstraction & Persistence Layer**:
   - Define a domain repository interface `I[Feature]Repository` in `interfaces/`.
   - Implement the concrete ORM repository (Prisma, TypeORM, or Mongoose) in `repositories/`.
   - Bind the interface token in the feature module using `providers: [{ provide: FEATURE_REPOSITORY, useClass: FeatureOrmRepository }]`.
4. **Service Layer Implementation**:
   - Implement `@Injectable()` business service methods containing domain validation, transaction boundaries, and event dispatching.
   - Throw NestJS standard exceptions (`NotFoundException`, `ConflictException`, `BadRequestException`) for domain failures.
   - Maintain pure return types (`Promise<FeatureEntity>`) to ensure caller predictability.
5. **Controller Layer Implementation**:
   - Decorate class with `@Controller('[feature-name]')` and `@ApiTags('[feature-name]')`.
   - Use standard NestJS decorators (`@Get()`, `@Post()`, `@Put()`, `@Delete()`, `@Body()`, `@Param()`, `@Query()`).
   - Enforce authentication/authorization using `@UseGuards(JwtAuthGuard, RolesGuard)`.
6. **Module Configuration & Export**:
   - Declare controllers, providers, and exported services in `[feature].module.ts`.
   - Re-export services needed by external modules to prevent duplicate provider instantiations.
7. **Unit & Integration Test Setup**:
   - Scaffold unit tests (`.spec.ts`) using `@nestjs/testing` `Test.createTestingModule()`.
   - Mock repository dependencies using `jest.fn()` or dedicated mock classes to isolate unit tests from live databases.

# Examples
Input: Scaffold a NestJS `ProductModule` with catalog management and inventory checks.
Output:
```typescript
// src/modules/product/interfaces/product-repository.interface.ts
export const PRODUCT_REPOSITORY = Symbol('PRODUCT_REPOSITORY');

export interface IProductRepository {
  findById(id: string): Promise<ProductEntity | null>;
  create(data: CreateProductDomainInput): Promise<ProductEntity>;
  updateStock(id: string, delta: number): Promise<ProductEntity>;
}

// src/modules/product/product.module.ts
import { Module } from '@nestjs/common';
import { ProductController } from './product.controller';
import { ProductService } from './product.service';
import { ProductPrismaRepository } from './repositories/product-prisma.repository';
import { PRODUCT_REPOSITORY } from './interfaces/product-repository.interface';

@Module({
  controllers: [ProductController],
  providers: [
    ProductService,
    {
      provide: PRODUCT_REPOSITORY,
      useClass: ProductPrismaRepository,
    },
  ],
  exports: [ProductService],
})
export class ProductModule {}
```

# Constraints
- Do NOT import database ORM entities across module boundaries; expose domain entities or interfaces instead.
- Do NOT use global mutable variables inside NestJS services to prevent race conditions in multi-threaded runtime environments.
- Always use `@Injectable()` scope `DEFAULT` (singleton) unless request-scoped processing is explicitly required for multi-tenant isolation.
