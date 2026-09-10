# Distributed Cron & Job Scheduling — Deep Architecture Guide

## 1. Why Distributed Locks Are Non-Negotiable

In containerized, horizontally scaled deployments, every replica pod runs the same cron scheduler. Without a coordination mechanism, all N pods fire the same job simultaneously at the scheduled time.

**Example failure scenario:**
- 3 pods running, daily subscription renewal cron fires at 02:00 UTC.
- All 3 pods acquire no lock → all 3 execute `renewAllSubscriptions()`.
- Each pod sends renewal emails to every user → 3× emails per user.
- Each pod calls Stripe to charge subscriptions → 3× charges per user.
- Support tickets flood in.

**Solution: Redis `SET NX EX` distributed lock (atomic):**
```
Pod A: SET cron-lock:daily-renewal pod-a NX EX 600
  → Returns OK (lock acquired) → EXECUTE

Pod B: SET cron-lock:daily-renewal pod-b NX EX 600
  → Returns nil (key exists) → SKIP (log DEBUG)

Pod C: SET cron-lock:daily-renewal pod-c NX EX 600
  → Returns nil (key exists) → SKIP (log DEBUG)
```

**Critical: `NX` and `EX` MUST be in ONE atomic command:**
```
# ❌ WRONG: Two-step is NOT atomic — race condition window between SET and EXPIRE
SET cron-lock:daily-renewal pod-a
EXPIRE cron-lock:daily-renewal 600

# ✅ CORRECT: Single atomic command
SET cron-lock:daily-renewal pod-a NX EX 600
```

---

## 2. Lock TTL Calculation

```
Lock TTL = ceil((maxExpectedJobDurationMs + 10_000) / 1000) seconds

Example:
  Daily cleanup job: expected 90 seconds max
  TTL = ceil((90_000 + 10_000) / 1000) = 100 seconds

  Heavy report generation: expected 10 minutes max
  TTL = ceil((600_000 + 10_000) / 1000) = 610 seconds

The 10-second buffer handles:
  - Network latency to Redis
  - GC pauses in JVM/Node.js
  - Unexpected I/O slowness

If the job crashes without releasing the lock → TTL auto-releases after the ceiling.
```

---

## 3. DB-Backed Schedulers (pg-boss, Quartz) for At-Least-Once Guarantees

Redis-based in-process cron fires once per schedule, in-memory. If the pod restarts during the job window, **the job is missed**.

For **at-least-once** semantics on HIGH criticality jobs:

**pg-boss (Node.js)** — persists job schedule state in PostgreSQL:
```typescript
const boss = new PgBoss(config.DATABASE_URL);
await boss.start();

// Schedule persisted in DB — survives pod restarts
await boss.schedule('daily-cleanup', '0 2 * * *', {}, { tz: 'UTC' });

boss.work('daily-cleanup', async (job) => {
  await runDailyCleanup(job.data);
});
```

**Quartz + ShedLock (Java Spring):**
```java
@Scheduled(cron = "${cron.daily-cleanup}", zone = "UTC")
@SchedulerLock(name = "daily-cleanup", lockAtMostFor = "10m", lockAtLeastFor = "1m")
public void runDailyCleanup() {
    // ShedLock acquires distributed lock via DB row lock
}
```

---

## 4. scheduled_jobs Tracking Table Schema

```sql
CREATE TABLE scheduled_jobs (
  job_name              VARCHAR PRIMARY KEY,
  cron_expression       VARCHAR NOT NULL,
  last_run_at           TIMESTAMP,
  last_duration_ms      INTEGER,
  consecutive_failures  INTEGER NOT NULL DEFAULT 0,
  is_enabled            BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Seed all known cron jobs on startup
INSERT INTO scheduled_jobs (job_name, cron_expression) VALUES
  ('daily-cleanup',          '0 2 * * *'),
  ('subscription-renewal',   '0 3 1 * *'),
  ('metrics-aggregation',    '*/15 * * * *')
ON CONFLICT (job_name) DO NOTHING;
```

---

## 5. Kubernetes CronJob for Heavy Workloads

For jobs > 30 seconds, use a Kubernetes CronJob resource instead of in-process cron:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-report-generation
spec:
  schedule: "0 2 * * *"           # UTC
  timeZone: "UTC"                  # K8s 1.27+ native timezone support
  concurrencyPolicy: Forbid        # Prevent parallel runs at K8s level
  startingDeadlineSeconds: 300     # Give 5 min to start before marking missed
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: report-generator
              image: myapp:${GIT_SHA}     # Always use immutable tag
              command: ["node", "dist/scripts/generate-daily-report.js"]
              env:
                - name: DATABASE_URL
                  valueFrom:
                    secretKeyRef:
                      name: app-secrets
                      key: DATABASE_URL
```

---

## 6. Tools Reference by Language

| Language | In-Process Cron | DB-Backed (At-Least-Once) | Notes |
|---|---|---|---|
| **Node.js** | `node-cron`, `BullMQ cron` | `pg-boss`, `BullMQ` | pg-boss: PostgreSQL-backed, best for guaranteed execution |
| **Python** | `APScheduler` | `Celery beat + Redis/RabbitMQ` | Use `celery beat` for distributed Python scheduling |
| **Go** | `robfig/cron v3` | `gocron + Redis lock` | robfig/cron v3 has timezone support built-in |
| **Java** | `Quartz Scheduler` | `Quartz + ShedLock` | ShedLock uses DB row lock — production battle-tested |
| **.NET** | `Hangfire` | `Hangfire + SQL Server` | Hangfire provides persistent scheduled job storage |
