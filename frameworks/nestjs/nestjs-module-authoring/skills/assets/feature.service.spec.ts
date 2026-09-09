import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { FeatureService } from './feature.service';
import { FEATURE_REPOSITORY, IFeatureRepository, FeatureEntity } from './feature-repository.interface';
import { CreateFeatureDto } from './create-feature.dto';

describe('FeatureService', () => {
  let service: FeatureService;
  let repository: jest.Mocked<IFeatureRepository>;

  const mockFeature: FeatureEntity = {
    id: 'feat-100',
    name: 'Test Feature',
    description: 'Test Description',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  beforeEach(async () => {
    const mockRepo: jest.Mocked<IFeatureRepository> = {
      findById: jest.fn(),
      findAll: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        FeatureService,
        {
          provide: FEATURE_REPOSITORY,
          useValue: mockRepo,
        },
      ],
    }).compile();

    service = module.get<FeatureService>(FeatureService);
    repository = module.get(FEATURE_REPOSITORY);
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should persist and return a new feature entity', async () => {
      const dto: CreateFeatureDto = { name: 'New Feature', description: 'Desc' };
      repository.create.mockResolvedValue(mockFeature);

      const result = await service.create(dto);

      expect(repository.create).toHaveBeenCalledWith(dto);
      expect(result).toEqual(mockFeature);
    });
  });

  describe('findOne', () => {
    it('should return the feature entity when found', async () => {
      repository.findById.mockResolvedValue(mockFeature);

      const result = await service.findOne('feat-100');

      expect(repository.findById).toHaveBeenCalledWith('feat-100');
      expect(result).toEqual(mockFeature);
    });

    it('should throw NotFoundException when the feature is missing', async () => {
      repository.findById.mockResolvedValue(null);

      await expect(service.findOne('invalid-id')).rejects.toThrow(NotFoundException);
    });
  });
});
