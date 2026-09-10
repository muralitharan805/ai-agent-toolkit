# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit CI/CD & Build Infrastructure Standards.

Audits codebases for compliance with enterprise CI/CD & container build standards:
1. Multi-stage Dockerfile architecture.
2. Non-root runtime user enforcement (USER instruction).
3. Frozen lockfile usage in container builds and CI (pnpm install --frozen-lockfile).
4. CI pipeline quality gate definition (.github/workflows).
5. Container vulnerability scanning integration (Trivy).
6. Immutable Git-SHA image versioning (prohibiting latest in production).
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
        description="Audit CI/CD pipelines, multi-stage Dockerfiles, non-root runtime, and vulnerability scanning."
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
        help="Exit with non-zero code if any critical build or security gate is missing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout",
    )
    return parser.parse_args()


def audit_dockerfiles(root_dir: Path) -> Dict[str, Any]:
    dockerfiles = []
    for root, _, files in os.walk(root_dir):
        if any(ignored in root for ignored in [".git", "node_modules", "dist", "coverage"]):
            continue
        for file in files:
            if file == "Dockerfile" or file.endswith(".dockerfile"):
                dockerfiles.append(Path(root) / file)

    has_multistage = False
    has_non_root = False
    has_frozen_lockfile = False
    inspected_files = []

    for df in dockerfiles:
        rel_path = str(df.relative_to(root_dir))
        inspected_files.append(rel_path)
        try:
            content = df.read_text(encoding="utf-8", errors="ignore")
            # Multi-stage check: multiple FROM or FROM ... AS
            from_matches = re.findall(r"^\s*FROM\s+", content, re.MULTILINE | re.IGNORECASE)
            if len(from_matches) > 1 or re.search(r"FROM\s+.*AS\s+", content, re.IGNORECASE):
                has_multistage = True

            # Non-root check: USER instruction with non-root username/uid
            user_match = re.search(r"^\s*USER\s+([a-zA-Z0-9_-]+)", content, re.MULTILINE)
            if user_match and user_match.group(1).lower() not in ["root", "0"]:
                has_non_root = True

            # Frozen lockfile check
            if "--frozen-lockfile" in content or "--frozen" in content:
                has_frozen_lockfile = True
        except Exception:
            pass

    return {
        "dockerfiles_found": inspected_files,
        "is_multistage": has_multistage,
        "runs_as_non_root": has_non_root,
        "uses_frozen_lockfile": has_frozen_lockfile,
    }


def audit_ci_workflows(root_dir: Path) -> Dict[str, Any]:
    workflows_dir = root_dir / ".github" / "workflows"
    workflow_files = []
    if workflows_dir.is_dir():
        workflow_files = [f for f in workflows_dir.glob("*.yml")] + [
            f for f in workflows_dir.glob("*.yaml")
        ]

    has_ci = len(workflow_files) > 0
    has_lint_check = False
    has_type_check = False
    has_unit_tests = False
    has_trivy_scan = False
    has_frozen_install = False
    has_sha_tag = False
    uses_latest_tag = False

    for wf in workflow_files:
        try:
            content = wf.read_text(encoding="utf-8", errors="ignore")
            if "lint" in content.lower():
                has_lint_check = True
            if "typecheck" in content.lower() or "tsc" in content.lower():
                has_type_check = True
            if "test" in content.lower():
                has_unit_tests = True
            if "trivy" in content.lower():
                has_trivy_scan = True
            if "--frozen-lockfile" in content or "--frozen" in content:
                has_frozen_install = True
            if "github.sha" in content or "sha-" in content:
                has_sha_tag = True
            if re.search(r":latest", content):
                uses_latest_tag = True
        except Exception:
            pass

    return {
        "has_ci_workflows": has_ci,
        "workflow_count": len(workflow_files),
        "checks": {
            "lint": has_lint_check,
            "typecheck": has_type_check,
            "tests": has_unit_tests,
            "trivy_scan": has_trivy_scan,
            "frozen_install": has_frozen_install,
            "sha_tagging": has_sha_tag,
            "prohibited_latest_used": uses_latest_tag,
        },
    }


def run_audit(target_dir: str, strict: bool = False) -> Dict[str, Any]:
    root_path = Path(target_dir).resolve()
    docker_details = audit_dockerfiles(root_path)
    ci_details = audit_ci_workflows(root_path)

    findings: List[str] = []
    passed = True

    if docker_details["dockerfiles_found"]:
        if not docker_details["is_multistage"]:
            findings.append("Dockerfile is single-stage (bloats image size and exposes build tools in production).")
            if strict:
                passed = False
        if not docker_details["runs_as_non_root"]:
            findings.append("Dockerfile lacks non-root USER instruction (runs container as root UID 0).")
            if strict:
                passed = False
        if not docker_details["uses_frozen_lockfile"]:
            findings.append("Dockerfile does not use --frozen-lockfile during dependency installation.")

    if ci_details["has_ci_workflows"]:
        if not ci_details["checks"]["frozen_install"]:
            findings.append("CI workflow does not enforce frozen lockfile installation.")
        if not ci_details["checks"]["trivy_scan"]:
            findings.append("CI workflow lacks container vulnerability scanning (Trivy / Snyk).")
        if ci_details["checks"]["prohibited_latest_used"]:
            findings.append("Mutable 'latest' tag referenced in CI/CD configuration (prohibited in production).")

    report = {
        "target": str(root_path),
        "status": "PASS" if passed and not findings else ("WARNING" if passed else "FAIL"),
        "docker": docker_details,
        "ci_pipeline": ci_details,
        "findings": findings,
    }
    return report


def main() -> None:
    args = parse_arguments()
    report = run_audit(args.target, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stderr.write(f"CI/CD & Build Infrastructure Audit: {report['target']}\n")
        sys.stderr.write(f"Status: {report['status']}\n")
        sys.stderr.write(f"Multi-Stage Docker:  {report['docker']['is_multistage']}\n")
        sys.stderr.write(f"Non-Root Container:  {report['docker']['runs_as_non_root']}\n")
        sys.stderr.write(f"CI Workflows Found:  {report['ci_pipeline']['has_ci_workflows']}\n")
        sys.stderr.write(f"Trivy Scan in CI:    {report['ci_pipeline']['checks']['trivy_scan']}\n")
        if report["findings"]:
            sys.stderr.write("\nFindings / Recommendations:\n")
            for finding in report["findings"]:
                sys.stderr.write(f"  - {finding}\n")

    if report["status"] == "FAIL" and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
