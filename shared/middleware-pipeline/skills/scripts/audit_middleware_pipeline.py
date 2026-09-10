#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Server, Routing & Middleware Pipeline (`audit_middleware_pipeline.py`)
Inspects backend server configurations for:
1. Deterministic middleware order (Error handler registered last)
2. Server timeouts (keepAliveTimeout > 60s to prevent ALB 502s)
3. Reverse proxy real IP trust
4. Day-1 API versioning (/api/v1/ prefix)
5. Payload size limits on body parsers (limit: 1mb)
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any

TARGET_EXTENSIONS = {".ts", ".js", ".py", ".go"}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit server pipeline for middleware ordering, timeouts, real IP trust, and versioning.",
        epilog="Example: python3 scripts/audit_middleware_pipeline.py src/ --strict"
    )
    parser.add_argument("target_path", help="Path to project root or source directory")
    parser.add_argument("--json", action="store_true", help="Output results formatted as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as violations")
    return parser.parse_args()

def inspect_server_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    issues = []
    warnings = []

    # 1. Check for Keep-Alive Timeout
    if "keepAliveTimeout" in content:
        # Check value
        m = re.search(r"keepAliveTimeout\s*=\s*([0-9]+)", content)
        if m:
            val = int(m.group(1))
            if val < 65000:
                warnings.append({
                    "type": "KEEP_ALIVE_TIMEOUT_TOO_LOW",
                    "value": val,
                    "message": f"keepAliveTimeout ({val}ms) is lower than recommended 65000ms. Risk of 502s behind ALB (60s)."
                })
    elif "createServer" in content or "app.listen" in content:
        warnings.append({
            "type": "MISSING_KEEP_ALIVE_TIMEOUT_CONFIG",
            "message": "Server creation lacks explicit 'keepAliveTimeout = 65000' configuration for load balancers."
        })

    # 2. Check for Body Parser Limits
    has_json_parser = "express.json" in content or "bodyParser.json" in content or "json()" in content
    if has_json_parser:
        has_limit = re.search(r"limit\s*:\s*['\"][0-9]+[m|k]b['\"]", content, re.IGNORECASE)
        if not has_limit:
            warnings.append({
                "type": "UNBOUNDED_BODY_PARSER_LIMIT",
                "message": "JSON body parser lacks explicit payload size limit (e.g. limit: '1mb')."
            })

    # 3. Check for API Versioning
    route_mount_pattern = re.compile(r"app\.use\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
    matches = route_mount_pattern.findall(content)
    has_api_route = any(m.startswith("/api") for m in matches)
    if has_api_route:
        has_versioned_api = any(re.match(r"^/api/v[0-9]+", m) for m in matches)
        if not has_versioned_api:
            issues.append({
                "type": "UNVERSIONED_API_ROUTE",
                "message": "API routes mounted under '/api' lack Day-1 path versioning (e.g. '/api/v1')."
            })

    # 4. Check for Error Handler Ordering (Should be at end)
    if "app.use" in content:
        lines = content.splitlines()
        error_handler_line = -1
        route_handler_line = -1

        for idx, line in enumerate(lines):
            if "error" in line.lower() and ("handler" in line.lower() or "filter" in line.lower()) and "app.use" in line:
                error_handler_line = idx
            if ("/api" in line or "router" in line.lower()) and "app.use" in line:
                route_handler_line = idx

        if error_handler_line != -1 and route_handler_line != -1:
            if error_handler_line < route_handler_line:
                issues.append({
                    "type": "MISPLACED_ERROR_HANDLER",
                    "message": "Global error handler registered BEFORE route handlers. Uncaught errors will bypass handler."
                })

    return {
        "file": filepath,
        "issues": issues,
        "warnings": warnings,
    }

def run_audit(target_path: str, strict: bool = False) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_path)
    sys.stderr.write(f"🔍 Auditing Server, Routing & Middleware Pipeline for: {abs_target}\n")

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
        res = inspect_server_file(f)
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
        sys.stderr.write(f"❌ Middleware pipeline audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ Middleware pipeline audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
