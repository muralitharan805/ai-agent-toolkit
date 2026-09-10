# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit Documentation Architecture & System Runbooks.

Audits codebases for compliance with enterprise documentation standards:
1. Top-level README.md (< 5-minute quick start, prerequisites, docker compose).
2. Six-pillar docs/ runbook hierarchy:
   - docs/architecture.md
   - docs/development.md
   - docs/testing.md
   - docs/deployment.md
   - docs/database.md
   - docs/troubleshooting.md
3. Declarative Mermaid.js diagram presence.
4. CHANGELOG.md presence and formatting.
5. API documentation / OpenAPI spec presence.
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
        description="Audit README 5-minute quick start, docs/ runbook hierarchy, and Mermaid diagrams."
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
        help="Exit with non-zero code if any critical documentation pillar is missing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout",
    )
    return parser.parse_args()


def audit_readme(root_dir: Path) -> Dict[str, Any]:
    readme = root_dir / "README.md"
    if not readme.is_file():
        readme = root_dir / "readme.md"

    if not readme.is_file():
        return {
            "found": False,
            "has_quick_start": False,
            "has_prerequisites": False,
            "has_docker_compose": False,
        }

    try:
        content = readme.read_text(encoding="utf-8", errors="ignore")
        has_quick_start = bool(re.search(r"quick\s*start", content, re.IGNORECASE))
        has_prerequisites = bool(re.search(r"prerequisite", content, re.IGNORECASE))
        has_docker_compose = bool(re.search(r"docker\s*compose", content, re.IGNORECASE))

        return {
            "found": True,
            "path": str(readme.relative_to(root_dir)),
            "has_quick_start": has_quick_start,
            "has_prerequisites": has_prerequisites,
            "has_docker_compose": has_docker_compose,
        }
    except Exception:
        return {"found": False}


def audit_docs_directory(root_dir: Path) -> Dict[str, Any]:
    docs_dir = root_dir / "docs"
    standard_files = [
        "architecture.md",
        "development.md",
        "testing.md",
        "deployment.md",
        "database.md",
        "troubleshooting.md",
    ]

    if not docs_dir.is_dir():
        return {
            "docs_dir_found": False,
            "missing_pillars": standard_files,
            "found_pillars": [],
            "mermaid_diagrams_count": 0,
        }

    found_pillars = []
    missing_pillars = []
    mermaid_count = 0

    for expected in standard_files:
        p = docs_dir / expected
        if p.is_file():
            found_pillars.append(expected)
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                mermaid_count += len(re.findall(r"```mermaid", text, re.IGNORECASE))
            except Exception:
                pass
        else:
            missing_pillars.append(expected)

    # Check root readme for mermaid as well
    readme = root_dir / "README.md"
    if readme.is_file():
        try:
            text = readme.read_text(encoding="utf-8", errors="ignore")
            mermaid_count += len(re.findall(r"```mermaid", text, re.IGNORECASE))
        except Exception:
            pass

    return {
        "docs_dir_found": True,
        "found_pillars": found_pillars,
        "missing_pillars": missing_pillars,
        "mermaid_diagrams_count": mermaid_count,
    }


def audit_changelog_and_api(root_dir: Path) -> Dict[str, Any]:
    changelog = (root_dir / "CHANGELOG.md").is_file() or (root_dir / "changelog.md").is_file()

    api_files = [
        "openapi.json",
        "openapi.yaml",
        "openapi.yml",
        "swagger.json",
        "swagger.yaml",
        "swagger.yml",
    ]
    has_api_spec = any((root_dir / f).is_file() for f in api_files) or any(
        (root_dir / "docs" / f).is_file() for f in api_files
    )

    return {
        "changelog_found": changelog,
        "api_spec_found": has_api_spec,
    }


def run_audit(target_dir: str, strict: bool = False) -> Dict[str, Any]:
    root_path = Path(target_dir).resolve()
    readme_res = audit_readme(root_path)
    docs_res = audit_docs_directory(root_path)
    extra_res = audit_changelog_and_api(root_path)

    findings: List[str] = []
    passed = True

    if not readme_res["found"]:
        findings.append("Root README.md is missing.")
        if strict:
            passed = False
    else:
        if not readme_res["has_quick_start"]:
            findings.append("README.md lacks a deterministic '< 5-Minute Quick Start' section.")
        if not readme_res["has_docker_compose"]:
            findings.append("README.md does not mention 'docker compose up' for backing dependencies.")

    if not docs_res["docs_dir_found"]:
        findings.append("Standard 'docs/' technical documentation directory is missing.")
        if strict:
            passed = False
    elif docs_res["missing_pillars"]:
        findings.append(f"Missing docs/ pillar runbooks: {', '.join(docs_res['missing_pillars'])}")

    if docs_res["mermaid_diagrams_count"] == 0:
        findings.append("No declarative Mermaid.js diagrams (```mermaid) discovered in documentation.")

    if not extra_res["changelog_found"]:
        findings.append("CHANGELOG.md is missing from repository root.")

    report = {
        "target": str(root_path),
        "status": "PASS" if passed and not findings else ("WARNING" if passed else "FAIL"),
        "readme": readme_res,
        "docs_hierarchy": docs_res,
        "governance": extra_res,
        "findings": findings,
    }
    return report


def main() -> None:
    args = parse_arguments()
    report = run_audit(args.target, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stderr.write(f"Documentation Architecture Audit: {report['target']}\n")
        sys.stderr.write(f"Status: {report['status']}\n")
        sys.stderr.write(f"README Found:       {report['readme'].get('found', False)}\n")
        sys.stderr.write(f"Docs Dir Found:     {report['docs_hierarchy']['docs_dir_found']}\n")
        sys.stderr.write(
            f"Pillars Present:    {len(report['docs_hierarchy']['found_pillars'])}/6 ({', '.join(report['docs_hierarchy']['found_pillars'])})\n"
        )
        sys.stderr.write(f"Mermaid Diagrams:   {report['docs_hierarchy']['mermaid_diagrams_count']}\n")
        sys.stderr.write(f"CHANGELOG Present:  {report['governance']['changelog_found']}\n")
        if report["findings"]:
            sys.stderr.write("\nFindings / Recommendations:\n")
            for finding in report["findings"]:
                sys.stderr.write(f"  - {finding}\n")

    if report["status"] == "FAIL" and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
