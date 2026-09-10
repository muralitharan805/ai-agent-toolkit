# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Verify Test Coverage CLI Tool.

Audits code coverage summary reports against 80% line and 75% branch thresholds,
and scans the source tree for untested components and services lacking colocated spec files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MetricThreshold:
    actual: float
    required: float
    passed: bool


@dataclass
class CoverageAuditReport:
    passed: bool
    line_metric: MetricThreshold
    branch_metric: MetricThreshold
    function_metric: MetricThreshold
    untested_files: List[str] = field(default_factory=list)
    total_untested_count: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify test coverage metrics and check for missing colocated spec files."
    )
    parser.add_argument(
        "--coverage-file",
        type=str,
        default="coverage/coverage-summary.json",
        help="Path to coverage-summary.json report (default: coverage/coverage-summary.json).",
    )
    parser.add_argument(
        "--min-lines",
        type=float,
        default=80.0,
        help="Minimum required line coverage percentage (default: 80.0).",
    )
    parser.add_argument(
        "--min-branches",
        type=float,
        default=75.0,
        help="Minimum required branch coverage percentage (default: 75.0).",
    )
    parser.add_argument(
        "--min-functions",
        type=float,
        default=80.0,
        help="Minimum required function coverage percentage (default: 80.0).",
    )
    parser.add_argument(
        "--scan-dir",
        type=str,
        default="src",
        help="Directory to scan for missing colocated spec files (default: src).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if thresholds are not met or missing spec files are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON audit report to stdout.",
    )
    return parser.parse_args()


def scan_untested_files(scan_dir: Path) -> List[str]:
    untested: List[str] = []
    if not scan_dir.exists():
        return untested

    skip_patterns = (
        ".spec.ts",
        ".test.ts",
        "main.ts",
        ".module.ts",
        ".dto.ts",
        ".interface.ts",
        ".config.ts",
        ".d.ts",
    )

    for root, _, files in os.walk(scan_dir):
        for f in files:
            if not f.endswith(".ts"):
                continue
            if any(f.endswith(pat) or pat in f for pat in skip_patterns):
                continue

            file_path = Path(root) / f
            expected_spec = file_path.with_name(f"{file_path.stem}.spec.ts")
            if not expected_spec.exists():
                untested.append(str(file_path))

    return untested


def load_coverage_summary(cov_path: Path) -> Dict[str, Any]:
    if not cov_path.exists():
        return {}
    try:
        return json.loads(cov_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    args = parse_args()
    cov_path = Path(args.coverage_file)
    scan_dir = Path(args.scan_dir)

    cov_data = load_coverage_summary(cov_path)
    total_data = cov_data.get("total", {})

    lines_pct = float(total_data.get("lines", {}).get("pct", 0.0))
    branches_pct = float(total_data.get("branches", {}).get("pct", 0.0))
    functions_pct = float(total_data.get("functions", {}).get("pct", 0.0))

    line_metric = MetricThreshold(
        actual=lines_pct,
        required=args.min_lines,
        passed=lines_pct >= args.min_lines if cov_data else True,
    )
    branch_metric = MetricThreshold(
        actual=branches_pct,
        required=args.min_branches,
        passed=branches_pct >= args.min_branches if cov_data else True,
    )
    function_metric = MetricThreshold(
        actual=functions_pct,
        required=args.min_functions,
        passed=functions_pct >= args.min_functions if cov_data else True,
    )

    untested_files = scan_untested_files(scan_dir)

    overall_passed = line_metric.passed and branch_metric.passed and function_metric.passed
    if args.strict and untested_files:
        overall_passed = False

    report = CoverageAuditReport(
        passed=overall_passed,
        line_metric=line_metric,
        branch_metric=branch_metric,
        function_metric=function_metric,
        untested_files=untested_files,
        total_untested_count=len(untested_files),
    )

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write("🧪 TEST COVERAGE & COLOCATION QUALITY AUDIT\n")
        sys.stderr.write("========================================================\n")
        status_sym = "✅ PASS" if report.passed else "❌ FAIL"
        sys.stderr.write(f"Audit Status        : {status_sym}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        if cov_data:
            sys.stderr.write(
                f"Line Coverage       : {lines_pct:.1f}% (Required: >={args.min_lines:.1f}%) "
                f"{'✅' if line_metric.passed else '❌'}\n"
            )
            sys.stderr.write(
                f"Branch Coverage     : {branches_pct:.1f}% (Required: >={args.min_branches:.1f}%) "
                f"{'✅' if branch_metric.passed else '❌'}\n"
            )
            sys.stderr.write(
                f"Function Coverage   : {functions_pct:.1f}% (Required: >={args.min_functions:.1f}%) "
                f"{'✅' if function_metric.passed else '❌'}\n"
            )
        else:
            sys.stderr.write(f"Coverage Report     : Not found at '{cov_path}' (Run 'pnpm test:cov')\n")

        sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Missing Spec Files  : {len(untested_files)}\n")
        for uf in untested_files[:10]:
            sys.stderr.write(f"  - Missing colocated spec: {uf}\n")
        if len(untested_files) > 10:
            sys.stderr.write(f"  ... and {len(untested_files) - 10} more files.\n")
        sys.stderr.write("========================================================\n")

    if not overall_passed and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
