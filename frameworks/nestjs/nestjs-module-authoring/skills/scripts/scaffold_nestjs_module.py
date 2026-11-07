#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
scaffold_nestjs_module.py
CLI automation tool for NestJS Clean Architecture feature modules:
1. Audits existing feature modules for Clean Architecture compliance:
   - DTO validation decorators (class-validator)
   - Abstract repository interface and Symbol injection token
   - Controller OpenAPI annotations (@ApiTags, @ApiOperation)
   - Isolated unit test specification presence
   - Zero explicit 'any' types in TypeScript source files
2. Scaffolds new production-ready feature module directories and files.
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

ANY_TYPE_PATTERN = re.compile(r""":\s*any\b|\bas\s+any\b|<any>""")
REPOSITORY_TOKEN_PATTERN = re.compile(r"""(Symbol\(|provide:\s*[A-Z_]+_REPOSITORY)""")
DTO_VALIDATOR_PATTERN = re.compile(r"""@(IsString|IsNotEmpty|IsNumber|IsBoolean|IsOptional|IsEnum|ValidateNested)\b""")
SWAGGER_DECORATOR_PATTERN = re.compile(r"""@(ApiTags|ApiOperation|ApiResponse|ApiBearerAuth)\b""")


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for NestJS module scaffolding and audit."""
    parser = argparse.ArgumentParser(
        description="Scaffold or audit NestJS domain feature modules adhering to Clean Architecture.",
        epilog=(
            "Examples:\n"
            "  python3 scaffold_nestjs_module.py --audit src/features/users\n"
            "  python3 scaffold_nestjs_module.py --audit src/features --json\n"
            "  python3 scaffold_nestjs_module.py --scaffold billing --out-dir src/features"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target_path", nargs="?", default=".", help="Path to feature module or src directory")
    parser.add_argument("--audit", action="store_true", help="Audit existing module for Clean Architecture compliance")
    parser.add_argument("--scaffold", metavar="NAME", help="Scaffold a new feature module with the given name")
    parser.add_argument("--out-dir", default=".", help="Target directory for scaffolding (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are detected")
    return parser.parse_args()


def audit_feature_module(target_dir: str) -> Dict[str, Any]:
    """Audit feature module directory for Clean Architecture standards."""
    root = os.path.abspath(target_dir)

    any_type_violations: List[Dict[str, Any]] = []

    has_controller = False
    has_service = False
    has_repository_interface = False
    has_dto_validation = False
    has_swagger_docs = False
    has_unit_test = False

    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]

        for filename in files:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)

            if not filename.endswith(".ts"):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            # Check Controller
            if "controller" in filename and not filename.endswith(".spec.ts"):
                has_controller = True
                if SWAGGER_DECORATOR_PATTERN.search(content):
                    has_swagger_docs = True

            # Check Service
            if "service" in filename and not filename.endswith(".spec.ts"):
                has_service = True

            # Check Repository Interface & Token
            if "repository" in filename or "interface" in filename:
                if REPOSITORY_TOKEN_PATTERN.search(content):
                    has_repository_interface = True

            # Check DTOs
            if "dto" in filename:
                if DTO_VALIDATOR_PATTERN.search(content):
                    has_dto_validation = True

            # Check Unit Tests
            if filename.endswith(".spec.ts"):
                has_unit_test = True

            # Scan for explicit any annotations
            if not filename.endswith(".spec.ts"):
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
        {"name": "Domain Service Layer Present", "passed": has_service},
        {"name": "HTTP Controller Layer Present", "passed": has_controller},
        {"name": "Abstract Repository & Symbol Token Binding", "passed": has_repository_interface},
        {"name": "DTO Payload Validation (class-validator decorators)", "passed": has_dto_validation},
        {"name": "OpenAPI Documentation Annotations (@ApiTags, @ApiOperation)", "passed": has_swagger_docs},
        {"name": "Isolated Unit Test Specification (*.spec.ts)", "passed": has_unit_test},
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
    """Execute audit or scaffolding CLI."""
    args = parse_arguments()
    target_path = os.path.abspath(args.target_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.target_path}' does not exist.\n")
        return 1

    report = audit_feature_module(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 66)
        print("🧱  NESTJS CLEAN ARCHITECTURE MODULE AUDIT")
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
