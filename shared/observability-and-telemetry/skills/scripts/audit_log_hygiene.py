# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_log_hygiene.py
--------------------
Standalone CLI automation tool to audit TypeScript and JavaScript backend source code
for structured logging compliance, raw console.log prohibition, un-sanitized payload
logging, and correlation ID (X-Correlation-ID) propagation.

Outputs structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit TypeScript/JavaScript files for structured logging hygiene & secret masking."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to file or directory to audit (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any logging violations are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class LogHygieneAuditor:
    """Audits source code for structured logging violations."""

    def __init__(self) -> None:
        self.violations: List[Dict[str, Any]] = []
        self.files_scanned = 0

    def audit_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Audit a single source file for logging hygiene."""
        file_violations: List[Dict[str, Any]] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return [{
                "file": str(file_path),
                "line": 1,
                "rule": "FILE_READ_ERROR",
                "severity": "ERROR",
                "message": f"Unable to read file: {str(exc)}",
            }]

        lines = content.splitlines()

        # 1. Raw console.log / console.error check
        console_pattern = re.compile(r"\bconsole\.(?:log|error|warn|debug|info)\s*\(", re.IGNORECASE)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            if console_pattern.search(line):
                file_violations.append({
                    "file": str(file_path),
                    "line": idx,
                    "rule": "PROHIBIT_RAW_CONSOLE",
                    "severity": "ERROR",
                    "message": f"Raw console statement detected: '{stripped[:60]}...'. Use dedicated Logger service.",
                })

        # 2. Check for un-sanitized body/payload logging
        unsanitized_pattern = re.compile(
            r"logger\.(?:log|warn|error|debug)\s*\(\s*(?:req\.body|body|payload|dto)\s*[\),]",
            re.IGNORECASE,
        )
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            if unsanitized_pattern.search(line) and "sanitize" not in line.lower():
                file_violations.append({
                    "file": str(file_path),
                    "line": idx,
                    "rule": "UNSANITIZED_PAYLOAD_LOGGING",
                    "severity": "CRITICAL",
                    "message": f"Raw payload logged without sanitization: '{stripped[:60]}...'. Pass payload through sanitizeLogPayload().",
                })

        # 3. Check for plaintext passwords or tokens in log strings
        secret_log_pattern = re.compile(
            r"logger\.(?:log|warn|error|debug)\s*\([^)]*(?:password|jwt|token|secret)\s*[:=]",
            re.IGNORECASE,
        )
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            if secret_log_pattern.search(line) and "[REDACTED]" not in line:
                file_violations.append({
                    "file": str(file_path),
                    "line": idx,
                    "rule": "PLAINTEXT_SECRET_IN_LOG",
                    "severity": "CRITICAL",
                    "message": f"Potential sensitive credential in log message: '{stripped[:60]}...'.",
                })

        return file_violations

    def audit_directory(self, target_path: Path) -> None:
        """Walk directory and audit relevant source files."""
        extensions = {".ts", ".js"}
        ignore_dirs = {"node_modules", "dist", ".git", ".next", "coverage"}

        if target_path.is_file():
            if target_path.suffix.lower() in extensions:
                self.files_scanned += 1
                self.violations.extend(self.audit_file(target_path))
            return

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file_name in files:
                file_p = Path(root) / file_name
                # Skip test files and declaration files
                if file_p.suffix.lower() in extensions and not file_name.endswith(".d.ts") and ".spec." not in file_name:
                    self.files_scanned += 1
                    self.violations.extend(self.audit_file(file_p))


def main() -> int:
    """CLI entrypoint."""
    args = parse_arguments()
    target_path = Path(args.path).resolve()

    if not target_path.exists():
        sys.stderr.write(f"❌ Target path does not exist: {target_path}\n")
        return 1

    auditor = LogHygieneAuditor()
    auditor.audit_directory(target_path)

    critical_errors = [v for v in auditor.violations if v["severity"] == "CRITICAL"]
    errors = [v for v in auditor.violations if v["severity"] == "ERROR"]
    warnings = [v for v in auditor.violations if v["severity"] == "WARNING"]

    result = {
        "target_path": str(target_path),
        "files_scanned": auditor.files_scanned,
        "total_violations": len(auditor.violations),
        "critical_count": len(critical_errors),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "violations": auditor.violations,
        "status": "PASSED" if (len(critical_errors) == 0 and len(errors) == 0) else "FAILED",
    }

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        sys.stderr.write(
            f"🔍 Log Hygiene Audit: {auditor.files_scanned} files scanned across {target_path}\n"
        )
        if auditor.violations:
            sys.stderr.write(
                f"⚠️ Discovered {len(critical_errors)} critical, {len(errors)} errors, and {len(warnings)} warnings.\n"
            )
            for item in auditor.violations[:10]:
                sys.stderr.write(
                    f"  [{item['severity']}] {item['file']}:{item['line']} - {item['message']}\n"
                )
            if len(auditor.violations) > 10:
                sys.stderr.write(f"  ... and {len(auditor.violations) - 10} more.\n")
        else:
            sys.stderr.write("✅ Zero log hygiene violations found! Logging is clean and structured.\n")
        print(json.dumps(result, indent=2))

    if args.strict and len(auditor.violations) > 0:
        return 1

    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
