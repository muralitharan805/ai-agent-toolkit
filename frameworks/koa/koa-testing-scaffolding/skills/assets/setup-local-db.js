/**
 * @file setup-local-db.js
 * @description Zero-Docker local MySQL test database provisioner.
 * Connects to your existing local MySQL server and ensures the test database
 * exists with the appropriate character set and collation.
 *
 * Usage: node tests/setup/setup-local-db.js
 */

const mysql = require('mysql2/promise');

const config = {
  host: process.env.TEST_DB_HOST || '127.0.0.1',
  port: Number(process.env.TEST_DB_PORT) || 3306,
  user: process.env.TEST_DB_USER || 'root',
  password: process.env.TEST_DB_PASSWORD || '',
  databaseName: process.env.TEST_DB_NAME || 'koa_app_test',
};

async function ensureLocalTestDatabase() {
  process.stdout.write(`[Local DB Setup] Connecting to MySQL at ${config.host}:${config.port} as '${config.user}'...\n`);

  let connection;
  try {
    // Connect without database selected to run CREATE DATABASE
    connection = await mysql.createConnection({
      host: config.host,
      port: config.port,
      user: config.user,
      password: config.password,
    });

    const createSql = `CREATE DATABASE IF NOT EXISTS \`${config.databaseName}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`;
    await connection.query(createSql);

    process.stdout.write(`✅ [Local DB Setup] Database '${config.databaseName}' is ready for testing!\n`);
    process.stdout.write(`   Connection URI: mysql://${config.user}@${config.host}:${config.port}/${config.databaseName}\n`);
  } catch (error) {
    process.stderr.write(`❌ [Local DB Setup] Failed to setup test database: ${error.message}\n`);
    process.stderr.write(`   Tip: Ensure local MySQL service is running: 'sudo systemctl status mysql'\n`);
    process.exit(1);
  } finally {
    if (connection) {
      await connection.end();
    }
  }
}

ensureLocalTestDatabase();
