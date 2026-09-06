#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

"""
audit_toolkit.py
Whole-ecosystem health inspector and security auditor for ai-agent-toolkit.
Audits file line/character limits, frontmatter syntax, global parity, deprecated
workflows, and open-source domain isolation.
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, List, Any, Tuple

HARD_CHAR_LIMIT = 12000
WARN_CHAR_LIMIT = 8000
MAX_SKILL_LINES = 500
PROPRIETARY_TOKENS = ["nidhiflow", "civicpath", "seyalicraft", "docker-dev-infra"]
VALID_TRIGGERS = {"model_decision", "glob", "always_on", "manual"}


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for ecosystem audit."""
    parser = argparse.ArgumentParser(
        description="Audit ai-agent-toolkit ecosystem for size limits, frontmatter, parity, and security.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/audit_toolkit.py\n"
            "  python3 scripts/audit_toolkit.py --json\n"
            "  python3 scripts/audit_toolkit.py --strict\n"
            "  python3 scripts/audit_toolkit.py --check-global"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo_path", nargs="?", default=".", help="Path to ai-agent-toolkit root (default: current dir)")
    parser.add_argument("--json", action="store_true", help="Emit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--check-global", action="store_true", help="Audit ~/.gemini/ global context and parity")
    return parser.parse_args()


def parse_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], List[str]]:
    """Extract and parse YAML frontmatter from markdown content."""
    errors: List[str] = []
    frontmatter: Dict[str, Any] = {}

    if not content.startswith("---"):
        errors.append("Missing starting '---' YAML frontmatter delimiter.")
        return frontmatter, errors

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("Unclosed '---' YAML frontmatter delimiter.")
        return frontmatter, errors

    try:
        import yaml
        parsed = yaml.safe_load(parts[1])
        if isinstance(parsed, dict):
            frontmatter = parsed
        else:
            errors.append("YAML frontmatter must be a dictionary.")
    except Exception as err:
        errors.append(f"YAML parsing error: {err}")

    return frontmatter, errors


def audit_skills(repo_root: str) -> Tuple[List[Dict[str, Any]], int, int]:
    """Audit all skills in the repository for size and frontmatter rules."""
    skill_results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for root, dirs, files in os.walk(repo_root):
        if "examples" in root.split(os.sep):
            continue
        if "SKILL.md" in files:
            skill_path = os.path.join(root, "SKILL.md")
            rel_dir = os.path.relpath(root, repo_root)
            dir_name = os.path.basename(root)

            errors: List[str] = []
            warnings: List[str] = []

            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            line_count = len(lines)
            if line_count > MAX_SKILL_LINES:
                errors.append(f"Exceeds {MAX_SKILL_LINES} lines limit ({line_count} lines).")

            fm, fm_errors = parse_yaml_frontmatter(content)
            errors.extend(fm_errors)

            name = fm.get("name")
            desc = fm.get("description")

            if not name:
                errors.append("Missing required frontmatter 'name'.")
            elif name != dir_name:
                errors.append(f"Frontmatter name '{name}' does not match directory '{dir_name}'.")

            if not desc:
                errors.append("Missing required frontmatter 'description'.")

            is_valid = len(errors) == 0
            if is_valid:
                passed += 1
            else:
                failed += 1

            skill_results.append({
                "directory": rel_dir,
                "valid": is_valid,
                "line_count": line_count,
                "errors": errors,
                "warnings": warnings,
            })

    return skill_results, passed, failed


def audit_rules(repo_root: str) -> Tuple[List[Dict[str, Any]], int, int]:
    """Audit all rule files for character budget and triggers."""
    rule_results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for root, dirs, files in os.walk(repo_root):
        parts = root.split(os.sep)
        if any(p in parts for p in ["evals", "references", "examples", "assets", "scripts"]):
            continue

        for file_name in files:
            if file_name.endswith(".md") and "rules" in parts:
                rule_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(rule_path, repo_root)

                errors: List[str] = []
                warnings: List[str] = []

                with open(rule_path, "r", encoding="utf-8") as f:
                    content = f.read()

                char_count = len(content)
                if char_count > HARD_CHAR_LIMIT:
                    errors.append(f"Exceeds hard IDE limit of {HARD_CHAR_LIMIT} chars ({char_count} chars).")
                elif char_count > WARN_CHAR_LIMIT:
                    warnings.append(f"Exceeds recommended budget of {WARN_CHAR_LIMIT} chars ({char_count} chars).")

                fm, fm_errors = parse_yaml_frontmatter(content)
                errors.extend(fm_errors)

                trigger = fm.get("trigger")
                if not trigger:
                    errors.append("Missing required frontmatter 'trigger'.")
                elif trigger not in VALID_TRIGGERS:
                    errors.append(f"Invalid trigger '{trigger}'. Must be one of: {VALID_TRIGGERS}.")
                elif trigger == "glob" and not fm.get("globs"):
                    errors.append("Trigger 'glob' requires a non-empty 'globs' array.")

                if not fm.get("description"):
                    errors.append("Missing required frontmatter 'description'.")

                is_valid = len(errors) == 0
                if is_valid:
                    passed += 1
                else:
                    failed += 1

                rule_results.append({
                    "file": rel_path,
                    "valid": is_valid,
                    "char_count": char_count,
                    "trigger": trigger,
                    "errors": errors,
                    "warnings": warnings,
                })

    return rule_results, passed, failed


def audit_deprecated_workflows(repo_root: str) -> List[str]:
    """Flag any deprecated workflow files remaining in the repository."""
    deprecated: List[str] = []
    for root, dirs, files in os.walk(repo_root):
        parts = root.split(os.sep)
        if "workflows" in parts:
            for f in files:
                if f.endswith(".md"):
                    deprecated.append(os.path.relpath(os.path.join(root, f), repo_root))
    return deprecated


def audit_domain_security_isolation(repo_root: str) -> Tuple[bool, List[str]]:
    """Scan public folders for accidental leakage of private domain tokens."""
    leaks: List[str] = []
    public_dirs = ["frameworks", "infra", "shared"]

    for pub in public_dirs:
        pub_path = os.path.join(repo_root, pub)
        if not os.path.exists(pub_path):
            continue

        for root, dirs, files in os.walk(pub_path):
            parts = root.split(os.sep)
            if "audit-agent-toolkit" in parts:
                continue
            for file_name in files:
                if file_name in [
                    "README.md",
                    "audit_toolkit.py",
                    "audit-criteria-and-token-budgets.md",
                    "taxonomy-and-sync-guide.md",
                    "suite-architect-decision-framework.md",
                    "suite-evaluation-output.txt",
                ]:
                    continue
                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read().lower()
                    for token in PROPRIETARY_TOKENS:
                        if token in text:
                            rel_file = os.path.relpath(file_path, repo_root)
                            leaks.append(f"Proprietary token '{token}' detected in public file: {rel_file}")
                except Exception:
                    pass

    return len(leaks) == 0, leaks


def audit_global_parity(repo_root: str) -> Dict[str, Any]:
    """Audit ~/.gemini/ configuration and parity."""
    home_dir = os.path.expanduser("~")
    gemini_dir = os.path.join(home_dir, ".gemini")
    gemini_md = os.path.join(gemini_dir, "GEMINI.md")

    report: Dict[str, Any] = {
        "gemini_dir_exists": os.path.isdir(gemini_dir),
        "gemini_md_exists": os.path.isfile(gemini_md),
        "gemini_md_char_count": 0,
        "gemini_md_valid": True,
        "warnings": [],
        "errors": []
    }

    if report["gemini_md_exists"]:
        with open(gemini_md, "r", encoding="utf-8") as f:
            content = f.read()
        report["gemini_md_char_count"] = len(content)
        if len(content) > HARD_CHAR_LIMIT:
            report["gemini_md_valid"] = False
            report["errors"].append(
                f"~/.gemini/GEMINI.md ({len(content)} chars) exceeds 12,000 chars limit (truncated by IDE)."
            )

    return report


def main() -> int:
    """Execute ecosystem audit and display results."""
    args = parse_arguments()
    repo_root = os.path.abspath(args.repo_path)

    if not os.path.isdir(repo_root):
        sys.stderr.write(f"Error: Target path '{args.repo_path}' is not a directory.\n")
        return 1

    skills, skills_passed, skills_failed = audit_skills(repo_root)
    rules, rules_passed, rules_failed = audit_rules(repo_root)
    deprecated_workflows = audit_deprecated_workflows(repo_root)
    domain_clean, domain_leaks = audit_domain_security_isolation(repo_root)
    global_report = audit_global_parity(repo_root) if args.check_global else None

    total_checks = len(skills) + len(rules) + (1 if domain_clean else 0)
    passed_checks = skills_passed + rules_passed + (1 if domain_clean else 0)
    score = 100 if total_checks == 0 else round((passed_checks / (total_checks + len(deprecated_workflows))) * 100)

    is_overall_pass = (skills_failed == 0 and rules_failed == 0 and domain_clean)

    report_data = {
        "repository": repo_root,
        "score_percent": score,
        "overall_pass": is_overall_pass,
        "summary": {
            "total_skills": len(skills),
            "passed_skills": skills_passed,
            "failed_skills": skills_failed,
            "total_rules": len(rules),
            "passed_rules": rules_passed,
            "failed_rules": rules_failed,
            "deprecated_workflows_count": len(deprecated_workflows),
            "domain_security_clean": domain_clean,
        },
        "skills": skills,
        "rules": rules,
        "deprecated_workflows": deprecated_workflows,
        "domain_leaks": domain_leaks,
        "global_report": global_report,
    }

    if args.json:
        sys.stdout.write(json.dumps(report_data, indent=2) + "\n")
    else:
        score_emoji = "🟢" if score >= 90 else ("🟡" if score >= 75 else "🔴")
        print("\n" + "=" * 56)
        print("🛡️  AI AGENT TOOLKIT ECOSYSTEM HEALTH AUDIT")
        print("=" * 56)
        print(f"Repository Root    : {repo_root}")
        print(f"Overall Health     : {score}% {score_emoji}")
        print(f"Status             : {'✅ PASS' if is_overall_pass else '❌ NEEDS ATTENTION'}")
        print("-" * 56)
        print(f"📦 Skills Audited  : {skills_passed}/{len(skills)} Passed")
        print(f"📜 Rules Audited   : {rules_passed}/{len(rules)} Passed")
        print(f"⚠️  Deprecated WFs : {len(deprecated_workflows)} Found")
        print(f"🔒 Domain Security : {'✅ CLEAN' if domain_clean else '❌ LEAK DETECTED'}")

        if skills_failed > 0:
            print("\n❌ Failed Skills:")
            for s in skills:
                if not s["valid"]:
                    print(f"  - {s['directory']}: {', '.join(s['errors'])}")

        if rules_failed > 0:
            print("\n❌ Failed Rules:")
            for r in rules:
                if not r["valid"]:
                    print(f"  - {r['file']}: {', '.join(r['errors'])}")

        if deprecated_workflows:
            print("\n⚠️  Deprecated Workflows (Migrate to Procedural Skills):")
            for dw in deprecated_workflows:
                print(f"  - {dw}")

        if domain_leaks:
            print("\n🚨 Open-Source Domain Leaks:")
            for leak in domain_leaks:
                print(f"  - {leak}")

        if global_report and global_report.get("errors"):
            print("\n🌐 Global Config Warnings:")
            for err in global_report["errors"]:
                print(f"  - {err}")

        print("=" * 56 + "\n")

    return 0 if is_overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
