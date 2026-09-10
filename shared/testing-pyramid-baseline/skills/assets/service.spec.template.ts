import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';

// Interfaces & Tokens (adjust to target domain)
export const ITEM_REPOSITORY = Symbol('ITEM_REPOSITORY');

export interface ItemEntity {
  id: string;
  title: string;
}

export interface IItemRepository {
  findById(id: string): Promise<ItemEntity | null>;
  create(data: { title: string }): Promise<ItemEntity>;
}

// Sample Domain Service
export class ItemService {
  constructor(private readonly repo: IItemRepository) {}

  async getItem(id: string): Promise<ItemEntity> {
    const item = await this.repo.findById(id);
    if (!item) {
      throw new NotFoundException(`Item with ID ${id} not found`);
    }
    return item;
  }
}

describe('ItemService', () => {
  let service: ItemService;
  let mockRepo: {
    findById: ReturnType<typeof vi.fn>;
    create: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    mockRepo = {
      findById: vi.fn(),
      create: vi.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        {
          provide: ItemService,
          useFactory: () => new ItemService(mockRepo),
        },
        {
          provide: ITEM_REPOSITORY,
          useValue: mockRepo,
        },
      ],
    }).compile();

    service = module.get<ItemService>(ItemService);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should return item when item exists', async () => {
    const expectedItem: ItemEntity = { id: 'item_1', title: 'Test Title' };
    mockRepo.findById.mockResolvedValue(expectedItem);

    const result = await service.getItem('item_1');

    expect(mockRepo.findById).toHaveBeenCalledWith('item_1');
    expect(result).toEqual(expectedItem);
  });

  it('should throw NotFoundException when item does not exist', async () => {
    mockRepo.findById.mockResolvedValue(null);

    await expect(service.getItem('missing_id')).rejects.toThrow(NotFoundException);
    expect(mockRepo.findById).toHaveBeenCalledWith('missing_id');
  });
});
