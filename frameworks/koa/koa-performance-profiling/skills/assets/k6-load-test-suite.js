import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

// Custom metrics
const propertyListDuration = new Trend('property_list_duration', true);
const errorRate = new Rate('custom_error_rate');

export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Warm-up ramp
    { duration: '1m', target: 10 },   // Standard concurrency
    { duration: '1m', target: 25 },   // Peak concurrency target
    { duration: '30s', target: 50 },  // Stress load
    { duration: '30s', target: 0 },   // Graceful cooldown
  ],
  thresholds: {
    // 95% of requests must complete under 500ms
    http_req_duration: ['p(95)<500'],
    property_list_duration: ['p(95)<450'],
    // Overall error rate must stay below 1%
    http_req_failed: ['rate<0.01'],
    custom_error_rate: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:3000';

export default function () {
  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'k6-performance-runner/1.0',
  };

  // 1. Scenario: Paginated Property Search
  const response = http.get(`${BASE_URL}/api/properties?page=1&limit=20`, { headers });
  propertyListDuration.add(response.timings.duration);

  const isSuccess = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has data array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.data);
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

  // Realistic human think-time pause (1-2s)
  sleep(Math.random() * 1 + 1);
}

/**
 * Automatically generates HTML report, JSON metrics, and CLI summary upon completion.
 * @param {Object} data - Execution summary metrics
 * @returns {Object} Output file mappings
 */
export function handleSummary(data) {
  return {
    'k6-report.html': htmlReport(data),
    'k6-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
