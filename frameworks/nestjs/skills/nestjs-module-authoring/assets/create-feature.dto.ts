import { IsNotEmpty, IsOptional, IsString, MaxLength } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

/**
 * Payload contract for creating a new domain feature resource.
 */
export class CreateFeatureDto {
  /** Descriptive name of the feature entity */
  @ApiProperty({ example: 'Loan Amortization Schedule', description: 'Unique name of the feature' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  readonly name: string;

  /** Optional detailed explanation or notes */
  @ApiPropertyOptional({ example: 'Calculates monthly payment schedules', description: 'Feature description' })
  @IsString()
  @IsOptional()
  @MaxLength(500)
  readonly description?: string;
}
