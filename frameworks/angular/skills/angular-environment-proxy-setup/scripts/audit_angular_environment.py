#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
audit_angular_environment.py
Audits Angular codebases for hardcoded API URLs, verifies presence of typed environment files,
and checks dev/staging proxy configurations.
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

HARDCODED_URL_PATTERN = re.compile(r"""['"`](https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[^\s'"`]*)['"`]""", re.IGNORECASE)


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for environment and proxy audit."""
    parser = argparse.ArgumentParser(
        description="Audit Angular project for hardcoded URLs, environment files, and proxy configs.",
        epilog=(
            "Examples:\n"
            "  python3 audit_angular_environment.py src/app\n"
            "  python3 audit_angular_environment.py --json\n"
            "  python3 audit_angular_environment.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to Angular project root (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are discovered")
    return parser.parse_args()


def audit_environment_and_proxy(target_dir: str) -> Dict[str, Any]:
    """Execute deep scan of environment files, proxies, and source files."""
    root = os.path.abspath(target_dir)

    # 1. Check environment files
    env_dir = os.path.join(root, "src", "environments")
    has_dev_env = os.path.exists(os.path.join(env_dir, "environment.ts")) or os.path.exists(os.path.join(root, "environment.ts"))
    has_prod_env = os.path.exists(os.path.join(env_dir, "environment.prod.ts")) or os.path.exists(os.path.join(root, "environment.prod.ts"))

    # 2. Check proxy configurations
    has_dev_proxy = os.path.exists(os.path.join(root, "proxy.dev.json")) or os.path.exists(os.path.join(root, "proxy.conf.json"))
    has_staging_proxy = os.path.exists(os.path.join(root, "proxy.staging.json"))

    # 3. Check angular.json proxy and replacement wiring
    angular_json_path = os.path.join(root, "angular.json")
    has_file_replacements = False
    has_proxy_wiring = False

    if os.path.exists(angular_json_path):
        try:
            with open(angular_json_path, "r", encoding="utf-8") as f:
                content = f.read()
                has_file_replacements = "fileReplacements" in content and "environment.prod.ts" in content
                has_proxy_wiring = "proxyConfig" in content
        except Exception as e:
            sys.stderr.write(f"Warning reading angular.json: {e}\n")

    # 4. Scan source files for hardcoded URLs
    hardcoded_violations: List[Dict[str, Any]] = []
    search_dirs = [os.path.join(root, "src"), target_dir] if os.path.exists(os.path.join(root, "src")) else [root]

    for search_root in search_dirs:
        for dirpath, dirs, files in os.walk(search_root):
            # Skip node_modules, dist, .git
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]
            for filename in files:
                if filename.endswith(".ts") and not filename.endswith(".spec.ts"):
                    filepath = os.path.join(dirpath, filename)
                    # Skip the proxy/environment configuration files themselves
                    if "environment.prod.ts" in filepath or "proxy" in filepath:
                        continue
                    try:
                        with open(filepath, "r", encoding="utf-8") as source_file:
                            for line_num, line in enumerate(source_file, start=1):
                                stripped = line.strip()
                                if stripped.startswith("//") or stripped.startswith("/*"):
                                    continue
                                match = HARDCODED_URL_PATTERN.search(line)
                                if match:
                                    hardcoded_violations.append({
                                        "file": os.path.relpath(filepath, root),
                                        "line": line_num,
                                        "url": match.group(1),
                                        "snippet": stripped
                                    })
                    except Exception:
                        pass

    checkpoints = [
        {"name": "Development Environment (environment.ts)", "passed": has_dev_env},
        {"name": "Production Environment (environment.prod.ts)", "passed": has_prod_env},
        {"name": "Local Dev Proxy (proxy.dev.json / proxy.conf.json)", "passed": has_dev_proxy},
        {"name": "Staging Proxy Config (proxy.staging.json)", "passed": has_staging_proxy},
        {"name": "Zero Hardcoded URLs in Source Code", "passed": len(hardcoded_violations) == 0}
    ]

    passed_count = sum(1 for c in checkpoints if c["passed"])
    score_percentage = round((passed_count / len(checkpoints)) * 100, 1)

    return {
        "target_path": root,
        "score_percentage": score_percentage,
        "is_compliant": len(hardcoded_violations) == 0 and has_dev_env and has_prod_env and has_dev_proxy,
        "checkpoints": checkpoints,
        "hardcoded_violations": hardcoded_violations,
        "angular_json_audit": {
            "has_file_replacements": has_file_replacements,
            "has_proxy_wiring": has_proxy_wiring
        }
    }


def main() -> int:
    """Execute audit and render report."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Project path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_environment_and_proxy(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 62)
        print("🌐  ANGULAR ENVIRONMENT & PROXY AUDIT REPORT")
        print("=" * 62)
        print(f"Target Directory : {report['target_path']}")
        print(f"Compliance Score : {report['score_percentage']}%")
        print("-" * 62)

        for cp in report["checkpoints"]:
            icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            print(f"{icon} - {cp['name']}")

        if report["hardcoded_violations"]:
            print(f"\n🚨 {len(report['hardcoded_violations'])} HARDCODED URL VIOLATIONS FOUND:")
            for v in report["hardcoded_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['url']}")

        print("=" * 62 + "\n")

    if args.strict and not report["is_compliant"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
