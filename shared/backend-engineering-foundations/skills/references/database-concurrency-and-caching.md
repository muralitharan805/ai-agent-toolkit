# Database Pooling, Concurrency & Distributed Caching

## 1. Connection Pool Sizing Math

Arbitrary pool sizing causes disk thrashing and process starvation. Use the PostgreSQL/HikariCP formula:

$$\text{PoolSize} = (\text{CPU Cores} \times 2) + \text{Effective Spindles}$$

- An 8-core server with SSD requires:
  $$(8 \times 2) + 1 = 17 \text{ connections}.$$
- If 10 container replicas run, total connections reach 170. Always use a connection proxy (**PgBouncer** or **AWS RDS Proxy**) to multiplex thousands of client connections onto a small, optimal pool.

---

## 2. Safe Zero-Downtime DDL Migrations (Expand-and-Contract)

Never rename or drop columns in a single release. Execute across 3 phases:
1. **Expand**: Add new column as `NULLable`. Application writes to both old and new columns.
2. **Backfill**: Run throttled background migration copying historical data from old column to new column.
3. **Contract**: Switch reads to new column. Drop old column in subsequent deployment.

### Safe DDL Rules
- Always set lock timeout: `SET lock_timeout = '2s';`
- Always create indexes concurrently: `CREATE INDEX CONCURRENTLY idx_users_email ON users(email);`

---

## 3. High-Concurrency Mutations & Optimistic Concurrency Control (OCC)

### Atomic Conditional Updates
```sql
-- Prevents inventory overselling without row-level deadlocks
UPDATE inventory_items
SET available_quantity = available_quantity - :requestedQuantity,
    updated_at = CURRENT_TIMESTAMP_UTC
WHERE id = :itemId 
  AND available_quantity >= :requestedQuantity;
-- IF rows_affected == 0 THEN THROW InsufficientStockException
```

### Monotonic Version Numbers (OCC)
```sql
UPDATE accounts
SET balance = :newBalance,
    version = version + 1,
    updated_at = CURRENT_TIMESTAMP_UTC
WHERE id = :accountId 
  AND version = :expectedVersion;
-- IF rows_affected == 0 THEN THROW OptimisticLockConflictException
```

---

## 4. Cache-Aside Pattern & Stampede Defense

```text
FUNCTION GetCachedEntity(EntityId):
    CacheKey = "entity:" + EntityId
    CachedData = Redis.GET(CacheKey)
    IF CachedData IS NOT NULL:
        RETURN JSON.deserialize(CachedData)
        
    // Prevent Cache Stampede using Distributed Mutex
    LockKey = "lock:" + CacheKey
    Acquired = Redis.SET(LockKey, "LOCKED", NX=TRUE, EX=5)
    
    IF Acquired:
        TRY:
            FreshData = Database.fetchById(EntityId)
            // Apply TTL with random jitter (+/- 10%) to prevent simultaneous mass expiration
            TTL = 3600 + RandomInteger(-300, 300)
            Redis.SET(CacheKey, JSON.serialize(FreshData), EX=TTL)
            RETURN FreshData
        FINALLY:
            Redis.DEL(LockKey)
    ELSE:
        // Another worker is recalculating. Sleep briefly and read from cache.
        Sleep(50ms)
        RETURN GetCachedEntity(EntityId)
```
