# Brownfield Project Audit & Decoupling Guide

## Overview
This guide provides a safe, non-destructive methodology for introducing an automated testing setup into an **existing, running production Koa.js backend** without breaking live PM2 workers, existing routes, or production configurations.

---

## 1. The Pre-Implementation Repository Audit Checklist

Before writing tests or installing packages, inspect the codebase across these 6 architectural dimensions:

| Dimension | Inspection Target | Key Questions to Answer |
| :--- | :--- | :--- |
| **Runtime & Dependencies** | `package.json`, lockfile, Node version | Does the project use CommonJS (`require`) or ESM (`import`)? Which Sequelize version? |
| **Bootstrap Architecture** | `server.js`, `app.js`, `index.js` | Is `app.listen()` directly inside the same file that configures middleware and routes? |
| **Layer Separation** | Controllers, services, models | Do controllers talk to services, or are Sequelize queries written directly inside route handlers? |
| **Database Lifecycle** | Sequelize config, migrations, seeders | Is `sequelize.authenticate()` called globally at startup? Are connection pool limits set? |
| **Authentication Flow** | JWT middleware, sessions, headers | How is `ctx.state.user` populated? What is the secret key environment variable? |
| **External Dependencies** | Payment gateways, CRMs, email | Which third-party services make outbound HTTP calls during normal route execution? |

---

## 2. Decoupling `createApp()` from `server.listen()`

### The Problem
In many legacy or un-tested Koa applications, the server is started in a single monolithic file:

```javascript
// ❌ MONOLITHIC server.js (Untestable with Supertest)
const Koa = require('koa');
const router = require('./routes');
const app = new Koa();

app.use(router.routes());

// PROBLEM: Importing this file in a test immediately binds port 3000!
app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```
If Supertest imports this file, it causes `EADDRINUSE` port collisions and prevents parallel test execution.

---

### The Safe Minimal Refactoring Pattern
Do NOT refactor business logic. Perform only a clean two-file separation:

#### File 1: `src/app.js` (Pure Application Factory)
Configures middleware and routes without listening on any port:
```javascript
// ✅ src/app.js
const Koa = require('koa');
const router = require('./routes');

function createApp() {
  const app = new Koa();

  // Register existing middleware & routes
  app.use(router.routes()).use(router.allowedMethods());

  return app;
}

const app = createApp();

module.exports = { app, createApp };
```

#### File 2: `src/server.js` (Production Listener Entry Point)
Keeps PM2 and production deployment completely intact:
```javascript
// ✅ src/server.js (Unchanged PM2 target)
const { app } = require('./app');
const { sequelize } = require('./database');

const PORT = process.env.PORT || 3000;

async function bootstrap() {
  await sequelize.authenticate();
  app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
}

bootstrap().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
```

### Supertest Test Integration
Now Supertest can test the Koa pipeline directly in memory:
```javascript
// tests/api/health.spec.js
const request = require('supertest');
const { app } = require('../../src/app');

it('should respond 200 without opening network ports', async () => {
  const res = await request(app.callback()).get('/health');
  expect(res.status).toBe(200);
});
```

---

## 3. Production Safety Guardrails

1. **Zero Production DB Mutation**: Test runners MUST explicitly verify `process.env.NODE_ENV === 'test'` and abort execution immediately if pointed at production hostnames.
2. **Preserve Coding Conventions**: If the project uses CommonJS (`require`), author all test fixtures and helpers in CommonJS. Do not force TypeScript or build steps onto an existing JavaScript project.
3. **Keep PM2 Untouched**: Ensure `ecosystem.config.js` continues to target `src/server.js` with identical cluster configurations.
