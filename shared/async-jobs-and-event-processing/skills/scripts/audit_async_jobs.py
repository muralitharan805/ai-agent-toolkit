#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Asynchronous Jobs Script
Audits backend codebases for background processing architecture standards:
- Detection of heavy blocking operations inside HTTP route handlers
- Verification of Dead Letter Queue (DLQ) configuration
- Verification of exponential backoff retry strategies with jitter
- Consumer idempotency safeguards
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

HEAVY_OP_PATTERN = re.compile(r'\b(sendMail|sendEmail|generatePdf|createPdf|exportToCsv|transcode|sharp\s*\(|sentry\.capture|renderPdf)\b', re.IGNORECASE)
HTTP_HANDLER_PATTERN = re.compile(r'(\.post\s*\(|\.get\s*\(|\.put\s*\(|@Post\s*\(|@Put\s*\()', re.IGNORECASE)
QUEUE_ENQUEUE_PATTERN = re.compile(r'\b(queue\.add|enqueue|publish|sendToQueue|sendMessage|dispatchJob|producer\.send)\b', re.IGNORECASE)
DLQ_PATTERN = re.compile(r'\b(deadLetter|dead_letter|dlq|deadLetterTargetArn|x-dead-letter)\b', re.IGNORECASE)
BACKOFF_JITTER_PATTERN = re.compile(r'\b(backoff|jitter|attempts|exponential)\b', re.IGNORECASE)
IDEMPOTENCY_PATTERN = re.compile(r'\b(idempotencyKey|idempotent|processedJobs|dedupKey|jobId)\b', re.IGNORECASE)

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
    blocking_http_violations = 0
    has_queue_usage = False
    has_dlq = False
    has_backoff = False
    has_idempotency = False

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

            if QUEUE_ENQUEUE_PATTERN.search(content):
                has_queue_usage = True

            if DLQ_PATTERN.search(content):
                has_dlq = True

            if BACKOFF_JITTER_PATTERN.search(content):
                has_backoff = True

            if IDEMPOTENCY_PATTERN.search(content):
                has_idempotency = True

            # Detect heavy operations inside HTTP handlers
            if HTTP_HANDLER_PATTERN.search(content):
                lines = content.splitlines()
                for line_no, line in enumerate(lines, start=1):
                    match = HEAVY_OP_PATTERN.search(line)
                    if match and not QUEUE_ENQUEUE_PATTERN.search(line):
                        # Flag suspicious blocking call in controller
                        if 'controller' in rel_path.lower() or 'route' in rel_path.lower():
                            blocking_http_violations += 1
                            findings.append({
                                "file": rel_path,
                                "line": line_no,
                                "type": "blocking_heavy_operation_in_http",
                                "severity": "high",
                                "message": f"Found heavy synchronous operation `{match.group(0)}` in HTTP controller. Heavy work must be enqueued asynchronously."
                            })

    summary = {
        "scanned_files": scanned_files_count,
        "queue_architecture": {
            "queue_usage_detected": has_queue_usage,
            "dlq_configured": has_dlq or not has_queue_usage,
            "backoff_jitter_detected": has_backoff or not has_queue_usage,
            "idempotency_guards_detected": has_idempotency or not has_queue_usage,
            "blocking_http_violations": blocking_http_violations
        },
        "is_compliant": (
            blocking_http_violations == 0 and
            (not has_queue_usage or (has_dlq and has_backoff and has_idempotency))
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for asynchronous background processing standards."
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
        help="Exit with non-zero status if any violations or missing async job patterns are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Async jobs audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
