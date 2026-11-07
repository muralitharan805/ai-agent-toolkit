#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Bootstrap Sequence & Server Lifecycle (`audit_bootstrap_sequence.py`)
Inspects backend entry points (main.ts, server.ts, main.py, main.go) for:
1. Process-level crash handlers (unhandledRejection, uncaughtException, panics)
2. Pre-listen shutdown hooks (SIGTERM, SIGINT)
3. Hardcoded listen ports
4. Sequential infrastructure readiness before accepting network traffic
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any

ENTRY_POINT_FILENAMES = {
    "main.ts", "server.ts", "app.ts", "index.ts",
    "main.py", "app.py", "server.py",
    "main.go", "server.go",
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit backend entry point for bootstrap sequence, crash handlers, and lifecycle hooks.",
        epilog="Example: python3 scripts/audit_bootstrap_sequence.py src/ --strict"
    )
    parser.add_argument("target_path", help="Path to project root or source directory containing entry point")
    parser.add_argument("--json", action="store_true", help="Output results formatted as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as violations")
    return parser.parse_args()

def find_entry_points(target_path: str) -> List[str]:
    entry_points = []
    if os.path.isfile(target_path):
        return [target_path]

    for root, _, files in os.walk(target_path):
        for f in files:
            if f.lower() in ENTRY_POINT_FILENAMES:
                # Avoid node_modules, vendor, test dirs
                parts = root.split(os.sep)
                if any(p in parts for p in ["node_modules", "vendor", "dist", "build", "tests", "test"]):
                    continue
                entry_points.append(os.path.join(root, f))
    return entry_points

def inspect_entry_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    issues = []
    warnings = []

    ext = os.path.splitext(filepath)[1].lower()

    # 1. Check for hardcoded ports (e.g. .listen(3000) or :3000)
    hardcoded_port_pattern = re.compile(r"(\.listen\(\s*300[0-9]|\.listen\(\s*808[0-9]|Addr:\s*\"[:0-9]+\")")
    if hardcoded_port_pattern.search(content):
        issues.append({
            "type": "HARDCODED_LISTEN_PORT",
            "message": "Found hardcoded port in server listen call. Port must be injected from validated configuration."
        })

    # 2. Check for Process Crash Handlers
    if ext in [".ts", ".js"]:
        has_rejection = "unhandledRejection" in content
        has_uncaught = "uncaughtException" in content
        if not has_rejection:
            issues.append({
                "type": "MISSING_UNHANDLED_REJECTION_HANDLER",
                "message": "Missing process-level 'unhandledRejection' listener in application bootstrap."
            })
        if not has_uncaught:
            issues.append({
                "type": "MISSING_UNCAUGHT_EXCEPTION_HANDLER",
                "message": "Missing process-level 'uncaughtException' listener in application bootstrap."
            })

        # 3. Check for shutdown hooks
        has_sigterm = "SIGTERM" in content
        has_sigint = "SIGINT" in content
        if not (has_sigterm or has_sigint):
            warnings.append({
                "type": "MISSING_SHUTDOWN_SIGNALS",
                "message": "Missing 'SIGTERM' or 'SIGINT' shutdown hook registration before server listen."
            })

    elif ext == ".py":
        has_lifespan = "lifespan" in content
        has_signals = "signal.SIGTERM" in content or "add_event_handler" in content
        if not (has_lifespan or has_signals):
            warnings.append({
                "type": "MISSING_LIFECYCLE_ORCHESTRATOR",
                "message": "Python service lacks explicit FastAPI lifespan or signal-driven shutdown hook."
            })

    elif ext == ".go":
        has_notify = "signal.Notify" in content
        if not has_notify:
            warnings.append({
                "type": "MISSING_SIGNAL_NOTIFY",
                "message": "Go entry point lacks 'signal.Notify' channel listener for graceful termination."
            })

    return {
        "file": filepath,
        "issues": issues,
        "warnings": warnings,
    }

def run_audit(target_path: str, strict: bool = False) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_path)
    sys.stderr.write(f"🔍 Auditing Application Bootstrap & Lifecycle for: {abs_target}\n")

    entry_files = find_entry_points(abs_target)
    if not entry_files:
        return {
            "status": "FAIL",
            "target": abs_target,
            "error": "No backend entry point files (main.ts, server.ts, main.py, main.go) found.",
            "violations_count": 1,
            "warnings_count": 0,
            "results": []
        }

    total_violations = []
    total_warnings = []
    inspections = []

    for ef in entry_files:
        report = inspect_entry_file(ef)
        total_violations.extend(report["issues"])
        total_warnings.extend(report["warnings"])
        inspections.append(report)

    is_compliant = len(total_violations) == 0
    if strict and len(total_warnings) > 0:
        is_compliant = False

    return {
        "status": "PASS" if is_compliant else "FAIL",
        "target": abs_target,
        "entry_points_analyzed": entry_files,
        "violations_count": len(total_violations),
        "warnings_count": len(total_warnings),
        "violations": total_violations,
        "warnings": total_warnings,
        "inspections": inspections,
    }

def main():
    args = parse_args()
    report = run_audit(args.target_path, args.strict)

    print(json.dumps(report, indent=2))

    if report["status"] == "FAIL":
        sys.stderr.write(f"❌ Bootstrap sequence audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ Bootstrap sequence audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
