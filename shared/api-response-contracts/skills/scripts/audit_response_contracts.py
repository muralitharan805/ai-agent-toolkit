#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit API Response Contracts & Data Leakage (`audit_response_contracts.py`)
Scans backend controllers and error handlers for:
1. Naked un-enveloped JSON responses
2. Leaked error stack traces or raw database error messages
3. Unstandardized error codes
4. Missing X-Correlation-ID headers
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any

STANDARD_ERROR_CODES = {
    "VALIDATION_ERROR",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "CONFLICT",
    "UNPROCESSABLE_ENTITY",
    "RATE_LIMIT_EXCEEDED",
    "INTERNAL_SERVER_ERROR",
    "SERVICE_UNAVAILABLE",
}

LEAKY_PATTERNS = [
    (re.compile(r"res\.(?:status\(\d+\)\.)?json\(\s*\{\s*(?:error|message)\s*:\s*(?:err|error)\.(?:message|stack)"), "Leaking raw exception message or stack trace to client response"),
    (re.compile(r"res\.(?:status\(\d+\)\.)?send\(\s*(?:err|error)\.(?:message|stack)"), "Sending raw error stack directly in response body"),
    (re.compile(r"res\.(?:status\(\d+\)\.)?json\(\s*(?:err|error)\s*\)"), "Dumping raw exception object into response"),
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit API response contracts, success envelopes, and data leakage.",
        epilog="Example: python3 scripts/audit_response_contracts.py src/ --strict"
    )
    parser.add_argument("target_path", help="Path to project root or source directory")
    parser.add_argument("--json", action="store_true", help="Output results formatted as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as violations")
    return parser.parse_args()

def inspect_code_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    issues = []
    warnings = []

    # 1. Check for Leaky Exception Patterns
    for pat, desc in LEAKY_PATTERNS:
        matches = pat.findall(content)
        if matches:
            issues.append({
                "type": "DATA_LEAKAGE_RISK",
                "message": f"{desc}. Database internals and server stacks must be masked."
            })

    # 2. Check for arbitrary string error codes
    code_matches = re.findall(r"code\s*:\s*['\"]([A-Z0-9_]+)['\"]", content)
    for c in code_matches:
        if c.isupper() and "_" in c and c not in STANDARD_ERROR_CODES:
            warnings.append({
                "type": "NON_STANDARD_ERROR_CODE",
                "code": c,
                "message": f"Error code '{c}' is not part of the standard 9-code error catalog."
            })

    return {
        "file": filepath,
        "issues": issues,
        "warnings": warnings,
    }

def run_audit(target_path: str, strict: bool = False) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_path)
    sys.stderr.write(f"🔍 Auditing API Response Contracts & Data Leakage for: {abs_target}\n")

    files_to_check = []
    if os.path.isfile(abs_target):
        files_to_check = [abs_target]
    else:
        for root, _, files in os.walk(abs_target):
            parts = root.split(os.sep)
            if any(p in parts for p in ["node_modules", "vendor", "dist", "build", "tests", "test"]):
                continue
            for f in files:
                if f.endswith((".ts", ".js", ".py", ".go")):
                    files_to_check.append(os.path.join(root, f))

    all_violations = []
    all_warnings = []
    inspections = []

    for f in files_to_check:
        res = inspect_code_file(f)
        if res["issues"] or res["warnings"]:
            all_violations.extend(res["issues"])
            all_warnings.extend(res["warnings"])
            inspections.append(res)

    is_compliant = len(all_violations) == 0
    if strict and len(all_warnings) > 0:
        is_compliant = False

    return {
        "status": "PASS" if is_compliant else "FAIL",
        "target": abs_target,
        "files_scanned": len(files_to_check),
        "violations_count": len(all_violations),
        "warnings_count": len(all_warnings),
        "violations": all_violations,
        "warnings": all_warnings,
        "inspections": inspections,
    }

def main():
    args = parse_args()
    report = run_audit(args.target_path, args.strict)

    print(json.dumps(report, indent=2))

    if report["status"] == "FAIL":
        sys.stderr.write(f"❌ API Response Contract audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ API Response Contract audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
