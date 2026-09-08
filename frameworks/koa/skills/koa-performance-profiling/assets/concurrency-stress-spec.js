/**
 * @file concurrency-stress-spec.js
 * @description In-suite Vitest parallel stress test template using Promise.all
 * to simulate concurrent requests, test MySQL connection pool saturation, and prevent deadlocks.
 */

const { describe, it, expect, beforeAll, afterAll } = require('vitest');
const request = require('supertest');
const { createTestApp } = require('../../setup/app');
const { getAuthHeader } = require('../../fixtures/auth.fixture');
const { benchmarkReporter } = require('./benchmark-reporter');

describe('Integration: Parallel Concurrency Stress Test Suite', () => {
  let app;
  const authHeader = getAuthHeader({ role: 'AGENT' });

  beforeAll(async () => {
    app = createTestApp();
  });

  afterAll(async () => {
    // Print the formatted scorecard at the end of the test suite run
    benchmarkReporter.printReport();
  });

  it('should execute 10 concurrent requests simultaneously without deadlocks', async () => {
    const CONCURRENCY = 10;
    const requests = Array.from({ length: CONCURRENCY }, (_, i) => ({
      id: `C.${i + 1}`,
      page: (i % 3) + 1,
    }));

    const overallStart = performance.now();

    // Fire 10 simultaneous API calls at the EXACT same millisecond using Promise.all
    const promises = requests.map(async (reqItem) => {
      const singleStart = performance.now();
      const res = await request(app.callback())
        .get(`/api/properties?page=${reqItem.page}&limit=10`)
        .set(authHeader);

      const singleDuration = performance.now() - singleStart;

      // Record in the benchmark scorecard
      benchmarkReporter.record({
        id: reqItem.id,
        name: `Concurrent Request #${reqItem.id} (Page ${reqItem.page})`,
        endpoint: 'GET /api/properties',
        durationMs: singleDuration,
        status: res.status,
      });

      return res;
    });

    const results = await Promise.all(promises);
    const overallDuration = performance.now() - overallStart;

    // Assert all requests completed with valid responses
    results.forEach((res) => {
      expect(res.status).toBeLessThan(500); // Zero internal server crashes
    });

    // Total parallel batch duration should complete in under 2 seconds
    expect(overallDuration).toBeLessThan(2000);
  });
});
