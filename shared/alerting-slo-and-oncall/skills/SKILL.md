---
name: alerting-slo-and-oncall
description: "Enforces SLI/SLO/SLA/error-budget definitions, minimum alert set with thresholds (5xx rate, p99 latency, DB pool, DLQ depth), alert quality rules (runbook mandatory, actionable, 5-minute minimum window), and runbook template standards for every CRITICAL alert. Triggered by 'alerting:', 'slo:', 'oncall:', 'sli:', 'error-budget:', or '/alerting-slo-and-oncall'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# Alerting, SLO & On-Call Strategy Skill

## Overview

This skill establishes production engineering standards for **SLI/SLO/SLA/Error Budget Definitions**, **Minimum Alert Set per Service** (5xx rate, p99 latency, DB connection pool, DLQ depth), **Alert Quality Rules** (runbook mandatory, actionable, minimum 5-minute window), **Alert Routing by Severity** (CRITICAL → page, WARNING → Slack), and **Runbook Template Standards**. It prevents alert fatigue, eliminates 3am guessing, and enforces a culture where every alert is actionable and every CRITICAL alert has a pre-written runbook.

```
┌──────────────────────────────────────────────────────────────────────┐
│            Alerting Architecture — Signal → Severity → Action        │
│                                                                      │
│  [Metric / Log Signal]                                               │
│         │                                                            │
│  [Prometheus AlertManager / Grafana Alerting / CloudWatch Alarms]    │
│         │                                                            │
│  ┌──────┴──────────────────────────────────────────────────┐        │
│  │ CRITICAL (5xx > 1%, 0 healthy pods, DB pool > 90%)      │        │
│  │   → PagerDuty / OpsGenie / Grafana OnCall (page now)    │        │
│  ├─────────────────────────────────────────────────────────┤        │
│  │ WARNING  (p99 > 1s, 5xx > 0.1%, DLQ > 100, disk > 80%) │        │
│  │   → Slack #alerts channel (no page)                     │        │
│  ├─────────────────────────────────────────────────────────┤        │
│  │ INFO  (missed cron, error budget < 20%)                  │        │
│  │   → Slack #monitoring (digest)                           │        │
│  └─────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3-Phase Execution Guide

### Phase 1: SLI/SLO/Error Budget Definition (Per Service)
1. **Define SLIs** — measurable, objective metrics:
   - HTTP 5xx error rate (rolling 30-day window).
   - HTTP p99 response latency (rolling 7-day window).
   - Availability (percentage of time the service responds to health checks).
2. **Set SLOs** — internal targets (more ambitious than SLA):
   - Example: Error rate < 0.1% / p99 < 500ms / Availability 99.95%.
3. **Derive Error Budget** = `100% - SLO %` converted to minutes/month.
   - 99.9% SLO → 43.8 minutes/month of allowed downtime.
4. **Define SLA** — contractual commitment BELOW SLO (buffer for recovery).
5. **Error budget policy**: Budget consumed → freeze non-critical feature deploys → reliability sprint.

### Phase 2: Minimum Alert Set Implementation
Every service MUST have at minimum:
```
SEVERITY   CONDITION                                   WINDOW   ACTION
─────────────────────────────────────────────────────────────────────────
CRITICAL   5xx rate > 1%                               5 min    Page on-call
CRITICAL   0 healthy pods                              1 min    Page on-call
CRITICAL   DB connection pool > 90% saturated          5 min    Page on-call
WARNING    p99 latency > 1000ms                        10 min   Slack
WARNING    5xx rate > 0.1%                             15 min   Slack
WARNING    DLQ depth > 100 messages                    5 min    Slack
WARNING    Cache hit rate < 60%                        15 min   Slack
WARNING    Disk / memory usage > 80%                   10 min   Slack
INFO       Cron job missed (2× interval elapsed)       —        Slack
INFO       Error budget < 20% remaining this month     —        Slack
```

### Phase 3: Alert Quality Enforcement
Every alert MUST pass these quality gates before enabling:
1. **Runbook link** — every CRITICAL alert MUST link to a pre-written runbook.
2. **Actionable** — if no action required, it is a metric not an alert. Remove it.
3. **Minimum `for: 5m`** — never alert on single-point momentary spikes.
4. **Severity routing** — CRITICAL pages on-call, WARNING goes to Slack only.
5. **Child suppression** — when DB is down, suppress all DB query latency alerts.
6. **Quarterly audit** — remove alerts nobody acts on (noise = ignored = useless).

---

## Runbook Template (Mandatory for Every CRITICAL Alert)

```markdown
# Runbook: [Alert Name]

## Symptoms
Alert fires when [condition] for [duration].

## Immediate Checks (< 2 minutes)
1. Was there a recent deploy? Check deployment timeline in CI/CD.
2. Check pod logs: `kubectl logs -l app={service} --tail=100 -f`
3. Check DB health: `kubectl exec -it db-pod -- psql -c "SELECT count(*) FROM pg_stat_activity"`

## Rollback (if deploy-related)
`kubectl rollout undo deployment/{service}`

## Escalation
No resolution in 20 minutes → escalate to Tier 2 (team lead / SRE).
```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/slo-error-budget-and-alert-design.md](references/slo-error-budget-and-alert-design.md) for Prometheus AlertManager config, Grafana alert rules YAML, and error budget burn rate alerting.
- **Production Asset**: Inspect [assets/minimum-alert-set.yaml](assets/minimum-alert-set.yaml) for Prometheus AlertManager rules covering the minimum required alert set.
- **CLI Auditor Tool**: Execute [scripts/audit_alerting_coverage.py](scripts/audit_alerting_coverage.py) to verify runbook links, alert thresholds, and severity routing.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Risk |
| :--- | :--- | :--- | :--- |
| **Runbooks** | Alert with no runbook | Every CRITICAL alert has runbook link | Engineer guesses at 3am → MTTR doubles |
| **Alert Window** | Alert on single spike | Minimum `for: 5m` window | Alert fatigue — team ignores all alerts |
| **Actionability** | Alert nobody acts on | Quarterly audit — remove noise alerts | Ignored alerts → miss real incidents |
| **Routing** | All alerts page on-call | CRITICAL pages, WARNING Slack only | On-call burnout → pager fatigue |
| **SLO** | No SLO defined | SLO per service, reviewed monthly | No objective reliability target |
| **Error Budget** | No budget tracking | Budget exhausted → freeze deploys | Reliability degraded while adding features |
| **Child Alerts** | All alerts fire simultaneously | Parent suppresses child correlated alerts | Flood of 50 alerts when 1 root cause exists |
