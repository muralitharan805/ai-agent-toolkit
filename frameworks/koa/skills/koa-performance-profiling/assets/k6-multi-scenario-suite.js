import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

// Custom Trend Metrics
const searchLatency = new Trend('search_latency_ms', true);
const errorRate = new Rate('api_error_rate');

// Configurable Test Mode (smoke, baseline, load, stress, spike, soak)
const TEST_MODE = __ENV.TEST_MODE || 'load';
const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:3000';

const SCENARIO_CONFIGS = {
  smoke: {
    stages: [
      { duration: '30s', target: 2 },
    ],
  },
  baseline: {
    stages: [
      { duration: '1m', target: 5 },
    ],
  },
  load: {
    stages: [
      { duration: '30s', target: 5 },   // Warm-up ramp
      { duration: '1m', target: 15 },   // Normal load
      { duration: '1m', target: 25 },   // Peak target
      { duration: '30s', target: 0 },   // Cooldown
    ],
  },
  stress: {
    stages: [
      { duration: '30s', target: 10 },
      { duration: '1m', target: 30 },
      { duration: '1m', target: 60 },  // Concurrency breaking point
      { duration: '30s', target: 0 },
    ],
  },
  spike: {
    stages: [
      { duration: '10s', target: 5 },
      { duration: '30s', target: 80 },  // Sudden traffic surge
      { duration: '1m', target: 5 },    // Rapid recovery
    ],
  },
  soak: {
    stages: [
      { duration: '2m', target: 15 },
      { duration: '15m', target: 15 }, // Extended duration memory leak test
      { duration: '1m', target: 0 },
    ],
  },
};

export const options = {
  stages: SCENARIO_CONFIGS[TEST_MODE] ? SCENARIO_CONFIGS[TEST_MODE].stages : SCENARIO_CONFIGS.load.stages,
  thresholds: {
    http_req_duration: ['p(95)<500'],
    search_latency_ms: ['p(95)<450'],
    http_req_failed: ['rate<0.01'],
    api_error_rate: ['rate<0.01'],
  },
};

export default function () {
  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': `k6-multi-scenario/${TEST_MODE}`,
  };

  // 1. Critical Read Endpoint (Paginated Filter)
  const res = http.get(`${BASE_URL}/api/properties?page=1&limit=20&status=AVAILABLE`, { headers });
  searchLatency.add(res.timings.duration);

  const isSuccess = check(res, {
    'status is 200': (r) => r.status === 200,
    'has valid payload': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body && body.success === true;
      } catch (_) {
        return false;
      }
    },
  });

  if (!isSuccess) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }

  // Realistic user pacing (1-2s delay)
  sleep(Math.random() * 1 + 1);
}

/**
 * Exports single-file interactive HTML dashboard, raw JSON metrics, and terminal summary.
 * @param {Object} data - Execution metrics
 * @returns {Object} Target export file map
 */
export function handleSummary(data) {
  return {
    'k6-performance-report.html': htmlReport(data),
    'k6-performance-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
