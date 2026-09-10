# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Scheduled Jobs & Cron Audit Tool
Scans backend source for common cron job anti-patterns:
  - Missing distributed lock (Redis NX pattern)
  - Hardcoded cron expressions
  - Missing last_run_at tracking
  - Missing structured logs on start/complete/failure

Usage:
  python3 audit_scheduled_jobs.py <source-dir>
  python3 audit_scheduled_jobs.py --help

Output: JSON to stdout, diagnostics to stderr
"""

from __future__ import annotations
import json
import sys
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CronAuditResult:
    """Audit result for a single cron job finding."""

    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    recommendation: str


@dataclass
class AuditReport:
    """Complete audit report for scheduled jobs."""

    scanned_files: int = 0
    issues_found: list[CronAuditResult] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)


HARDCODED_CRON_PATTERN = re.compile(
    r"""(?:schedule|cron|addJob)\s*\(\s*['"](\d+\s+\d+\s+\d+\s+\d+\s+\d+)['"]""",
    re.MULTILINE,
)
REDIS_NX_PATTERN = re.compile(r"NX.*EX|set\s*\(.*NX", re.IGNORECASE)
LAST_RUN_AT_PATTERN = re.compile(r"last_run_at|lastRunAt", re.IGNORECASE)
STRUCTURED_LOG_PATTERN = re.compile(r"cron_job_started|cron_job_completed|cron_job_failed", re.IGNORECASE)


def scan_file(file_path: Path, report: AuditReport) -> None:
    """Scan a single source file for cron anti-patterns."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(f"[WARN] Cannot read {file_path}: {exc}", file=sys.stderr)
        return

    report.scanned_files += 1

    # Check for hardcoded cron expressions
    for match in HARDCODED_CRON_PATTERN.finditer(content):
        line_number = content[: match.start()].count("\n") + 1
        report.issues_found.append(
            CronAuditResult(
                file_path=str(file_path),
                line_number=line_number,
                issue_type="HARDCODED_CRON_EXPRESSION",
                severity="WARNING",
                description=f"Hardcoded cron expression '{match.group(1)}' found in source",
                recommendation="Load cron expression from config service or environment variable",
            )
        )

    # Only audit files that appear to contain cron/scheduler logic
    is_cron_file = bool(re.search(r"cron|schedule|scheduler|job", content, re.IGNORECASE))
    if not is_cron_file:
        return

    # Check for distributed lock
    if not REDIS_NX_PATTERN.search(content):
        report.issues_found.append(
            CronAuditResult(
                file_path=str(file_path),
                line_number=0,
                issue_type="MISSING_DISTRIBUTED_LOCK",
                severity="CRITICAL",
                description="Cron-related file has no Redis NX lock pattern detected",
                recommendation="Add Redis SET NX EX lock before every cron job execution to prevent duplicate runs",
            )
        )

    # Check for last_run_at tracking
    if not LAST_RUN_AT_PATTERN.search(content):
        report.issues_found.append(
            CronAuditResult(
                file_path=str(file_path),
                line_number=0,
                issue_type="MISSING_LAST_RUN_AT_TRACKING",
                severity="WARNING",
                description="No last_run_at tracking found in cron-related file",
                recommendation="Update last_run_at in scheduled_jobs table on every successful completion",
            )
        )

    # Check for structured logs
    if not STRUCTURED_LOG_PATTERN.search(content):
        report.issues_found.append(
            CronAuditResult(
                file_path=str(file_path),
                line_number=0,
                issue_type="MISSING_STRUCTURED_LOGS",
                severity="WARNING",
                description="No structured cron job event logs (cron_job_started/completed/failed) detected",
                recommendation="Emit structured logs with event names on start, completion, and failure",
            )
        )


def audit_directory(source_dir: Path) -> AuditReport:
    """Scan all TypeScript, JavaScript, and Python source files."""
    report = AuditReport()
    extensions = {".ts", ".js", ".py", ".java", ".go", ".cs"}

    for file_path in source_dir.rglob("*"):
        if file_path.suffix not in extensions:
            continue
        if any(part in file_path.parts for part in {"node_modules", ".git", "dist", "__pycache__"}):
            continue
        scan_file(file_path, report)

    if not report.issues_found:
        report.passed_checks.append("No cron anti-patterns detected in scanned files")

    return report


def main() -> None:
    """Entry point for the audit CLI tool."""
    parser = argparse.ArgumentParser(
        description="Audit scheduled jobs and cron patterns for production anti-patterns"
    )
    parser.add_argument("source_dir", nargs="?", default="src", help="Source directory to scan")
    args = parser.parse_args()

    source_path = Path(args.source_dir)
    if not source_path.exists():
        print(json.dumps({"error": f"Directory not found: {source_path}"}))
        sys.exit(1)

    print(f"[INFO] Scanning {source_path} for cron anti-patterns...", file=sys.stderr)
    report = audit_directory(source_path)

    output = {
        "tool": "audit_scheduled_jobs",
        "scanned_files": report.scanned_files,
        "issues_found": len(report.issues_found),
        "passed_checks": report.passed_checks,
        "issues": [
            {
                "file": r.file_path,
                "line": r.line_number,
                "type": r.issue_type,
                "severity": r.severity,
                "description": r.description,
                "recommendation": r.recommendation,
            }
            for r in report.issues_found
        ],
    }

    print(json.dumps(output, indent=2))

    critical_count = sum(1 for i in report.issues_found if i.severity == "CRITICAL")
    if critical_count > 0:
        print(f"[ERROR] {critical_count} CRITICAL issues found.", file=sys.stderr)
        sys.exit(1)

    print("[OK] Audit passed.", file=sys.stderr)


if __name__ == "__main__":
    main()
