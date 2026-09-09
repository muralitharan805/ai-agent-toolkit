#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
audit_angular_spa.py
Audits Angular Single Page Applications (CSR) for Google Suite and Cloudflare Pages compliance:
- Cloudflare Pages SPA client routing fallback (_redirects)
- Google AdSense publisher authorization (ads.txt)
- Mandatory legal policy routes (/privacy and /terms)
- Keyword-rich route titles (prohibits bare titles like 'Home', 'Login')
- GA4 client-side route tracking (NavigationEnd)
- AdSense Cumulative Layout Shift (CLS) min-height container reservation
- Zero explicit 'any' types in SPA analytics and SEO code
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

BARE_TITLE_PATTERN = re.compile(r"""title:\s*['"](Home|Login|Dashboard|App|Index|Tool|Page)['"]""", re.IGNORECASE)
ANY_TYPE_PATTERN = re.compile(r""":\s*any\b|\bas\s+any\b|<any>""")
AD_CONTAINER_MIN_HEIGHT_PATTERN = re.compile(r"""min-height:\s*(250|280|300|90)px""", re.IGNORECASE)


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for Angular SPA audit."""
    parser = argparse.ArgumentParser(
        description="Audit Angular SPA for Google Suite SEO, GA4, AdSense, and Cloudflare Pages compliance.",
        epilog=(
            "Examples:\n"
            "  python3 audit_angular_spa.py src/app\n"
            "  python3 audit_angular_spa.py --json\n"
            "  python3 audit_angular_spa.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to Angular project root or src (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are detected")
    return parser.parse_args()


def audit_spa_compliance(target_dir: str) -> Dict[str, Any]:
    """Inspect Angular project files for SPA routing and Google Suite best practices."""
    root = os.path.abspath(target_dir)

    bare_title_violations: List[Dict[str, Any]] = []
    any_type_violations: List[Dict[str, Any]] = []

    has_redirects = False
    has_ads_txt = False
    has_privacy_route = False
    has_terms_route = False
    has_ga4_navigation_tracking = False
    has_adsense_cls_guard = False

    # Check for static assets in public/ or src/assets/ or current dir
    asset_search_paths = [
        os.path.join(root, "public"),
        os.path.join(root, "src", "assets"),
        os.path.join(root, "assets"),
        root
    ]

    for p in asset_search_paths:
        redirects_path = os.path.join(p, "_redirects")
        if os.path.exists(redirects_path):
            try:
                with open(redirects_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "/index.html" in content and "200" in content:
                        has_redirects = True
            except Exception:
                pass

        ads_path = os.path.join(p, "ads.txt")
        if os.path.exists(ads_path):
            try:
                with open(ads_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "google.com" in content and "pub-" in content:
                        has_ads_txt = True
            except Exception:
                pass

    # Walk directory to analyze routes, services, components
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]

        for filename in files:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)

            if not filename.endswith((".ts", ".html")):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()
            except Exception:
                continue

            # Check routes files
            if "route" in filename.lower() or "app.routes" in filename:
                if "'privacy'" in file_content or '"privacy"' in file_content:
                    has_privacy_route = True
                if "'terms'" in file_content or '"terms"' in file_content:
                    has_terms_route = True

                for line_num, line in enumerate(file_content.splitlines(), start=1):
                    match = BARE_TITLE_PATTERN.search(line)
                    if match:
                        bare_title_violations.append({
                            "file": relpath,
                            "line": line_num,
                            "title": match.group(0),
                            "snippet": line.strip()
                        })

            # Check GA4 tracking service
            if "analytics" in filename.lower():
                if "NavigationEnd" in file_content and "gtag" in file_content:
                    has_ga4_navigation_tracking = True

            # Check AdSense CLS container
            if "adsense" in filename.lower():
                if AD_CONTAINER_MIN_HEIGHT_PATTERN.search(file_content):
                    has_adsense_cls_guard = True

            # Check for forbidden explicit 'any' types in typescript files
            if filename.endswith(".ts") and not filename.endswith(".spec.ts"):
                for line_num, line in enumerate(file_content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("/*"):
                        continue
                    if ANY_TYPE_PATTERN.search(line):
                        any_type_violations.append({
                            "file": relpath,
                            "line": line_num,
                            "snippet": stripped
                        })

    checkpoints = [
        {"name": "SPA Client Fallback Routing (_redirects with /* /index.html 200)", "passed": has_redirects},
        {"name": "Google AdSense Authorization (ads.txt with google.com, pub-*)", "passed": has_ads_txt},
        {"name": "Mandatory Legal Policy Routes (/privacy & /terms registered)", "passed": has_privacy_route and has_terms_route},
        {"name": "Keyword-Rich Route Titles (Zero bare titles like 'Home')", "passed": len(bare_title_violations) == 0},
        {"name": "GA4 Single Page App Route Tracking (NavigationEnd subscription)", "passed": has_ga4_navigation_tracking},
        {"name": "AdSense CLS Layout Shift Protection (min-height container reserved)", "passed": has_adsense_cls_guard},
        {"name": "Strict Type Safety (Zero explicit 'any' annotations)", "passed": len(any_type_violations) == 0}
    ]

    passed_count = sum(1 for cp in checkpoints if cp["passed"])
    score_percentage = round((passed_count / len(checkpoints)) * 100, 1)

    return {
        "target_path": root,
        "score_percentage": score_percentage,
        "is_compliant": passed_count == len(checkpoints),
        "checkpoints": checkpoints,
        "bare_title_violations": bare_title_violations,
        "any_type_violations": any_type_violations
    }


def main() -> int:
    """Execute audit and report findings."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_spa_compliance(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 66)
        print("🌐  ANGULAR SPA GOOGLE SUITE & CLOUDFLARE PAGES AUDIT")
        print("=" * 66)
        print(f"Target Directory : {report['target_path']}")
        print(f"Compliance Score : {report['score_percentage']}%")
        print("-" * 66)

        for cp in report["checkpoints"]:
            icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            print(f"{icon} - {cp['name']}")

        if report["bare_title_violations"]:
            print(f"\n🚨 {len(report['bare_title_violations'])} BARE ROUTE TITLE VIOLATIONS:")
            for v in report["bare_title_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['title']}")

        if report["any_type_violations"]:
            print(f"\n🚨 {len(report['any_type_violations'])} EXPLICIT 'ANY' TYPE VIOLATIONS:")
            for v in report["any_type_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['snippet']}")

        print("=" * 66 + "\n")

    if args.strict and not report["is_compliant"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
