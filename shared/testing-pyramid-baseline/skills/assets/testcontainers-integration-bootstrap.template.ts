/**
 * Production Testcontainers Integration Harness & Rollback Isolation Asset.
 *
 * Provides a managed singleton lifecycle for ephemeral PostgreSQL and Redis containers,
 * automated migration execution, and transaction rollback isolation for integration tests.
 */

import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer, StartedRedisContainer } from '@testcontainers/redis';
import { Pool, PoolClient } from 'pg';

/**
 * Singleton manager coordinating Testcontainers lifecycles across test suites.
 */
export class TestcontainersManager {
  private static postgresContainer: StartedPostgreSqlContainer | null = null;
  private static redisContainer: StartedRedisContainer | null = null;
  private static pool: Pool | null = null;

  /**
   * Initializes ephemeral PostgreSQL and Redis test containers.
   *
   * @returns Dynamic connection configuration for database and cache
   */
  public static async start(): Promise<{ databaseUrl: string; redisUrl: string }> {
    if (!this.postgresContainer) {
      this.postgresContainer = await new PostgreSqlContainer('postgres:16-alpine')
        .withDatabase('test_db')
        .withUsername('test_user')
        .withPassword('test_password')
        .start();

      this.pool = new Pool({
        connectionString: this.postgresContainer.getConnectionUri(),
        max: 10,
        idleTimeoutMillis: 1000,
      });

      // Run database migrations before executing tests
      await this.runMigrations(this.pool);
    }

    if (!this.redisContainer) {
      this.redisContainer = await new RedisContainer('redis:7-alpine').start();
    }

    return {
      databaseUrl: this.postgresContainer.getConnectionUri(),
      redisUrl: this.redisContainer.getConnectionUrl(),
    };
  }

  /**
   * Provides the shared connection pool connected to the Testcontainers PostgreSQL instance.
   *
   * @returns Active PostgreSQL connection pool
   * @throws {Error} When TestcontainersManager has not been initialized
   */
  public static getPool(): Pool {
    if (!this.pool) {
      throw new Error('TestcontainersManager has not been started. Call start() in beforeAll.');
    }
    return this.pool;
  }

  /**
   * Stops containers and drains connection pools on test suite completion.
   */
  public static async stop(): Promise<void> {
    if (this.pool) {
      await this.pool.end();
      this.pool = null;
    }
    if (this.postgresContainer) {
      await this.postgresContainer.stop();
      this.postgresContainer = null;
    }
    if (this.redisContainer) {
      await this.redisContainer.stop();
      this.redisContainer = null;
    }
  }

  /**
   * Executes database migrations against the container database.
   *
   * @param pool - PostgreSQL connection pool
   */
  private static async runMigrations(pool: Pool): Promise<void> {
    const client = await pool.connect();
    try {
      await client.query(`
        CREATE TABLE IF NOT EXISTS orders (
          id VARCHAR(64) PRIMARY KEY,
          customer_id VARCHAR(64) NOT NULL,
          total_amount_cents INTEGER NOT NULL,
          status VARCHAR(32) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
      `);
    } finally {
      client.release();
    }
  }
}

/**
 * Executes a test block within an isolated transaction that unconditionally rolls back.
 * Guarantees zero side-effects and prevents test cross-pollution.
 *
 * @param pool - PostgreSQL connection pool
 * @param testFn - Test callback receiving an active client in a transaction
 */
export async function withRollbackTransaction(
  pool: Pool,
  testFn: (client: PoolClient) => Promise<void>
): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await testFn(client);
  } finally {
    await client.query('ROLLBACK');
    client.release();
  }
}

/**
 * k6 Performance Test Baseline Script Template.
 * Demonstrates SLA enforcement: p50 < 50ms, p95 < 200ms, p99 < 500ms, error rate < 0.1%.
 */
export const k6PerformanceTemplate = `
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },  // Ramp-up to 50 virtual users
    { duration: '1m', target: 50 },   // Steady load
    { duration: '15s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    'http_req_duration{status:200}': ['p(50)<50', 'p(95)<200', 'p(99)<500'],
    'http_req_failed': ['rate<0.001'],
  },
};

export default function () {
  const res = http.get(__ENV.BASE_URL + '/api/v1/health/ready');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
`;
