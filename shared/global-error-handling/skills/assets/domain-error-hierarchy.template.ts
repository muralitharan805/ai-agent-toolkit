/**
 * Domain Error Hierarchy & Global Error Handler Template
 * Distinguishes between Operational (Expected) and Programmer (Unexpected) Errors.
 */

import { Request, Response, NextFunction } from 'express';

export type ErrorCode =
  | 'VALIDATION_ERROR'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'UNPROCESSABLE_ENTITY'
  | 'RATE_LIMIT_EXCEEDED'
  | 'INTERNAL_SERVER_ERROR'
  | 'SERVICE_UNAVAILABLE';

export interface ValidationErrorDetail {
  readonly field: string;
  readonly message: string;
}

/**
 * Base class for all operational business domain errors.
 */
export abstract class BaseAppError extends Error {
  public readonly isOperational = true;

  constructor(
    public readonly code: ErrorCode,
    public readonly message: string,
    public readonly httpStatus: number,
    public readonly details?: ReadonlyArray<ValidationErrorDetail>
  ) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError extends BaseAppError {
  constructor(message: string, details: ReadonlyArray<ValidationErrorDetail>) {
    super('VALIDATION_ERROR', message, 400, details);
  }
}

export class UnauthorizedError extends BaseAppError {
  constructor(message: string = 'Authentication required') {
    super('UNAUTHORIZED', message, 401);
  }
}

export class ForbiddenError extends BaseAppError {
  constructor(message: string = 'Access denied') {
    super('FORBIDDEN', message, 403);
  }
}

export class NotFoundError extends BaseAppError {
  constructor(entityName: string, identifier: string) {
    super('NOT_FOUND', `${entityName} with identifier '${identifier}' was not found`, 404);
  }
}

export class ConflictError extends BaseAppError {
  constructor(message: string) {
    super('CONFLICT', message, 409);
  }
}

export class InternalServerError extends BaseAppError {
  constructor(message: string = 'Internal server failure') {
    super('INTERNAL_SERVER_ERROR', message, 500);
  }
}

export interface ErrorNotifier {
  sendAlert(payload: {
    correlationId: string;
    errorName: string;
    message: string;
    stack?: string;
    path: string;
  }): Promise<void>;
}

/**
 * Global Terminal Catch-All Error Handling Middleware.
 */
export function createGlobalErrorHandler(notifier?: ErrorNotifier) {
  return (err: Error, req: Request, res: Response, _next: NextFunction): void => {
    const correlationId = (req.headers['x-correlation-id'] as string) || 'unknown';

    // 1. Operational Domain Errors (Handled, Expected, Safe)
    if (err instanceof BaseAppError) {
      console.warn(JSON.stringify({
        level: 'WARN',
        event: 'operational_error',
        correlationId,
        code: err.code,
        message: err.message,
        httpStatus: err.httpStatus,
        path: req.originalUrl,
      }));

      res.status(err.httpStatus).json({
        success: false,
        error: {
          code: err.code,
          message: err.message,
          details: err.details,
        },
        meta: {
          correlationId,
          timestamp: new Date().toISOString(),
          path: req.originalUrl,
        },
      });
      return;
    }

    // 2. Unexpected Programmer Errors (Bugs, Crashes, DB Outages)
    console.error(JSON.stringify({
      level: 'ERROR',
      event: 'unhandled_programmer_error',
      correlationId,
      errorName: err.name,
      message: err.message,
      stack: err.stack,
      path: req.originalUrl,
    }));

    // Trigger On-Call Alerting
    if (notifier) {
      notifier.sendAlert({
        correlationId,
        errorName: err.name,
        message: err.message,
        stack: err.stack,
        path: req.originalUrl,
      }).catch((notifyErr) => {
        console.error('Failed to dispatch on-call alert:', notifyErr);
      });
    }

    // Sanitize response to prevent data leakage
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An unexpected internal error occurred. Engineering has been notified.',
      },
      meta: {
        correlationId,
        timestamp: new Date().toISOString(),
        path: req.originalUrl,
      },
    });
  };
}
