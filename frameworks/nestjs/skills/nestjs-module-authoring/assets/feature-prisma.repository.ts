import { Injectable } from '@nestjs/common';
import { IFeatureRepository, FeatureEntity, CreateFeatureInput, UpdateFeatureInput } from './feature-repository.interface';

/**
 * Concrete database adapter implementing IFeatureRepository using Prisma ORM.
 */
@Injectable()
export class FeaturePrismaRepository implements IFeatureRepository {
  // In a live project, inject PrismaService: constructor(private readonly prisma: PrismaService) {}

  async findById(id: string): Promise<FeatureEntity | null> {
    // Simulated Prisma query: return this.prisma.feature.findUnique({ where: { id } });
    return {
      id,
      name: 'Sample Feature',
      description: 'Feature description',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  }

  async findAll(skip: number, limit: number): Promise<[FeatureEntity[], number]> {
    // Simulated: return Promise.all([this.prisma.feature.findMany({ skip, take: limit }), this.prisma.feature.count()]);
    const items: FeatureEntity[] = [
      {
        id: 'feat-1',
        name: 'First Feature',
        description: 'First description',
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    ];
    return [items, 1];
  }

  async create(data: CreateFeatureInput): Promise<FeatureEntity> {
    return {
      id: `feat-${Date.now()}`,
      name: data.name,
      description: data.description ?? null,
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  }

  async update(id: string, data: UpdateFeatureInput): Promise<FeatureEntity> {
    return {
      id,
      name: data.name ?? 'Updated Feature',
      description: data.description ?? null,
      isActive: data.isActive ?? true,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  }

  async delete(id: string): Promise<void> {
    // Simulated: await this.prisma.feature.delete({ where: { id } });
  }
}
