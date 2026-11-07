/**
 * @file setup-app.js
 * @description Test HTTP harness exporting an initialized Koa application instance
 * for Supertest integration tests in pure JavaScript.
 */

const Koa = require('koa');
const bodyParser = require('koa-bodyparser');

/**
 * Creates and configures a lightweight Koa app instance equipped with
 * correlation ID tracking, JSON body parsing, and error-handling middleware.
 * @returns {Koa} Configured Koa instance ready for Supertest testing
 */
function createTestApp() {
  const app = new Koa();

  // 1. Error handling middleware
  app.use(async (ctx, next) => {
    try {
      await next();
    } catch (err) {
      const status = err.status || err.statusCode || 500;
      ctx.status = status;
      ctx.body = {
        success: false,
        message: err.message || 'Internal Server Error',
      };
    }
  });

  // 2. Correlation ID tracking
  app.use(async (ctx, next) => {
    const requestId = ctx.get('x-request-id') || `test-${Date.now()}`;
    ctx.state.requestId = requestId;
    ctx.set('x-request-id', requestId);
    await next();
  });

  // 3. Body parser
  app.use(bodyParser());

  return app;
}

module.exports = {
  createTestApp,
};
