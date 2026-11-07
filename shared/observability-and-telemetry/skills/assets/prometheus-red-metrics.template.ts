/**
 * Observability & Telemetry Production Toolkit
 * Implements the 3 Pillars of Observability:
 * 1. Structured JSON Logger with Correlation ID & Recursive PII Masking
 * 2. Prometheus RED Metrics Middleware with Cardinality Protection
 * 3. OpenTelemetry Distributed Tracing Helper
 */

import client from 'prom-client';
import type { Request, Response, NextFunction } from 'express';
import { trace, SpanStatusCode, Tracer, Span } from '@opentelemetry/api';

// ============================================================================
// Pillar 1: Structured JSON Logger & PII Redaction
// ============================================================================

/**
 * Standard log levels supported by the telemetry subsystem.
 */
export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';

/**
 * Baseline structured JSON log payload schema.
 */
export interface StructuredLogPayload {
  readonly timestamp: string;
  readonly level: LogLevel;
  readonly service: string;
  readonly correlationId: string;
  readonly message: string;
  readonly durationMs?: number;
  readonly event?: string;
  readonly context?: Record<string, unknown>;
  readonly error?: {
    readonly name: string;
    readonly message: string;
    readonly stack?: string;
  };
}

const SENSITIVE_KEY_NAMES = new Set([
  'password',
  'token',
  'refreshtoken',
  'accesstoken',
  'authorization',
  'creditcard',
  'cardnumber',
  'cvv',
  'ssn',
  'secret',
  'apikey',
  'privatekey',
]);

/**
 * Recursively sanitizes data payloads, replacing sensitive credentials and PII with [REDACTED].
 *
 * @param payload - Arbitrary data payload to sanitize
 * @param depth - Current recursion depth to prevent stack overflow
 * @returns Sanitized object tree with secrets masked
 */
export function sanitizeLogPayload(payload: unknown, depth = 0): unknown {
  if (depth > 5 || payload === null || typeof payload !== 'object') {
    return payload;
  }

  if (Array.isArray(payload)) {
    return payload.map((item) => sanitizeLogPayload(item, depth + 1));
  }

  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload as Record<string, unknown>)) {
    const normalizedKey = key.toLowerCase().replace(/[-_]/g, '');
    if (SENSITIVE_KEY_NAMES.has(normalizedKey)) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeLogPayload(value, depth + 1);
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
}

/**
 * Production-ready JSON Logger service.
 */
export class TelemetryLogger {
  private readonly serviceName: string;

  /**
   * Initializes the logger with the service identifier.
   *
   * @param serviceName - Application or microservice identifier
   */
  public constructor(serviceName: string) {
    this.serviceName = serviceName;
  }

  /**
   * Emits a single-line serialized JSON log event to stdout.
   *
   * @param level - Log severity level
   * @param message - Human-readable log message
   * @param correlationId - Trace / correlation UUID
   * @param context - Optional sanitized contextual payload
   */
  public log(
    level: LogLevel,
    message: string,
    correlationId: string,
    context?: Record<string, unknown>
  ): void {
    const payload: StructuredLogPayload = {
      timestamp: new Date().toISOString(),
      level,
      service: this.serviceName,
      correlationId,
      message,
      context: context ? (sanitizeLogPayload(context) as Record<string, unknown>) : undefined,
    };

    // Output to stdout as a single-line JSON string for high-throughput collectors
    process.stdout.write(JSON.stringify(payload) + '\n');
  }
}

// ============================================================================
// Pillar 2: Prometheus RED Metrics
// ============================================================================

/**
 * Prometheus registry with default process metrics enabled.
 */
export const prometheusRegistry = new client.Registry();
client.collectDefaultMetrics({ register: prometheusRegistry });

/**
 * Rate (R): Total HTTP requests counter partitioned by method, route template, and status code.
 */
export const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of inbound HTTP requests processed',
  labelNames: ['method', 'route', 'status'] as const,
  registers: [prometheusRegistry],
});

/**
 * Errors (E): Total failure count partitioned by error type and code.
 */
export const errorsTotal = new client.Counter({
  name: 'errors_total',
  help: 'Total number of operational and system errors',
  labelNames: ['type', 'code'] as const,
  registers: [prometheusRegistry],
});

/**
 * Duration (D): HTTP request latency distribution in seconds.
 * Standard buckets covering 10ms to 10s for p50, p90, p99 evaluation.
 */
export const httpRequestDurationSeconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration distribution in seconds',
  labelNames: ['method', 'route'] as const,
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [prometheusRegistry],
});

/**
 * Express middleware that records Prometheus RED metrics with cardinality protection.
 *
 * @param req - Express HTTP request
 * @param res - Express HTTP response
 * @param next - Express next middleware function
 */
export function redMetricsMiddleware(req: Request, res: Response, next: NextFunction): void {
  const startHrTime = process.hrtime();

  res.on('finish', () => {
    const [seconds, nanoseconds] = process.hrtime(startHrTime);
    const durationInSeconds = seconds + nanoseconds / 1e9;

    // Use parameterized route template to strictly avoid cardinality explosion
    const routeTemplate = (req.route?.path as string) || req.baseUrl || 'unmatched';

    httpRequestsTotal.inc({
      method: req.method,
      route: routeTemplate,
      status: res.statusCode.toString(),
    });

    httpRequestDurationSeconds.observe(
      {
        method: req.method,
        route: routeTemplate,
      },
      durationInSeconds
    );
  });

  next();
}

/**
 * Express handler serving standard Prometheus metrics format at /metrics.
 *
 * @param _req - Express HTTP request
 * @param res - Express HTTP response
 */
export async function prometheusMetricsHandler(_req: Request, res: Response): Promise<void> {
  res.setHeader('Content-Type', prometheusRegistry.contentType);
  const metrics = await prometheusRegistry.metrics();
  res.send(metrics);
}

// ============================================================================
// Pillar 3: OpenTelemetry Distributed Tracing Helper
// ============================================================================

/**
 * Distributed tracing helper wrapping operations in OpenTelemetry spans.
 */
export class DistributedTracer {
  private readonly tracer: Tracer;

  /**
   * Initializes the tracer instance.
   *
   * @param serviceName - Logical service name
   */
  public constructor(serviceName: string) {
    this.tracer = trace.getTracer(serviceName);
  }

  /**
   * Executes an asynchronous operation inside a named OpenTelemetry active span.
   *
   * @typeParam T - Return type of the traced asynchronous operation
   * @param spanName - Human-readable span name (e.g. 'db.query.findUser')
   * @param operation - Workload function to execute within the span
   * @returns Result of the operation
   */
  public async traceSpan<T>(
    spanName: string,
    operation: (span: Span) => Promise<T>
  ): Promise<T> {
    return this.tracer.startActiveSpan(spanName, async (span) => {
      try {
        const result = await operation(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.recordException(error as Error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: (error as Error).message,
        });
        throw error;
      } finally {
        span.end();
      }
    });
  }
}
