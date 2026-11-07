/**
 * Universal Application Bootstrap & Lifecycle Orchestrator Template
 * Implements the 13-Step Deterministic Startup Pipeline.
 */

import http from 'node:http';

export interface BootstrapDependencies {
  readonly configService: {
    readonly port: number;
    readonly appEnv: string;
    readonly logLevel: string;
    readonly databaseUrl: string;
    readonly redisUrl: string;
  };
  readonly logger: {
    info(payload: Record<string, unknown>): void;
    warn(payload: Record<string, unknown>): void;
    fatal(payload: Record<string, unknown>): void;
  };
  readonly databasePool: {
    connectWithRetry(maxRetries?: number): Promise<void>;
    close(): Promise<void>;
  };
  readonly cacheClient: {
    connect(): Promise<void>;
    close(): Promise<void>;
  };
  readonly createHttpApp: () => http.RequestListener;
}

/**
 * Registers process-level crash handlers to prevent silent failures.
 */
export function registerProcessCrashHandlers(logger: BootstrapDependencies['logger']): void {
  process.on('unhandledRejection', (reason: unknown) => {
    logger.fatal({
      event: 'process_unhandled_rejection',
      error: reason instanceof Error ? reason.stack : String(reason),
    });
    process.exit(1);
  });

  process.on('uncaughtException', (error: Error) => {
    logger.fatal({
      event: 'process_uncaught_exception',
      error: error.stack,
    });
    process.exit(1);
  });
}

/**
 * Registers pre-listen OS termination handlers for graceful connection draining.
 */
export function registerTerminationHooks(
  server: http.Server,
  dbPool: BootstrapDependencies['databasePool'],
  cache: BootstrapDependencies['cacheClient'],
  logger: BootstrapDependencies['logger']
): void {
  const shutdown = async (signal: string): Promise<void> => {
    logger.info({ event: 'shutdown_signal_received', signal });

    // Stop accepting new incoming requests
    server.close(async (err) => {
      if (err) {
        logger.fatal({ event: 'server_close_error', error: err.message });
      }

      try {
        await cache.close();
        await dbPool.close();
        logger.info({ event: 'graceful_shutdown_complete' });
        process.exit(0);
      } catch (teardownErr) {
        logger.fatal({ event: 'teardown_failure', error: teardownErr });
        process.exit(1);
      }
    });

    // Fallback safety timeout (15s)
    setTimeout(() => {
      logger.fatal({ event: 'shutdown_timeout_exceeded_forced_exit' });
      process.exit(1);
    }, 15000).unref();
  };

  process.on('SIGTERM', () => void shutdown('SIGTERM'));
  process.on('SIGINT', () => void shutdown('SIGINT'));
}

/**
 * Executes the complete 13-step bootstrap sequence.
 */
export async function bootstrapApplication(deps: BootstrapDependencies): Promise<http.Server> {
  // Step 2 & 3: Process crash handlers
  registerProcessCrashHandlers(deps.logger);

  // Step 4 & 5: Pre-flight infrastructure gates with retry
  deps.logger.info({ event: 'connecting_infrastructure' });
  await deps.databasePool.connectWithRetry(3);
  await deps.cacheClient.connect();

  // Step 8, 9, 10: Create HTTP app instance
  const requestHandler = deps.createHttpApp();
  const server = http.createServer(requestHandler);

  // Step 11: Register shutdown hooks BEFORE server.listen
  registerTerminationHooks(server, deps.databasePool, deps.cacheClient, deps.logger);

  // Step 12 & 13: Start network listener & log confirmation
  const { port, appEnv } = deps.configService;
  server.listen(port, '0.0.0.0', () => {
    deps.logger.info({
      event: 'server_ready',
      port,
      environment: appEnv,
      host: '0.0.0.0',
    });
  });

  return server;
}
