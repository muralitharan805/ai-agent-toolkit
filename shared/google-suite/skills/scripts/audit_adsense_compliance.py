# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_adsense_compliance.py
----------------------------
Standalone CLI tool to audit web applications and static builds for Google AdSense
compliance, script tags, Publisher ID syntax, ads.txt presence, legal page disclosures,
and Cumulative Layout Shift (CLS) reservation.

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
        description="Audit web projects for Google AdSense compliance, ads.txt, legal pages, and CLS safety."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to directory or public build to inspect (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any AdSense violations or missing assets are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class AdSenseAuditor:
    """Audits AdSense script placement, ads.txt, legal policy disclosures, and CLS reservation."""

    ADSENSE_SCRIPT_REGEX = re.compile(
        r"pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=(ca-pub-\d{16})"
    )
    ADS_TXT_ENTRY_REGEX = re.compile(
        r"google\.com,\s*(pub-\d{16}),\s*DIRECT,\s*f08c47fec0942fa0",
        re.IGNORECASE,
    )
    CLS_MIN_HEIGHT_REGEX = re.compile(
        r"(?:\.ad-|\.adsbygoogle)[^{]*\{[^}]*min-height\s*:\s*([0-9]+px)",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []
        self.discovered_pub_id: str | None = None

    def audit(self) -> Dict[str, Any]:
        """Run all AdSense compliance checks."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        html_files: List[Path] = []
        css_files: List[Path] = []

        if self.target_path.is_file():
            if self.target_path.suffix == ".html":
                html_files.append(self.target_path)
            elif self.target_path.suffix in (".css", ".scss"):
                css_files.append(self.target_path)
        else:
            for root, dirs, files in os.walk(self.target_path):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "dist", ".git")]
                for f in files:
                    full_p = Path(root) / f
                    if f.endswith(".html"):
                        html_files.append(full_p)
                    elif f.endswith((".css", ".scss")):
                        css_files.append(full_p)

        self._check_html_scripts(html_files)
        self._check_ads_txt()
        self._check_cls_reservations(html_files, css_files)
        self._check_legal_pages()

        return self._build_report()

    def _check_html_scripts(self, html_files: List[Path]) -> None:
        """Check HTML files for AdSense script tag and publisher ID syntax."""
        found_script = False

        for html_path in html_files:
            try:
                content = html_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            match = self.ADSENSE_SCRIPT_REGEX.search(content)
            if match:
                found_script = True
                pub_id = match.group(1)
                self.discovered_pub_id = pub_id
                self.passes.append(f"Discovered valid AdSense script tag with ID '{pub_id}' in {html_path.name}")

                if "async" not in content[max(0, match.start()-100):match.end()+100]:
                    self.violations.append({
                        "file": str(html_path),
                        "type": "missing_async_attribute",
                        "message": "AdSense script tag should be loaded with 'async' to avoid blocking initial render.",
                        "severity": "MEDIUM"
                    })

                if 'crossorigin="anonymous"' not in content[max(0, match.start()-100):match.end()+100]:
                    self.violations.append({
                        "file": str(html_path),
                        "type": "missing_crossorigin_attribute",
                        "message": "AdSense script tag is missing crossorigin='anonymous' attribute.",
                        "severity": "LOW"
                    })

        if not found_script and html_files:
            self.violations.append({
                "type": "missing_adsense_script",
                "message": "No Google AdSense script tag (adsbygoogle.js?client=ca-pub-...) discovered in HTML files.",
                "severity": "HIGH"
            })

    def _check_ads_txt(self) -> None:
        """Check for root ads.txt and verify Google publisher entry."""
        search_dirs = [self.target_path]
        if self.target_path.is_dir():
            search_dirs.append(self.target_path / "public")
            search_dirs.append(self.target_path / "src" / "assets")

        ads_txt_path: Path | None = None
        for d in search_dirs:
            candidate = d / "ads.txt"
            if candidate.is_file():
                ads_txt_path = candidate
                break

        if not ads_txt_path:
            self.violations.append({
                "type": "missing_ads_txt",
                "message": "No 'ads.txt' file found in root domain or public directory.",
                "severity": "HIGH"
            })
            return

        try:
            content = ads_txt_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.violations.append({
                "file": str(ads_txt_path),
                "type": "ads_txt_read_error",
                "message": str(e),
                "severity": "HIGH"
            })
            return

        match = self.ADS_TXT_ENTRY_REGEX.search(content)
        if match:
            self.passes.append(f"Valid ads.txt Google entry found: {match.group(0).strip()}")
        else:
            self.violations.append({
                "file": str(ads_txt_path),
                "type": "invalid_ads_txt_entry",
                "message": "ads.txt does not contain a valid entry matching 'google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0'",
                "severity": "HIGH"
            })

    def _check_cls_reservations(self, html_files: List[Path], css_files: List[Path]) -> None:
        """Check for CSS min-height reservation to prevent layout shifts."""
        has_min_height = False

        for p in css_files + html_files:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            match = self.CLS_MIN_HEIGHT_REGEX.search(content)
            if match:
                has_min_height = True
                self.passes.append(f"CLS layout reservation found ({match.group(1)}) in {p.name}")
                break

        if not has_min_height and (css_files or html_files):
            self.violations.append({
                "type": "missing_cls_reservation",
                "message": "No min-height reservation discovered on ad wrapper containers (.ad-*, .adsbygoogle).",
                "severity": "MEDIUM"
            })

    def _check_legal_pages(self) -> None:
        """Check for presence of privacy policy and terms of service files."""
        candidates = ["privacy", "privacy-policy", "terms", "terms-of-service"]
        found_privacy = False

        for root, _, files in os.walk(self.target_path):
            for f in files:
                lower = f.lower()
                if any(c in lower for c in ("privacy", "terms")):
                    found_privacy = True
                    self.passes.append(f"Discovered legal policy document: {f}")
                    break
            if found_privacy:
                break

        if not found_privacy:
            self.violations.append({
                "type": "missing_legal_pages",
                "message": "No Privacy Policy or Terms page discovered. Google AdSense requires mandatory legal disclosure pages.",
                "severity": "HIGH"
            })

    def _build_report(self) -> Dict[str, Any]:
        """Construct structured report dict."""
        critical_count = sum(1 for v in self.violations if v.get("severity") in ("CRITICAL", "HIGH"))
        return {
            "valid": critical_count == 0,
            "target_path": str(self.target_path),
            "publisher_id": self.discovered_pub_id,
            "passes_count": len(self.passes),
            "violations_count": len(self.violations),
            "passes": self.passes,
            "violations": self.violations,
        }


def main() -> int:
    args = parse_arguments()
    target_path = Path(args.path)

    auditor = AdSenseAuditor(target_path)
    report = auditor.audit()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== 💰 GOOGLE ADSENSE COMPLIANCE AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: Google AdSense Setup is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: Google AdSense Setup has Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
