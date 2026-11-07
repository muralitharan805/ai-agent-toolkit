# Database Integration & Transaction Rollback Testing Guide (JavaScript)

## Purpose
This guide defines how to execute deterministic database integration tests using **Sequelize ORM** and **MySQL** in JavaScript without cross-test state pollution or data leaks.

---

## 1. Test Database Environment Setup

### Environment Isolation
Integration tests MUST target an isolated database schema (e.g. `myapp_test`), never development or staging databases:

```bash
# .env.test
NODE_ENV=test
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=test_user
DB_PASS=test_secret
DB_NAME=myapp_test
```

---

## 2. Deterministic Isolation Patterns

### Pattern A: Explicit Managed Transaction Rollback (Recommended for Speed)
This is the fastest pattern for isolated database tests because no disk table truncations occur between tests:

```javascript
const { describe, it, expect, beforeEach, afterEach } = require('vitest');
const { sequelize } = require('../setup/database');
const { PropertyRepository } = require('../../src/repositories/property.repository');

describe('PropertyRepository (Transactional Isolation)', () => {
  let transaction;
  let repo;

  beforeEach(async () => {
    // Start uncommitted transaction
    transaction = await sequelize.transaction();
    repo = new PropertyRepository(transaction);
  });

  afterEach(async () => {
    // Rollback every database write performed during test
    await transaction.rollback();
  });

  it('should create property within transaction boundary', async () => {
    const created = await repo.create({
      title: 'Waterfront Villa',
      price: 1250000,
      status: 'AVAILABLE'
    });

    expect(created.id).toBeDefined();
    expect(created.title).toBe('Waterfront Villa');
  });
});
```

### Pattern B: Fast Table Truncation (For Multi-Transaction Workflows)
When the service under test commits internal transactions itself, use table truncation in `beforeEach()`:

```javascript
// tests/setup/database.js
async function truncateAllTables() {
  const models = Object.values(sequelize.models);
  await sequelize.query('SET FOREIGN_KEY_CHECKS = 0;');
  for (const model of models) {
    await model.destroy({ truncate: true, cascade: true, force: true });
  }
  await sequelize.query('SET FOREIGN_KEY_CHECKS = 1;');
}

module.exports = { truncateAllTables };
```

---

## 3. Testing Complex Relational Integrity

### Foreign Key Constraint Validation
Verify that database constraints properly reject orphaned child rows:

```javascript
it('should throw ForeignKeyConstraintError when assigning non-existent branchId', async () => {
  await expect(
    Property.create({
      title: 'Downtown Loft',
      branchId: 99999999, // Non-existent foreign key
      ownerId: 1
    }, { transaction })
  ).rejects.toThrow(/foreign key constraint fails/i);
});
```

### Complex Eager Loading & Scopes
Mocks cannot verify whether Sequelize includes associations correctly:

```javascript
it('should eager load active branches and agent profiles', async () => {
  const branch = await Branch.create({ name: 'Central London' }, { transaction });
  const property = await Property.create({
    title: 'Modern Apartment',
    branchId: branch.id,
    ownerId: 1
  }, { transaction });

  const retrieved = await Property.findByPk(property.id, {
    include: [{ model: Branch, as: 'branch' }],
    transaction
  });

  expect(retrieved).not.toBeNull();
  expect(retrieved.branch.name).toBe('Central London');
});
```
