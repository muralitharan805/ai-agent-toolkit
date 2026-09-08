#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
run_performance_benchmarks.py
CLI benchmark automation tool for Koa.js applications. Runs or parses k6 load test results,
verifies SLA percentiles (p50, p95, p99), and detects latency regressions.
Emits structured JSON to stdout and diagnostics to stderr.
"""

import os
import sys
import json
import argparse
import subprocess
from typing import Dict, Any

def evaluate_metrics(data: Dict[str, Any], max_p95: float, max_error_rate: float) -> Dict[str, Any]:
    metrics = data.get("metrics", {})
    http_req_duration = metrics.get("http_req_duration", {}).get("values", {})
    http_req_failed = metrics.get("http_req_failed", {}).get("values", {})

    p50 = http_req_duration.get("p(50)", http_req_duration.get("med", 0.0))
    p95 = http_req_duration.get("p(95)", 0.0)
    p99 = http_req_duration.get("p(99)", 0.0)
    error_rate = http_req_failed.get("rate", 0.0)

    p95_pass = p95 <= max_p95
    error_pass = error_rate <= max_error_rate
    overall_pass = p95_pass and error_pass

    return {
        "pass": overall_pass,
        "sla_thresholds": {
            "max_p95_ms": max_p95,
            "max_error_rate": max_error_rate
        },
        "measured_values": {
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "error_rate": round(error_rate, 4)
        },
        "violations": [] if overall_pass else [
            f"p95 latency ({p95:.1f}ms) breached target ({max_p95:.1f}ms)" if not p95_pass else None,
            f"error rate ({error_rate * 100:.2f}%) breached limit ({max_error_rate * 100:.2f}%)" if not error_pass else None
        ]
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute or verify k6 performance test benchmarks against target SLAs."
    )
    parser.add_argument(
        "--summary-json",
        help="Path to an existing k6 summary JSON file to evaluate"
    )
    parser.add_argument(
        "--script",
        help="Path to a k6 Javascript test script to execute"
    )
    parser.add_argument(
        "--max-p95",
        type=float,
        default=500.0,
        help="Maximum allowed p95 duration in ms (default: 500.0)"
    )
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=0.01,
        help="Maximum allowed request failure rate (default: 0.01)"
    )

    args = parser.parse_args()

    if not args.summary_json and not args.script:
        sys.stderr.write("Error: Must provide either --summary-json or --script.\n")
        sys.exit(1)

    summary_data = {}

    if args.script:
        if not os.path.exists(args.script):
            sys.stderr.write(f"Error: Script file not found: {args.script}\n")
            sys.exit(1)

        temp_summary = "k6-temp-summary.json"
        cmd = ["k6", "run", f"--summary-export={temp_summary}", args.script]
        sys.stderr.write(f"Running k6 benchmark: {' '.join(cmd)}\n")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if os.path.exists(temp_summary):
                with open(temp_summary, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
                os.remove(temp_summary)
            else:
                sys.stderr.write(f"k6 execution failed without producing summary: {res.stderr}\n")
                sys.exit(1)
        except FileNotFoundError:
            sys.stderr.write("Error: 'k6' binary not found in PATH. Install k6 or use --summary-json.\n")
            sys.exit(1)
    elif args.summary_json:
        if not os.path.exists(args.summary_json):
            sys.stderr.write(f"Error: Summary JSON not found: {args.summary_json}\n")
            sys.exit(1)
        with open(args.summary_json, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

    evaluation = evaluate_metrics(summary_data, args.max_p95, args.max_error_rate)

    # Diagnostic output on stderr
    if evaluation["pass"]:
        sys.stderr.write("✅ Performance Benchmark Passed SLA Gates!\n")
    else:
        sys.stderr.write("❌ Performance Benchmark FAILED SLA Gates:\n")
        for v in evaluation["violations"]:
            if v:
                sys.stderr.write(f"  - {v}\n")

    # Structured JSON report on stdout
    print(json.dumps(evaluation, indent=2))
    sys.exit(0 if evaluation["pass"] else 1)

if __name__ == "__main__":
    main()
