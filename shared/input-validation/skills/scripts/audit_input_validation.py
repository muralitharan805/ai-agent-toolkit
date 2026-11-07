#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Inbound Input Validation & Mass Assignment Hygiene (`audit_input_validation.py`)
Scans backend controllers and routes for:
1. Untyped / any request body access
2. Missing whitelist configuration (mass assignment vulnerability)
3. Direct unvalidated req.body passing into database queries
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any

TARGET_EXTENSIONS = {".ts", ".js", ".py", ".go"}

VULNERABILITY_PATTERNS = [
    (re.compile(r"@Body\(\)\s+[a-zA-Z0-9_]+\s*:\s*any\b"), "Controller accepts 'any' type for request body. Must use typed DTO class."),
    (re.compile(r"new\s+ValidationPipe\(\s*\)"), "ValidationPipe instantiated without '{ whitelist: true }'. Mass assignment vulnerability risk."),
    (re.compile(r"(?:db|prisma|repo|repository)\.[a-zA-Z0-9_]+\.(?:create|update)\(\s*\{\s*data\s*:\s*req\.body\s*\}"), "Passing raw unvalidated 'req.body' directly into database query. Critical mass assignment flaw!"),
    (re.compile(r"\.safeParse\([^)]+\)"), "VALIDATION_FOUND"),
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for input validation standards and mass assignment risks.",
        epilog="Example: python3 scripts/audit_input_validation.py src/ --strict"
    )
    parser.add_argument("target_path", help="Path to project root or source directory")
    parser.add_argument("--json", action="store_true", help="Output results formatted as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as violations")
    return parser.parse_args()

def inspect_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    issues = []
    warnings = []

    for pat, desc in VULNERABILITY_PATTERNS:
        if desc == "VALIDATION_FOUND":
            continue
        matches = pat.findall(content)
        if matches:
            issues.append({
                "type": "INPUT_VALIDATION_FLAW",
                "message": desc,
                "count": len(matches),
            })

    return {
        "file": filepath,
        "issues": issues,
        "warnings": warnings,
    }

def run_audit(target_path: str, strict: bool = False) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_path)
    sys.stderr.write(f"🔍 Auditing Input Validation & Mass Assignment Hygiene for: {abs_target}\n")

    files_to_check = []
    if os.path.isfile(abs_target):
        files_to_check = [abs_target]
    else:
        for root, _, files in os.walk(abs_target):
            parts = root.split(os.sep)
            if any(p in parts for p in ["node_modules", "vendor", "dist", "build", "tests", "test"]):
                continue
            for f in files:
                if os.path.splitext(f)[1].lower() in TARGET_EXTENSIONS:
                    files_to_check.append(os.path.join(root, f))

    all_violations = []
    all_warnings = []
    inspections = []

    for f in files_to_check:
        res = inspect_file(f)
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
        sys.stderr.write(f"❌ Input validation audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ Input validation audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
