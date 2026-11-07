/**
 * @file benchmark-reporter.js
 * @description In-suite Vitest latency profiling, performance budget guardrails,
 * and automated benchmark scorecard generator. Prints a formatted table at the end of test runs.
 *
 * SLA Thresholds:
 * - FAST / Ideal: < 500ms
 * - WARN: 500ms – 2000ms
 * - SLOW / Critical: > 2000ms
 */

class BenchmarkReporter {
  constructor() {
    this.records = [];
    this.WARNING_THRESHOLD_MS = 500;
    this.CRITICAL_THRESHOLD_MS = 2000;
  }

  /**
   * Records a scenario benchmark result.
   *
   * @param {Object} entry
   * @param {string} entry.id - Scenario ID (e.g., '1.1')
   * @param {string} entry.name - Scenario description
   * @param {string} entry.endpoint - HTTP endpoint (e.g., 'GET /api/properties')
   * @param {number} entry.durationMs - Execution latency in milliseconds
   * @param {number} entry.status - HTTP status code
   * @param {number} [entry.hits=0] - Result count if applicable
   * @returns {Object} Recorded entry with tier and SLA status
   */
  record({ id, name, endpoint, durationMs, status, hits = 0 }) {
    const isWarning = durationMs > this.WARNING_THRESHOLD_MS && durationMs <= this.CRITICAL_THRESHOLD_MS;
    const isCritical = durationMs > this.CRITICAL_THRESHOLD_MS;
    const isSuccess = status >= 200 && status < 300;

    let tier = 'FAST';
    if (isWarning) tier = 'WARN';
    if (isCritical) tier = 'SLOW';

    const entry = {
      id,
      name,
      endpoint,
      durationMs: parseFloat(durationMs.toFixed(2)),
      status,
      hits,
      tier,
      slaMet: !isCritical && isSuccess,
    };

    this.records.push(entry);
    return entry;
  }

  /**
   * Returns all recorded benchmark entries.
   * @returns {Array<Object>}
   */
  getRecords() {
    return this.records;
  }

  /**
   * Generates and logs a formatted ASCII markdown scorecard table to stdout.
   */
  printReport() {
    if (this.records.length === 0) return;

    process.stdout.write('\n' + '='.repeat(90) + '\n');
    process.stdout.write('                 API PERFORMANCE BENCHMARK SCORECARD\n');
    process.stdout.write('='.repeat(90) + '\n');
    process.stdout.write(
      'Scenario'.padEnd(10) +
      '| Endpoint'.padEnd(24) +
      '| Latency (ms)'.padEnd(16) +
      '| Status'.padEnd(10) +
      '| SLA (<500ms)'.padEnd(16) +
      '| Description\n'
    );
    process.stdout.write('-'.repeat(90) + '\n');

    let fastCount = 0;
    let warnCount = 0;
    let criticalCount = 0;
    let totalMs = 0;

    for (const r of this.records) {
      totalMs += r.durationMs;
      let badge = '✅ PASS';
      if (r.tier === 'WARN') {
        badge = '⚠️ WARN (>500ms)';
        warnCount++;
      } else if (r.tier === 'SLOW') {
        badge = '❌ FAIL (>2s)';
        criticalCount++;
      } else {
        fastCount++;
      }

      process.stdout.write(
        r.id.padEnd(10) +
        `| ${r.endpoint}`.padEnd(24) +
        `| ${r.durationMs.toFixed(2)}ms`.padEnd(16) +
        `| ${r.status}`.padEnd(10) +
        `| ${badge}`.padEnd(16) +
        `| ${r.name}\n`
      );
    }

    const avgMs = (totalMs / this.records.length).toFixed(2);
    process.stdout.write('='.repeat(90) + '\n');
    process.stdout.write(
      `SUMMARY: Total Scenarios: ${this.records.length} | Fast: ${fastCount} | Warn: ${warnCount} | Critical: ${criticalCount} | Avg Latency: ${avgMs}ms\n`
    );
    process.stdout.write('='.repeat(90) + '\n\n');
  }
}

const benchmarkReporter = new BenchmarkReporter();

module.exports = {
  BenchmarkReporter,
  benchmarkReporter,
};
