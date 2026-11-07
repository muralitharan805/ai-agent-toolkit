/**
 * Production Database Connection Pool & Persistence Template
 * Implements hardened connection pooling, audit column standards,
 * and slow query telemetry logging.
 */

export interface DatabasePoolConfig {
  readonly host: string;
  readonly port: number;
  readonly database: string;
  readonly user: string;
  readonly password?: string;
  readonly ssl: boolean;
  readonly pool: {
    readonly min: number;
    readonly max: number;
    readonly acquireTimeoutMs: number;
    readonly idleTimeoutMs: number;
    readonly connectionTimeoutMs: number;
    readonly queryTimeoutMs: number;
  };
}

/**
 * Standard audit and lifecycle properties required on all business database entities.
 */
export interface AuditedEntityRecord {
  /**
   * Primary key identifier (UUIDv7 recommended for B-tree index preservation).
   */
  readonly id: string;

  /**
   * Record creation timestamp in UTC.
   */
  readonly createdAt: Date;

  /**
   * Record last updated timestamp in UTC.
   */
  readonly updatedAt: Date;

  /**
   * Soft-delete timestamp. NULL indicates an active record; non-NULL indicates soft-deletion.
   */
  readonly deletedAt: Date | null;

  /**
   * User or service account UUID that created the record.
   */
  readonly createdBy: string | null;

  /**
   * User or service account UUID that last modified the record.
   */
  readonly updatedBy: string | null;
}

/**
 * Creates a production-hardened database pool configuration with defensive defaults.
 *
 * @param env - Environment variables dictionary
 * @returns Validated DatabasePoolConfig object
 */
export function createDatabasePoolConfig(
  env: Record<string, string | undefined> = process.env
): DatabasePoolConfig {
  const isProduction = env.NODE_ENV === 'production';

  return {
    host: env.DB_HOST || '127.0.0.1',
    port: Number(env.DB_PORT) || 5432,
    database: env.DB_NAME || 'application_db',
    user: env.DB_USER || 'postgres',
    password: env.DB_PASSWORD,
    ssl: isProduction,
    pool: {
      min: 2, // Keep warm connections
      max: 10, // Prevent DB overload
      acquireTimeoutMs: 30000, // 30s fail fast if pool is exhausted
      idleTimeoutMs: 600000, // 10m release idle connections
      connectionTimeoutMs: 5000, // 5s initial connect fail fast
      queryTimeoutMs: 30000, // 30s kill runaway queries
    },
  };
}

/**
 * Slow query logger interceptor. Logs a structured WARN event for any query exceeding 200ms.
 *
 * @param queryText - Parameterized SQL query string (secrets must not be interpolated)
 * @param durationMs - Total query execution duration in milliseconds
 * @param correlationId - Active request tracing correlation ID
 */
export function recordDatabaseQueryTelemetry(
  queryText: string,
  durationMs: number,
  correlationId?: string
): void {
  const SLOW_QUERY_THRESHOLD_MS = 200;

  if (durationMs >= SLOW_QUERY_THRESHOLD_MS) {
    const logEvent = {
      timestamp: new Date().toISOString(),
      level: 'WARN',
      event: 'database.slow_query',
      correlationId: correlationId || 'unknown',
      durationMs,
      thresholdMs: SLOW_QUERY_THRESHOLD_MS,
      query: queryText,
      message: `Database query exceeded slow query threshold: ${durationMs}ms`,
    };

    process.stdout.write(JSON.stringify(logEvent) + '\n');
  }
}
