#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Observability Pipeline Script
Audits backend codebases for adherence to the Three Pillars of Observability:
- Single-line structured JSON logging (zero raw console.log)
- Prometheus RED metrics instrumentation and /metrics endpoint
- OpenTelemetry distributed tracing and W3C traceparent propagation
- PII and credential sanitization utilities
- Metric label cardinality safety
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

RAW_CONSOLE_PATTERN = re.compile(r'\bconsole\.(log|info|debug|warn|error)\s*\(', re.IGNORECASE)
STRUCTURED_LOGGER_PATTERN = re.compile(r'(pino|winston|structlog|zerolog|loguru|@opentelemetry/api|Logger)', re.IGNORECASE)
METRICS_PROMETHEUS_PATTERN = re.compile(r'(prom-client|prometheus_client|http_requests_total|http_request_duration_seconds|/metrics)', re.IGNORECASE)
OTEL_TRACING_PATTERN = re.compile(r'(@opentelemetry|startActiveSpan|traceparent|OTLPTraceExporter|tracer\.startSpan)', re.IGNORECASE)
PII_REDACTION_PATTERN = re.compile(r'(REDACTED|sanitizeLogPayload|maskSensitive|redact)', re.IGNORECASE)
CARDINALITY_RISK_PATTERN = re.compile(r'req\.(originalUrl|url|path)\b', re.IGNORECASE)

EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
    '__pycache__', '.venv', 'venv', 'target'
}

def is_source_file(file_path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in file_path.parts):
        return False
    # Skip test files from console.log prohibitions
    name = file_path.name.lower()
    if '.test.' in name or '.spec.' in name or name.startswith('test_'):
        return False
    return file_path.suffix in {'.ts', '.js', '.py', '.go', '.rs', '.java'}

def audit_directory(target_path: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    has_structured_logger = False
    has_metrics = False
    has_tracing = False
    has_pii_redaction = False
    cardinality_warnings: List[str] = []
    scanned_files_count = 0

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            file_path = Path(root) / f
            if not is_source_file(file_path):
                continue
            
            scanned_files_count += 1
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to read {file_path}: {e}\n")
                continue

            rel_path = str(file_path.relative_to(target_path))

            # Check for structured logger
            if STRUCTURED_LOGGER_PATTERN.search(content):
                has_structured_logger = True

            # Check for Prometheus metrics
            if METRICS_PROMETHEUS_PATTERN.search(content):
                has_metrics = True

            # Check for OTel tracing
            if OTEL_TRACING_PATTERN.search(content):
                has_tracing = True

            # Check for PII redaction
            if PII_REDACTION_PATTERN.search(content):
                has_pii_redaction = True

            # Check for raw console statements
            lines = content.splitlines()
            for line_no, line in enumerate(lines, start=1):
                match = RAW_CONSOLE_PATTERN.search(line)
                if match:
                    findings.append({
                        "file": rel_path,
                        "line": line_no,
                        "type": "raw_console_log",
                        "severity": "high",
                        "message": f"Found forbidden raw `{match.group(0).strip('(')}` call. Production code must use structured logger."
                    })

                # Check for metric label cardinality risk
                if 'httpRequestsTotal' in line or 'httpRequestDurationSeconds' in line:
                    if CARDINALITY_RISK_PATTERN.search(line):
                        cardinality_warnings.append(f"{rel_path}:{line_no} Uses unparameterized raw URL in metric labels.")

    summary = {
        "scanned_files": scanned_files_count,
        "raw_console_violations": len(findings),
        "pillars": {
            "structured_logging_detected": has_structured_logger,
            "metrics_prometheus_detected": has_metrics,
            "distributed_tracing_detected": has_tracing,
            "pii_redaction_detected": has_pii_redaction
        },
        "cardinality_risks": cardinality_warnings,
        "is_compliant": (
            len(findings) == 0 and
            has_structured_logger and
            has_metrics and
            has_tracing and
            has_pii_redaction and
            len(cardinality_warnings) == 0
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for adherence to the 3 Pillars of Observability."
    )
    parser.add_argument(
        "target_path",
        nargs="?",
        default=".",
        help="Path to backend codebase or directory to audit (default: current directory)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any violations or missing observability pillars are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Observability audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
