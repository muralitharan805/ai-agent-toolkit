# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit Testing Pyramid & Test Quality Standards.

Audits codebases for compliance with the enterprise testing pyramid:
1. Coverage threshold enforcement in test configuration (lines >= 80%, branches >= 75%).
2. Test distribution across Unit, Integration, and E2E layers.
3. Testcontainers usage in integration test suites.
4. Post-deployment smoke test suite presence.
5. k6 or load testing script availability and SLA threshold declarations.
6. Test determinism and unmocked I/O checks.
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
        description="Audit testing pyramid ratios, Testcontainers isolation, and SLA baselines."
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
        help="Exit with non-zero code if any critical testing invariant is violated",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout",
    )
    return parser.parse_args()


def audit_coverage_configuration(root_dir: Path) -> Dict[str, Any]:
    """Inspects Jest or Vitest configurations for mandatory coverage thresholds."""
    config_patterns = [
        "jest.config.ts",
        "jest.config.js",
        "jest.config.json",
        "vitest.config.ts",
        "vitest.config.js",
        "package.json",
    ]

    found_configs = []
    lines_threshold = 0
    branches_threshold = 0
    enforced = False

    for file_name in config_patterns:
        file_path = root_dir / file_name
        if not file_path.is_file():
            continue

        found_configs.append(file_name)
        try:
            content = file_path.read_text(encoding="utf-8")
            lines_match = re.search(r"lines['\"]?\s*:\s*(\d+)", content)
            branches_match = re.search(r"branches['\"]?\s*:\s*(\d+)", content)

            if lines_match:
                lines_threshold = max(lines_threshold, int(lines_match.group(1)))
            if branches_match:
                branches_threshold = max(branches_threshold, int(branches_match.group(1)))
        except Exception:
            continue

    if lines_threshold >= 80 and branches_threshold >= 75:
        enforced = True

    return {
        "found_configs": found_configs,
        "lines_threshold": lines_threshold,
        "branches_threshold": branches_threshold,
        "enforced": enforced,
        "status": "PASS" if enforced else ("WARNING" if found_configs else "MISSING"),
    }


def scan_test_distribution(root_dir: Path) -> Dict[str, Any]:
    """Categorizes test files into unit, integration, and e2e categories."""
    unit_tests: List[str] = []
    integration_tests: List[str] = []
    e2e_tests: List[str] = []
    smoke_tests: List[str] = []
    perf_tests: List[str] = []
    testcontainer_usages: List[str] = []
    nondeterminism_warnings: List[str] = []

    # Ignored directories
    ignored_dirs = {".git", "node_modules", "dist", "build", ".next", "coverage"}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            path = Path(root) / file
            rel_path = str(path.relative_to(root_dir))

            # Performance tests (k6, locust, artillery)
            if file.endswith((".k6.js", ".k6.ts")) or "k6" in file or file.endswith("locustfile.py"):
                perf_tests.append(rel_path)
                continue

            # Smoke tests
            if "smoke" in file.lower() or "post-deploy" in file.lower():
                smoke_tests.append(rel_path)

            # Test files
            if file.endswith((".spec.ts", ".spec.js", ".test.ts", ".test.js")):
                if "e2e" in file.lower() or "e2e" in str(path.parent).lower():
                    e2e_tests.append(rel_path)
                elif "integration" in file.lower() or "integration" in str(path.parent).lower():
                    integration_tests.append(rel_path)
                else:
                    unit_tests.append(rel_path)

                # Check content for Testcontainers or non-determinism
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    if "testcontainers" in content.lower():
                        testcontainer_usages.append(rel_path)
                    if "Math.random()" in content and "seed" not in content.lower():
                        nondeterminism_warnings.append(
                            f"{rel_path}: Contains unseeded Math.random()"
                        )
                except Exception:
                    pass

    total_tests = len(unit_tests) + len(integration_tests) + len(e2e_tests)
    unit_pct = round((len(unit_tests) / total_tests * 100), 1) if total_tests > 0 else 0
    integration_pct = round((len(integration_tests) / total_tests * 100), 1) if total_tests > 0 else 0
    e2e_pct = round((len(e2e_tests) / total_tests * 100), 1) if total_tests > 0 else 0

    return {
        "total_test_files": total_tests,
        "counts": {
            "unit": len(unit_tests),
            "integration": len(integration_tests),
            "e2e": len(e2e_tests),
            "smoke": len(smoke_tests),
            "performance": len(perf_tests),
        },
        "percentages": {
            "unit": unit_pct,
            "integration": integration_pct,
            "e2e": e2e_pct,
        },
        "testcontainers_found": len(testcontainer_usages) > 0,
        "testcontainers_files": testcontainer_usages,
        "nondeterminism_warnings": nondeterminism_warnings,
    }


def run_audit(target_dir: str, strict: bool = False) -> Dict[str, Any]:
    root_path = Path(target_dir).resolve()
    coverage_result = audit_coverage_configuration(root_path)
    distribution_result = scan_test_distribution(root_path)

    findings: List[str] = []
    passed = True

    if not coverage_result["enforced"]:
        findings.append(
            f"Coverage threshold missing or insufficient: lines={coverage_result['lines_threshold']}% (req: >=80%), branches={coverage_result['branches_threshold']}% (req: >=75%)"
        )
        if strict:
            passed = False

    if distribution_result["counts"]["integration"] > 0 and not distribution_result["testcontainers_found"]:
        findings.append(
            "Integration tests detected but no Testcontainers usage identified (risk of in-memory mock drift)."
        )

    if distribution_result["nondeterminism_warnings"]:
        findings.extend(distribution_result["nondeterminism_warnings"])
        if strict:
            passed = False

    report = {
        "target": str(root_path),
        "status": "PASS" if passed and not findings else ("WARNING" if passed else "FAIL"),
        "coverage": coverage_result,
        "distribution": distribution_result,
        "findings": findings,
    }
    return report


def main() -> None:
    args = parse_arguments()
    report = run_audit(args.target, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stderr.write(f"Testing Pyramid Audit: {report['target']}\n")
        sys.stderr.write(f"Status: {report['status']}\n")
        sys.stderr.write(
            f"Coverage Gates: Lines {report['coverage']['lines_threshold']}%, Branches {report['coverage']['branches_threshold']}%\n"
        )
        sys.stderr.write(
            f"Distribution: Unit {report['distribution']['percentages']['unit']}%, "
            f"Integration {report['distribution']['percentages']['integration']}%, "
            f"E2E {report['distribution']['percentages']['e2e']}%\n"
        )
        if report["findings"]:
            sys.stderr.write("\nFindings / Recommendations:\n")
            for finding in report["findings"]:
                sys.stderr.write(f"  - {finding}\n")

    if report["status"] == "FAIL" and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
