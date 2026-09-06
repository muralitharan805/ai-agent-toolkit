# DTO Validation & OpenAPI Swagger Documentation in NestJS

This reference documents the standards for request payload validation, schema inheritance, and automated OpenAPI documentation in NestJS feature modules.

---

## 1. DTO Validation Pipeline with `class-validator`

Every external payload received by a controller method must be validated through an explicit DTO class:

```typescript
import { IsString, IsNotEmpty, IsEmail, IsEnum, IsOptional, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export enum UserRole {
  ADMIN = 'ADMIN',
  MEMBER = 'MEMBER',
}

export class AddressDto {
  @ApiProperty({ example: '100 Market St' })
  @IsString()
  @IsNotEmpty()
  readonly street: string;
}

export class CreateUserDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  @IsNotEmpty()
  readonly email: string;

  @ApiProperty({ enum: UserRole, default: UserRole.MEMBER })
  @IsEnum(UserRole)
  readonly role: UserRole;

  @ApiPropertyOptional({ type: () => AddressDto })
  @IsOptional()
  @ValidateNested()
  @Type(() => AddressDto)
  readonly address?: AddressDto;
}
```

---

## 2. Schema Inheritance via `@nestjs/swagger`

Always use `@nestjs/swagger` utility functions (`PartialType`, `OmitType`, `PickType`) to prevent code duplication between create and update DTOs:

```typescript
import { PartialType } from '@nestjs/swagger';
import { CreateUserDto } from './create-user.dto';

/**
 * Updates inherit all validation rules and Swagger metadata as optional fields.
 */
export class UpdateUserDto extends PartialType(CreateUserDto) {}
```

---

## 3. Controller OpenAPI Annotation Standards

Every controller method must declare its OpenAPI contracts:
- `@ApiTags('DomainName')` on the controller class.
- `@ApiBearerAuth()` for secured routes.
- `@ApiOperation({ summary: 'Short action summary' })`.
- `@ApiResponse({ status: 200, description: 'Success payload' })`.
- `@ApiResponse({ status: 400, description: 'Validation failed' })`.
- `@ApiResponse({ status: 404, description: 'Resource not found' })`.
