/**
 * @file sequelize-profiler-hook.js
 * @description Sequelize query execution duration profiler and slow query detector in JavaScript.
 * Captures query timing in milliseconds, alerts on slow queries (> 200ms), and formats single-line JSON logs.
 */

/**
 * Attaches benchmark query profiling to a Sequelize configuration object.
 *
 * @param {Object} baseOptions - Existing Sequelize connection options
 * @param {number} [slowQueryThresholdMs=200] - Execution duration in ms to classify as slow
 * @returns {Object} Updated Sequelize Options with benchmark and logging enabled
 */
function configureSequelizeProfiler(baseOptions, slowQueryThresholdMs = 200) {
  return {
    ...baseOptions,
    benchmark: true,
    logging: (sql, timingMs) => {
      const duration = timingMs || 0;
      if (duration > slowQueryThresholdMs) {
        const logEvent = {
          timestamp: new Date().toISOString(),
          level: 'WARN',
          event: 'slow_database_query',
          durationMs: duration,
          query: sql.length > 1000 ? `${sql.substring(0, 1000)}... [TRUNCATED]` : sql,
        };

        process.stderr.write(`${JSON.stringify(logEvent)}\n`);
      }
    },
  };
}

module.exports = {
  configureSequelizeProfiler,
};
