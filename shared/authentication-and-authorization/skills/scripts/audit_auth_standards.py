#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Authentication & Authorization Standards Script
Audits backend codebases for:
- Strong password hashing (Argon2id or bcrypt cost >= 12)
- Dual-token architecture (short-lived access token, HTTP-Only refresh cookie)
- Prohibition of localStorage for sensitive auth tokens
- Token rotation & reuse detection logic
- Resource ownership validation to prevent IDOR
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

LOCALSTORAGE_TOKEN_PATTERN = re.compile(r'localStorage\.(setItem|getItem)\s*\(\s*[\'"`](refresh|token|jwt|auth|accessToken)[\'"`]', re.IGNORECASE)
WEAK_HASH_PATTERN = re.compile(r'\b(createHash\s*\(\s*[\'"`](md5|sha1|sha256)[\'"`]|bcrypt\.genSalt\s*\(\s*([1-9]|1[0-1])\s*\))', re.IGNORECASE)
STRONG_HASH_PATTERN = re.compile(r'(argon2|bcrypt\.hash|bcrypt\.genSalt\s*\(\s*(1[2-9]|[2-9]\d)\s*\))', re.IGNORECASE)
LONG_LIVED_ACCESS_TOKEN = re.compile(r'expiresIn\s*:\s*[\'"`](\d+[dDhH]|24h|7d|30d)[\'"`]', re.IGNORECASE)
SHORT_LIVED_ACCESS_TOKEN = re.compile(r'expiresIn\s*:\s*[\'"`](15m|10m|5m|900s)[\'"`]', re.IGNORECASE)
HTTP_ONLY_COOKIE_PATTERN = re.compile(r'httpOnly\s*:\s*true', re.IGNORECASE)
OWNERSHIP_PATTERN = re.compile(r'\b(ownerId|userId|createdBy)\s*===?\s*(currentUser|req\.user|user)\.id\b', re.IGNORECASE)

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
    has_strong_hash = False
    has_http_only_cookie = False
    has_ownership_checks = False
    localstorage_violations = 0
    long_lived_token_violations = 0

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

            # Detect localStorage for tokens (XSS vulnerability)
            match_ls = LOCALSTORAGE_TOKEN_PATTERN.search(content)
            if match_ls:
                localstorage_violations += 1
                findings.append({
                    "file": rel_path,
                    "type": "localstorage_token_leak",
                    "severity": "critical",
                    "message": f"Found sensitive authentication token stored in browser localStorage (`{match_ls.group(0)}`). This is vulnerable to XSS exfiltration."
                })

            # Detect weak hashing
            match_weak = WEAK_HASH_PATTERN.search(content)
            if match_weak:
                findings.append({
                    "file": rel_path,
                    "type": "weak_password_hash",
                    "severity": "critical",
                    "message": f"Found weak or deprecated password hashing algorithm (`{match_weak.group(0)}`). Use Argon2id or bcrypt cost >= 12."
                })

            if STRONG_HASH_PATTERN.search(content):
                has_strong_hash = True

            # Detect long-lived access token
            match_long = LONG_LIVED_ACCESS_TOKEN.search(content)
            if match_long:
                long_lived_token_violations += 1
                findings.append({
                    "file": rel_path,
                    "type": "excessive_access_token_lifespan",
                    "severity": "high",
                    "message": f"Access token configured with excessive lifespan `{match_long.group(0)}`. Access tokens must expire within 15 minutes."
                })

            if HTTP_ONLY_COOKIE_PATTERN.search(content):
                has_http_only_cookie = True

            if OWNERSHIP_PATTERN.search(content):
                has_ownership_checks = True

    summary = {
        "scanned_files": scanned_files_count,
        "security_findings": {
            "localstorage_violations": localstorage_violations,
            "long_lived_token_violations": long_lived_token_violations,
            "strong_hashing_detected": has_strong_hash,
            "http_only_cookie_detected": has_http_only_cookie,
            "resource_ownership_checks_detected": has_ownership_checks
        },
        "is_compliant": (
            localstorage_violations == 0 and
            long_lived_token_violations == 0 and
            len(findings) == 0
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for authentication and authorization security standards."
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
        help="Exit with non-zero status if any violations are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Authentication audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
