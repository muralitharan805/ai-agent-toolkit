/**
 * Health Check Probes & Orchestration Service Template
 * Implements Kubernetes & Load Balancer probe endpoints:
 * - GET /live (Liveness: pure process check, zero external I/O)
 * - GET /ready (Readiness: dependency checks, 503 on failure)
 * - GET /startup (Startup: warmup check)
 * - GET /health/details (Diagnostic: internal-only IP-restricted)
 */

import type { Request, Response, Router } from 'express';

/**
 * Status indicator for individual health checks.
 */
export type DependencyHealthStatus = 'healthy' | 'unhealthy' | 'degraded';

/**
 * Individual dependency check result.
 */
export interface DependencyCheckResult {
  readonly status: DependencyHealthStatus;
  readonly responseTimeMs: number;
  readonly error?: string;
}

/**
 * Comprehensive diagnostic response schema.
 */
export interface DetailedHealthResponse {
  readonly status: 'healthy' | 'unhealthy' | 'degraded';
  readonly timestamp: string;
  readonly version: string;
  readonly uptimeSeconds: number;
  readonly checks: Record<string, DependencyCheckResult>;
}

/**
 * Interface defining dependency ping probes.
 */
export interface HealthProbeProvider {
  /**
   * Pings the primary database within the given timeout.
   *
   * @param timeoutMs - Maximum execution timeout in milliseconds
   * @returns Resolves true if healthy, false if timeout or error
   */
  pingDatabase(timeoutMs: number): Promise<boolean>;

  /**
   * Pings the cache layer within the given timeout.
   *
   * @param timeoutMs - Maximum execution timeout in milliseconds
   * @returns Resolves true if healthy, false if timeout or error
   */
  pingCache(timeoutMs: number): Promise<boolean>;
}

/**
 * Coordinates and serves container orchestration health check probes.
 */
export class HealthCheckOrchestrator {
  private readonly version: string;
  private readonly probeProvider: HealthProbeProvider;
  private isWarmupComplete = false;
  private isDraining = false;

  /**
   * Initializes the health check orchestrator.
   *
   * @param version - Application semantic version string
   * @param probeProvider - Backing dependency health ping provider
   */
  public constructor(version: string, probeProvider: HealthProbeProvider) {
    this.version = version;
    this.probeProvider = probeProvider;
  }

  /**
   * Signals that application warmup routines (caching, migrations) are finished.
   */
  public markStartupComplete(): void {
    this.isWarmupComplete = true;
  }

  /**
   * Signals that the server is shutting down and draining connections.
   */
  public markDraining(): void {
    this.isDraining = true;
  }

  /**
   * Handles GET /live (Liveness Probe).
   * Verifies process event loop responsiveness ONLY. Never performs external I/O.
   *
   * @param _req - Express request
   * @param res - Express response
   */
  public handleLiveness(_req: Request, res: Response): void {
    // If the process can execute this line, the event loop is alive
    res.status(200).json({
      status: 'alive',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Handles GET /ready (Readiness Probe).
   * Verifies critical dependencies and draining status. Returns 503 on degradation.
   *
   * @param _req - Express request
   * @param res - Express response
   */
  public async handleReadiness(_req: Request, res: Response): Promise<void> {
    if (this.isDraining) {
      res.status(503).json({
        status: 'draining',
        message: 'Server process is shutting down',
      });
      return;
    }

    const [dbHealthy, cacheHealthy] = await Promise.all([
      this.probeProvider.pingDatabase(1000).catch(() => false),
      this.probeProvider.pingCache(500).catch(() => false),
    ]);

    if (dbHealthy && cacheHealthy) {
      res.status(200).json({ status: 'ready' });
      return;
    }

    // Return 503 to detach replica from active traffic routing
    res.status(503).json({
      status: 'not_ready',
      dependencies: {
        database: dbHealthy ? 'up' : 'down',
        cache: cacheHealthy ? 'up' : 'down',
      },
    });
  }

  /**
   * Handles GET /startup (Startup Probe).
   * Prevents liveness kills during cold startup.
   *
   * @param _req - Express request
   * @param res - Express response
   */
  public handleStartup(_req: Request, res: Response): void {
    if (this.isWarmupComplete) {
      res.status(200).json({ status: 'started' });
    } else {
      res.status(503).json({ status: 'starting' });
    }
  }

  /**
   * Handles GET /health/details (Diagnostic Telemetry).
   * Deep component latency report. Protected by IP whitelist or internal network.
   *
   * @param req - Express request
   * @param res - Express response
   */
  public async handleDiagnosticDetails(req: Request, res: Response): Promise<void> {
    const startDb = Date.now();
    const dbHealthy = await this.probeProvider.pingDatabase(1000).catch(() => false);
    const dbDuration = Date.now() - startDb;

    const startCache = Date.now();
    const cacheHealthy = await this.probeProvider.pingCache(500).catch(() => false);
    const cacheDuration = Date.now() - startCache;

    const overallHealthy = dbHealthy && cacheHealthy;
    const responsePayload: DetailedHealthResponse = {
      status: overallHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      version: this.version,
      uptimeSeconds: Math.floor(process.uptime()),
      checks: {
        database: {
          status: dbHealthy ? 'healthy' : 'unhealthy',
          responseTimeMs: dbDuration,
        },
        cache: {
          status: cacheHealthy ? 'healthy' : 'unhealthy',
          responseTimeMs: cacheDuration,
        },
      },
    };

    res.status(overallHealthy ? 200 : 503).json(responsePayload);
  }

  /**
   * Binds health probe routes to an Express router.
   *
   * @param router - Express Router instance
   */
  public registerRoutes(router: Router): void {
    router.get('/live', (req, res) => this.handleLiveness(req, res));
    router.get('/ready', (req, res) => {
      void this.handleReadiness(req, res);
    });
    router.get('/startup', (req, res) => this.handleStartup(req, res));
    router.get('/health/details', (req, res) => {
      void this.handleDiagnosticDetails(req, res);
    });
  }
}
