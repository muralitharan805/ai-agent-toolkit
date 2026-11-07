---
name: scheduled-jobs-and-cron
description: "Enforces distributed cron lock pattern (Redis NX), cron expression authoring, missed job detection via last_run_at tracking, timezone UTC invariant, and K8s CronJob separation for heavy workloads. Triggered by 'scheduled-jobs:', 'cron:', 'distributed-lock:', or '/scheduled-jobs-and-cron'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Scheduled Jobs & Cron Tasks Skill

## Overview

This skill establishes production engineering standards for **Distributed Cron Lock Acquisition (Redis `SET NX EX`)**, **Cron Expression Authoring**, **Missed Job Detection via `last_run_at` Tracking**, **UTC Timezone Enforcement**, **Health Monitoring (start / complete / failure events)**, and **K8s CronJob separation for heavy workloads**. It guarantees that in a multi-pod (horizontal scaling) environment, exactly one pod executes each scheduled job, and failures are always observed and alerted.

```
┌───────────────────────────────────────────────────────────────────────┐
│              Distributed Cron Execution Pipeline                      │
│                                                                       │
│  [All Pods — cron fires] ──► [Attempt Redis NX Lock]                 │
│                                        │                             │
│               ┌────────────────────────┴──────────────────────┐      │
│          [Lock Acquired]                            [Lock Denied]     │
│               │                                        │             │
│        [Execute Job]                          [Skip — log DEBUG]      │
│               │                                                       │
│  [Complete → DEL lock → update last_run_at]                          │
│               │                                                       │
│  [Failure → DEL lock → alert → increment failure counter]            │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3-Phase Execution Guide

### Phase 1: Distributed Lock Acquisition
1. **Redis NX Lock** — Before executing any cron job body:
   - Attempt `SET cron-lock:{jobName} {instanceId} NX EX {lockTtlSeconds}`.
   - `NX` = set only if key does NOT exist (atomic — prevents race condition).
   - `EX` = auto-expire TTL = `(max expected job duration ms + 10_000ms buffer) / 1000`.
   - If lock NOT acquired → log at DEBUG level → return immediately (not an error).
   - If lock acquired → proceed to Phase 2.
2. **Instance ID in lock value** — Store the pod hostname/UUID as the lock value to enable forensic debugging of which instance holds the lock.

### Phase 2: Structured Job Execution
1. **Structured start log**: `{ event: 'cron_job_started', jobName, instanceId }`.
2. **Execute job function** inside try/catch.
3. **On success**:
   - Log: `{ event: 'cron_job_completed', jobName, durationMs }`.
   - Increment metric: `cron_jobs_completed_total{jobName}`.
   - Update `last_run_at` in DB — critical for missed job detection.
4. **On failure**:
   - Log: `{ event: 'cron_job_failed', jobName, error }`.
   - Increment metric: `cron_jobs_failed_total{jobName}`.
   - Alert on-call after 3 consecutive failures.
5. **In `finally`**: Always release lock with `DEL cron-lock:{jobName}`.

### Phase 3: Missed Job Detection & Health Monitoring
1. **Track `last_run_at`** in a `scheduled_jobs` DB table per job name.
2. **Startup check**: On app boot, query jobs where `last_run_at < NOW() - 2 × schedule_interval`. If missed → execute immediately (for Medium/High criticality jobs).
3. **Alert thresholds**:
   - Job not run in `> 2 × schedule interval` → MISSED JOB alert (Slack/PagerDuty).
   - Duration `> 3 × historical average` → SLOW JOB alert.
   - Consecutive failures `> 3` → CRITICAL alert.

---

## Cron Expression Reference
```
┌──────────── Minute  (0–59)
│  ┌─────────── Hour   (0–23)
│  │  ┌────────── Day of Month (1–31)
│  │  │  ┌───────── Month (1–12)
│  │  │  │  ┌────── Day of Week (0–7, Sunday=0 or 7)
│  │  │  │  │
*  *  *  *  *

Production examples (all UTC):
  0 2 * * *     → Every day at 02:00 UTC (daily cleanup)
  */5 * * * *   → Every 5 minutes (health sync, metrics flush)
  0 9 * * 1-5   → 09:00 UTC, weekdays only (business reports)
  0 0 1 * *     → First day of month at midnight UTC (billing cycle)
  0 */4 * * *   → Every 4 hours (cache warm-up)
```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/distributed-cron-and-job-scheduling.md](references/distributed-cron-and-job-scheduling.md) for lock patterns, Quartz/pg-boss internals, and DB-backed scheduler architecture.
- **Production Asset**: Inspect [assets/cron-registry.template.ts](assets/cron-registry.template.ts) for the central cron registry with distributed lock integration.
- **CLI Auditor Tool**: Execute [scripts/audit_scheduled_jobs.py](scripts/audit_scheduled_jobs.py) to detect missing locks, hardcoded schedules, and missing `last_run_at` tracking.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Risk |
| :--- | :--- | :--- | :--- |
| **Multi-Pod Safety** | No distributed lock | Redis `SET NX EX` before every execution | Duplicate execution → double email / double charge |
| **Process Isolation** | Heavy cron inside HTTP server process | Kubernetes CronJob or separate worker process | Blocks request handling under load |
| **Timezone** | System default timezone | Explicit UTC (`TZ=UTC` env var + cron config) | DST transitions → double-fire or miss |
| **Schedule Config** | Hardcoded cron expression in code | Expression from env var / DB config | Cannot override without redeploy |
| **Observability** | No start/complete/failure logs | Structured logs + metric counters per event | Invisible failures — jobs silently stop running |
| **Missed Jobs** | No `last_run_at` tracking | DB table tracking last successful run | Pod was down during schedule → silent data gap |
| **Lock TTL** | No TTL on Redis lock | TTL = job max duration + 10s buffer | Crashed pod holds lock forever → no future runs |
