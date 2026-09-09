#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.9"
# ///

"""
audit_signal_antipatterns.py
Autonomous diagnostic script for auditing Angular source files for Signal anti-patterns.
Emits structured JSON to stdout and diagnostic progress to stderr.
"""

import os
import sys
import re
import json
import argparse
from typing import List, Dict, Any

# Anti-pattern regular expressions
PATTERNS = [
    {
        "id": "DEPRECATED_MUTATE",
        "severity": "error",
        "regex": re.compile(r"\b[a-zA-Z0-9_$]+\.mutate\s*\("),
        "message": "Signal .mutate() is deprecated and removed in modern Angular. Use .update() with immutable state transformation instead."
    },
    {
        "id": "MUTATION_IN_UPDATE",
        "severity": "error",
        "regex": re.compile(r"\.update\s*\(\s*(?:\w+|\([^)]*\))\s*=>\s*\{?[^}]*\.(?:push|pop|shift|unshift|splice|sort|reverse)\s*\("),
        "message": "In-place array mutation inside signal .update(). Always return a new array instance (e.g., [...prev, item])."
    },
    {
        "id": "TO_SIGNAL_UNGUARDED",
        "severity": "warning",
        "regex": re.compile(r"toSignal\s*\(\s*[^,)]+\s*\)"),
        "message": "toSignal() called without options. Supply '{ initialValue: ... }' or '{ requireSync: true }' to avoid 'undefined' type widening."
    },
    {
        "id": "EFFECT_SIGNAL_WRITE",
        "severity": "warning",
        "regex": re.compile(r"effect\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\.(?:set|update)\s*\("),
        "message": "Writing to signals inside an effect() is an architectural code smell. Consider computed() or linkedSignal() instead."
    },
    {
        "id": "BEHAVIOR_SUBJECT_USAGE",
        "severity": "info",
        "regex": re.compile(r"new\s+BehaviorSubject\s*<"),
        "message": "BehaviorSubject detected. In modern Angular (v19+), signal() or linkedSignal() is preferred for synchronous state."
    }
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit Angular TypeScript files for Signal anti-patterns.",
        epilog="Example:\n  python3 scripts/audit_signal_antipatterns.py src/app\n  python3 scripts/audit_signal_antipatterns.py --strict src/app",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target_path", help="Path to directory or TypeScript file to inspect")
    parser.add_argument("--strict", action="store_true", help="Fail with exit code 1 if any warnings or errors are found")
    parser.add_argument("--json", action="store_true", default=True, help="Emit results as JSON on stdout (default)")
    return parser.parse_args()

def check_file(file_path: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        sys.stderr.write(f"⚠️ Failed to read {file_path}: {e}\n")
        return findings

    # Check for computed writing into signals
    computed_blocks = re.finditer(r"computed\s*(?:<[^>]+>)?\s*\(\s*\(\s*\)\s*=>\s*\{([^}]+)\}", content)
    for match in computed_blocks:
        body = match.group(1)
        if re.search(r"\.(?:set|update)\s*\(", body):
            line_no = content[:match.start()].count("\n") + 1
            findings.append({
                "rule_id": "COMPUTED_SIGNAL_MUTATION",
                "severity": "error",
                "line": line_no,
                "message": "Writing or modifying signals inside computed() is strictly forbidden and causes runtime errors."
            })

    # Line-by-line / regex audits
    lines = content.splitlines()
    for pattern in PATTERNS:
        matches = pattern["regex"].finditer(content)
        for m in matches:
            line_no = content[:m.start()].count("\n") + 1
            findings.append({
                "rule_id": pattern["id"],
                "severity": pattern["severity"],
                "line": line_no,
                "message": pattern["message"]
            })

    return findings

def main():
    args = parse_args()
    target = os.path.abspath(args.target_path)

    if not os.path.exists(target):
        sys.stderr.write(f"❌ Target path does not exist: {target}\n")
        sys.exit(1)

    sys.stderr.write(f"🔍 Auditing Angular signal usage in '{target}'...\n")

    files_to_scan = []
    if os.path.isfile(target):
        if target.endswith((".ts", ".html")):
            files_to_scan.append(target)
    else:
        for root, _, files in os.walk(target):
            for file in files:
                if file.endswith(".ts") and not file.endswith(".spec.ts"):
                    files_to_scan.append(os.path.join(root, file))

    total_files = len(files_to_scan)
    total_errors = 0
    total_warnings = 0
    report_items = []

    for file_path in files_to_scan:
        rel_path = os.path.relpath(file_path, os.getcwd())
        file_findings = check_file(file_path)
        if file_findings:
            for f in file_findings:
                if f["severity"] == "error":
                    total_errors += 1
                elif f["severity"] == "warning":
                    total_warnings += 1

            report_items.append({
                "file": rel_path,
                "findings": file_findings
            })

    status = "clean" if total_errors == 0 and total_warnings == 0 else "issues_found"
    passed = total_errors == 0 and (not args.strict or total_warnings == 0)

    report = {
        "status": status,
        "passed": passed,
        "scanned_files_count": total_files,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "reports": report_items
    }

    if passed:
        sys.stderr.write(f"✅ Audit completed: {total_files} files scanned, {total_errors} errors, {total_warnings} warnings.\n")
    else:
        sys.stderr.write(f"❌ Audit failed: {total_files} files scanned, {total_errors} errors, {total_warnings} warnings.\n")

    print(json.dumps(report, indent=2))

    if not passed:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
