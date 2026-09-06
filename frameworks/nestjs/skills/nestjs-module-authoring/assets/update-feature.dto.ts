import { PartialType, ApiPropertyOptional } from '@nestjs/swagger';
import { IsBoolean, IsOptional } from 'class-validator';
import { CreateFeatureDto } from './create-feature.dto';

/**
 * Payload contract for updating an existing domain feature resource.
 * Inherits validated optional properties from CreateFeatureDto via PartialType.
 */
export class UpdateFeatureDto extends PartialType(CreateFeatureDto) {
  /** Optional activation flag */
  @ApiPropertyOptional({ example: true, description: 'Activation status of the feature' })
  @IsBoolean()
  @IsOptional()
  readonly isActive?: boolean;
}
