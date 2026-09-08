/**
 * @file setup-database.js
 * @description Centralized database test lifecycle harness for Sequelize + MySQL in JavaScript.
 * Provides connection pooling, schema synchronization, and deterministic table truncation.
 */

const { Sequelize } = require('sequelize');

/**
 * Global test Sequelize instance targeting the isolated test database.
 */
const testSequelize = new Sequelize(
  process.env.TEST_DB_NAME || 'koa_app_test',
  process.env.TEST_DB_USER || 'root',
  process.env.TEST_DB_PASSWORD || 'secret',
  {
    host: process.env.TEST_DB_HOST || '127.0.0.1',
    port: Number(process.env.TEST_DB_PORT) || 3306,
    dialect: 'mysql',
    logging: false, // Suppress standard query output during tests
    pool: {
      max: 5,
      min: 0,
      acquire: 10000,
      idle: 1000,
    },
  }
);

/**
 * Connects and synchronizes test database schema before test execution.
 * @returns {Promise<void>}
 */
async function initializeTestDatabase() {
  await testSequelize.authenticate();
  await testSequelize.sync({ force: false });
}

/**
 * Truncates all registered model tables in reverse dependency order.
 * Ensures zero cross-test data pollution without dropping schemas.
 * @returns {Promise<void>}
 */
async function truncateTestDatabase() {
  await testSequelize.query('SET FOREIGN_KEY_CHECKS = 0;');
  const models = Object.values(testSequelize.models);
  for (const model of models) {
    await model.destroy({ truncate: true, cascade: true, force: true });
  }
  await testSequelize.query('SET FOREIGN_KEY_CHECKS = 1;');
}

/**
 * Closes the database connection pool gracefully after all tests complete.
 * @returns {Promise<void>}
 */
async function closeTestDatabase() {
  await testSequelize.close();
}

module.exports = {
  testSequelize,
  initializeTestDatabase,
  truncateTestDatabase,
  closeTestDatabase,
};
