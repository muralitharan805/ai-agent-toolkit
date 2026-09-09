/**
 * @file timing-tracer-middleware.js
 * @description Koa middleware providing request timing, unique request-id correlation,
 * and structured JSON duration logging for performance bottleneck diagnosis in JavaScript.
 */

const crypto = require('node:crypto');

/**
 * Creates Koa middleware that calculates accurate route duration in milliseconds,
 * attaches or forwards `x-request-id`, and emits structured single-line JSON logs.
 *
 * @param {number} [slowThresholdMs=500] - Latency in ms above which a WARN level is emitted
 * @returns {Function} Koa Middleware function
 */
function createTimingTracerMiddleware(slowThresholdMs = 500) {
  return async (ctx, next) => {
    const startTime = process.hrtime.bigint();
    const requestId = ctx.get('x-request-id') || crypto.randomUUID();

    // Attach to context state and response headers
    ctx.state.requestId = requestId;
    ctx.set('x-request-id', requestId);

    try {
      await next();
    } finally {
      const endTime = process.hrtime.bigint();
      const durationMs = Number(endTime - startTime) / 1e6;
      const roundedDuration = Math.round(durationMs * 100) / 100;

      ctx.set('x-response-time', `${roundedDuration}ms`);

      const logEvent = {
        timestamp: new Date().toISOString(),
        level: roundedDuration > slowThresholdMs ? 'WARN' : 'INFO',
        event: 'http_request_finished',
        requestId,
        method: ctx.method,
        url: ctx.originalUrl,
        statusCode: ctx.status,
        durationMs: roundedDuration,
      };

      // Emit single-line structured JSON (compatible with Winston/Pino)
      process.stdout.write(`${JSON.stringify(logEvent)}\n`);
    }
  };
}

module.exports = {
  createTimingTracerMiddleware,
};
