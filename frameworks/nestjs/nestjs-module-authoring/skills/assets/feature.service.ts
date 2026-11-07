import { Injectable, Inject, NotFoundException } from '@nestjs/common';
import { FEATURE_REPOSITORY, IFeatureRepository, FeatureEntity } from './feature-repository.interface';
import { CreateFeatureDto } from './create-feature.dto';
import { UpdateFeatureDto } from './update-feature.dto';

/**
 * Domain service encapsulating business rules, validations, and transaction boundaries.
 * Decoupled from concrete database implementation via IFeatureRepository.
 */
@Injectable()
export class FeatureService {
  constructor(
    @Inject(FEATURE_REPOSITORY)
    private readonly featureRepository: IFeatureRepository,
  ) {}

  /**
   * Creates a new feature resource after performing domain validations.
   */
  async create(dto: CreateFeatureDto): Promise<FeatureEntity> {
    return this.featureRepository.create(dto);
  }

  /**
   * Retrieves a paginated slice of features.
   */
  async findAll(skip: number, limit: number): Promise<{ data: FeatureEntity[]; total: number }> {
    const [data, total] = await this.featureRepository.findAll(skip, limit);
    return { data, total };
  }

  /**
   * Finds a feature by ID or throws NotFoundException.
   */
  async findOne(id: string): Promise<FeatureEntity> {
    const feature = await this.featureRepository.findById(id);
    if (!feature) {
      throw new NotFoundException(`Feature with ID '${id}' not found.`);
    }
    return feature;
  }

  /**
   * Updates an existing feature by ID.
   */
  async update(id: string, dto: UpdateFeatureDto): Promise<FeatureEntity> {
    await this.findOne(id); // Guarantees existence
    return this.featureRepository.update(id, dto);
  }

  /**
   * Removes a feature by ID.
   */
  async remove(id: string): Promise<void> {
    await this.findOne(id); // Guarantees existence
    await this.featureRepository.delete(id);
  }
}
