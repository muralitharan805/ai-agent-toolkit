#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit API Contracts & Documentation Script
Audits backend codebases for OpenAPI 3.x standards and contract testing:
- OpenAPI endpoint annotations and schema documentation
- Modeling of both success and error responses (400, 401, 404, 500)
- Production environment restrictions on interactive /docs sandboxes
- Consumer-driven contract testing (Pact) usage
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

OPENAPI_ANNOTATION_PATTERN = re.compile(r'(@ApiOperation|@ApiResponse|@ApiTags|@ApiProperty|openapi:|swagger:)', re.IGNORECASE)
ERROR_STATUS_MODEL_PATTERN = re.compile(r'(@ApiResponse\s*\(\s*\{[^}]*status\s*:\s*(400|401|403|404|409|422|500)|responses\s*:\s*\{[^}]*[\'"`](4\d\d|5\d\d)[\'"`])', re.DOTALL | re.IGNORECASE)
DOCS_ROUTE_PATTERN = re.compile(r'(\.setup\s*\(\s*[\'"`]docs[\'"`]|SwaggerModule\.setup|app\.use\s*\(\s*[\'"`]/docs[\'"`])', re.IGNORECASE)
PROD_DOCS_GUARD_PATTERN = re.compile(r'\b(NODE_ENV\s*===?\s*[\'"`]production[\'"`]|isProduction|enableDocs)\b', re.IGNORECASE)
PACT_PATTERN = re.compile(r'(@pact-foundation|pact-broker|PactV3|PactConsumer)', re.IGNORECASE)

EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
    '__pycache__', '.venv', 'venv', 'target'
}

def is_source_file(file_path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in file_path.parts):
        return False
    name = file_path.name.lower()
    if '.test.' in name or '.spec.' in name or name.startswith('test_'):
        return False
    return file_path.suffix in {'.ts', '.js', '.py', '.go', '.rs', '.java', '.yaml', '.yml'}

def audit_directory(target_path: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    scanned_files_count = 0
    has_openapi_annotations = False
    has_error_models = False
    has_pact_contracts = False
    unprotected_docs_count = 0

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            file_path = Path(root) / f
            if not is_source_file(file_path):
                continue

            scanned_files_count += 1
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to read {file_path}: {e}\n")
                continue

            rel_path = str(file_path.relative_to(target_path))

            if OPENAPI_ANNOTATION_PATTERN.search(content):
                has_openapi_annotations = True

            if ERROR_STATUS_MODEL_PATTERN.search(content):
                has_error_models = True

            if PACT_PATTERN.search(content):
                has_pact_contracts = True

            # Detect Swagger /docs setup without production guard
            if DOCS_ROUTE_PATTERN.search(content):
                if not PROD_DOCS_GUARD_PATTERN.search(content):
                    unprotected_docs_count += 1
                    findings.append({
                        "file": rel_path,
                        "type": "unprotected_swagger_docs_in_production",
                        "severity": "high",
                        "message": f"Interactive documentation mounted in `{rel_path}` lacks production environment checks. Public documentation exposes internal routes and attack surface."
                    })

    summary = {
        "scanned_files": scanned_files_count,
        "api_documentation": {
            "openapi_annotations_detected": has_openapi_annotations,
            "error_response_models_detected": has_error_models,
            "contract_testing_detected": has_pact_contracts,
            "unprotected_docs_endpoints": unprotected_docs_count
        },
        "is_compliant": (
            unprotected_docs_count == 0 and
            has_openapi_annotations
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for OpenAPI documentation standards and contract testing."
    )
    parser.add_argument(
        "target_path",
        nargs="?",
        default=".",
        help="Path to backend codebase or directory to audit (default: current directory)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any documentation or contract violations are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("API documentation audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
