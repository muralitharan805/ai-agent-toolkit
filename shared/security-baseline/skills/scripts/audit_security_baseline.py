#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Security Baseline Script
Audits backend codebases for runtime security baseline configurations:
- HTTP security headers (Helmet / CSP / HSTS / X-Frame-Options)
- Strict CORS origin whitelisting (prohibiting wildcard with credentials)
- Ingress rate limiting enforcement
- Request payload and body size ceilings (e.g. 1MB limits)
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

HELMET_PATTERN = re.compile(r'\b(helmet\s*\(|contentSecurityPolicy|hsts|frameguard|noSniff)\b', re.IGNORECASE)
CORS_WILDCARD_CREDENTIALS = re.compile(r'origin\s*:\s*(\*|true|[\'"`]\*[\'"`]).*?credentials\s*:\s*true', re.DOTALL | re.IGNORECASE)
RATE_LIMIT_PATTERN = re.compile(r'\b(rateLimit|express-rate-limit|RateLimiter|Throttler|throttle)\b', re.IGNORECASE)
BODY_LIMIT_PATTERN = re.compile(r'limit\s*:\s*[\'"`](1mb|2mb|500kb|\d+mb)[\'"`]', re.IGNORECASE)

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
    has_security_headers = False
    has_rate_limiting = False
    has_body_limit = False
    has_cors_wildcard_flaw = False

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

            if HELMET_PATTERN.search(content):
                has_security_headers = True

            if RATE_LIMIT_PATTERN.search(content):
                has_rate_limiting = True

            if BODY_LIMIT_PATTERN.search(content):
                has_body_limit = True

            if CORS_WILDCARD_CREDENTIALS.search(content):
                has_cors_wildcard_flaw = True
                findings.append({
                    "file": rel_path,
                    "type": "insecure_cors_wildcard_credentials",
                    "severity": "critical",
                    "message": "Found wildcard or dynamic CORS origin combined with credentials: true. This violates browser security and enables credential theft."
                })

    summary = {
        "scanned_files": scanned_files_count,
        "security_baseline": {
            "security_headers_detected": has_security_headers,
            "rate_limiting_detected": has_rate_limiting,
            "body_payload_limits_configured": has_body_limit,
            "zero_cors_wildcard_flaws": not has_cors_wildcard_flaw
        },
        "is_compliant": (
            not has_cors_wildcard_flaw and
            has_security_headers
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for runtime security baseline configurations."
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
        help="Exit with non-zero status if any security baseline violations are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Security baseline audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
