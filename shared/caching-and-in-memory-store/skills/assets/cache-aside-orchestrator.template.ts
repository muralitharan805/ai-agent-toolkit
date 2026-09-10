/**
 * Production Multi-Tier Caching & Stampede Prevention Template
 * Implements:
 * - Hierarchical cache key formatting ({service}:{entity}:{id}:{version})
 * - Bounded L1 in-process LRU cache
 * - L2 distributed Redis cache with mutex stampede guards
 * - Transparent database fallback on cache outages
 */

export interface CacheOptions {
  /**
   * Time-to-live expiration in seconds.
   */
  readonly ttlSeconds: number;

  /**
   * Whether to store in local L1 in-memory tier as well.
   */
  readonly enableL1?: boolean;
}

export interface CacheClientAdapter {
  get(key: string): Promise<string | null>;
  set(key: string, value: string, mode: string, duration: number): Promise<unknown>;
  del(key: string): Promise<number>;
}

/**
 * Builds standard hierarchical cache keys.
 *
 * @param service - Microservice namespace
 * @param entity - Business entity domain noun
 * @param identifier - Entity ID or filter hash
 * @param version - Schema version string (default: 'v1')
 * @returns Fully qualified cache key string
 */
export function formatCacheKey(
  service: string,
  entity: string,
  identifier: string,
  version = 'v1'
): string {
  return `${service}:${entity}:${identifier}:${version}`;
}

/**
 * Enterprise Cache-Aside Orchestrator with Stampede Protection.
 */
export class CacheAsideOrchestrator {
  private readonly serviceName: string;
  private readonly redisClient: CacheClientAdapter;
  private readonly l1Map = new Map<string, { value: unknown; expiresAt: number }>();
  private readonly maxL1Entries = 5000;

  /**
   * Initializes the orchestrator.
   *
   * @param serviceName - Application service identifier
   * @param redisClient - Backing Redis client adapter
   */
  public constructor(serviceName: string, redisClient: CacheClientAdapter) {
    this.serviceName = serviceName;
    this.redisClient = redisClient;
  }

  /**
   * Retrieves data using the Cache-Aside pattern with mutex locking to mitigate stampedes.
   *
   * @typeParam T - Type of the entity payload
   * @param entity - Entity domain noun
   * @param identifier - Unique entity key
   * @param dbLoader - Database loader fallback function
   * @param options - Cache options including TTL
   * @returns Resolves the requested entity
   */
  public async remember<T>(
    entity: string,
    identifier: string,
    dbLoader: () => Promise<T>,
    options: CacheOptions = { ttlSeconds: 300 }
  ): Promise<T> {
    const key = formatCacheKey(this.serviceName, entity, identifier);

    // 1. Check L1 in-process memory cache if enabled
    if (options.enableL1) {
      const l1Item = this.l1Map.get(key);
      if (l1Item && l1Item.expiresAt > Date.now()) {
        return l1Item.value as T;
      }
    }

    // 2. Check L2 distributed Redis cache
    try {
      const cached = await this.redisClient.get(key);
      if (cached !== null) {
        const parsed = JSON.parse(cached) as T;
        this.setL1(key, parsed, options.ttlSeconds);
        return parsed;
      }
    } catch {
      // Graceful degradation: Redis connection issue, proceed to lock/DB
    }

    // 3. Cache Miss: Acquire Distributed Mutex to prevent cache stampede
    const lockKey = `lock:${key}`;
    let lockAcquired = false;

    try {
      // SET lockKey token NX EX 10 (acquire lock for 10 seconds max)
      const res = await this.redisClient.set(lockKey, 'locked', 'NX', 10);
      lockAcquired = res !== null;
    } catch {
      lockAcquired = true; // If lock check fails due to network, allow direct DB load
    }

    if (!lockAcquired) {
      // Another replica is fetching; wait 50ms and retry read
      await new Promise((resolve) => setTimeout(resolve, 50));
      return this.remember(entity, identifier, dbLoader, options);
    }

    try {
      // 4. Load from primary database
      const freshData = await dbLoader();

      if (freshData !== null && freshData !== undefined) {
        // 5. Populate L2 and L1 caches with explicit TTL
        try {
          await this.redisClient.set(key, JSON.stringify(freshData), 'EX', options.ttlSeconds);
        } catch {
          // Log warning and continue
        }

        if (options.enableL1) {
          this.setL1(key, freshData, options.ttlSeconds);
        }
      }

      return freshData;
    } finally {
      // 6. Release distributed lock
      try {
        await this.redisClient.del(lockKey);
      } catch {
        // Safe to ignore on release
      }
    }
  }

  /**
   * Invalidates a cache key across both L1 and L2 tiers.
   *
   * @param entity - Entity domain noun
   * @param identifier - Unique identifier
   */
  public async invalidate(entity: string, identifier: string): Promise<void> {
    const key = formatCacheKey(this.serviceName, entity, identifier);
    this.l1Map.delete(key);
    try {
      await this.redisClient.del(key);
    } catch {
      // Log warning
    }
  }

  private setL1(key: string, value: unknown, ttlSeconds: number): void {
    if (this.l1Map.size >= this.maxL1Entries) {
      // Evict oldest item
      const firstKey = this.l1Map.keys().next().value;
      if (firstKey) this.l1Map.delete(firstKey);
    }
    this.l1Map.set(key, {
      value,
      expiresAt: Date.now() + ttlSeconds * 1000,
    });
  }
}
