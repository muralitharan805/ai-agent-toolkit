# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_seo_metadata.py
---------------------
Standalone CLI tool to audit HTML files and web directories for Google Search Console
SEO compliance, canonical link tags, sitemap.xml, robots.txt, and JSON-LD schemas.

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
        description="Audit HTML and public assets for SEO, canonical tags, sitemaps, and JSON-LD."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to directory or HTML file to audit (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any SEO violations or missing assets are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class SeoAuditor:
    """Audits HTML content and directory structures for SEO compliance."""

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def audit(self) -> Dict[str, Any]:
        """Run full SEO audit."""
        # 1. Check for sitemap.xml
        sitemap_path = self.target_path / "sitemap.xml"
        if not sitemap_path.exists():
            sitemap_path = self.target_path / "public" / "sitemap.xml"

        if sitemap_path.exists():
            content = sitemap_path.read_text(encoding="utf-8", errors="replace")
            if "<urlset" in content and "<loc>" in content:
                self.passes.append(f"Valid XML sitemap discovered at: {sitemap_path.name}")
            else:
                self.violations.append({
                    "file": str(sitemap_path),
                    "rule": "INVALID_SITEMAP_XML",
                    "severity": "HIGH",
                    "message": "sitemap.xml exists but lacks standard <urlset> and <loc> tags.",
                })
        else:
            self.violations.append({
                "file": "sitemap.xml",
                "rule": "MISSING_SITEMAP",
                "severity": "WARNING",
                "message": "Missing sitemap.xml in root or public/ directory.",
            })

        # 2. Check for robots.txt
        robots_path = self.target_path / "robots.txt"
        if not robots_path.exists():
            robots_path = self.target_path / "public" / "robots.txt"

        if robots_path.exists():
            content = robots_path.read_text(encoding="utf-8", errors="replace")
            if "sitemap:" in content.lower():
                self.passes.append(f"Valid robots.txt discovered with Sitemap directive: {robots_path.name}")
            else:
                self.violations.append({
                    "file": str(robots_path),
                    "rule": "ROBOTS_MISSING_SITEMAP",
                    "severity": "WARNING",
                    "message": "robots.txt lacks 'Sitemap: https://...' directive.",
                })
        else:
            self.violations.append({
                "file": "robots.txt",
                "rule": "MISSING_ROBOTS_TXT",
                "severity": "WARNING",
                "message": "Missing robots.txt in root or public/ directory.",
            })

        # 3. Check HTML files for canonical link tags and JSON-LD schemas
        html_files: List[Path] = []
        if self.target_path.is_file() and self.target_path.suffix.lower() == ".html":
            html_files.append(self.target_path)
        else:
            for root, dirs, files in os.walk(self.target_path):
                dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "dist"}]
                for f in files:
                    if f.endswith(".html"):
                        html_files.append(Path(root) / f)

        for html_file in html_files[:5]:  # Sample up to 5 HTML files
            try:
                html_text = html_file.read_text(encoding="utf-8", errors="replace")
                # Canonical tag check
                if re.search(r"<link\s+[^>]*rel=[\"']canonical[\"'][^>]*>", html_text, re.IGNORECASE):
                    self.passes.append(f"Canonical link tag verified in {html_file.name}")
                else:
                    self.violations.append({
                        "file": str(html_file.relative_to(self.target_path)),
                        "rule": "MISSING_CANONICAL_LINK",
                        "severity": "HIGH",
                        "message": "HTML document lacks <link rel='canonical' href='...'> tag.",
                    })

                # JSON-LD Schema check
                json_ld_matches = re.findall(
                    r"<script\s+type=[\"']application/ld\+json[\"']>([\s\S]*?)</script>",
                    html_text,
                    re.IGNORECASE,
                )
                if json_ld_matches:
                    for script_content in json_ld_matches:
                        try:
                            json.loads(script_content.strip())
                            self.passes.append(f"Valid JSON-LD schema parsed in {html_file.name}")
                        except json.JSONDecodeError as exc:
                            self.violations.append({
                                "file": str(html_file.relative_to(self.target_path)),
                                "rule": "MALFORMED_JSON_LD",
                                "severity": "ERROR",
                                "message": f"Malformed JSON-LD schema syntax: {str(exc)}",
                            })
                else:
                    self.violations.append({
                        "file": str(html_file.relative_to(self.target_path)),
                        "rule": "MISSING_JSON_LD",
                        "severity": "WARNING",
                        "message": "HTML document lacks <script type='application/ld+json'> structured data schema.",
                    })
            except Exception:
                pass

        error_count = sum(1 for v in self.violations if v["severity"] in {"CRITICAL", "ERROR"})
        warning_count = sum(1 for v in self.violations if v["severity"] in {"HIGH", "WARNING"})

        return {
            "target_path": str(self.target_path),
            "passes": self.passes,
            "violations": self.violations,
            "total_violations": len(self.violations),
            "error_count": error_count,
            "warning_count": warning_count,
            "status": "PASSED" if error_count == 0 else "FAILED",
        }


def main() -> int:
    """CLI entrypoint."""
    args = parse_arguments()
    target_path = Path(args.path).resolve()

    if not target_path.exists():
        sys.stderr.write(f"❌ Target path does not exist: {target_path}\n")
        return 1

    auditor = SeoAuditor(target_path)
    result = auditor.audit()

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        sys.stderr.write(f"🔍 Auditing SEO metadata across: {target_path}\n")
        for p in result["passes"]:
            sys.stderr.write(f"  ✅ {p}\n")
        for v in result["violations"]:
            sys.stderr.write(f"  ⚠️ [{v['severity']}] {v['file']}: {v['message']}\n")
        print(json.dumps(result, indent=2))

    if args.strict and result["total_violations"] > 0:
        return 1

    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
