/**
 * Injection token for decoupling domain services from concrete database ORM adapters.
 */
export const FEATURE_REPOSITORY = Symbol('FEATURE_REPOSITORY');

/**
 * Domain entity model representing the core business object.
 */
export interface FeatureEntity {
  readonly id: string;
  readonly name: string;
  readonly description?: string | null;
  readonly isActive: boolean;
  readonly createdAt: Date;
  readonly updatedAt: Date;
}

/**
 * Input contract for creating a new feature entity in the persistence layer.
 */
export interface CreateFeatureInput {
  readonly name: string;
  readonly description?: string;
}

/**
 * Input contract for updating an existing feature entity.
 */
export interface UpdateFeatureInput {
  readonly name?: string;
  readonly description?: string;
  readonly isActive?: boolean;
}

/**
 * Abstract repository interface declaring persistence operations.
 * Allows switching between Prisma, TypeORM, or In-Memory mocks without altering business logic.
 */
export interface IFeatureRepository {
  /**
   * Retrieves an entity by its unique identifier.
   */
  findById(id: string): Promise<FeatureEntity | null>;

  /**
   * Retrieves a paginated slice of entities.
   */
  findAll(skip: number, limit: number): Promise<[FeatureEntity[], number]>;

  /**
   * Persists a newly created entity.
   */
  create(data: CreateFeatureInput): Promise<FeatureEntity>;

  /**
   * Updates an existing entity by ID.
   */
  update(id: string, data: UpdateFeatureInput): Promise<FeatureEntity>;

  /**
   * Removes an entity by ID.
   */
  delete(id: string): Promise<void>;
}
