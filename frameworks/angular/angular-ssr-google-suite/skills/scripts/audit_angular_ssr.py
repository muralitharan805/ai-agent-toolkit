#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
audit_angular_ssr.py
Audits Angular Server-Side Rendered (SSR) applications for Cloudflare Edge and Google Suite compliance:
- Dynamic XML sitemap handler in src/server.ts
- Edge route bypass manifest (_routes.json)
- Browser global access guarding (isPlatformBrowser)
- Node.js native module restrictions (prohibiting fs, path, crypto, net, child_process)
- Mandatory legal policy routes (/privacy and /terms)
- Keyword-rich route titles (prohibiting bare titles like 'Home', 'Login')
- Zero explicit 'any' types in SSR codebase
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

BARE_TITLE_PATTERN = re.compile(r"""title:\s*['"](Home|Login|Dashboard|App|Index|Tool|Page)['"]""", re.IGNORECASE)
ANY_TYPE_PATTERN = re.compile(r""":\s*any\b|\bas\s+any\b|<any>""")
FORBIDDEN_NODE_MODULE_PATTERN = re.compile(
    r"""import\s+.*\s+from\s+['"](node:)?(fs|path|crypto|net|child_process|cluster|os|http|https)['"]|require\(['"](node:)?(fs|path|crypto|net|child_process)['"]\)"""
)
UNGUARDED_WINDOW_PATTERN = re.compile(r"""\b(window|localStorage|sessionStorage|document\.location)\b""")


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for Angular SSR audit."""
    parser = argparse.ArgumentParser(
        description="Audit Angular SSR project for Cloudflare Edge and Google Suite compliance.",
        epilog=(
            "Examples:\n"
            "  python3 audit_angular_ssr.py src\n"
            "  python3 audit_angular_ssr.py --json\n"
            "  python3 audit_angular_ssr.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to Angular project root or src (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are detected")
    return parser.parse_args()


def audit_ssr_compliance(target_dir: str) -> Dict[str, Any]:
    """Inspect Angular project files for SSR edge compatibility and SEO best practices."""
    root = os.path.abspath(target_dir)

    bare_title_violations: List[Dict[str, Any]] = []
    any_type_violations: List[Dict[str, Any]] = []
    forbidden_node_violations: List[Dict[str, Any]] = []
    unguarded_browser_violations: List[Dict[str, Any]] = []

    has_sitemap_handler = False
    has_routes_json = False
    has_privacy_route = False
    has_terms_route = False

    # Check for static _routes.json
    routes_json_candidates = [
        os.path.join(root, "public", "_routes.json"),
        os.path.join(root, "src", "_routes.json"),
        os.path.join(root, "_routes.json"),
        os.path.join(root, "assets", "_routes.json")
    ]
    for cand in routes_json_candidates:
        if os.path.exists(cand):
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    exclude_list = data.get("exclude", [])
                    if any("/sitemap.xml" in item for item in exclude_list):
                        has_routes_json = True
                        break
            except Exception:
                pass

    # Walk directory to analyze routes, server, components
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]

        for filename in files:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)

            if not filename.endswith((".ts", ".html", ".json")):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()
            except Exception:
                continue

            # Check server.ts sitemap handler
            if filename in ["server.ts", "entry.server.ts"]:
                if "/sitemap.xml" in file_content and "application/xml" in file_content:
                    has_sitemap_handler = True

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

            # Check TypeScript files for Node module imports and type safety
            if filename.endswith(".ts") and not filename.endswith(".spec.ts"):
                has_platform_import = "isPlatformBrowser" in file_content

                for line_num, line in enumerate(file_content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                        continue

                    # Forbidden Node.js modules
                    node_match = FORBIDDEN_NODE_MODULE_PATTERN.search(line)
                    if node_match:
                        forbidden_node_violations.append({
                            "file": relpath,
                            "line": line_num,
                            "module": node_match.group(0),
                            "snippet": stripped
                        })

                    # Explicit 'any' types
                    if ANY_TYPE_PATTERN.search(line):
                        any_type_violations.append({
                            "file": relpath,
                            "line": line_num,
                            "snippet": stripped
                        })

                    # Un-guarded window access in top-level fields
                    if UNGUARDED_WINDOW_PATTERN.search(line) and not has_platform_import:
                        if "=" in line and ("window." in line or "localStorage." in line):
                            unguarded_browser_violations.append({
                                "file": relpath,
                                "line": line_num,
                                "snippet": stripped
                            })

    checkpoints = [
        {"name": "Dynamic XML Sitemap Response Handler (src/server.ts)", "passed": has_sitemap_handler},
        {"name": "Cloudflare Edge Route Bypass Manifest (_routes.json)", "passed": has_routes_json},
        {"name": "Zero Forbidden Node Native Modules (workerd V8 isolation)", "passed": len(forbidden_node_violations) == 0},
        {"name": "Browser Global Guarding (Zero top-level window/localStorage calls)", "passed": len(unguarded_browser_violations) == 0},
        {"name": "Mandatory Legal Policy Routes (/privacy & /terms registered)", "passed": has_privacy_route and has_terms_route},
        {"name": "Keyword-Rich Route Titles (Zero bare titles like 'Home')", "passed": len(bare_title_violations) == 0},
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
        "forbidden_node_violations": forbidden_node_violations,
        "unguarded_browser_violations": unguarded_browser_violations,
        "any_type_violations": any_type_violations
    }


def main() -> int:
    """Execute audit and report findings."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_ssr_compliance(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 66)
        print("⚡  ANGULAR EDGE SSR GOOGLE SUITE & CLOUDFLARE AUDIT")
        print("=" * 66)
        print(f"Target Directory : {report['target_path']}")
        print(f"Compliance Score : {report['score_percentage']}%")
        print("-" * 66)

        for cp in report["checkpoints"]:
            icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            print(f"{icon} - {cp['name']}")

        if report["forbidden_node_violations"]:
            print(f"\n🚨 {len(report['forbidden_node_violations'])} FORBIDDEN NODE.JS MODULE IMPORTS:")
            for v in report["forbidden_node_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['module']}")

        if report["bare_title_violations"]:
            print(f"\n🚨 {len(report['bare_title_violations'])} BARE ROUTE TITLE VIOLATIONS:")
            for v in report["bare_title_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['title']}")

        if report["unguarded_browser_violations"]:
            print(f"\n🚨 {len(report['unguarded_browser_violations'])} UNGUARDED BROWSER GLOBAL VIOLATIONS:")
            for v in report["unguarded_browser_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['snippet']}")

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
