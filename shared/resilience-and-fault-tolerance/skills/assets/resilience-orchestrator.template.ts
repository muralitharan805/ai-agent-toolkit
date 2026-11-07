/**
 * Resilience & Fault Tolerance Production Toolkit
 * Implements:
 * 1. Circuit Breaker (CLOSED, OPEN, HALF-OPEN state machine)
 * 2. Exponential Backoff with Randomized Jitter (Transient errors only)
 * 3. HTTP Idempotency-Key Middleware with Redis Caching
 */

import type { Request, Response, NextFunction } from 'express';

// ============================================================================
// 1. Circuit Breaker Pattern
// ============================================================================

export type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export interface CircuitBreakerConfig {
  readonly failureThreshold: number;
  readonly resetTimeoutMs: number;
}

/**
 * Standard Circuit Breaker implementation for external service protection.
 */
export class CircuitBreaker {
  private state: CircuitState = 'CLOSED';
  private failureCount = 0;
  private lastFailureTime = 0;
  private readonly failureThreshold: number;
  private readonly resetTimeoutMs: number;

  public constructor(config: CircuitBreakerConfig = { failureThreshold: 5, resetTimeoutMs: 30000 }) {
    this.failureThreshold = config.failureThreshold;
    this.resetTimeoutMs = config.resetTimeoutMs;
  }

  public getState(): CircuitState {
    if (this.state === 'OPEN' && Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
      this.state = 'HALF_OPEN';
    }
    return this.state;
  }

  /**
   * Executes a protected asynchronous action through the circuit breaker.
   *
   * @typeParam T - Return type
   * @param action - Workload function to execute
   * @param fallback - Optional fallback function if circuit is open
   * @returns Resolves result of action or fallback
   */
  public async execute<T>(action: () => Promise<T>, fallback?: () => Promise<T>): Promise<T> {
    const currentState = this.getState();

    if (currentState === 'OPEN') {
      if (fallback) return fallback();
      throw new Error('CircuitBreaker: Circuit is OPEN. Request failed fast.');
    }

    try {
      const result = await action();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      if (fallback) return fallback();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  private onFailure(): void {
    this.failureCount += 1;
    this.lastFailureTime = Date.now();
    if (this.failureCount >= this.failureThreshold || this.state === 'HALF_OPEN') {
      this.state = 'OPEN';
    }
  }
}

// ============================================================================
// 2. Exponential Backoff with Jitter for Transient Errors
// ============================================================================

export interface RetryOptions {
  readonly maxAttempts: number;
  readonly baseDelayMs: number;
  readonly maxDelayMs: number;
  readonly isTransient?: (error: unknown) => boolean;
}

/**
 * Evaluates whether an error is transient (5xx, 429, network failure).
 *
 * @param error - Caught exception
 * @returns True if retryable
 */
export function isTransientError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const status = (error as { status?: number; response?: { status?: number } }).status ||
                   (error as { response?: { status?: number } }).response?.status;
    if (status) {
      return status === 429 || status >= 500;
    }
    const code = (error as { code?: string }).code;
    return code === 'ECONNRESET' || code === 'ETIMEDOUT' || code === 'EAI_AGAIN';
  }
  return false;
}

/**
 * Retries an asynchronous operation with exponential backoff and randomized jitter.
 *
 * @typeParam T - Return type
 * @param operation - Workload function to execute
 * @param options - Retry configuration
 * @returns Result of operation
 */
export async function retryWithBackoffAndJitter<T>(
  operation: () => Promise<T>,
  options: RetryOptions = { maxAttempts: 3, baseDelayMs: 1000, maxDelayMs: 10000 }
): Promise<T> {
  const isTransient = options.isTransient || isTransientError;

  for (let attempt = 0; attempt < options.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (!isTransient(error) || attempt === options.maxAttempts - 1) {
        throw error;
      }
      const exponentialDelay = Math.min(options.baseDelayMs * Math.pow(2, attempt), options.maxDelayMs);
      const jitter = (Math.random() - 0.5) * (exponentialDelay * 0.2); // 20% jitter
      const delay = Math.max(0, Math.round(exponentialDelay + jitter));
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw new Error('Retry attempts unexpectedly exhausted without error throw');
}

// ============================================================================
// 3. HTTP Idempotency-Key Middleware
// ============================================================================

export interface IdempotencyStore {
  get(key: string): Promise<string | null>;
  set(key: string, value: string, mode: string, ttlSeconds: number): Promise<unknown>;
}

/**
 * Creates Express middleware to enforce and handle Idempotency-Key on mutating routes.
 *
 * @param store - Key-value store (e.g. Redis adapter)
 * @returns Express Middleware
 */
export function createIdempotencyMiddleware(store: IdempotencyStore) {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    const key = req.headers['idempotency-key'] as string | undefined;
    if (!key) {
      return next();
    }

    const cacheKey = `idempotency:${key}`;

    try {
      const cached = await store.get(cacheKey);
      if (cached) {
        const record = JSON.parse(cached) as { status: string; statusCode: number; body: unknown };
        if (record.status === 'IN_PROGRESS') {
          res.status(409).json({ message: 'Request currently being processed' });
          return;
        }
        res.status(record.statusCode).json(record.body);
        return;
      }

      // Mark in-progress with a 60-second lock
      await store.set(cacheKey, JSON.stringify({ status: 'IN_PROGRESS' }), 'EX', 60);

      const originalJson = res.json.bind(res);
      res.json = (body: unknown) => {
        void store.set(
          cacheKey,
          JSON.stringify({ status: 'COMPLETED', statusCode: res.statusCode, body }),
          'EX',
          86400 // 24 hours
        );
        return originalJson(body);
      };

      next();
    } catch {
      next();
    }
  };
}
