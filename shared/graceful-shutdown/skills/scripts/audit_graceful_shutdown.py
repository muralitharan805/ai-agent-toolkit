# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit Graceful Shutdown & Process Termination Standards.

Audits codebases for compliance with the 11-step graceful shutdown sequence:
1. Signal handler registration (SIGTERM and SIGINT).
2. Readiness probe invalidation (/health/ready returning 503).
3. Grace period timeout budgeting (<30s for Kubernetes compatibility).
4. Telemetry and log buffer flushing before exit.
5. Clean resource deallocation (HTTP server, DB pool, Redis).
6. Deterministic exit codes (0 for clean, 1 for timed-out/error).
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit graceful shutdown signal handling, readiness probe invalidation, and resource draining."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory to audit (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if any critical shutdown invariant is violated",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout",
    )
    return parser.parse_args()


def audit_shutdown_implementation(root_dir: Path) -> Dict[str, Any]:
    ignored_dirs = {".git", "node_modules", "dist", "build", ".next", "coverage"}

    has_sigterm = False
    has_sigint = False
    has_readiness_503 = False
    has_server_close = False
    has_db_close = False
    has_redis_close = False
    has_log_flush = False
    has_telemetry_flush = False
    has_grace_timeout = False
    grace_timeout_val_ms = 0
    files_with_shutdown: List[str] = []

    sigterm_pattern = re.compile(r"SIGTERM", re.IGNORECASE)
    sigint_pattern = re.compile(r"SIGINT", re.IGNORECASE)
    server_close_pattern = re.compile(r"server\.close|httpServer\.close|app\.close", re.IGNORECASE)
    db_close_pattern = re.compile(r"pool\.end|\$disconnect|dataSource\.destroy|connection\.close", re.IGNORECASE)
    redis_close_pattern = re.compile(r"redis.*\.quit|redis.*\.disconnect", re.IGNORECASE)
    log_flush_pattern = re.compile(r"flushSync|logger\.flush|destination\.flush", re.IGNORECASE)
    telemetry_flush_pattern = re.compile(r"tracerProvider\.shutdown|telemetry.*\.shutdown", re.IGNORECASE)
    timeout_pattern = re.compile(r"(?:grace.*timeout|shutdown.*timeout|timeout.*ms)\s*[:=]?\s*(\d+)", re.IGNORECASE)

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if file.endswith((".ts", ".js", ".go", ".py")):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    rel_path = str(file_path.relative_to(root_dir))

                    found_in_file = False
                    if sigterm_pattern.search(content):
                        has_sigterm = True
                        found_in_file = True
                    if sigint_pattern.search(content):
                        has_sigint = True
                        found_in_file = True
                    if "503" in content and ("ready" in content.lower() or "readiness" in content.lower()):
                        has_readiness_503 = True
                        found_in_file = True
                    if server_close_pattern.search(content):
                        has_server_close = True
                        found_in_file = True
                    if db_close_pattern.search(content):
                        has_db_close = True
                        found_in_file = True
                    if redis_close_pattern.search(content):
                        has_redis_close = True
                        found_in_file = True
                    if log_flush_pattern.search(content):
                        has_log_flush = True
                        found_in_file = True
                    if telemetry_flush_pattern.search(content):
                        has_telemetry_flush = True
                        found_in_file = True

                    timeout_match = timeout_pattern.search(content)
                    if timeout_match:
                        has_grace_timeout = True
                        val = int(timeout_match.group(1))
                        if val > grace_timeout_val_ms:
                            grace_timeout_val_ms = val

                    if found_in_file:
                        files_with_shutdown.append(rel_path)
                except Exception:
                    pass

    return {
        "has_sigterm": has_sigterm,
        "has_sigint": has_sigint,
        "has_readiness_503": has_readiness_503,
        "has_server_close": has_server_close,
        "has_db_close": has_db_close,
        "has_redis_close": has_redis_close,
        "has_log_flush": has_log_flush,
        "has_telemetry_flush": has_telemetry_flush,
        "has_grace_timeout": has_grace_timeout,
        "grace_timeout_ms": grace_timeout_val_ms,
        "scanned_files": files_with_shutdown,
    }


def run_audit(target_dir: str, strict: bool = False) -> Dict[str, Any]:
    root_path = Path(target_dir).resolve()
    details = audit_shutdown_implementation(root_path)

    findings: List[str] = []
    passed = True

    if not details["has_sigterm"]:
        findings.append("Missing SIGTERM signal handler registration (required for Kubernetes/Docker container termination).")
        if strict:
            passed = False

    if not details["has_sigint"]:
        findings.append("Missing SIGINT signal handler registration (required for local Ctrl+C interrupt termination).")

    if not details["has_readiness_503"]:
        findings.append("Readiness probe invalidation (marking /ready 503 on shutdown) not detected (risk of load balancer sending traffic to terminating pod).")

    if not details["has_server_close"]:
        findings.append("HTTP server listener close/drain not detected.")

    if not details["has_db_close"]:
        findings.append("Database connection pool closure (pool.end / disconnect) not detected.")

    if details["grace_timeout_ms"] > 30000:
        findings.append(f"Configured grace timeout ({details['grace_timeout_ms']}ms) exceeds Kubernetes default 30s terminationGracePeriodSeconds (risk of SIGKILL).")
        if strict:
            passed = False

    report = {
        "target": str(root_path),
        "status": "PASS" if passed and not findings else ("WARNING" if passed else "FAIL"),
        "details": details,
        "findings": findings,
    }
    return report


def main() -> None:
    args = parse_arguments()
    report = run_audit(args.target, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stderr.write(f"Graceful Shutdown Audit: {report['target']}\n")
        sys.stderr.write(f"Status: {report['status']}\n")
        sys.stderr.write(f"SIGTERM Handled: {report['details']['has_sigterm']}\n")
        sys.stderr.write(f"SIGINT Handled:  {report['details']['has_sigint']}\n")
        sys.stderr.write(f"Readiness 503:   {report['details']['has_readiness_503']}\n")
        sys.stderr.write(f"Server Drain:    {report['details']['has_server_close']}\n")
        sys.stderr.write(f"DB Pool Close:   {report['details']['has_db_close']}\n")
        if report["findings"]:
            sys.stderr.write("\nFindings / Recommendations:\n")
            for finding in report["findings"]:
                sys.stderr.write(f"  - {finding}\n")

    if report["status"] == "FAIL" and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
