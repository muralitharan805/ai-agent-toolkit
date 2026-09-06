# Clean Architecture & Module Boundary Patterns in NestJS

This reference documents architectural guidelines for isolating domain logic from infrastructure adapters when constructing NestJS feature modules.

---

## 1. Clean Architecture Layering

Enterprise NestJS applications must enforce strict separation between architectural rings:

```text
src/features/[feature-name]/
├── controllers/                  # Presentation Layer (HTTP routing, validation pipe, auth guards)
├── services/                     # Application/Domain Layer (Business rules, workflows, transactions)
├── interfaces/                   # Contracts (Repository interfaces, domain entity definitions)
├── repositories/                 # Infrastructure/Persistence Layer (Prisma, TypeORM adapters)
├── dto/                          # Data Transfer Objects (class-validator & OpenAPI decorators)
└── spec/                         # Automated Unit & Integration Test Specifications
```

### Prohibited Cross-Layer Leaks
- **Controllers MUST NOT** call database ORM models (`prisma.user.findMany()`) directly.
- **Services MUST NOT** depend on HTTP Request or Response objects (`@Req() req: Request`).
- **External Modules MUST NOT** import concrete repository classes directly; they must interact via exported domain services.

---

## 2. Dependency Inversion via Injection Tokens

By relying on abstract interfaces rather than concrete ORM classes, domain services remain 100% testable and decoupled from database technologies:

### 1. Interface & Symbol Token Definition (`interfaces/[feature]-repository.interface.ts`):
```typescript
export const PRODUCT_REPOSITORY = Symbol('PRODUCT_REPOSITORY');

export interface IProductRepository {
  findById(id: string): Promise<ProductEntity | null>;
  create(data: CreateProductInput): Promise<ProductEntity>;
}
```

### 2. Service Constructor Injection:
```typescript
@Injectable()
export class ProductService {
  constructor(
    @Inject(PRODUCT_REPOSITORY)
    private readonly productRepo: IProductRepository,
  ) {}
}
```

### 3. Module Provider Binding (`[feature].module.ts`):
```typescript
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

---

## 3. Transaction Management & Domain Events

When multiple repository operations must execute atomically:
1. Inject the database transaction coordinator (e.g. `PrismaService.$transaction`).
2. Alternatively, dispatch asynchronous side-effects using `@nestjs/event-emitter` after the primary database transaction commits, ensuring event listeners do not roll back the primary write operation.
