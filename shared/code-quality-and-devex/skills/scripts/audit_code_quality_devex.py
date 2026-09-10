# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit Code Quality, DevEx & Tooling Standards.

Audits codebases for compliance with enterprise DevEx & quality tooling:
1. Linter & Formatter presence (ESLint, Prettier, Ruff, golangci-lint).
2. Strict Type Safety (tsconfig.json with strict: true, noImplicitAny: true).
3. Pre-commit Hooks (Husky, lint-staged, pre-commit framework).
4. Conventional Commits enforcement (commitlint config, commit-msg hook).
5. Pre-commit Secret Scanning (GitLeaks, TruffleHog).
6. One-command local environment (compose.yaml / docker-compose.yml).
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit code quality, developer tooling, pre-commit hooks, and secret scanning."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory to audit (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if any critical DevEx tool or gate is missing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout",
    )
    return parser.parse_args()


def audit_linter_and_formatter(root_dir: Path) -> Dict[str, Any]:
    linter_files = [
        ".eslintrc.js",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        "eslint.config.js",
        "eslint.config.mjs",
        ".golangci.yml",
        ".golangci.yaml",
        "ruff.toml",
    ]
    formatter_files = [
        ".prettierrc",
        ".prettierrc.json",
        ".prettierrc.js",
        ".prettierrc.cjs",
        "prettier.config.js",
        ".editorconfig",
    ]

    found_linters = [f for f in linter_files if (root_dir / f).is_file()]
    found_formatters = [f for f in formatter_files if (root_dir / f).is_file()]

    # Also check package.json for eslintConfig or prettier keys
    pkg_json = root_dir / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "eslintConfig" in data and "package.json:eslintConfig" not in found_linters:
                found_linters.append("package.json:eslintConfig")
            if "prettier" in data and "package.json:prettier" not in found_formatters:
                found_formatters.append("package.json:prettier")
        except Exception:
            pass

    return {
        "linter_found": len(found_linters) > 0,
        "linter_configs": found_linters,
        "formatter_found": len(found_formatters) > 0,
        "formatter_configs": found_formatters,
    }


def audit_type_safety(root_dir: Path) -> Dict[str, Any]:
    tsconfig = root_dir / "tsconfig.json"
    strict_enabled = False
    no_implicit_any = False
    details: Dict[str, Any] = {"found": False}

    if tsconfig.is_file():
        details["found"] = True
        try:
            content = tsconfig.read_text(encoding="utf-8")
            # Strip comments for simple regex matching
            if re.search(r'"strict"\s*:\s*true', content):
                strict_enabled = True
            if re.search(r'"noImplicitAny"\s*:\s*true', content):
                no_implicit_any = True
        except Exception:
            pass

    # Check python pyproject.toml for mypy strict
    pyproject = root_dir / "pyproject.toml"
    if pyproject.is_file():
        details["found"] = True
        try:
            content = pyproject.read_text(encoding="utf-8")
            if "mypy" in content and "strict = true" in content:
                strict_enabled = True
        except Exception:
            pass

    details["strict_enabled"] = strict_enabled
    details["no_implicit_any"] = no_implicit_any
    return details


def audit_precommit_and_commitlint(root_dir: Path) -> Dict[str, Any]:
    husky_dir = root_dir / ".husky"
    has_husky = husky_dir.is_dir()
    has_precommit_hook = (husky_dir / "pre-commit").is_file() if has_husky else False
    has_commit_msg_hook = (husky_dir / "commit-msg").is_file() if has_husky else False

    commitlint_configs = [
        "commitlint.config.js",
        "commitlint.config.ts",
        "commitlint.config.cjs",
        ".commitlintrc.json",
        ".commitlintrc.js",
    ]
    has_commitlint_config = any((root_dir / f).is_file() for f in commitlint_configs)

    pkg_json = root_dir / "package.json"
    has_lint_staged = False
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "lint-staged" in data or "lint-staged" in data.get("devDependencies", {}):
                has_lint_staged = True
        except Exception:
            pass

    return {
        "husky_installed": has_husky,
        "pre_commit_hook": has_precommit_hook,
        "commit_msg_hook": has_commit_msg_hook,
        "commitlint_configured": has_commitlint_config,
        "lint_staged_configured": has_lint_staged,
    }


def audit_secret_scanning_and_docker(root_dir: Path) -> Dict[str, Any]:
    secret_configs = [
        ".gitleaks.toml",
        ".gitleaksignore",
        ".trufflehog.yaml",
        ".trufflehog.yml",
    ]
    has_secret_scanner = any((root_dir / f).is_file() for f in secret_configs)

    # Check pre-commit hook content for gitleaks
    husky_precommit = root_dir / ".husky" / "pre-commit"
    if husky_precommit.is_file():
        try:
            content = husky_precommit.read_text(encoding="utf-8", errors="ignore")
            if "gitleaks" in content.lower() or "trufflehog" in content.lower():
                has_secret_scanner = True
        except Exception:
            pass

    compose_files = [
        "compose.yaml",
        "compose.yml",
        "docker-compose.yaml",
        "docker-compose.yml",
    ]
    has_docker_compose = any((root_dir / f).is_file() for f in compose_files)

    return {
        "secret_scanner_configured": has_secret_scanner,
        "docker_compose_found": has_docker_compose,
    }


def run_audit(target_dir: str, strict: bool = False) -> Dict[str, Any]:
    root_path = Path(target_dir).resolve()
    linter_fmt = audit_linter_and_formatter(root_path)
    type_safety = audit_type_safety(root_path)
    precommit = audit_precommit_and_commitlint(root_path)
    security_docker = audit_secret_scanning_and_docker(root_path)

    findings: List[str] = []
    passed = True

    if not linter_fmt["linter_found"]:
        findings.append("Linter configuration (ESLint, Ruff, golangci-lint) not found.")
        if strict:
            passed = False

    if not linter_fmt["formatter_found"]:
        findings.append("Formatter configuration (Prettier, EditorConfig) not found.")

    if type_safety["found"] and not type_safety["strict_enabled"]:
        findings.append("Type safety is not configured with 'strict: true' (risk of type drift / unhandled nulls).")
        if strict:
            passed = False

    if not precommit["pre_commit_hook"] and not precommit["lint_staged_configured"]:
        findings.append("Pre-commit quality gate (Husky + lint-staged) not configured on staged files.")
        if strict:
            passed = False

    if not precommit["commitlint_configured"] and not precommit["commit_msg_hook"]:
        findings.append("Conventional Commits enforcement (@commitlint/cli commit-msg hook) not found.")

    if not security_docker["secret_scanner_configured"]:
        findings.append("Pre-commit secret scanning (GitLeaks / TruffleHog) not configured.")

    if not security_docker["docker_compose_found"]:
        findings.append("One-command local development setup (compose.yaml / docker-compose.yml) not found.")

    report = {
        "target": str(root_path),
        "status": "PASS" if passed and not findings else ("WARNING" if passed else "FAIL"),
        "linter_and_formatter": linter_fmt,
        "type_safety": type_safety,
        "precommit_hooks": precommit,
        "secret_scanning_and_docker": security_docker,
        "findings": findings,
    }
    return report


def main() -> None:
    args = parse_arguments()
    report = run_audit(args.target, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stderr.write(f"Code Quality & DevEx Audit: {report['target']}\n")
        sys.stderr.write(f"Status: {report['status']}\n")
        sys.stderr.write(f"Linter Configured:    {report['linter_and_formatter']['linter_found']}\n")
        sys.stderr.write(f"Formatter Configured: {report['linter_and_formatter']['formatter_found']}\n")
        sys.stderr.write(f"Strict Type Safety:   {report['type_safety']['strict_enabled']}\n")
        sys.stderr.write(f"Pre-commit Hooks:     {report['precommit_hooks']['pre_commit_hook']}\n")
        sys.stderr.write(f"Conventional Commits: {report['precommit_hooks']['commitlint_configured']}\n")
        sys.stderr.write(f"Secret Scanner:       {report['secret_scanning_and_docker']['secret_scanner_configured']}\n")
        sys.stderr.write(f"Docker Compose:       {report['secret_scanning_and_docker']['docker_compose_found']}\n")
        if report["findings"]:
            sys.stderr.write("\nFindings / Recommendations:\n")
            for finding in report["findings"]:
                sys.stderr.write(f"  - {finding}\n")

    if report["status"] == "FAIL" and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
