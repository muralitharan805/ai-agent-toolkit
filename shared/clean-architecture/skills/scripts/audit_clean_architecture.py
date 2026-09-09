#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Clean Architecture & Domain-First Standards (`audit_clean_architecture.py`)
Scans backend source trees for layer-first antipatterns, leaky domain entity imports,
and test co-location compliance. Emits JSON to stdout and diagnostics to stderr.
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any

FORBIDDEN_TOP_LEVEL_DIRS = {
    "controllers",
    "services",
    "repositories",
    "handlers",
    "models",
}

FORBIDDEN_DOMAIN_IMPORTS = [
    r"@nestjs",
    r"express",
    r"koa",
    r"fastify",
    r"typeorm",
    r"prisma",
    r"mongoose",
    r"sequelize",
    r"sqlalchemy",
    r"django\.db",
    r"gorm\.io",
    r"github\.com/gin-gonic",
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit a backend project for Clean Architecture and Domain-First compliance.",
        epilog="Example: python3 scripts/audit_clean_architecture.py src/ --json"
    )
    parser.add_argument("target_dir", help="Path to project root or source directory (e.g., ./src)")
    parser.add_argument("--json", action="store_true", help="Output results strictly formatted as JSON (default: True)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as violations")
    return parser.parse_args()

def check_layer_first_structure(base_dir: str) -> List[Dict[str, str]]:
    violations = []
    # Check immediate subdirectories of target_dir
    if not os.path.exists(base_dir):
        return [{"type": "DIRECTORY_NOT_FOUND", "message": f"Target directory does not exist: {base_dir}"}]

    try:
        entries = os.listdir(base_dir)
    except Exception as e:
        return [{"type": "READ_ERROR", "message": str(e)}]

    for entry in entries:
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            norm_name = entry.lower()
            if norm_name in FORBIDDEN_TOP_LEVEL_DIRS:
                violations.append({
                    "type": "LAYER_FIRST_TOP_LEVEL_DIR",
                    "path": full_path,
                    "message": f"Found forbidden layer-first top-level directory '{entry}/'. Refactor into 'modules/<feature>/' domain-first packaging."
                })
    return violations

def check_domain_entity_purity(base_dir: str) -> List[Dict[str, str]]:
    violations = []
    entity_pattern = re.compile(r".*(\.entity\.(ts|js|py)|_entity\.(go|py))$")
    import_patterns = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_DOMAIN_IMPORTS]

    for root, _, files in os.walk(base_dir):
        for f in files:
            if entity_pattern.match(f):
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as file_handle:
                        for idx, line in enumerate(file_handle, 1):
                            for pat in import_patterns:
                                if pat.search(line):
                                    violations.append({
                                        "type": "LEAKY_DOMAIN_DEPENDENCY",
                                        "path": f"{file_path}:{idx}",
                                        "message": f"Domain entity imports external framework/ORM: '{line.strip()}'. Domain entities must have zero external dependencies."
                                    })
                except Exception as ex:
                    violations.append({
                        "type": "FILE_READ_ERROR",
                        "path": file_path,
                        "message": f"Failed to read file: {str(ex)}"
                    })
    return violations

def check_test_colocation(base_dir: str) -> Dict[str, Any]:
    stats = {"services_found": 0, "colocated_tests_found": 0}
    warnings = []
    service_pattern = re.compile(r"^(.+)\.(service|usecase)\.(ts|js|py|go)$")

    for root, _, files in os.walk(base_dir):
        file_set = set(files)
        for f in files:
            m = service_pattern.match(f)
            if m:
                base_name = m.group(1)
                ext = m.group(3)
                service_type = m.group(2)
                stats["services_found"] += 1
                
                # Check for co-located test
                expected_tests = [
                    f"{base_name}.{service_type}.test.{ext}",
                    f"{base_name}.{service_type}.spec.{ext}",
                    f"{base_name}_{service_type}_test.{ext}",
                    f"test_{base_name}_{service_type}.py",
                ]
                has_test = any(t in file_set for t in expected_tests)
                if has_test:
                    stats["colocated_tests_found"] += 1
                else:
                    warnings.append({
                        "type": "MISSING_COLOCATED_TEST",
                        "path": os.path.join(root, f),
                        "message": f"Service '{f}' lacks a co-located unit test file in the same directory."
                    })
    return {"stats": stats, "warnings": warnings}

def run_audit(target_dir: str, strict: bool = False) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_dir)
    sys.stderr.write(f"🔍 Auditing Clean Architecture compliance for: {abs_target}\n")

    structure_violations = check_layer_first_structure(abs_target)
    entity_violations = check_domain_entity_purity(abs_target)
    test_audit = check_test_colocation(abs_target)

    all_violations = structure_violations + entity_violations
    all_warnings = test_audit["warnings"]

    is_compliant = len(all_violations) == 0
    if strict and len(all_warnings) > 0:
        is_compliant = False

    report = {
        "status": "PASS" if is_compliant else "FAIL",
        "target_directory": abs_target,
        "violations_count": len(all_violations),
        "warnings_count": len(all_warnings),
        "violations": all_violations,
        "warnings": all_warnings,
        "test_stats": test_audit["stats"],
    }
    return report

def main():
    args = parse_args()
    report = run_audit(args.target_dir, args.strict)
    
    print(json.dumps(report, indent=2))
    
    if report["status"] == "FAIL":
        sys.stderr.write(f"❌ Clean Architecture audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ Clean Architecture audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
