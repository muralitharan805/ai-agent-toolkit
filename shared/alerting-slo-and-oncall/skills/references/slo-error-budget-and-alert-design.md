# SLO, Error Budget & Alert Design — Deep Architecture Guide

## 1. SLI/SLO/SLA/Error Budget Definitions

```
SLI (Service Level Indicator)
  → What you measure (an objective, quantifiable metric)
  → Example: "percentage of HTTP requests returning non-5xx status in 30 days"

SLO (Service Level Objective)
  → Your internal target for the SLI (more ambitious than SLA)
  → Example: "SLI must be ≥ 99.9% over a rolling 30-day window"

SLA (Service Level Agreement)
  → Contractual commitment to customers (below SLO — buffer for violations)
  → Example: "We guarantee 99.5% availability or issue SLA credit"

Error Budget
  → The permissible failure margin from 100% perfect reliability
  → Formula: Error Budget = (100% - SLO%) × period_in_minutes
  → Example (99.9% SLO, 30 days):
       Error Budget = 0.1% × 43,200 min = 43.2 min/month of allowed downtime
```

---

## 2. Error Budget Burn Rate Alerting (Google SRE Method)

Simple threshold alerting tells you "you're over the limit now". Burn rate alerting warns you "at this speed, you'll exhaust your budget before the month ends."

**Burn rate = how fast you're consuming the error budget:**
```
Burn Rate 1x = consuming budget at exactly the SLO-allowed pace
Burn Rate 14.4x = will exhaust 30-day budget in 2 hours (critical: page immediately)
Burn Rate 6x = will exhaust 30-day budget in 5 hours (warning: investigate)
```

**Prometheus AlertManager burn rate rules:**
```yaml
# Critical: 14.4x burn rate — budget exhausted in 2 hours
- alert: ErrorBudgetBurnRateCritical
  expr: |
    (
      sum(rate(http_requests_total{status=~"5.."}[5m]))
      / sum(rate(http_requests_total[5m]))
    ) > (14.4 * 0.001)  # 14.4x burn × 0.1% error rate SLO
  for: 2m
  labels:
    severity: critical
  annotations:
    runbook: "https://wiki.company.com/runbooks/error-budget-burn"
    summary: "Error budget burning at 14.4x — exhausted in 2 hours"

# Warning: 6x burn rate — budget exhausted in 5 hours
- alert: ErrorBudgetBurnRateWarning
  expr: |
    (
      sum(rate(http_requests_total{status=~"5.."}[30m]))
      / sum(rate(http_requests_total[30m]))
    ) > (6 * 0.001)
  for: 15m
  labels:
    severity: warning
```

---

## 3. Complete Minimum Alert Set (Prometheus YAML)

```yaml
groups:
  - name: service-slo-critical
    rules:
      - alert: HTTP5xxSpikeHigh
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          runbook: "https://wiki.company.com/runbooks/http-5xx"

      - alert: NoHealthyPods
        expr: kube_deployment_status_replicas_available{deployment="my-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          runbook: "https://wiki.company.com/runbooks/no-healthy-pods"

      - alert: DatabaseConnectionPoolSaturated
        expr: db_connection_pool_active / db_connection_pool_max > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          runbook: "https://wiki.company.com/runbooks/db-pool-saturated"

  - name: service-slo-warning
    rules:
      - alert: HTTP5xxSpikeModerate
        expr: |
          rate(http_requests_total{status=~"5.."}[15m])
          / rate(http_requests_total[15m]) > 0.001
        for: 15m
        labels:
          severity: warning

      - alert: HighP99Latency
        expr: histogram_quantile(0.99, rate(http_request_duration_ms_bucket[10m])) > 1000
        for: 10m
        labels:
          severity: warning

      - alert: DeadLetterQueueBacklog
        expr: rabbitmq_queue_messages{queue="dlq"} > 100
        for: 5m
        labels:
          severity: warning
```

---

## 4. Alert Routing Architecture

```yaml
# AlertManager routing configuration
route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: slack-warnings    # Default: Slack
  routes:
    - matchers:
        - severity = "critical"
      receiver: pagerduty-oncall
      continue: false           # CRITICAL: page only, no Slack duplicate

receivers:
  - name: pagerduty-oncall
    pagerduty_configs:
      - routing_key: ${PAGERDUTY_INTEGRATION_KEY}

  - name: slack-warnings
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_URL}
        channel: '#alerts'
        title: '⚠️ {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

# Inhibition rules: suppress child alerts when parent fires
inhibit_rules:
  - source_matchers:
      - alertname = "NoHealthyPods"
    target_matchers:
      - alertname =~ "HighP99Latency|HTTP5xxSpikeModerate"
    equal: ['service']
```
