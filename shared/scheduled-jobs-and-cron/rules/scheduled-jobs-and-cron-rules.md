---
trigger: model_decision
description: "Enforces distributed cron lock pattern (Redis NX), cron expression UTC timezone, missed job detection via last_run_at tracking, structured start/complete/failure logs, K8s CronJob separation, and alert thresholds for missed/slow/failed cron jobs."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Scheduled Jobs & Cron Tasks Standards

## Description
Enforces production engineering standards for distributed scheduled job execution across multi-pod (horizontally scaled) backend architectures. Mandates Redis `SET NX EX` distributed lock acquisition before any cron job execution to prevent duplicate runs across pods, structured logging on job start/complete/failure events with `durationMs`, `last_run_at` tracking in the database for missed job detection and startup recovery, explicit UTC timezone enforcement to prevent DST-related double-fire or skip bugs, config-driven cron expressions (never hardcoded), separation of heavy workloads to Kubernetes CronJob resources (not inside the HTTP server process), and on-call alerting after 3 consecutive job failures.

## Constraints

### 1. Distributed Lock Mandatory Before Every Cron Execution
- Every scheduled job MUST attempt to acquire a Redis distributed lock before executing its business logic.
- Lock syntax: `SET cron-lock:{jobName} {instanceId} NX EX {lockTtlSeconds}`.
- `NX` (only set if Not eXists) and `EX` (auto-expire TTL) MUST both be present in a single atomic command — split two-step operations are STRICTLY FORBIDDEN.
- Lock TTL MUST be set to `(expected max job duration in milliseconds + 10,000ms buffer) / 1000` seconds.
- If lock acquisition fails (key already exists) → skip silently at DEBUG log level. This is normal behavior, not an error.
- Lock MUST always be released via `DEL cron-lock:{jobName}` in a `finally` block — even on failure.

### 2. Structured Observability on Every Execution
- Every cron job MUST emit a structured log at job start, completion, and failure.
- Start log MUST include: `{ event: 'cron_job_started', jobName, instanceId, scheduledAt }`.
- Completion log MUST include: `{ event: 'cron_job_completed', jobName, durationMs }`.
- Failure log MUST include: `{ event: 'cron_job_failed', jobName, error, durationMs }`.
- Prometheus metrics MUST be incremented: `cron_jobs_completed_total{jobName}` and `cron_jobs_failed_total{jobName}`.
- `last_run_at` MUST be updated in the `scheduled_jobs` DB table on every successful completion.

### 3. Missed Job Detection & Startup Recovery
- A `scheduled_jobs` table MUST exist in the database tracking `job_name`, `last_run_at`, `last_duration_ms`, and `consecutive_failures` per job.
- On application startup, the service MUST query for jobs where `last_run_at < NOW() - (2 × schedule_interval)` and execute them immediately for Medium/High criticality jobs.
- Alerting thresholds:
  - Job not run in `> 2 × schedule_interval` → MISSED JOB → Slack/PagerDuty alert.
  - Execution duration `> 3 × historical average` → SLOW JOB → Slack alert.
  - `consecutive_failures > 3` → CRITICAL → page on-call.

### 4. UTC Timezone & Config-Driven Schedules
- All cron expressions MUST run in explicit UTC timezone — never system/local timezone.
- Cron schedule expressions MUST be loaded from environment configuration (never hardcoded as string literals in source code).
- Business-time jobs (e.g., "run at 9am user's local time") MUST store the user timezone and convert at runtime — cron fires in UTC and calculates offset.

### 5. Process Separation for Heavy Workloads
- Cron jobs with expected duration > 30 seconds MUST run as a Kubernetes CronJob resource or a separate worker process.
- Running heavy cron jobs inside the HTTP server process is STRICTLY FORBIDDEN — it blocks the event loop and degrades request handling.

## Examples

### 1. Correct Distributed Lock Pattern (TypeScript)
```typescript
// ✅ CORRECT: Redis NX lock prevents duplicate execution across pods
async function runScheduledJob(
  jobName: string,
  jobFn: () => Promise<void>,
  maxExecutionMs: number
): Promise<void> {
  const lockKey = `cron-lock:${jobName}`;
  const lockTtlSeconds = Math.ceil((maxExecutionMs + 10_000) / 1000);
  const instanceId = process.env.HOSTNAME ?? crypto.randomUUID();

  const acquired = await redis.set(lockKey, instanceId, { NX: true, EX: lockTtlSeconds });

  if (!acquired) {
    logger.debug({ event: 'cron_lock_skipped', jobName, instanceId });
    return;
  }

  const startTime = Date.now();
  logger.info({ event: 'cron_job_started', jobName, instanceId });

  try {
    await jobFn();
    const durationMs = Date.now() - startTime;
    logger.info({ event: 'cron_job_completed', jobName, durationMs });
    metrics.increment('cron_jobs_completed_total', { jobName });
    await db.query(
      'UPDATE scheduled_jobs SET last_run_at = NOW(), consecutive_failures = 0 WHERE job_name = $1',
      [jobName]
    );
  } catch (error: unknown) {
    const durationMs = Date.now() - startTime;
    logger.error({ event: 'cron_job_failed', jobName, error, durationMs });
    metrics.increment('cron_jobs_failed_total', { jobName });
    await db.query(
      'UPDATE scheduled_jobs SET consecutive_failures = consecutive_failures + 1 WHERE job_name = $1',
      [jobName]
    );
  } finally {
    await redis.del(lockKey);
  }
}
```

### 2. Config-Driven Cron Registration (Forbidden Hardcoding)
```typescript
// ❌ FORBIDDEN: Hardcoded cron expression in source
cron.schedule('0 2 * * *', () => runDailyCleanup());

// ✅ CORRECT: Expression from environment config — overridable without redeploy
const dailyCleanupSchedule = config.get('CRON_DAILY_CLEANUP_SCHEDULE'); // '0 2 * * *' from .env
cron.schedule(dailyCleanupSchedule, () =>
  runScheduledJob('daily-cleanup', runDailyCleanup, 120_000)
);
```
