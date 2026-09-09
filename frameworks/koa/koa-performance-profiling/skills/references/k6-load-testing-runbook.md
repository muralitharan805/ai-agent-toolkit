# k6 Load & Performance Testing Runbook

## Overview
This runbook guides performance engineers and backend developers on conducting deterministic load tests for Koa.js applications using Grafana **k6**. It defines traffic simulation stages, SLA thresholds, and continuous regression verification.

---

## 1. Execution Modes (Docker Compose vs. Standalone)

### Mode A: Docker Compose (Recommended — Zero Host Installation)
Run k6 containerized using the pre-configured `tests/docker-compose.test.yml`:
```bash
# Smoke Test (Quick sanity check: 2 VUs, 30s)
docker compose -f tests/docker-compose.test.yml run --rm k6-smoke

# Baseline & Peak Load Test (25 VUs, 2m)
docker compose -f tests/docker-compose.test.yml run --rm k6-load

# Stress Test (Find breaking point: 50 VUs)
docker compose -f tests/docker-compose.test.yml run --rm k6-stress
```
*Benefits: Uses pinned official `grafana/k6:0.55.0`, `--rm` auto-destructs the container on completion, `--network=host` hits `localhost:3000` natively, and mounts project folder to output `k6-performance-report.html` and individual JSON summaries.*

### Mode B: Standalone Host Binary (For Dedicated Load Generators)
- **Debian / Ubuntu**:
  ```bash
  sudo gpg -k
  sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
  echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
  sudo apt-get update && sudo apt-get install k6
  ```
- Run directly:
  ```bash
  k6 run tests/performance/k6-multi-scenario-suite.js
  ```

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

---

## 5. Production & Staging Safety Protocol

When testing an application running in production or staging, adhere to strict safety guardrails:
1. **Never Run Aggressive Stress/Spike Tests on Live Production**:
   - Limit production runs strictly to **Smoke Tests** (5 VUs, < 30 seconds) during off-peak hours.
   - High-VU stress and soak testing must ONLY target local or staging environments.
2. **Third-Party API & Webhook Isolation**:
   - Ensure external email (SendGrid), SMS (Twilio), and payment gateways (Stripe/PayPal) are mocked or disabled during load testing to avoid sending thousands of spam messages or incurring real charges.
3. **Database Mutation Safeguards**:
   - Use dedicated test user accounts (`test_perf_user@example.com`) and clean up generated test leads/records post-test.

---

## 6. Security & Sensitive Data Redaction

Ensure performance testing logs and artifacts never leak credentials:
- **Redact Authorization Headers**: Never print raw JWT tokens (`Bearer eyJ...`) in k6 console output or exported summaries.
- **Environment Variable Isolation**: Pass credentials via environment variables (`TEST_AUTH_TOKEN`), never hardcode passwords in test scripts.
- **Sanitize HTML Reports**: Verify that `k6-performance-report.html` does not contain sensitive customer PII in request payloads or URL parameters.

---

## 7. PM2 Cluster Impact on Performance Measurements

The application runs under PM2. Understand how PM2 worker count alters benchmarks:
- **Fork Mode (1 Worker)**:
  - Single event loop. Useful for establishing the true baseline CPU saturation of a single Node process.
- **Cluster Mode (`instances: 2` on 2-core VM)**:
  - Distributes HTTP traffic across 2 CPU cores. Doubles throughput for CPU-bound tasks.
  - **Connection Pool Caveat**: Each PM2 worker creates its own independent Sequelize connection pool. If `pool.max = 10`, 2 workers will open up to 20 connections to MySQL. Ensure MySQL's `max_connections` handles the sum of all PM2 workers plus admin connections.

---

## 8. Automated CI Regression Integration

Strictly separate fast PR validation from heavy performance testing:
- **Pull Request CI**: Run Vitest unit, integration, and coverage checks (< 2 minutes). Do NOT run heavy k6 tests on every PR.
- **Nightly / Release CI**: Run k6 smoke and baseline tests via GitHub Actions using the official runner:
  ```yaml
  - name: Execute k6 Smoke Benchmark
    uses: grafana/k6-action@v0.3.0
    with:
      filename: tests/performance/k6-multi-scenario-suite.js
      flags: -e TEST_MODE=smoke
  ```
- **Evaluation Gate**: Fail builds if $p95$ latency breaches the threshold:
  ```bash
  python3 tests/performance/run_performance_benchmarks.py --summary-json k6-summary.json --max-p95 500
  ```

