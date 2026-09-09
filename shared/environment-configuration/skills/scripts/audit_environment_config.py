#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Environment Configuration & Secrets Hygiene (`audit_environment_config.py`)
Inspects projects for .env gitignore compliance, .env.example parity, junior-friendly documentation,
and detects scattered raw process.env / os.environ access in business logic.
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Set, Any

RAW_ENV_PATTERNS = [
    re.compile(r"process\.env\.([A-Z0-9_]+)"),
    re.compile(r"os\.environ\[['\"]([A-Z0-9_]+)['\"]\]"),
    re.compile(r"os\.getenv\(['\"]([A-Z0-9_]+)['\"]\)"),
    re.compile(r"os\.Getenv\(\"([A-Z0-9_]+)\"\)"),
]

ALLOWED_CONFIG_PATHS = {
    "config",
    "src/config",
    "src/common/config",
    "app/config",
    "internal/config",
    "pkg/config",
}

SUSPICIOUS_SECRET_PATTERNS = [
    re.compile(r"(ghp_[A-Za-z0-9_]{36}|github_pat_[A-Za-z0-9_]{82})"),
    re.compile(r"ey[A-Za-z0-9-_]+\.ey[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"),  # JWT token pattern
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key ID
    re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"),  # Slack Token
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit project environment configuration, secrets hygiene, and scattered env variables.",
        epilog="Example: python3 scripts/audit_environment_config.py . --strict"
    )
    parser.add_argument("project_dir", help="Path to project root directory")
    parser.add_argument("--json", action="store_true", help="Output results formatted as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    return parser.parse_args()

def parse_env_file(filepath: str) -> Dict[str, Any]:
    variables = {}
    comments_before = {}
    current_comments = []

    if not os.path.isfile(filepath):
        return {"exists": False, "variables": variables, "comments": comments_before}

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                current_comments = []
                continue
            if stripped.startswith("#"):
                current_comments.append(stripped)
                continue
            if "=" in stripped:
                key, val = stripped.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                variables[key] = val
                comments_before[key] = list(current_comments)
                current_comments = []

    return {"exists": True, "variables": variables, "comments": comments_before}

def check_gitignore(project_dir: str) -> List[Dict[str, str]]:
    violations = []
    gitignore_path = os.path.join(project_dir, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return [{"type": "MISSING_GITIGNORE", "message": "No .gitignore file found in project root."}]

    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Check for .env ignore pattern
    has_env_ignore = any(re.search(r"^\s*\.env(\s+.*|\*|\b)?$", line, re.MULTILINE) for line in content.splitlines())
    if not has_env_ignore:
        violations.append({
            "type": "UNIGNORED_ENV",
            "message": "'.env' is not properly ignored in .gitignore. Secrets risk being committed to version control."
        })

    # Check if a committed .env file exists
    dot_env_path = os.path.join(project_dir, ".env")
    if os.path.isfile(dot_env_path):
        # Warning if it's there
        pass
    return violations

def check_env_example_quality(project_dir: str) -> Dict[str, Any]:
    issues = []
    warnings = []
    example_path = os.path.join(project_dir, ".env.example")

    parsed = parse_env_file(example_path)
    if not parsed["exists"]:
        issues.append({
            "type": "MISSING_ENV_EXAMPLE",
            "message": "Missing required '.env.example' template in project root."
        })
        return {"issues": issues, "warnings": warnings, "variables": {}}

    vars_dict = parsed["variables"]
    comments_dict = parsed["comments"]

    for var_name, var_value in vars_dict.items():
        # Check for junior-friendly comments
        comments = comments_dict.get(var_name, [])
        if not comments or len(comments) == 0:
            warnings.append({
                "type": "UNDOCUMENTED_ENV_VARIABLE",
                "variable": var_name,
                "message": f"Variable '{var_name}' in .env.example lacks explanatory comments."
            })

        # Check for leaked secrets in .env.example
        for pat in SUSPICIOUS_SECRET_PATTERNS:
            if pat.search(var_value):
                issues.append({
                    "type": "COMMITTED_SECRET_IN_EXAMPLE",
                    "variable": var_name,
                    "message": f"Variable '{var_name}' appears to contain a real live credential in .env.example! Use placeholder values."
                })

    return {"issues": issues, "warnings": warnings, "variables": vars_dict}

def check_scattered_env_access(project_dir: str) -> List[Dict[str, Any]]:
    violations = []
    src_dirs = ["src", "app", "internal", "pkg"]

    for src_root in src_dirs:
        full_src = os.path.join(project_dir, src_root)
        if not os.path.isdir(full_src):
            continue

        for root, _, files in os.walk(full_src):
            rel_root = os.path.relpath(root, project_dir)
            if any(rel_root.startswith(allowed) for allowed in ALLOWED_CONFIG_PATHS):
                continue

            for f in files:
                if f.endswith((".ts", ".js", ".py", ".go")):
                    file_path = os.path.join(root, f)
                    rel_file = os.path.relpath(file_path, project_dir)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                            for idx, line in enumerate(fh, 1):
                                for pat in RAW_ENV_PATTERNS:
                                    m = pat.search(line)
                                    if m:
                                        var_name = m.group(1)
                                        violations.append({
                                            "type": "SCATTERED_RAW_ENV_ACCESS",
                                            "path": f"{rel_file}:{idx}",
                                            "variable": var_name,
                                            "message": f"Direct raw environment access '{m.group(0)}' in business code. Access via central ConfigService instead."
                                        })
                    except Exception:
                        pass
    return violations

def run_audit(project_dir: str, strict: bool = False) -> Dict[str, Any]:
    abs_project = os.path.abspath(project_dir)
    sys.stderr.write(f"🔍 Auditing Environment & Secrets Hygiene for: {abs_project}\n")

    gitignore_issues = check_gitignore(abs_project)
    example_audit = check_env_example_quality(abs_project)
    scattered_issues = check_scattered_env_access(abs_project)

    all_violations = gitignore_issues + example_audit["issues"] + scattered_issues
    all_warnings = example_audit["warnings"]

    is_compliant = len(all_violations) == 0
    if strict and len(all_warnings) > 0:
        is_compliant = False

    report = {
        "status": "PASS" if is_compliant else "FAIL",
        "target_directory": abs_project,
        "violations_count": len(all_violations),
        "warnings_count": len(all_warnings),
        "violations": all_violations,
        "warnings": all_warnings,
        "example_variables_count": len(example_audit.get("variables", {})),
    }
    return report

def main():
    args = parse_args()
    report = run_audit(args.project_dir, args.strict)

    print(json.dumps(report, indent=2))

    if report["status"] == "FAIL":
        sys.stderr.write(f"❌ Environment & Secrets audit FAILED with {report['violations_count']} violation(s).\n")
        sys.exit(1)
    else:
        sys.stderr.write("✅ Environment & Secrets audit PASSED cleanly.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
