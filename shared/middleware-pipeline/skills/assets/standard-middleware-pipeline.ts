/**
 * Standard HTTP Middleware Pipeline & Server Hardening Template
 * Implements the 15-Step Deterministic Middleware Order & ALB Keep-Alive Tuning.
 */

import http from 'node:http';
import express, { Express, Request, Response, NextFunction } from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';

export interface PipelineConfig {
  readonly port: number;
  readonly allowedOrigins: string[];
  readonly trustProxy: boolean;
  readonly maxBodySizeBytes: string; // e.g. '1mb'
}

/**
 * Attaches the complete 15-step middleware sequence to an Express app.
 */
export function configureServerPipeline(app: Express, config: PipelineConfig, apiV1Router: express.Router): void {
  // [1] Correlation ID Injection
  app.use((req: Request, res: Response, next: NextFunction) => {
    const correlationId = (req.headers['x-correlation-id'] as string) || crypto.randomUUID();
    req.headers['x-correlation-id'] = correlationId;
    res.setHeader('X-Correlation-ID', correlationId);
    next();
  });

  // [2] Real IP Resolution & Proxy Trust
  if (config.trustProxy) {
    app.set('trust proxy', true);
  }

  // [3] Structured Request Logger (Inbound)
  app.use((req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    res.on('finish', () => {
      const durationMs = Date.now() - startTime;
      console.log(JSON.stringify({
        level: 'INFO',
        timestamp: new Date().toISOString(),
        correlationId: req.headers['x-correlation-id'],
        method: req.method,
        path: req.originalUrl,
        statusCode: res.statusCode,
        clientIp: req.ip,
        durationMs,
      }));
    });
    next();
  });

  // [4] Security Headers (Helmet)
  app.use(helmet({
    contentSecurityPolicy: true,
    strictTransportSecurity: { maxAge: 31536000, includeSubDomains: true },
    xFrameOptions: { action: 'deny' },
  }));

  // [5] CORS Whitelist Check
  app.use(cors({
    origin: config.allowedOrigins,
    credentials: true,
  }));

  // [6] Response Compression (Responses > 1KB)
  app.use(compression({ threshold: 1024 }));

  // [7 & 8] Body Parsers & Request Size Limiters
  app.use(express.json({ limit: config.maxBodySizeBytes }));
  app.use(express.urlencoded({ extended: true, limit: config.maxBodySizeBytes }));

  // [9] Rate Limiter Placeholder (Token bucket per Real IP + User)
  // [10 - 13] Versioned API Router (Mounted at /api/v1)
  app.use('/api/v1', apiV1Router);

  // [14 & 15] Terminal Global Error Handler (MUST BE THE FINAL MIDDLEWARE)
  app.use((err: Error, req: Request, res: Response, _next: NextFunction) => {
    const correlationId = req.headers['x-correlation-id'] || 'unknown';
    console.error(JSON.stringify({
      level: 'ERROR',
      timestamp: new Date().toISOString(),
      correlationId,
      errorName: err.name,
      message: err.message,
      stack: err.stack,
    }));

    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An unexpected error occurred',
        correlationId,
        timestamp: new Date().toISOString(),
      },
    });
  });
}

/**
 * Creates and hardens the HTTP server with keep-alive and network timeouts.
 */
export function createHardenedHttpServer(app: Express): http.Server {
  const server = http.createServer(app);

  // Eliminate ALB / Cloudflare 502 Bad Gateway race conditions
  server.keepAliveTimeout = 65000;  // 65s (> ALB 60s idle timeout)
  server.headersTimeout = 66000;    // Must strictly exceed keepAliveTimeout
  server.requestTimeout = 30000;    // 30s read timeout (Slowloris protection)

  return server;
}
