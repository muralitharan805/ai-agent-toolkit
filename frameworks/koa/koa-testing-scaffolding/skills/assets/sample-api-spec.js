/**
 * @file sample-api-spec.js
 * @description Exemplary end-to-end route specification demonstrating
 * Supertest assertions, authentication guards, and validation checks in JavaScript.
 */

const { describe, it, expect, beforeAll } = require('vitest');
const request = require('supertest');
const Router = require('@koa/router');
const { createTestApp } = require('./setup-app');

describe('Sample Koa API Route Suite (JavaScript)', () => {
  const app = createTestApp();
  const router = new Router();

  beforeAll(() => {
    // Register mock test routes
    router.post('/api/users', (ctx) => {
      const body = ctx.request.body;
      if (!body || !body.email || !body.role) {
        ctx.throw(400, 'Missing required fields: email and role');
      }

      ctx.status = 201;
      ctx.body = {
        success: true,
        data: {
          id: 1,
          email: body.email,
          role: body.role,
        },
      };
    });

    router.get('/api/protected', (ctx) => {
      const authHeader = ctx.get('Authorization');
      if (!authHeader || !authHeader.startsWith('Bearer valid-token')) {
        ctx.throw(401, 'Invalid or missing authentication token');
      }

      ctx.status = 200;
      ctx.body = {
        success: true,
        message: 'Protected resource accessible',
      };
    });

    app.use(router.routes()).use(router.allowedMethods());
  });

  describe('POST /api/users (Validation & Creation)', () => {
    it('should return 400 Bad Request when payload is incomplete', async () => {
      const res = await request(app.callback())
        .post('/api/users')
        .send({ role: 'AGENT' }); // Missing email

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('Missing required fields');
    });

    it('should return 201 Created and return valid user payload', async () => {
      const res = await request(app.callback())
        .post('/api/users')
        .send({ email: 'agent@example.com', role: 'AGENT' });

      expect(res.status).toBe(201);
      expect(res.body.success).toBe(true);
      expect(res.body.data.email).toBe('agent@example.com');
    });
  });

  describe('GET /api/protected (Authentication Guard)', () => {
    it('should return 401 Unauthorized when authorization token is omitted', async () => {
      const res = await request(app.callback()).get('/api/protected');

      expect(res.status).toBe(401);
      expect(res.body.success).toBe(false);
    });

    it('should return 200 OK when valid Bearer token is provided', async () => {
      const res = await request(app.callback())
        .get('/api/protected')
        .set('Authorization', 'Bearer valid-token-123');

      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
    });
  });
});
