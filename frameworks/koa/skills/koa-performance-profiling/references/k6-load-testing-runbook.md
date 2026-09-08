# k6 Load & Performance Testing Runbook

## Overview
This runbook guides performance engineers and backend developers on conducting deterministic load tests for Koa.js applications using Grafana **k6**. It defines traffic simulation stages, SLA thresholds, and continuous regression verification.

---

## 1. Installation & Environment Setup

### Installing k6
- **Debian / Ubuntu**:
  ```bash
  sudo gpg -k
  sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
  echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
  sudo apt-get update && sudo apt-get install k6
  ```
- **Local Binary Execution**:
  Download the standalone binary or use `docker run -i grafana/k6 run - <script.js`.

---

## 2. Multi-Stage Virtual User (VU) Ramping

Do not execute load tests with flat traffic or only single requests. Test concurrency inflection points:

```javascript
export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Warm-up & baseline
    { duration: '1m', target: 10 },   // Standard production traffic
    { duration: '1m', target: 25 },   // Peak traffic
    { duration: '30s', target: 50 },  // Stress threshold (2-core VM limit)
    { duration: '30s', target: 0 },   // Cool-down
  ],
  thresholds: {
    // 95% of standard requests must complete under 500ms
    'http_req_duration{type:standard}': ['p(95)<500'],
    // 95% of complex search requests must complete under 1000ms
    'http_req_duration{type:search}': ['p(95)<1000'],
    // Failure rate must remain strictly below 1%
    http_req_failed: ['rate<0.01'],
  },
};
```

---

## 3. SLA & Threshold Criteria

| Endpoint Category | Concurrency (VUs) | Target p50 | Target p95 | Hard Ceiling (p99) | Error Rate Max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Health & Ping** | 50 | < 10ms | < 30ms | < 100ms | < 0.1% |
| **Standard Read (GET /users)** | 25 | < 150ms | < 500ms | < 1000ms | < 1.0% |
| **Filtered Search (GET /properties)** | 25 | < 300ms | < 1000ms | < 2000ms | < 1.0% |
| **Mutations (POST /api/leads)** | 10 | < 250ms | < 800ms | < 1500ms | < 0.5% |

---

## 4. Identifying Latency Spikes: Average vs. Percentiles
Never assess system performance using average response times. Averages conceal outlier latency:

```text
Request Sample: [100ms, 120ms, 110ms, 115ms, 4800ms]
Average Latency: ~1049ms (appears moderately acceptable)
p95 / Max Latency: 4800ms (reveals catastrophic thread lock or DB pool stall)
```
Always diagnose using:
- **p50 (Median)**: General user experience.
- **p90 / p95**: Tail latency affecting significant portions of traffic.
- **p99 / Max**: Unindexed queries, garbage collection pauses, or database lock contentions.

---

## 5. Automated CI Regression Integration
Run k6 in CI pipelines and fail builds if thresholds are breached:

```bash
k6 run --summary-export=k6-summary.json tests/performance/k6-load-suite.js
```
