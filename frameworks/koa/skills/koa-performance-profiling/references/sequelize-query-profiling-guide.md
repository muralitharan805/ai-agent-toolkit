# Sequelize Query Profiling & Optimization Guide (JavaScript)

## Purpose
This guide details how to detect, analyze, and eliminate database bottlenecks in Node.js applications using Sequelize and MySQL in JavaScript.

---

## 1. Why 3–4 Second Latency Almost Always Stems From MySQL
In typical Koa applications, CPU processing in JavaScript handles requests in 10–50ms. Latencies of 2–4 seconds are predominantly caused by:
1. **Unindexed Table Scans (`ALL`)**: Queries scanning entire tables because of missing composite indexes.
2. **N+1 Query Cascades**: Fetching child relations in separate queries inside a loop instead of performing eager loads with JOINs.
3. **Cartesian Product JOINs**: Eager loading multiple `hasMany` relationships in a single `findAll` query.
4. **Leading Wildcard Searches**: Using `LIKE '%search%'` which prevents B-Tree index traversal.
5. **Unbounded `SELECT *`**: Fetching heavy text/blob columns without `attributes` projections.

---

## 2. Enabling Query Timing & Slow Query Logging

Attach a benchmark logging hook to your Sequelize connection:

```javascript
const { Sequelize } = require('sequelize');
const logger = require('../utils/logger');

const sequelize = new Sequelize(dbName, dbUser, dbPass, {
  dialect: 'mysql',
  benchmark: true, // Instructs Sequelize to pass execution duration in milliseconds
  logging: (sql, timingMs) => {
    const duration = timingMs || 0;
    if (duration > 200) {
      logger.warn(JSON.stringify({
        event: 'slow_database_query',
        durationMs: duration,
        query: sql.substring(0, 1000), // Truncate very long queries
      }));
    }
  },
});

module.exports = { sequelize };
```

---

## 3. Investigating Bottlenecks with MySQL EXPLAIN ANALYZE

When a query exceeds 200ms, extract the raw SQL from the logger and run `EXPLAIN ANALYZE` in MySQL:

```sql
EXPLAIN ANALYZE
SELECT `Property`.`id`, `Property`.`title`, `Property`.`price`
FROM `properties` AS `Property`
WHERE `Property`.`status` = 'AVAILABLE' AND `Property`.`branchId` = 4
ORDER BY `Property`.`createdAt` DESC
LIMIT 20;
```

### Key Red Flags in EXPLAIN Output:
- **`type: ALL`**: Full table scan. Add an index on the `WHERE` and `ORDER BY` columns.
- **`Using filesort`**: MySQL could not sort rows using an index. Create a composite index `(branchId, status, createdAt DESC)`.
- **`Using temporary`**: A temporary table was created on disk. Optimize grouping or reduce join volume.
- **`rows: 500000`**: High row inspection volume before filtering.

---

## 4. Sequelize Anti-Patterns vs. Recommended Fixes

### Pitfall 1: Missing Projections (`SELECT *`)
```javascript
// ❌ BAD: Fetches heavy columns (descriptions, JSON metadata)
const properties = await Property.findAll();

// ✅ GOOD: Projects only necessary card attributes
const properties = await Property.findAll({
  attributes: ['id', 'title', 'price', 'slug', 'thumbnailUrl'],
  limit: 20,
});
```

### Pitfall 2: Eager Loading Cartesian Explosion
```javascript
// ❌ BAD: Joins 3 hasMany tables simultaneously creating massive row duplication
const property = await Property.findByPk(id, {
  include: [Images, Reviews, Floorplans],
});

// ✅ GOOD: Use separate indexed queries or subqueries
const property = await Property.findByPk(id);
const [images, reviews] = await Promise.all([
  Image.findAll({ where: { propertyId: id } }),
  Review.findAll({ where: { propertyId: id } }),
]);
```
