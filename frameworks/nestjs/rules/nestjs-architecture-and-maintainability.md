---
trigger: always_on
description: "Enforces strict architectural boundaries, dependency injection practices, DTO validation, exception filtering, and configuration safety for long-term NestJS backend maintainability."
---
# NestJS Architecture and Maintainability Standards

## Description
This rule enforces enterprise-grade NestJS backend practices designed for long-term software maintainability, microservice readiness, and type-safe Clean Architecture. It prevents common NestJS code smells such as monolithic controller logic, unvalidated request payloads, unhandled async errors, direct ORM coupling in controllers, and unsafe environment configuration.

## Constraints
- **Module Architecture**: MUST structure the application into bounded domain modules (`CoreModule` for global singletons, `SharedModule` for reusable utilities, and isolated Feature Modules).
- **DTO Validation**: MUST pass all incoming request payloads through validated DTO classes using `class-validator` and `class-transformer`. MUST configure global `ValidationPipe` with `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`.
- **Controller Decoupling**: MUST NOT put business logic or direct database ORM queries (Prisma/TypeORM/Knex) inside controllers. Controllers MUST only handle HTTP parsing, delegation to services, and response formatting.
- **Dependency Injection**: MUST inject service interfaces or abstract repositories using NestJS custom providers (`provide` tokens) when decoupling implementation detail from business logic.
- **Exception Filters**: MUST handle errors using custom `@Catch()` filters extending `BaseExceptionFilter` or `HttpExceptionFilter`. NEVER expose raw database error stack traces to clients.
- **Configuration Safety**: MUST validate environment variables at bootstrap using a `Joi` or `Zod` schema with `ConfigModule.forRoot()`.
- **Strict Typing**: MUST NOT use `any` or implicit `Object` types in service method signatures or DTO fields. All asynchronous operations MUST explicitly declare return types as `Promise<T>` or `Observable<T>`.

## Examples

- **Correct implementation:**
```typescript
// user.dto.ts
import { IsEmail, IsNotEmpty, IsString, MinLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ example: 'user@example.com', description: 'User primary email' })
  @IsEmail()
  @IsNotEmpty()
  readonly email: string;

  @ApiProperty({ example: 'SecureP@ss123', description: 'User password' })
  @IsString()
  @MinLength(8)
  readonly password: string;
}

// user.service.ts
import { Injectable, ConflictException, Inject } from '@nestjs/common';
import { CreateUserDto } from './dto/create-user.dto';
import { USER_REPOSITORY, IUserRepository } from './interfaces/user-repository.interface';
import { UserEntity } from './entities/user.entity';

@Injectable()
export class UserService {
  constructor(
    @Inject(USER_REPOSITORY)
    private readonly userRepository: IUserRepository,
  ) {}

  async createUser(dto: CreateUserDto): Promise<UserEntity> {
    const existing = await this.userRepository.findByEmail(dto.email);
    if (existing) {
      throw new ConflictException(`User with email ${dto.email} already exists.`);
    }
    return this.userRepository.save(dto);
  }
}

// user.controller.ts
import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { UserService } from './user.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UserEntity } from './entities/user.entity';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(@Body() createUserDto: CreateUserDto): Promise<UserEntity> {
    return this.userService.createUser(createUserDto);
  }
}
```

- **Incorrect implementation:**
```typescript
// Bad Pattern: Controller direct ORM manipulation, unvalidated body, any type
@Controller('users')
export class UserController {
  constructor(@InjectRepository(User) private repo: any) {}

  @Post()
  async create(@Body() body: any) { // Violation: body is 'any', no validation
    // Violation: Business logic & direct database access inside controller
    const user = await this.repo.findOne({ where: { email: body.email } });
    if (user) {
      return { status: 'error', msg: 'exists' }; // Violation: raw error response instead of NestJS exception
    }
    return await this.repo.save(body);
  }
}
```
