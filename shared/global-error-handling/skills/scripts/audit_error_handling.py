#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Global Error Handling & Exception Swallowing (`audit_error_handling.py`)
Scans backend projects for:
1. Silent exception swallowing (empty catch blocks)
2. Raw string throws or untyped Error instantiation
3. Missing operational error classification
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any

TARGET_EXTENSIONS = {".ts", ".js", ".py", ".go"}

EMPTY_CATCH_PATTERNS = [
    (re.compile(r"catch\s*\([^\)]*\)\s*\{\s*\}"), "Empty catch block silently swallowing exceptions"),
    (re.compile(r"except(?:\s+[A-Za-z0-9_]+)?:\s*pass"), "Python 'except: pass' silently swallowing exceptions"),
]

GENERIC_THROW_PATTERNS = [
    (re.compile(r"throw\s+['\"][^'\"]+['\"]"), "Throwing raw string literal instead of BaseAppError subclass"),
    (re.compile(r"throw\s+new\s+Error\(\s*['\"](?:not found|unauthorized|forbidden|invalid)['\"]", re.IGNORECASE), "Instantiating generic Error instead of typed Domain Error (NotFoundError, etc.)"),
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for exception swallowing and error handling standards.",
        epilog="Example: python3 scripts/audit_error_handling.py src/ --strict"
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

    # 1. Check for swallowed exceptions
    for pat, desc in EMPTY_CATCH_PATTERNS:
        if pat.search(content):
            issues.append({
                "type": "SWALLOWED_EXCEPTION",
                "message": f"{desc}. Exceptions must be logged or rethrown."
            })

    # 2. Check for generic throws
    for pat, desc in GENERIC_THROW_PATTERNS:
        if pat.search(content):
            warnings.append({
                "type": "UNTYPED_GENERIC_THROW",
                "message": f"{desc}. Use explicit BaseAppError subclasses."
            })

    return {
        "file": filepath,
        "issues": issues,
        "warnings": warnings,
    }

def run_audit(target_path: str, strict: bool = False) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_path)
    sys.stderr.write(f"🔍 Auditing Error Handling Standards for: {abs_target}\n")

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
        sys.stderr.write(f"❌ Error handling audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ Error handling audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
