/**
 * Production-Grade 11-Step Graceful Shutdown Orchestrator Asset.
 *
 * Implements deterministic signal trapping (SIGTERM/SIGINT), readiness probe
 * invalidation (HTTP 503), in-flight connection draining, queue consumer pause,
 * telemetry buffer flushing, and database/cache pool teardown.
 */

import { Server } from 'http';

/**
 * Disposable resource interface representing connections requiring clean teardown.
 */
export interface DisposableResource {
  readonly name: string;
  close(): Promise<void>;
}

/**
 * Logger interface required by the shutdown coordinator.
 */
export interface ShutdownLogger {
  info(payload: Record<string, unknown>): void;
  error(payload: Record<string, unknown>): void;
  flushSync?(): void;
}

/**
 * Configuration options for the graceful shutdown coordinator.
 */
export interface ShutdownOptions {
  /**
   * Internal grace period timeout in milliseconds before forcing process exit.
   * MUST be strictly less than the orchestrator timeout (e.g. 25000ms for K8s 30s).
   */
  readonly graceTimeoutMs?: number;

  /**
   * Load balancer propagation sleep delay in milliseconds before closing HTTP socket.
   */
  readonly lbPropagationDelayMs?: number;
}

/**
 * Coordinates the deterministic 11-step graceful shutdown lifecycle.
 */
export class GracefulShutdownCoordinator {
  private isShuttingDown = false;
  private readonly graceTimeoutMs: number;
  private readonly lbPropagationDelayMs: number;
  private readonly resources: DisposableResource[] = [];

  /**
   * Initializes the graceful shutdown coordinator.
   *
   * @param server - Active HTTP server instance
   * @param logger - Structured logger instance
   * @param options - Custom timeout and delay configuration
   */
  constructor(
    private readonly server: Server,
    private readonly logger: ShutdownLogger,
    options?: ShutdownOptions
  ) {
    this.graceTimeoutMs = options?.graceTimeoutMs ?? 25000;
    this.lbPropagationDelayMs = options?.lbPropagationDelayMs ?? 3000;
  }

  /**
   * Registers a disposable dependency (e.g. DB pool, Redis client, RabbitMQ channel).
   *
   * @param resource - Disposable resource to close during shutdown
   */
  public registerResource(resource: DisposableResource): void {
    this.resources.push(resource);
  }

  /**
   * Binds process signal listeners for POSIX SIGTERM and SIGINT termination.
   */
  public bindSignalHandlers(): void {
    const onSignal = (signal: NodeJS.Signals): void => {
      if (this.isShuttingDown) {
        this.logger.info({ msg: 'Termination signal received again, shutdown already in progress' });
        return;
      }
      this.isShuttingDown = true;
      this.executeShutdown(signal).catch((err: unknown) => {
        this.logger.error({ msg: 'Fatal unhandled exception during shutdown sequence', error: err });
        process.exit(1);
      });
    };

    process.on('SIGTERM', () => onSignal('SIGTERM'));
    process.on('SIGINT', () => onSignal('SIGINT'));
  }

  /**
   * Returns whether the application is currently healthy and accepting new traffic.
   * Used directly by the /health/ready probe handler.
   *
   * @returns True if active and healthy; false if draining/shutting down
   */
  public isReady(): boolean {
    return !this.isShuttingDown;
  }

  /**
   * Executes the 11-step shutdown sequence sequentially.
   *
   * @param signal - Caught operating system signal name
   */
  private async executeShutdown(signal: string): Promise<void> {
    const startTimeMs = Date.now();
    this.logger.info({
      event: 'shutdown_initiated',
      signal,
      graceTimeoutMs: this.graceTimeoutMs,
      lbDelayMs: this.lbPropagationDelayMs,
    });

    // Enforce hard ceiling timeout timer
    const forceExitTimer = setTimeout(() => {
      this.logger.error({
        event: 'shutdown_grace_period_expired',
        msg: 'Grace timeout reached. Forcing immediate process termination.',
      });
      process.exit(1);
    }, this.graceTimeoutMs);

    try {
      // Step 1 & 2: Readiness invalidated (isReady returns false) -> Wait for LB propagation
      this.logger.info({ msg: 'Waiting for load balancer routing table propagation...' });
      await new Promise((resolve) => setTimeout(resolve, this.lbPropagationDelayMs));

      // Step 3 & 4: Stop accepting new connections & drain in-flight requests
      this.logger.info({ msg: 'Closing HTTP server socket and draining in-flight requests...' });
      await new Promise<void>((resolve, reject) => {
        this.server.close((err) => (err ? reject(err) : resolve()));
      });

      // Step 5 to 10: Close all registered infrastructure resources (DB, Redis, Queues)
      for (const resource of this.resources) {
        this.logger.info({ msg: `Closing resource: ${resource.name}` });
        try {
          await resource.close();
        } catch (resErr) {
          this.logger.error({ msg: `Failed to cleanly close resource: ${resource.name}`, error: resErr });
        }
      }

      // Flush structured log buffer
      if (this.logger.flushSync) {
        this.logger.flushSync();
      }

      clearTimeout(forceExitTimer);
      const uptimeSec = Math.floor(process.uptime());
      this.logger.info({
        event: 'shutdown_complete',
        uptimeSeconds: uptimeSec,
        totalShutdownDurationMs: Date.now() - startTimeMs,
      });

      // Step 11: Clean exit
      process.exit(0);
    } catch (error: unknown) {
      clearTimeout(forceExitTimer);
      this.logger.error({ event: 'shutdown_failed', error });
      process.exit(1);
    }
  }
}
