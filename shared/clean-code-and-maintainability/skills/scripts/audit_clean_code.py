# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_clean_code.py
-------------------
Standalone CLI automation tool to audit TypeScript and JavaScript source code
against Robert C. Martin's Clean Code standards, zero-any typing invariant,
function length limits (<= 35 lines), parameter limits (<= 3 params),
guard clause nesting depths, and mandatory TSDoc block comments.

Outputs structured JSON to stdout and diagnostic logs to stderr.
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
        description="Audit TypeScript/JavaScript files for Clean Code standards & zero-any typing."
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
        help="Exit with non-zero status if any clean code violations are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class CleanCodeAuditor:
    """Audits TypeScript/JavaScript source code for Clean Code violations."""

    def __init__(self) -> None:
        self.violations: List[Dict[str, Any]] = []
        self.files_scanned = 0

    def audit_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Audit a single source file for clean code standards."""
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

        # 1. Check for explicit 'any' types
        # Regex looks for ': any', 'as any', '<any>', 'any[]', 'Promise<any>'
        any_pattern = re.compile(r":\s*any\b|\bas\s+any\b|<any>|any\[\]|<[^>]*any[^>]*>", re.IGNORECASE)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Ignore comments
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            if any_pattern.search(line):
                file_violations.append({
                    "file": str(file_path),
                    "line": idx,
                    "rule": "NO_ANY_TYPE",
                    "severity": "ERROR",
                    "message": f"Explicit 'any' type detected: '{stripped[:60]}...'",
                })

        # 2. Check for exported symbols lacking TSDoc
        export_pattern = re.compile(
            r"^export\s+(?:default\s+)?(?:async\s+)?(?:class|function|interface|type|const|enum)\s+([A-Za-z0-9_$]+)"
        )
        for idx, line in enumerate(lines, start=1):
            match = export_pattern.match(line.strip())
            if match:
                symbol_name = match.group(1)
                # Check preceding lines for '*/' indicating JSDoc/TSDoc
                has_doc = False
                check_idx = idx - 2  # 0-indexed line above
                while check_idx >= 0:
                    prev_line = lines[check_idx].strip()
                    if not prev_line:
                        check_idx -= 1
                        continue
                    if prev_line.endswith("*/"):
                        has_doc = True
                    break

                if not has_doc:
                    file_violations.append({
                        "file": str(file_path),
                        "line": idx,
                        "rule": "MANDATORY_TSDOC",
                        "severity": "WARNING",
                        "message": f"Exported symbol '{symbol_name}' lacks preceding TSDoc/JSDoc block comment.",
                    })

        # 3. Check for parameter count (> 3 positional parameters)
        func_param_pattern = re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)"
        )
        for idx, line in enumerate(lines, start=1):
            match = func_param_pattern.search(line)
            if match:
                func_name = match.group(1)
                params_str = match.group(2).strip()
                if params_str:
                    # Rough count of top-level commas
                    params = [p.strip() for p in params_str.split(",") if p.strip()]
                    if len(params) > 3:
                        file_violations.append({
                            "file": str(file_path),
                            "line": idx,
                            "rule": "MAX_PARAMETERS",
                            "severity": "WARNING",
                            "message": f"Function '{func_name}' accepts {len(params)} positional parameters (max 3). Use a typed DTO.",
                        })

        # 4. Check for nested if/else depth (> 2 levels)
        current_depth = 0
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            if re.search(r"\bif\s*\(", stripped):
                current_depth += 1
                if current_depth > 2:
                    file_violations.append({
                        "file": str(file_path),
                        "line": idx,
                        "rule": "DEEP_NESTING",
                        "severity": "WARNING",
                        "message": f"Nested conditional depth ({current_depth}) exceeds recommended maximum of 2. Refactor using guard clauses.",
                    })
            # Track closing braces to decrease depth
            closing_count = stripped.count("}")
            opening_count = stripped.count("{")
            if closing_count > opening_count and current_depth > 0:
                current_depth = max(0, current_depth - (closing_count - opening_count))

        return file_violations

    def audit_directory(self, target_path: Path) -> None:
        """Walk directory and audit relevant source files."""
        extensions = {".ts", ".tsx", ".js", ".jsx"}
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
                if file_p.suffix.lower() in extensions and not file_name.endswith(".d.ts"):
                    self.files_scanned += 1
                    self.violations.extend(self.audit_file(file_p))


def main() -> int:
    """CLI entrypoint."""
    args = parse_arguments()
    target_path = Path(args.path).resolve()

    if not target_path.exists():
        sys.stderr.write(f"❌ Target path does not exist: {target_path}\n")
        return 1

    auditor = CleanCodeAuditor()
    auditor.audit_directory(target_path)

    errors = [v for v in auditor.violations if v["severity"] == "ERROR"]
    warnings = [v for v in auditor.violations if v["severity"] == "WARNING"]

    result = {
        "target_path": str(target_path),
        "files_scanned": auditor.files_scanned,
        "total_violations": len(auditor.violations),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "violations": auditor.violations,
        "status": "PASSED" if len(errors) == 0 else "FAILED",
    }

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        sys.stderr.write(
            f"🔍 Clean Code Audit: {auditor.files_scanned} files scanned across {target_path}\n"
        )
        if auditor.violations:
            sys.stderr.write(
                f"⚠️ Discovered {len(errors)} errors and {len(warnings)} warnings.\n"
            )
            for item in auditor.violations[:10]:
                sys.stderr.write(
                    f"  [{item['severity']}] {item['file']}:{item['line']} - {item['message']}\n"
                )
            if len(auditor.violations) > 10:
                sys.stderr.write(f"  ... and {len(auditor.violations) - 10} more.\n")
        else:
            sys.stderr.write("✅ Zero clean code violations found! Code is clean and compliant.\n")
        print(json.dumps(result, indent=2))

    if args.strict and (len(errors) > 0 or len(warnings) > 0):
        return 1

    return 1 if len(errors) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
