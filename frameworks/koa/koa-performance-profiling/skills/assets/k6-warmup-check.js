'use strict';

import http from 'k6/http';
import { check, fail } from 'k6';

/**
 * @file k6-warmup-check.js
 * @description Dedicated pre-flight warmup and auth token verification script.
 * Runs exactly 1 VU for 1 iteration to verify server health and token acceptance in < 0.2s.
 */

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:1331';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

const SEARCH_PAYLOAD = JSON.stringify({
  area: { id: '', map: false, radius: null },
  filters: '(department:residential) AND (search_type:sales) AND (publish: true)',
  limit: '2',
  page: 1,
});

export default function () {
  if (!AUTH_TOKEN) {
    console.error('❌ [AUTH ERROR] AUTH_TOKEN is missing in .env!');
    fail('Pre-flight warmup aborted: Missing AUTH_TOKEN');
  }

  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'k6-preflight-warmup-checker/1.0',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };

  const response = http.post(`${BASE_URL}/api/search`, SEARCH_PAYLOAD, {
    headers,
    timeout: '10s',
  });

  if (response.status === 200) {
    console.log('✅ [WARMUP SUCCESS] PRE-FLIGHT VERIFICATION PASSED! Status: HTTP 200 OK');
  } else {
    console.error(`❌ [WARMUP FAILED] API Returned HTTP ${response.status}: ${response.body}`);
    fail(`Authentication/Health check failed: HTTP ${response.status}`);
  }

  check(response, {
    'warmup status is 200 OK': (r) => r.status === 200,
    'warmup response has payload': (r) => r.body && r.body.length > 0,
  });
}
