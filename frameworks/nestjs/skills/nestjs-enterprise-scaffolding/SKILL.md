---
name: nestjs-enterprise-scaffolding
description: "Best practices, architecture specifications, directory structures, and code patterns for scaffolding enterprise NestJS backend applications."
---
# NestJS Enterprise Scaffolding Skill

## Goal
Guide developers and AI coding agents in bootstrapping production-grade NestJS backend applications adhering to the 20-Point Enterprise Scaffolding Architecture (executed via 12 automated pipeline steps).

## 20-Point Enterprise Architecture Blueprint

### 1. Directory Tree Structure (`src/`)
```
src/
├── core/                         # Global singleton services & cross-cutting layers
│   ├── config/                   # Zod environment validation schema
│   ├── decorators/               # Custom decorators (@Public, @CurrentUser, @Roles)
│   ├── filters/                  # Custom exception filters (HttpExceptionFilter)
│   ├── guards/                   # Security guards (JwtAuthGuard, RolesGuard)
│   ├── interceptors/             # Logging & correlation ID interceptors
│   ├── logger/                   # Structured Application Logger
│   └── core.module.ts            # @Global() Core Module
│
├── database/                     # ORM / Database layer
│   ├── prisma.service.ts         # Lifecycle-managed Prisma/ORM Service
│   └── database.module.ts
│
├── features/                     # Domain feature modules
│   ├── auth/                     # Authentication & Token domain
│   │   ├── dto/
│   │   ├── strategies/
│   │   ├── auth.controller.ts
│   │   ├── auth.service.ts
│   │   └── auth.module.ts
│   └── users/                    # User management domain
│       ├── dto/
│       ├── entities/
│       ├── users.controller.ts
│       ├── users.service.ts
│       └── users.module.ts
│
├── health/                       # Terminus health check module
│   ├── health.controller.ts
│   └── health.module.ts
│
├── app.module.ts                 # Root Application Module
└── main.ts                       # Application Bootstrap entry point
```

### 2. Main Bootstrap Configuration (`src/main.ts`)
```typescript
import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import helmet from 'helmet';
import { AppModule } from './app.module';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // Security Middleware
  app.use(helmet());
  app.enableCors({ origin: true, credentials: true });

  // Global Prefix
  app.setGlobalPrefix('api/v1');

  // Global Pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  // OpenAPI / Swagger Documentation
  const swaggerConfig = new DocumentBuilder()
    .setTitle('Enterprise NestJS API')
    .setDescription('Production Backend API Documentation')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env['PORT'] || 3000;
  await app.listen(port);
  logger.log(`🚀 Application running on http://localhost:${port}/api/v1`);
  logger.log(`📚 Swagger Docs available on http://localhost:${port}/api/docs`);
}
bootstrap();
```

### 3. Environment Config Validation (`src/core/config/env.config.ts`)
```typescript
import { z } from 'zod';

export const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(16),
  JWT_EXPIRES_IN: z.string().default('1d'),
});

export type EnvConfig = z.infer<typeof envSchema>;

export function validateEnv(config: Record<string, unknown>): EnvConfig {
  const result = envSchema.safeParse(config);
  if (!result.success) {
    throw new Error(`Config validation error: ${JSON.stringify(result.error.format())}`);
  }
  return result.data;
}
```

### 4. Standardized Global Exception Filter (`src/core/filters/http-exception.filter.ts`)
```typescript
import { ExceptionFilter, Catch, ArgumentsHost, HttpException, HttpStatus } from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class GlobalHttpExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.getResponse()
        : 'Internal server error';

    response.status(status).json({
      success: false,
      statusCode: status,
      path: request.url,
      timestamp: new Date().toISOString(),
      error: typeof message === 'object' ? message : { message },
    });
  }
}
```

### 5. Standardized Response Envelope Interceptor (`src/core/interceptors/transform-response.interceptor.ts`)
All successful HTTP responses MUST be wrapped in a uniform API Envelope structure using a global NestJS `CallHandler` / `NestInterceptor`:

```typescript
import { Injectable, NestInterceptor, ExecutionContext, CallHandler } from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Request, Response } from 'express';

export interface ApiResponseEnvelope<T> {
  success: boolean;
  statusCode: number;
  message: string;
  data: T;
  meta?: Record<string, unknown>;
  timestamp: string;
  path: string;
}

@Injectable()
export class TransformResponseInterceptor<T> implements NestInterceptor<T, ApiResponseEnvelope<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<ApiResponseEnvelope<T>> {
    const ctx = context.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    return next.handle().pipe(
      map((resData) => {
        // If data contains pagination metadata, separate data and meta
        const isPaginated = resData && typeof resData === 'object' && 'data' in resData && 'meta' in resData;
        const data = isPaginated ? resData.data : resData;
        const meta = isPaginated ? resData.meta : undefined;

        return {
          success: true,
          statusCode: response.statusCode,
          message: 'Operation completed successfully',
          data,
          ...(meta ? { meta } : {}),
          timestamp: new Date().toISOString(),
          path: request.url,
        };
      }),
    );
  }
}
```

### 6. Default Mandatory GET Pagination Query DTO (`src/core/dto/pagination-query.dto.ts`)
ALL GET endpoints returning arrays/collections MUST enforce default pagination (`page = 1`, `limit = 10`, `maxLimit = 100`) to prevent memory leaks and database OOM crashes:

```typescript
import { IsOptional, IsInt, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class PaginationQueryDto {
  @ApiPropertyOptional({ default: 1, minimum: 1, description: 'Page number' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  readonly page: number = 1;

  @ApiPropertyOptional({ default: 10, minimum: 1, maximum: 100, description: 'Items per page' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  readonly limit: number = 10;

  get skip(): number {
    return (this.page - 1) * this.limit;
  }
}
```

### Usage in Feature Service / Repository:
```typescript
async findAll(query: PaginationQueryDto) {
  const [items, total] = await Promise.all([
    this.prisma.user.findMany({
      skip: query.skip,
      take: query.limit,
      orderBy: { createdAt: 'desc' },
    }),
    this.prisma.user.count(),
  ]);

  return {
    data: items,
    meta: {
      page: query.page,
      limit: query.limit,
      total,
      totalPages: Math.ceil(total / query.limit),
    },
  };
}
```

### 7. Sample Domain Feature CRUD Reference Scaffolding (`src/features/users/`)
Every enterprise scaffolding operation MUST generate a complete, working reference domain CRUD module (`UsersModule`) to demonstrate all 15 points working together:

#### `src/features/users/dto/create-user.dto.ts`:
```typescript
import { IsEmail, IsNotEmpty, IsString, MinLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ example: 'murali@example.com', description: 'User primary email' })
  @IsEmail()
  @IsNotEmpty()
  readonly email: string;

  @ApiProperty({ example: 'Murali', description: 'User full name' })
  @IsString()
  @IsNotEmpty()
  readonly name: string;
}
```

#### `src/features/users/users.controller.ts`:
```typescript
import { Controller, Get, Post, Body, Patch, Param, Delete, Query, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { PaginationQueryDto } from '../../core/dto/pagination-query.dto';

@ApiTags('Users')
@ApiBearerAuth()
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create a new user' })
  create(@Body() createUserDto: CreateUserDto) {
    return this.usersService.create(createUserDto);
  }

  @Get()
  @ApiOperation({ summary: 'Get paginated list of users' })
  findAll(@Query() query: PaginationQueryDto) {
    return this.usersService.findAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  findOne(@Param('id') id: string) {
    return this.usersService.findOne(id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update user by ID' })
  update(@Param('id') id: string, @Body() updateUserDto: UpdateUserDto) {
    return this.usersService.update(id, updateUserDto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete user by ID' })
  remove(@Param('id') id: string) {
    return this.usersService.remove(id);
  }
}
```

### 8. Strict Migration-Only DB Mutations & Seeder Architecture (`prisma/seed.ts`)
ALL database schema additions or modifications MUST be performed strictly through version-controlled database migrations (`pnpm prisma migrate dev`). Direct manual DB table edits are strictly prohibited. Every project MUST also scaffold a dedicated database seeder:

#### `prisma/seed.ts`:
```typescript
import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seeding...');

  // Seed default admin user
  const hashedPassword = await bcrypt.hash('AdminP@ss123!', 10);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@example.com' },
    update: {},
    create: {
      email: 'admin@example.com',
      name: 'System Admin',
      password: hashedPassword,
      role: 'ADMIN',
    },
  });

  console.log(`✅ Seeded Admin User: ${admin.email}`);
}

main()
  .catch((e) => {
    console.error('❌ Seeding error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

#### `package.json` Seeding Configuration:
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

### 9. Automated Production README Documentation (`README.md`)
Every enterprise scaffolding operation MUST generate or update a comprehensive `README.md` at the project root documenting tech stack, env variables, migration/seeder commands, and Swagger API links:

#### Generated `README.md` Template:
```markdown
# Enterprise NestJS Backend API

Production-grade NestJS backend service built with TypeScript, Prisma ORM, Zod validation, and Swagger API documentation.

## 🛠️ Tech Stack & Architecture
- **Framework**: NestJS v10+ (Modular Architecture, `pnpm`)
- **Validation**: Zod + `class-validator` (Global `ValidationPipe`)
- **Database & ORM**: PostgreSQL + Prisma ORM (Migration-only)
- **API Docs**: Swagger / OpenAPI (`/api/docs`)
- **Security**: Helmet, CORS, JWT Auth + RBAC, Throttler Rate Limiting
- **Observability**: Terminus Health Check (`/health`) & Correlation ID Logging

## 🔐 Environment Variables (`.env`)

| Variable | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `NODE_ENV` | App runtime environment | `development` | Yes |
| `PORT` | HTTP Server Port | `3000` | Yes |
| `DATABASE_URL` | PostgreSQL connection URL | - | Yes |
| `JWT_SECRET` | Secret key for signing JWTs | - | Yes |

## 🚀 Quick Start Commands

```bash
# 1. Install dependencies via pnpm
pnpm install

# 2. Run Database Migrations
pnpm db:migrate

# 3. Seed Database (Admin user & mock data)
pnpm db:seed

# 4. Start Development Server
pnpm start:dev
```

## 📚 API Documentation & Health
- **Swagger Interactive API Docs**: [http://localhost:3000/api/docs](http://localhost:3000/api/docs)
- **Health Check Endpoint**: [http://localhost:3000/api/v1/health](http://localhost:3000/api/v1/health)
```

### 10. Graceful Shutdown Hooks (`app.enableShutdownHooks()`) (Point 18)
Every NestJS bootstrap MUST enable graceful shutdown hooks so container termination signals (`SIGTERM`, `SIGINT`) cleanly drain active HTTP connections and close database/Redis connection pools:

```typescript
// main.ts
app.enableShutdownHooks();
```

### 11. Production Multi-Stage Dockerfile (`Dockerfile`) (Point 19)
Scaffold a production-optimized multi-stage Docker build using `pnpm`:

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# Stage 2: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --prod --frozen-lockfile
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 12. Automated CI/CD Quality Pipeline (`.github/workflows/ci.yml`) (Point 20)
Scaffold GitHub Actions workflow for automated PR quality checks:

```yaml
name: CI Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with:
          version: 11.1.3
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm run build
      - run: pnpm test
```

## Constraints & Rules
- Always use `pnpm` for installing NestJS dependencies (`pnpm add @nestjs/config zod`).
- Controllers MUST remain clean delegators without DB queries or complex conditional logic.
- All HTTP endpoints MUST return responses wrapped in the standardized `ApiResponseEnvelope` (Point 13).
- ALL list/collection GET endpoints MUST enforce default pagination (`PaginationQueryDto`) with a maximum hard limit of 100 (Point 14).
- Scaffolding operations MUST auto-generate the complete sample CRUD reference feature (`UsersModule`) implementing points 1 through 14 (Point 15).
- ALL database schema modifications MUST be executed exclusively through declarative migration files (`pnpm prisma migrate dev`) and include an automated DB seeder script (Point 16).
- Scaffolding operations MUST auto-generate or update a comprehensive `README.md` documenting architecture, env variables, migration/seeder scripts, and Swagger links (Point 17).
- Application MUST enable `enableShutdownHooks()` (Point 18), include multi-stage `Dockerfile` (Point 19), and scaffold `.github/workflows/ci.yml` (Point 20).
