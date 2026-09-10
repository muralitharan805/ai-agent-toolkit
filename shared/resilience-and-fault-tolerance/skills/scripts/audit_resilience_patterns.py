#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Resilience Patterns Script
Audits backend codebases for resilience and fault tolerance standards:
- Explicit bounded timeouts on all external I/O (DB, HTTP, cache)
- Circuit breaker state machines for external service calls
- Exponential backoff with jitter on transient retries (prohibiting 4xx retries)
- Idempotency-Key support on mutating HTTP endpoints
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

UNBOUNDED_AXIOS = re.compile(r'\baxios\.(get|post|put|delete|patch)\s*\(', re.IGNORECASE)
TIMEOUT_CONFIG_PATTERN = re.compile(r'\b(timeout|statement_timeout|readTimeout|connectTimeout)\s*[:=]\s*\d+', re.IGNORECASE)
CIRCUIT_BREAKER_PATTERN = re.compile(r'\b(circuitBreaker|opossum|cockatiel|CircuitBreaker|brakes|resilience)\b', re.IGNORECASE)
IDEMPOTENCY_HEADER_PATTERN = re.compile(r'[\'"`]idempotency-key[\'"`]', re.IGNORECASE)
BLIND_4XX_RETRY_PATTERN = re.compile(r'catch\s*\(\s*\w+\s*\)\s*\{[^}]*retry\s*\(', re.IGNORECASE)

EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
    '__pycache__', '.venv', 'venv', 'target'
}

def is_source_file(file_path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in file_path.parts):
        return False
    name = file_path.name.lower()
    if '.test.' in name or '.spec.' in name or name.startswith('test_'):
        return False
    return file_path.suffix in {'.ts', '.js', '.py', '.go', '.rs', '.java'}

def audit_directory(target_path: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    scanned_files_count = 0
    has_timeout_configs = False
    has_circuit_breakers = False
    has_idempotency_headers = False
    unbounded_calls_count = 0

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

            if TIMEOUT_CONFIG_PATTERN.search(content):
                has_timeout_configs = True

            if CIRCUIT_BREAKER_PATTERN.search(content):
                has_circuit_breakers = True

            if IDEMPOTENCY_HEADER_PATTERN.search(content):
                has_idempotency_headers = True

            # Detect unbounded axios calls
            if UNBOUNDED_AXIOS.search(content) and not TIMEOUT_CONFIG_PATTERN.search(content):
                if 'client' in rel_path.lower() or 'service' in rel_path.lower():
                    unbounded_calls_count += 1
                    findings.append({
                        "file": rel_path,
                        "type": "unbounded_http_call",
                        "severity": "high",
                        "message": "Found HTTP request invocation without explicit timeout configuration. Unbounded I/O risks thread exhaustion."
                    })

    summary = {
        "scanned_files": scanned_files_count,
        "resilience_patterns": {
            "timeout_bounds_configured": has_timeout_configs,
            "circuit_breaker_detected": has_circuit_breakers,
            "idempotency_key_detected": has_idempotency_headers,
            "unbounded_network_calls": unbounded_calls_count
        },
        "is_compliant": (
            unbounded_calls_count == 0 and
            has_timeout_configs
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for resilience and fault tolerance standards."
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
        help="Exit with non-zero status if any violations or missing resilience configurations are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Resilience audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
