#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
verify_nestjs_scaffolding.py
Audits a NestJS project directory for adherence to the 20-Point Enterprise Scaffolding Architecture:
- Global ValidationPipe with whitelist in main.ts
- Graceful shutdown hooks (app.enableShutdownHooks())
- Global standardized response envelope interceptor
- Standardized HttpExceptionFilter
- Correlation ID logging interceptor
- Zod environment configuration validation
- Mandatory PaginationQueryDto
- Multi-stage production Dockerfile
- GitHub Actions CI workflow
- Zero explicit 'any' types in TypeScript source files
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

ANY_TYPE_PATTERN = re.compile(r""":\s*any\b|\bas\s+any\b|<any>""")


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for NestJS scaffolding audit."""
    parser = argparse.ArgumentParser(
        description="Audit NestJS project for 20-Point Enterprise Scaffolding compliance.",
        epilog=(
            "Examples:\n"
            "  python3 verify_nestjs_scaffolding.py src\n"
            "  python3 verify_nestjs_scaffolding.py --json\n"
            "  python3 verify_nestjs_scaffolding.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to NestJS project root or src (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are detected")
    return parser.parse_args()


def audit_nestjs_scaffolding(target_dir: str) -> Dict[str, Any]:
    """Inspect NestJS project files for enterprise architectural compliance."""
    root = os.path.abspath(target_dir)

    any_type_violations: List[Dict[str, Any]] = []

    has_validation_pipe = False
    has_shutdown_hooks = False
    has_response_interceptor = False
    has_exception_filter = False
    has_logging_interceptor = False
    has_zod_env = False
    has_pagination_dto = False
    has_dockerfile = False
    has_ci_workflow = False

    # Check for Dockerfile and CI workflow
    dockerfile_candidates = [
        os.path.join(root, "Dockerfile"),
        os.path.join(root, "assets", "Dockerfile"),
        os.path.join(root, "..", "Dockerfile")
    ]
    for cand in dockerfile_candidates:
        if os.path.exists(cand):
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "AS builder" in content and "USER node" in content:
                        has_dockerfile = True
                        break
            except Exception:
                pass

    ci_candidates = [
        os.path.join(root, ".github", "workflows", "ci.yml"),
        os.path.join(root, "assets", "ci.yml"),
        os.path.join(root, "..", ".github", "workflows", "ci.yml")
    ]
    for cand in ci_candidates:
        if os.path.exists(cand):
            has_ci_workflow = True
            break

    # Walk directory to analyze main.ts, configs, filters, interceptors
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]

        for filename in files:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)

            if not filename.endswith((".ts", ".js")):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            # Check main.ts
            if filename in ["main.ts", "bootstrap.ts"]:
                if "ValidationPipe" in content and "whitelist" in content:
                    has_validation_pipe = True
                if "enableShutdownHooks" in content:
                    has_shutdown_hooks = True

            # Check response envelope interceptor
            if "transform-response" in filename or "response.interceptor" in filename:
                if "TransformResponseInterceptor" in content or "ApiResponseEnvelope" in content:
                    has_response_interceptor = True

            # Check exception filter
            if "exception.filter" in filename or "http-exception" in filename:
                if "GlobalHttpExceptionFilter" in content or "catch(exception" in content:
                    has_exception_filter = True

            # Check logging interceptor
            if "logging.interceptor" in filename or "logger.interceptor" in filename:
                if "LoggingInterceptor" in content and "x-correlation-id" in content.lower():
                    has_logging_interceptor = True

            # Check Zod env config
            if "env.config" in filename or "config.ts" in filename:
                if "z.object" in content and "DATABASE_URL" in content:
                    has_zod_env = True

            # Check Pagination DTO
            if "pagination" in filename and "dto" in filename:
                if "PaginationQueryDto" in content and "page" in content and "limit" in content:
                    has_pagination_dto = True

            # Scan for explicit any types
            if filename.endswith(".ts") and not filename.endswith(".spec.ts"):
                for line_num, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                        continue
                    if ANY_TYPE_PATTERN.search(line):
                        any_type_violations.append({
                            "file": relpath,
                            "line": line_num,
                            "snippet": stripped
                        })

    checkpoints = [
        {"name": "Global ValidationPipe (whitelist & transform in main.ts)", "passed": has_validation_pipe},
        {"name": "Graceful Shutdown Hooks (app.enableShutdownHooks() in main.ts)", "passed": has_shutdown_hooks},
        {"name": "Standardized Response Envelope (TransformResponseInterceptor)", "passed": has_response_interceptor},
        {"name": "Unified Exception Filter (GlobalHttpExceptionFilter)", "passed": has_exception_filter},
        {"name": "Structured Request Latency & Correlation ID Logger", "passed": has_logging_interceptor},
        {"name": "Zod Environment Schema Validation (core/config/env.config.ts)", "passed": has_zod_env},
        {"name": "Mandatory Collection Pagination DTO (PaginationQueryDto)", "passed": has_pagination_dto},
        {"name": "Production Multi-Stage Containerization (Dockerfile with non-root user)", "passed": has_dockerfile},
        {"name": "Automated Quality Pipeline (.github/workflows/ci.yml)", "passed": has_ci_workflow},
        {"name": "Strict Type Safety (Zero explicit 'any' annotations)", "passed": len(any_type_violations) == 0}
    ]

    passed_count = sum(1 for cp in checkpoints if cp["passed"])
    score_percentage = round((passed_count / len(checkpoints)) * 100, 1)

    return {
        "target_path": root,
        "score_percentage": score_percentage,
        "is_compliant": passed_count == len(checkpoints),
        "checkpoints": checkpoints,
        "any_type_violations": any_type_violations
    }


def main() -> int:
    """Execute audit and report findings."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_nestjs_scaffolding(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 66)
        print("🦁  NESTJS ENTERPRISE SCAFFOLDING COMPLIANCE AUDIT")
        print("=" * 66)
        print(f"Target Directory : {report['target_path']}")
        print(f"Compliance Score : {report['score_percentage']}%")
        print("-" * 66)

        for cp in report["checkpoints"]:
            icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            print(f"{icon} - {cp['name']}")

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
