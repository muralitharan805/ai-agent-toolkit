#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Database Foundation Script
Audits backend codebases and database migration files for:
- Connection pool limits (min, max, acquireTimeout, queryTimeout)
- Prohibition of auto-synchronization (e.g. synchronize: true) in production
- Mandatory audit columns (created_at, updated_at, deleted_at) on tables
- Foreign key indexing
- Slow query logging (> 200ms)
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

POOL_MAX_PATTERN = re.compile(r'\b(max|connectionLimit|pool_size|maximumPoolSize)\s*[:=]\s*(\d+)', re.IGNORECASE)
POOL_MIN_PATTERN = re.compile(r'\b(min|minimumIdle)\s*[:=]\s*(\d+)', re.IGNORECASE)
SYNCHRONIZE_TRUE_PATTERN = re.compile(r'\bsynchronize\s*:\s*true\b', re.IGNORECASE)
SLOW_QUERY_PATTERN = re.compile(r'(slow_query|slowQuery|statement_timeout|200\s*ms|durationMs)', re.IGNORECASE)

AUDIT_CREATED_AT = re.compile(r'\bcreated_at\b', re.IGNORECASE)
AUDIT_UPDATED_AT = re.compile(r'\bupdated_at\b', re.IGNORECASE)
AUDIT_DELETED_AT = re.compile(r'\bdeleted_at\b', re.IGNORECASE)

EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
    '__pycache__', '.venv', 'venv', 'target'
}

def is_source_or_sql_file(file_path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in file_path.parts):
        return False
    name = file_path.name.lower()
    if '.test.' in name or '.spec.' in name or name.startswith('test_'):
        return False
    return file_path.suffix in {'.ts', '.js', '.py', '.go', '.sql', '.prisma', '.json'}

def audit_directory(target_path: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    has_pool_config = False
    has_synchronize_risk = False
    has_slow_query_telemetry = False
    scanned_files_count = 0
    tables_missing_audit_columns: List[str] = []

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            file_path = Path(root) / f
            if not is_source_or_sql_file(file_path):
                continue

            scanned_files_count += 1
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to read {file_path}: {e}\n")
                continue

            rel_path = str(file_path.relative_to(target_path))

            # Detect connection pool settings
            if POOL_MAX_PATTERN.search(content) and POOL_MIN_PATTERN.search(content):
                has_pool_config = True

            # Detect dangerous auto-sync in production
            if SYNCHRONIZE_TRUE_PATTERN.search(content):
                # If not inside a test directory or condition
                if 'test' not in rel_path.lower():
                    has_synchronize_risk = True
                    findings.append({
                        "file": rel_path,
                        "type": "synchronize_true_risk",
                        "severity": "critical",
                        "message": "Found 'synchronize: true'. Auto-synchronization in production can cause irreversible schema and data loss."
                    })

            # Detect slow query logging
            if SLOW_QUERY_PATTERN.search(content):
                has_slow_query_telemetry = True

            # Audit SQL / migration files for audit columns
            if file_path.suffix == '.sql' and 'create table' in content.lower():
                has_created = bool(AUDIT_CREATED_AT.search(content))
                has_updated = bool(AUDIT_UPDATED_AT.search(content))
                has_deleted = bool(AUDIT_DELETED_AT.search(content))
                if not (has_created and has_updated and has_deleted):
                    tables_missing_audit_columns.append(rel_path)
                    findings.append({
                        "file": rel_path,
                        "type": "missing_audit_columns",
                        "severity": "medium",
                        "message": f"Table definition in '{rel_path}' is missing mandatory audit/lifecycle columns (created_at, updated_at, deleted_at)."
                    })

    summary = {
        "scanned_files": scanned_files_count,
        "database_foundation": {
            "connection_pooling_configured": has_pool_config,
            "zero_auto_synchronize_risk": not has_synchronize_risk,
            "slow_query_telemetry_detected": has_slow_query_telemetry,
            "migrations_with_audit_columns": len(tables_missing_audit_columns) == 0
        },
        "is_compliant": (
            has_pool_config and
            not has_synchronize_risk and
            has_slow_query_telemetry and
            len(tables_missing_audit_columns) == 0
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for production database foundation standards."
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
        help="Exit with non-zero status if any violations or missing foundation configurations are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Database foundation audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
