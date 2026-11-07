#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
scaffold_koa_test_suite.py
Automates the scaffolding of the recommended enterprise testing directory structure,
Vitest configuration, and harness setup files for Koa + Node.js + Sequelize projects in JavaScript.
Emits structured JSON to stdout and diagnostics to stderr.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

DEFAULT_DIRS = [
    "tests/unit/services",
    "tests/unit/utils",
    "tests/unit/validators",
    "tests/unit/mappers",
    "tests/integration/models",
    "tests/integration/repositories",
    "tests/integration/transactions",
    "tests/api/auth",
    "tests/api/users",
    "tests/fixtures",
    "tests/mocks",
    "tests/setup"
]

def scaffold_test_suite(target_root: str, dry_run: bool = False) -> Dict[str, Any]:
    target_path = os.path.abspath(target_root)
    created_dirs: List[str] = []
    created_files: List[str] = []

    if not os.path.exists(target_path) and not dry_run:
        os.makedirs(target_path, exist_ok=True)

    # 1. Create directories
    for rel_dir in DEFAULT_DIRS:
        full_dir = os.path.join(target_path, rel_dir)
        if not os.path.exists(full_dir):
            if not dry_run:
                os.makedirs(full_dir, exist_ok=True)
            created_dirs.append(rel_dir)

    # 2. Create global test setup in JavaScript if absent
    global_setup_rel = "tests/setup/global.js"
    global_setup_full = os.path.join(target_path, global_setup_rel)
    if not os.path.exists(global_setup_full):
        content = """/**
 * Global test environment bootstrap for Vitest in JavaScript.
 * Configures process environment variables before test files execute.
 */

process.env.NODE_ENV = 'test';
process.env.TEST_DB_NAME = process.env.TEST_DB_NAME || 'koa_app_test';
process.env.TEST_DB_USER = process.env.TEST_DB_USER || 'root';
process.env.TEST_DB_PASSWORD = process.env.TEST_DB_PASSWORD || 'secret';
process.env.TEST_DB_HOST = process.env.TEST_DB_HOST || '127.0.0.1';
process.env.TEST_DB_PORT = process.env.TEST_DB_PORT || '3306';
"""
        if not dry_run:
            with open(global_setup_full, "w", encoding="utf-8") as f:
                f.write(content)
        created_files.append(global_setup_rel)

    return {
        "status": "success",
        "target_path": target_path,
        "dry_run": dry_run,
        "created_directories": created_dirs,
        "created_files": created_files,
        "summary": {
            "total_directories_created": len(created_dirs),
            "total_files_created": len(created_files)
        }
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold Koa.js testing architecture directory structure and boilerplates in JavaScript."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Root directory of the target Koa project (default: current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing directories or files to disk"
    )

    args = parser.parse_args()
    report = scaffold_test_suite(args.target, dry_run=args.dry_run)

    # Diagnostic output on stderr
    sys.stderr.write(
        f"[scaffold_koa_test_suite] Scaffolding complete for: {report['target_path']}\n"
        f"  Directories created: {report['summary']['total_directories_created']}\n"
        f"  Files created: {report['summary']['total_files_created']}\n"
    )

    # Structured JSON on stdout
    print(json.dumps(report, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
