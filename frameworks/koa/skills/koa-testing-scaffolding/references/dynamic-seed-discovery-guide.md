# Dynamic Seed Discovery & Schema Introspection Guide

## Purpose
In brownfield production projects, hardcoding static database identifiers (e.g. `userId: 1` or `propertyId: 101`) in tests causes frequent test failures when running against real database dumps, sanitized snapshots, or environments with dynamic UUIDs/CRM IDs. This guide outlines how to dynamically discover valid seed data and introspect schemas at runtime.

---

## 1. The Dynamic Seed Discovery Pattern

Instead of assuming specific IDs exist in your test database, discover valid identifiers dynamically during test suite bootstrap:

```javascript
// tests/setup/database.js
const state = {
  availableTables: new Set(),
  seeds: {
    propertyId: null,
    officeId: null,
    userId: null,
  },
};

async function discoverActiveSeeds(sequelize) {
  // 1. Introspect existing database tables
  const [tables] = await sequelize.query('SHOW TABLES');
  state.availableTables = new Set(
    tables.map((t) => Object.values(t)[0].toLowerCase())
  );

  // 2. Dynamically sample active identifiers from available tables
  if (state.availableTables.has('properties')) {
    const [sampleProps] = await sequelize.query(
      'SELECT id, crm_id, slug FROM properties WHERE publish = 1 LIMIT 1'
    );
    if (sampleProps && sampleProps.length > 0) {
      state.seeds.propertyId = sampleProps[0].crm_id || sampleProps[0].slug || String(sampleProps[0].id);
    }
  }

  return state.seeds;
}
```

---

## 2. Graceful Schema Introspection (`hasTable`)

When tests run in minimal local environments where certain optional tables (e.g. `audit_logs`, `lands`, `archives`) might not yet be migrated, use schema detection to skip tests gracefully instead of failing entire suites:

```javascript
function hasTable(tableName) {
  return state.availableTables.has(tableName.toLowerCase());
}

// In test files:
it('should query land records if table exists', async () => {
  if (!hasTable('lands')) {
    console.warn('[SKIP] Table "lands" absent in current schema. Skipping test.');
    return;
  }

  const res = await request(app.callback()).get('/api/lands');
  expect(res.status).toBe(200);
});
```

---

## 3. Koa Application Context Binding (`ctx.appContext`)

If the target Koa backend attaches dependencies to `ctx.appContext` during bootstrap, initialize this context inside `tests/setup/database.js`:

```javascript
const { setAppContext } = require('../../src/utils/appContext');
const models = require('../../src/models');
const config = require('../../src/config');

// Ensure context is available to all controller and middleware executions in tests
setAppContext({ config, sequelize: testSequelize, models });
```
