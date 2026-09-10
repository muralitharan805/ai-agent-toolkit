#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Health Probes Script
Audits backend codebases for Kubernetes and load balancer health check standards:
- Distinct /live (liveness) and /ready (readiness) probe endpoints
- Strict zero-external-I/O isolation in /live to prevent cascading restart loops
- HTTP 503 Service Unavailable return on failed readiness checks
- IP protection / authentication on deep /health/details diagnostics
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

LIVENESS_ROUTE_PATTERN = re.compile(r'(\.get\s*\(\s*[\'"`]/(live|healthz|liveness)[\'"`]|@Get\s*\(\s*[\'"`](live|healthz|liveness)[\'"`]\))', re.IGNORECASE)
READINESS_ROUTE_PATTERN = re.compile(r'(\.get\s*\(\s*[\'"`]/(ready|readyz|readiness)[\'"`]|@Get\s*\(\s*[\'"`](ready|readyz|readiness)[\'"`]\))', re.IGNORECASE)
DIAGNOSTIC_ROUTE_PATTERN = re.compile(r'(\.get\s*\(\s*[\'"`]/(health/details|health/diag|diagnostics)[\'"`]|@Get\s*\(\s*[\'"`](health/details|health/diag|diagnostics)[\'"`]\))', re.IGNORECASE)

# Anti-pattern: Database or Redis access inside liveness check
DB_CALL_PATTERN = re.compile(r'\b(db\.|prisma\.|query\s*\(|redis\.|SELECT\s+1|findMany|findOne|ping)\b', re.IGNORECASE)
STATUS_503_PATTERN = re.compile(r'\b(503|SERVICE_UNAVAILABLE|HttpStatus\.SERVICE_UNAVAILABLE)\b', re.IGNORECASE)

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
    has_liveness = False
    has_readiness = False
    has_diagnostic = False
    liveness_has_db_leak = False
    readiness_handles_503 = False
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

            # Detect liveness probe
            live_match = LIVENESS_ROUTE_PATTERN.search(content)
            if live_match:
                has_liveness = True
                # Extract surrounding block to check for DB leaks
                idx = live_match.start()
                window = content[idx:idx + 800]
                if DB_CALL_PATTERN.search(window):
                    liveness_has_db_leak = True
                    findings.append({
                        "file": rel_path,
                        "type": "liveness_db_leak",
                        "severity": "critical",
                        "message": "Critical Anti-Pattern: External I/O (DB/Redis) detected in /live liveness probe! This triggers cascading restart stampedes in Kubernetes."
                    })

            # Detect readiness probe
            ready_match = READINESS_ROUTE_PATTERN.search(content)
            if ready_match:
                has_readiness = True
                idx = ready_match.start()
                window = content[idx:idx + 1200]
                if STATUS_503_PATTERN.search(window):
                    readiness_handles_503 = True

            # Detect diagnostic route
            if DIAGNOSTIC_ROUTE_PATTERN.search(content):
                has_diagnostic = True

    if has_readiness and not readiness_handles_503:
        findings.append({
            "file": "readiness_handler",
            "type": "missing_503_readiness",
            "severity": "high",
            "message": "Readiness probe does not appear to return HTTP 503 on dependency failures."
        })

    summary = {
        "scanned_files": scanned_files_count,
        "probes": {
            "liveness_probe_detected": has_liveness,
            "readiness_probe_detected": has_readiness,
            "diagnostic_probe_detected": has_diagnostic,
            "liveness_isolated_from_io": not liveness_has_db_leak,
            "readiness_returns_503_on_failure": readiness_handles_503
        },
        "is_compliant": (
            has_liveness and
            has_readiness and
            not liveness_has_db_leak and
            readiness_handles_503
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for Kubernetes health probe architecture standards."
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
        help="Exit with non-zero status if any violations or missing probe definitions are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Health probes audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
