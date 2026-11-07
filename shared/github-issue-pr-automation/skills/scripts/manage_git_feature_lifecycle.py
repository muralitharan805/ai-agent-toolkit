# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Manage Git Feature Lifecycle CLI Tool.

Enforces normalized feature branch naming, checks for mandatory PR issue auto-closing syntax,
and validates local git working tree hygiene.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


BRANCH_PATTERN = re.compile(
    r"^(?P<type>feat|fix|docs|refactor|chore|test|perf)/(?P<issue_id>\d+)-(?P<slug>[a-z0-9\-]+)$"
)

AUTO_CLOSE_PATTERN = re.compile(
    r"(?i)\b(?:closes|closed|fixes|fixed|resolves|resolved)\s+#(?P<issue_id>\d+)\b"
)


@dataclass
class LifecycleValidationReport:
    valid: bool
    branch_name: Optional[str] = None
    branch_valid: Optional[bool] = None
    extracted_issue_id: Optional[str] = None
    pr_body_valid: Optional[bool] = None
    auto_closed_issues: List[str] = field(default_factory=list)
    git_clean: Optional[bool] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify feature branch naming, PR issue auto-close syntax, and git hygiene."
    )
    parser.add_argument("--branch", type=str, help="Feature branch name to validate.")
    parser.add_argument("--pr-body", type=str, help="Pull request body text or path to markdown file.")
    parser.add_argument(
        "--check-git",
        action="store_true",
        help="Inspect current local git repository status and branch name.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero exit code if validation checks fail.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON result to stdout.")
    return parser.parse_args()


def get_current_git_branch() -> Optional[str]:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return None


def is_git_status_clean() -> bool:
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return len(res.stdout.strip()) == 0
    except Exception:
        return False


def main() -> None:
    args = parse_args()
    errors: List[str] = []
    warnings: List[str] = []

    target_branch = args.branch
    git_clean: Optional[bool] = None

    if args.check_git or not target_branch:
        current_branch = get_current_git_branch()
        if current_branch and not target_branch:
            target_branch = current_branch
        git_clean = is_git_status_clean()
        if not git_clean:
            warnings.append("Local git working tree contains uncommitted changes.")

    branch_valid: Optional[bool] = None
    extracted_issue_id: Optional[str] = None

    if target_branch:
        if target_branch in ("main", "master", "develop"):
            errors.append(
                f"Direct work on '{target_branch}' branch is forbidden. Checkout a feature branch ('feat/<id>-<slug>')."
            )
            branch_valid = False
        else:
            match = BRANCH_PATTERN.match(target_branch)
            if match:
                branch_valid = True
                extracted_issue_id = match.group("issue_id")
            else:
                branch_valid = False
                errors.append(
                    f"Branch '{target_branch}' does not match normalized pattern: '<type>/<issue-id>-<slug>' (e.g. 'feat/14-emi-schedule')."
                )

    pr_body_valid: Optional[bool] = None
    auto_closed: List[str] = []

    if args.pr_body:
        pr_text = args.pr_body
        pr_file = Path(args.pr_body)
        if pr_file.exists():
            pr_text = pr_file.read_text(encoding="utf-8", errors="ignore")

        matches = AUTO_CLOSE_PATTERN.findall(pr_text)
        auto_closed = matches
        if matches:
            pr_body_valid = True
            if extracted_issue_id and extracted_issue_id not in matches:
                warnings.append(
                    f"PR body closes issues {matches}, but feature branch issue ID is '{extracted_issue_id}'."
                )
        else:
            pr_body_valid = False
            errors.append(
                "PR body missing mandatory auto-closing keyword (e.g. 'Closes #<issue-id>' or 'Fixes #<issue-id>')."
            )

    valid = len(errors) == 0

    report = LifecycleValidationReport(
        valid=valid,
        branch_name=target_branch,
        branch_valid=branch_valid,
        extracted_issue_id=extracted_issue_id,
        pr_body_valid=pr_body_valid,
        auto_closed_issues=auto_closed,
        git_clean=git_clean,
        errors=errors,
        warnings=warnings,
    )

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write("🌿 GIT FEATURE LIFECYCLE AUDIT\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Branch       : {report.branch_name}\n")
        sys.stderr.write(f"Branch Valid : {report.branch_valid}\n")
        if report.extracted_issue_id:
            sys.stderr.write(f"Issue ID     : #{report.extracted_issue_id}\n")
        if report.pr_body_valid is not None:
            sys.stderr.write(f"PR Auto-Close: {'VALID ✅' if report.pr_body_valid else 'MISSING ❌'}\n")
            if report.auto_closed_issues:
                sys.stderr.write(f"Closes Issues: {', '.join(['#' + i for i in report.auto_closed_issues])}\n")
        sys.stderr.write(f"Overall Status: {'PASS ✅' if report.valid else 'FAIL ❌'}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        if report.errors:
            sys.stderr.write("Errors:\n")
            for err in report.errors:
                sys.stderr.write(f"  ❌ {err}\n")
        if report.warnings:
            sys.stderr.write("Warnings:\n")
            for warn in report.warnings:
                sys.stderr.write(f"  ⚠️ {warn}\n")
        sys.stderr.write("========================================================\n")

    if not valid and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
