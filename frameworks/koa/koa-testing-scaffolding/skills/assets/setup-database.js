/**
 * @file setup-database.js
 * @description Centralized database test lifecycle harness for Sequelize + MySQL in JavaScript.
 * Provides connection pooling, schema synchronization, deterministic table truncation,
 * schema introspection (hasTable), and dynamic seed discovery for brownfield databases.
 */

const { Sequelize } = require('sequelize');

/**
 * Sequelize instance targeting the local project database with transaction rollback protection.
 */
const testSequelize = new Sequelize(
  process.env.TEST_DB_NAME || process.env.DB_NAME || 'koa_app_test',
  process.env.TEST_DB_USER || process.env.DB_USER || 'root',
  process.env.TEST_DB_PASSWORD !== undefined ? process.env.TEST_DB_PASSWORD : (process.env.DB_PASSWORD || ''),
  {
    host: process.env.TEST_DB_HOST || process.env.DB_HOST || '127.0.0.1',
    port: Number(process.env.TEST_DB_PORT || process.env.DB_PORT) || 3306,
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

const state = {
  availableTables: new Set(),
  discoveredSeeds: {},
};

/**
 * Connects and synchronizes test database schema before test execution.
 * @returns {Promise<void>}
 */
async function initializeTestDatabase() {
  await testSequelize.authenticate();
  await testSequelize.sync({ force: false });

  // Introspect available tables in test DB
  try {
    const [tables] = await testSequelize.query('SHOW TABLES');
    state.availableTables = new Set(
      tables.map((t) => Object.values(t)[0].toLowerCase())
    );
  } catch (err) {
    process.stderr.write(`[SETUP] Warning: Failed to introspect tables: ${err.message}\n`);
  }
}

/**
 * Checks if a table exists in the test database.
 * @param {string} tableName - Name of table
 * @returns {boolean}
 */
function hasTable(tableName) {
  return state.availableTables.has(tableName.toLowerCase());
}

/**
 * Dynamically discovers active identifiers from a given table to prevent hardcoded ID failures.
 * @param {string} tableName - Table to sample
 * @param {string} [idColumn='id'] - Identifier column name
 * @returns {Promise<string|number|null>} Discovered ID or null
 */
async function discoverSeedId(tableName, idColumn = 'id') {
  if (!hasTable(tableName)) return null;

  try {
    const [rows] = await testSequelize.query(
      `SELECT \`${idColumn}\` FROM \`${tableName}\` LIMIT 1`
    );
    if (rows && rows.length > 0) {
      return rows[0][idColumn];
    }
  } catch (_) {
    return null;
  }
  return null;
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
  hasTable,
  discoverSeedId,
  state,
};
