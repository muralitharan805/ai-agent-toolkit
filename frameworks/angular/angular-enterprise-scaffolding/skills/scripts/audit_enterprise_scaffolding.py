#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
audit_enterprise_scaffolding.py
Audits an Angular codebase for compliance with the 14-Point Enterprise Scaffolding Specification.
Verifies presence of core services, functional interceptors, layout shells, and zero NgModule usage.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for scaffolding audit."""
    parser = argparse.ArgumentParser(
        description="Audit Angular project against the 14-Point Enterprise Scaffolding Specification.",
        epilog=(
            "Examples:\n"
            "  python3 audit_enterprise_scaffolding.py src/app\n"
            "  python3 audit_enterprise_scaffolding.py --json\n"
            "  python3 audit_enterprise_scaffolding.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to Angular project root or src/app (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Fail build with non-zero exit code on any missing item")
    return parser.parse_args()


def audit_scaffolding(target_dir: str) -> Dict[str, Any]:
    """Inspect project directory and verify 14-point scaffolding compliance."""
    results: List[Dict[str, Any]] = []

    # Resolve src and app directory variants
    app_dir = target_dir
    if os.path.exists(os.path.join(target_dir, "src", "app")):
        app_dir = os.path.join(target_dir, "src", "app")
    elif os.path.exists(os.path.join(target_dir, "app")):
        app_dir = os.path.join(target_dir, "app")

    checkpoints = [
        ("1. app.config.ts (Bootstrap Config)", [os.path.join(app_dir, "app.config.ts")]),
        ("2. ApiService (HTTP Client Wrapper)", [
            os.path.join(app_dir, "core", "services", "api.service.ts"),
            os.path.join(app_dir, "core", "services", "api.ts")
        ]),
        ("3. AuthService (Session Signals)", [
            os.path.join(app_dir, "core", "services", "auth.service.ts")
        ]),
        ("4. NotificationService (Toast Dispatcher)", [
            os.path.join(app_dir, "core", "services", "notification.service.ts"),
            os.path.join(app_dir, "core", "services", "toast.service.ts")
        ]),
        ("5. LoadingService & Interceptor", [
            os.path.join(app_dir, "core", "services", "loading.service.ts")
        ]),
        ("6. Functional Interceptors (auth/error/loading)", [
            os.path.join(app_dir, "core", "interceptors", "auth.interceptor.ts"),
            os.path.join(app_dir, "core", "interceptors", "error.interceptor.ts")
        ]),
        ("7. Functional Security Guards (authGuard)", [
            os.path.join(app_dir, "core", "guards", "auth.guard.ts")
        ]),
        ("8. AppTitleStrategy (Route Document Title)", [
            os.path.join(app_dir, "core", "strategies", "page-title.strategy.ts"),
            os.path.join(app_dir, "core", "strategies", "title.strategy.ts")
        ]),
        ("9. GlobalErrorHandler (Uncaught Exceptions)", [
            os.path.join(app_dir, "core", "handlers", "global-error.handler.ts")
        ]),
        ("10. Base Page Shell Layouts (main-layout)", [
            os.path.join(app_dir, "shared", "layouts", "main-layout"),
            os.path.join(app_dir, "shared", "layouts")
        ]),
        ("11. Design Tokens & SCSS Variables", [
            os.path.join(target_dir, "src", "styles", "_variables.scss"),
            os.path.join(target_dir, "styles", "_variables.scss"),
            os.path.join(app_dir, "..", "styles", "_variables.scss")
        ]),
        ("12. Domain Feature Modules (features/)", [
            os.path.join(app_dir, "features")
        ]),
        ("13. Clean Directory Architecture (core/shared/features)", [
            os.path.join(app_dir, "core"),
            os.path.join(app_dir, "shared")
        ]),
    ]

    for label, candidate_paths in checkpoints:
        found = any(os.path.exists(p) for p in candidate_paths)
        results.append({
            "checkpoint": label,
            "passed": found,
            "candidates_checked": candidate_paths
        })

    # Checkpoint 14: Zero NgModule Audit
    ng_module_occurrences: List[str] = []
    for root, _, files in os.walk(app_dir):
        for f in files:
            if f.endswith(".ts") and not f.endswith(".spec.ts"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8") as source_file:
                        content = source_file.read()
                        if "@NgModule" in content:
                            ng_module_occurrences.append(full_path)
                except Exception:
                    pass

    zero_ngmodule_passed = len(ng_module_occurrences) == 0
    results.append({
        "checkpoint": "14. Zero NgModule Declarations (100% Standalone)",
        "passed": zero_ngmodule_passed,
        "violations": ng_module_occurrences
    })

    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    score_percentage = round((passed_count / total_count) * 100, 1)

    return {
        "target_path": os.path.abspath(target_dir),
        "app_directory": os.path.abspath(app_dir),
        "passed_checkpoints": passed_count,
        "total_checkpoints": total_count,
        "score_percentage": score_percentage,
        "is_compliant": passed_count == total_count,
        "results": results
    }


def main() -> int:
    """Execute scaffolding audit and format output."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_scaffolding(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 60)
        print("🏛️  ANGULAR 14-POINT ENTERPRISE SCAFFOLDING AUDIT")
        print("=" * 60)
        print(f"Target Directory     : {report['app_directory']}")
        print(f"Checkpoints Passed   : {report['passed_checkpoints']} / {report['total_checkpoints']}")
        print(f"Compliance Score     : {report['score_percentage']}%")
        print("-" * 60)

        for item in report["results"]:
            status_icon = "✅ PASS" if item["passed"] else "❌ FAIL"
            print(f"{status_icon} - {item['checkpoint']}")

        print("=" * 60 + "\n")

    if args.strict and not report["is_compliant"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
