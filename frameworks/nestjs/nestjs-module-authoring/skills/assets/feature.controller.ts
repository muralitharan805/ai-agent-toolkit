import { Controller, Get, Post, Body, Patch, Param, Delete, Query, HttpCode, HttpStatus, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { FeatureService } from './feature.service';
import { CreateFeatureDto } from './create-feature.dto';
import { UpdateFeatureDto } from './update-feature.dto';
import { FeatureEntity } from './feature-repository.interface';

/**
 * Controller delegating HTTP requests to FeatureService.
 * Contains zero business logic and zero direct database queries.
 */
@ApiTags('Features')
@ApiBearerAuth()
@Controller('features')
export class FeatureController {
  constructor(private readonly featureService: FeatureService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create a new feature' })
  @ApiResponse({ status: 201, description: 'Feature created successfully' })
  async create(@Body() dto: CreateFeatureDto): Promise<FeatureEntity> {
    return this.featureService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: 'Get paginated list of features' })
  async findAll(
    @Query('page') page = 1,
    @Query('limit') limit = 10,
  ): Promise<{ data: FeatureEntity[]; total: number }> {
    const pageNum = Math.max(1, Number(page));
    const limitNum = Math.min(100, Math.max(1, Number(limit)));
    const skip = (pageNum - 1) * limitNum;
    return this.featureService.findAll(skip, limitNum);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Retrieve a feature by ID' })
  async findOne(@Param('id') id: string): Promise<FeatureEntity> {
    return this.featureService.findOne(id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update an existing feature by ID' })
  async update(@Param('id') id: string, @Body() dto: UpdateFeatureDto): Promise<FeatureEntity> {
    return this.featureService.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete a feature by ID' })
  async remove(@Param('id') id: string): Promise<void> {
    await this.featureService.remove(id);
  }
}
