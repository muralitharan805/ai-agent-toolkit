---
trigger: model_decision
description: "Enforces SLI/SLO/error budget definitions, minimum 10-alert set per service (5xx rate, p99 latency, DB pool, DLQ depth), alert quality rules (runbook mandatory, actionable, 5-minute minimum window), severity routing (CRITICAL pages, WARNING Slack), and runbook template standards."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Alerting, SLO & On-Call Strategy Standards

## Description
Enforces production engineering standards for observability-driven operations: mandatory SLI/SLO/SLA/Error Budget definition per service, minimum 10-alert coverage set (HTTP 5xx rate, p99 latency, zero healthy pods, DB connection pool saturation, DLQ depth, cache hit rate, disk/memory, cron missed, error budget), alert quality constraints (every CRITICAL alert requires a linked runbook, actionable condition, and minimum 5-minute evaluation window), structured severity routing (CRITICAL pages on-call via PagerDuty/OpsGenie, WARNING routes to Slack, INFO routes to email digest), and mandatory runbook authoring before activating any CRITICAL alert.

## Constraints

### 1. SLI/SLO/Error Budget Mandatory Per Service
- Every production service MUST define at minimum: HTTP 5xx error rate SLI, HTTP p99 latency SLI, and availability SLI.
- SLO targets MUST be documented and reviewed monthly by the owning team.
- Error budget MUST be tracked: `error_budget_minutes = (100% - SLO%) × 30_days_in_minutes`.
- When error budget is exhausted (< 0% remaining), non-critical feature deploys MUST be frozen until reliability is restored.

### 2. Minimum Alert Coverage Set
Every production service MUST have ALL of the following alerts configured:
- `CRITICAL`: HTTP 5xx rate > 1% for 5 minutes → page on-call.
- `CRITICAL`: Zero healthy pods for 1 minute → page on-call.
- `CRITICAL`: DB connection pool > 90% for 5 minutes → page on-call.
- `WARNING`: HTTP p99 latency > 1000ms for 10 minutes → Slack.
- `WARNING`: HTTP 5xx rate > 0.1% for 15 minutes → Slack.
- `WARNING`: DLQ depth > 100 messages for 5 minutes → Slack.
- `WARNING`: Cache hit rate < 60% for 15 minutes → Slack.
- `WARNING`: Disk or memory usage > 80% for 10 minutes → Slack.
- `INFO`: Cron job not run in 2× schedule interval → Slack.
- `INFO`: Error budget < 20% remaining this calendar month → Slack.

### 3. Alert Quality Rules
- Every `CRITICAL` alert MUST include a `runbook` URL field pointing to a pre-written runbook document.
- Every alert MUST be actionable — if no engineer action is required when it fires, it MUST be demoted to a metric (no alert).
- Every alert MUST use a minimum `for: 5m` evaluation window — single-point momentary spikes MUST NOT trigger pages.
- `CRITICAL` alerts MUST route to PagerDuty / OpsGenie / Grafana OnCall (phone/SMS page).
- `WARNING` alerts MUST route to Slack only (no page).
- Child alerts correlated to a parent alert MUST be suppressed when the parent fires.
- A quarterly alert audit MUST be conducted — alerts that nobody acts on MUST be removed to prevent alert fatigue.

### 4. Runbook Standards
- Every `CRITICAL` alert MUST have a corresponding runbook BEFORE the alert is activated in production.
- Runbooks MUST include: Symptoms, Immediate Checks (< 2 minutes), Rollback steps, and Escalation path.

## Examples

### 1. Prometheus AlertManager Rule (Correct)
```yaml
# ✅ CORRECT: 5-minute window, runbook link, severity routing
groups:
  - name: http-slo-alerts
    rules:
      - alert: HTTP5xxSpikeHigh
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "5xx rate {{ $value | humanizePercentage }} on {{ $labels.service }}"
          runbook: "https://wiki.company.com/runbooks/http-5xx-spike"
          dashboard: "https://grafana.company.com/d/service-overview"
```

### 2. Forbidden — Alert Without Runbook
```yaml
# ❌ FORBIDDEN: CRITICAL alert with no runbook — engineer guesses at 3am
- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Database is down"
    # No runbook URL — engineer has no guidance during incident
```
