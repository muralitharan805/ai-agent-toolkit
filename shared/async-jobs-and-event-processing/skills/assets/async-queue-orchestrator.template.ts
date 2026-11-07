/**
 * Asynchronous Background Queue & Worker Template
 * Implements:
 * - Versioned Job Envelope with Idempotency Key
 * - Worker with Exponential Backoff and Full Jitter
 * - Dead Letter Queue (DLQ) routing upon retry exhaustion
 * - Consumer deduplication guard
 */

export interface JobEnvelope<T> {
  readonly version: number;
  readonly jobId: string;
  readonly idempotencyKey: string;
  readonly queueName: string;
  readonly payload: T;
  readonly attempts: number;
  readonly maxAttempts: number;
  readonly createdAt: string;
}

export interface DeduplicationStore {
  /**
   * Checks if an idempotency key has already been executed.
   *
   * @param idempotencyKey - Unique operation identifier
   * @returns Resolves true if already processed
   */
  hasBeenProcessed(idempotencyKey: string): Promise<boolean>;

  /**
   * Marks an idempotency key as successfully executed.
   *
   * @param idempotencyKey - Unique operation identifier
   * @param ttlSeconds - Retention period for the deduplication record
   */
  markAsProcessed(idempotencyKey: string, ttlSeconds: number): Promise<void>;
}

export interface DeadLetterQueueSender {
  /**
   * Dispatches an unrecoverable failed job to the DLQ.
   *
   * @param job - Failed job envelope
   * @param error - Terminal error exception
   */
  sendToDlq<T>(job: JobEnvelope<T>, error: Error): Promise<void>;
}

/**
 * Computes exponential backoff delay with randomized jitter in milliseconds.
 *
 * @param attempt - Zero-based or 1-based attempt index
 * @param baseDelayMs - Initial delay in milliseconds (default: 1000)
 * @param maxDelayMs - Maximum delay ceiling in milliseconds (default: 30000)
 * @returns Randomized backoff duration in milliseconds
 */
export function calculateExponentialBackoffWithJitter(
  attempt: number,
  baseDelayMs = 1000,
  maxDelayMs = 30000
): number {
  const exponentialDelay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
  // Full jitter: random between 0 and exponentialDelay
  return Math.floor(Math.random() * exponentialDelay);
}

/**
 * Base abstract class for resilient background job consumers.
 */
export abstract class BaseJobConsumer<T> {
  protected readonly queueName: string;
  protected readonly dedupStore: DeduplicationStore;
  protected readonly dlqSender: DeadLetterQueueSender;

  public constructor(
    queueName: string,
    dedupStore: DeduplicationStore,
    dlqSender: DeadLetterQueueSender
  ) {
    this.queueName = queueName;
    this.dedupStore = dedupStore;
    this.dlqSender = dlqSender;
  }

  /**
   * Executes the business workload for this job.
   *
   * @param payload - Strongly-typed job payload
   * @param job - Full metadata envelope
   */
  protected abstract executeWorkload(payload: T, job: JobEnvelope<T>): Promise<void>;

  /**
   * Dispatches and processes an inbound job with deduplication and backoff guards.
   *
   * @param job - Inbound job envelope
   */
  public async handleJob(job: JobEnvelope<T>): Promise<void> {
    // 1. Consumer Idempotency Guard
    const alreadyProcessed = await this.dedupStore.hasBeenProcessed(job.idempotencyKey);
    if (alreadyProcessed) {
      // Acknowledge and skip without re-executing
      return;
    }

    try {
      // 2. Execute concrete business logic
      await this.executeWorkload(job.payload, job);

      // 3. Mark processed atomically
      await this.dedupStore.markAsProcessed(job.idempotencyKey, 86400 * 7); // 7 days retention
    } catch (error) {
      const currentAttempt = job.attempts + 1;

      if (currentAttempt >= job.maxAttempts) {
        // 4. Retries exhausted: Route to Dead Letter Queue (DLQ)
        await this.dlqSender.sendToDlq(job, error as Error);
      } else {
        // 5. Schedule retry with exponential backoff and jitter
        const delayMs = calculateExponentialBackoffWithJitter(currentAttempt);
        throw new Error(
          `Job failed on attempt ${currentAttempt}/${job.maxAttempts}. Rescheduling with ${delayMs}ms backoff. Cause: ${(error as Error).message}`
        );
      }
    }
  }
}
