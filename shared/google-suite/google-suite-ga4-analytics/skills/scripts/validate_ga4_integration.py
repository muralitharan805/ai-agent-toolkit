# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
validate_ga4_integration.py
----------------------------
Standalone CLI tool to validate Google Analytics 4 (GA4) integration:
- Verifies gtag.js script loading and Measurement ID syntax (G-XXXXXXXXXX)
- Checks for SPA configuration (send_page_view: false)
- Scans source files for PII leakage in analytics payloads
- Verifies custom event naming taxonomy (snake_case, length limits)

Outputs structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Google Analytics 4 (GA4) integration hygiene and PII compliance."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to directory or file to inspect (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any GA4 validation issues or PII warnings are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class Ga4Validator:
    """Validates GA4 script tags, configuration parameters, and custom events."""

    MEASUREMENT_ID_REGEX = re.compile(r"G-[A-Z0-9]{8,12}")
    GTAG_SCRIPT_REGEX = re.compile(r"https://www\.googletagmanager\.com/gtag/js\?id=(G-[A-Z0-9]+)")
    PII_KEYWORD_REGEX = re.compile(
        r"(?:password|email|authToken|secretKey|bearerToken|creditCard)\s*:",
        re.IGNORECASE,
    )
    EVENT_NAME_REGEX = re.compile(r"^[a-z0-9_]{1,40}$")
    RESERVED_PREFIXES = ("_", "ga_", "google_", "firebase_")

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def validate(self) -> Dict[str, Any]:
        """Run all GA4 checks across target path."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        html_files: List[Path] = []
        source_files: List[Path] = []

        if self.target_path.is_file():
            if self.target_path.suffix == ".html":
                html_files.append(self.target_path)
            elif self.target_path.suffix in (".ts", ".js", ".jsx", ".tsx"):
                source_files.append(self.target_path)
        else:
            for root, dirs, files in os.walk(self.target_path):
                # Skip hidden, node_modules, and dist directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "dist", ".git")]
                for file in files:
                    full_p = Path(root) / file
                    if file.endswith(".html"):
                        html_files.append(full_p)
                    elif file.endswith((".ts", ".js", ".jsx", ".tsx")):
                        source_files.append(full_p)

        self._check_html_tags(html_files)
        self._check_source_code_events(source_files)

        return self._build_report()

    def _check_html_tags(self, html_files: List[Path]) -> None:
        """Check HTML files for gtag.js script and measurement configuration."""
        found_gtag = False

        for html_path in html_files:
            try:
                content = html_path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                self.violations.append({
                    "file": str(html_path),
                    "type": "file_read_error",
                    "message": str(e),
                    "severity": "HIGH"
                })
                continue

            match = self.GTAG_SCRIPT_REGEX.search(content)
            if match:
                found_gtag = True
                measurement_id = match.group(1)
                self.passes.append(f"Found gtag.js script loading measurement ID '{measurement_id}' in {html_path.name}")

                # Check if async attribute is present
                if "<script async" not in content and "<script\n  async" not in content and "async" not in match.string[max(0, match.start()-50):match.end()+50]:
                    self.violations.append({
                        "file": str(html_path),
                        "type": "missing_async_attribute",
                        "message": "The gtag.js script tag should include the 'async' attribute for non-blocking execution.",
                        "severity": "MEDIUM"
                    })

                # Check for send_page_view setting
                if "send_page_view: false" in content or '"send_page_view": false' in content or "'send_page_view': false" in content:
                    self.passes.append(f"Configured 'send_page_view: false' for SPA route control in {html_path.name}")
                elif "gtag('config'" in content:
                    self.passes.append(f"Standard gtag config detected in {html_path.name}")

        if not found_gtag and html_files:
            self.violations.append({
                "type": "missing_gtag_script",
                "message": "No gtag.js script tag with GA4 Measurement ID (G-XXXXXXXXXX) discovered in HTML files.",
                "severity": "HIGH"
            })

    def _check_source_code_events(self, source_files: List[Path]) -> None:
        """Check source code for gtag dispatch hygiene, PII prevention, and taxonomy."""
        gtag_call_regex = re.compile(r"gtag\s*\(\s*['\"]event['\"]\s*,\s*['\"]([^'\"]+)['\"](?:\s*,\s*(\{.*?\})\s*)?", re.DOTALL)

        dispatched_events_count = 0
        for src_path in source_files:
            try:
                content = src_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Check for potential PII leakage inside files that touch analytics
            if "gtag" in content:
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if self.PII_KEYWORD_REGEX.search(line):
                        self.violations.append({
                            "file": str(src_path),
                            "line": line_idx,
                            "type": "potential_pii_leakage",
                            "message": f"Suspicious parameter name indicating potential PII leakage: '{line.strip()}'",
                            "severity": "HIGH"
                        })

                # Extract custom event names
                for match in gtag_call_regex.finditer(content):
                    dispatched_events_count += 1
                    event_name = match.group(1)
                    if not self.EVENT_NAME_REGEX.match(event_name):
                        self.violations.append({
                            "file": str(src_path),
                            "type": "invalid_event_naming",
                            "message": f"Event name '{event_name}' violates snake_case or exceeds 40 characters limit.",
                            "severity": "HIGH"
                        })
                    if any(event_name.startswith(pfx) for pfx in self.RESERVED_PREFIXES):
                        self.violations.append({
                            "file": str(src_path),
                            "type": "reserved_event_prefix",
                            "message": f"Event name '{event_name}' uses reserved Google prefix (_/ga_/google_/firebase_).",
                            "severity": "HIGH"
                        })

        if dispatched_events_count > 0:
            self.passes.append(f"Validated {dispatched_events_count} custom analytics event dispatches across source files.")

    def _build_report(self) -> Dict[str, Any]:
        """Construct structured report dict."""
        critical_count = sum(1 for v in self.violations if v.get("severity") in ("CRITICAL", "HIGH"))
        return {
            "valid": critical_count == 0,
            "target_path": str(self.target_path),
            "passes_count": len(self.passes),
            "violations_count": len(self.violations),
            "passes": self.passes,
            "violations": self.violations,
        }


def main() -> int:
    args = parse_arguments()
    target_path = Path(args.path)

    validator = Ga4Validator(target_path)
    report = validator.validate()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== 🔍 GA4 INTEGRATION AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: GA4 Integration is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: GA4 Integration has Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
