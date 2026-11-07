import { IsOptional, IsInt, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';
import { ApiPropertyOptional } from '@nestjs/swagger';

/**
 * Standardized pagination parameters enforced across all collection GET endpoints.
 * Protects database resources against bulk un-indexed scans by capping limit at 100.
 */
export class PaginationQueryDto {
  /** Page number offset (1-indexed) */
  @ApiPropertyOptional({ default: 1, minimum: 1, description: 'Page number' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  readonly page: number = 1;

  /** Maximum number of records to return per page (capped at 100) */
  @ApiPropertyOptional({ default: 10, minimum: 1, maximum: 100, description: 'Records per page' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  readonly limit: number = 10;

  /**
   * Computes the record offset for database query skip clauses.
   */
  get skip(): number {
    return (this.page - 1) * this.limit;
  }
}
