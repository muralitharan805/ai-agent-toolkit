#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# requires-python = ">=3.9"
# ///

"""
validate_skill.py
Universal validator utility for Agent Skills (agentskills.io open standard).
Emits structured JSON report to stdout and diagnostic progress to stderr.
"""

import os
import sys
import re
import json
import argparse
import yaml

NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory against the official Agent Skills specification.",
        epilog="Examples:\n  python3 scripts/validate_skill.py path/to/my-skill\n  python3 scripts/validate_skill.py --json path/to/my-skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("skill_dir", help="Path to the skill directory containing SKILL.md")
    parser.add_argument("--json", action="store_true", help="Format stdout as machine-readable JSON (default)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    return parser.parse_args()

def validate_skill(skill_dir: str):
    issues = []
    warnings = []
    stats = {}

    skill_path = os.path.abspath(skill_dir)
    dir_name = os.path.basename(skill_path.rstrip("/"))

    if not os.path.isdir(skill_path):
        return {
            "valid": False,
            "skill_dir": skill_dir,
            "errors": [f"Target path '{skill_dir}' is not a valid directory."],
            "warnings": [],
            "stats": {}
        }

    skill_md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md_path):
        return {
            "valid": False,
            "skill_dir": skill_dir,
            "errors": ["Missing required SKILL.md file at skill root."],
            "warnings": [],
            "stats": {}
        }

    with open(skill_md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    line_count = len(lines)
    char_count = sum(len(line) for line in lines)
    stats["line_count"] = line_count
    stats["char_count"] = char_count

    if line_count > 500:
        warnings.append(f"SKILL.md exceeds recommended 500 lines limit ({line_count} lines). Consider moving subdocs to references/.")

    content = "".join(lines)
    if not content.startswith("---"):
        issues.append("SKILL.md must start with YAML frontmatter bounded by '---'.")
        fm = {}
    else:
        parts = content.split("---", 2)
        if len(parts) < 3:
            issues.append("SKILL.md frontmatter is unclosed (missing closing '---').")
            fm = {}
        else:
            try:
                fm = yaml.safe_load(parts[1])
                if not isinstance(fm, dict):
                    issues.append("YAML frontmatter must be a key-value mapping.")
                    fm = {}
            except Exception as e:
                issues.append(f"Invalid YAML frontmatter: {str(e)}")
                fm = {}

    # Validate name
    name = fm.get("name")
    if not name:
        issues.append("Missing required frontmatter field: 'name'.")
    else:
        name_str = str(name)
        if len(name_str) > 64:
            issues.append(f"Field 'name' exceeds 64 characters ({len(name_str)} chars).")
        if not NAME_REGEX.match(name_str):
            issues.append(f"Field 'name' ('{name_str}') must be lowercase alphanumeric with single hyphens.")
        if name_str != dir_name:
            issues.append(f"Field 'name' ('{name_str}') must match parent directory name ('{dir_name}').")

    # Validate description
    desc = fm.get("description")
    if not desc:
        issues.append("Missing required frontmatter field: 'description'.")
    else:
        desc_str = str(desc).strip()
        if len(desc_str) > 1024:
            issues.append(f"Field 'description' exceeds 1024 characters ({len(desc_str)} chars).")
        if len(desc_str) < 15:
            warnings.append("Field 'description' is very short. Ensure it includes what the skill does and when to use it.")

    # Validate relative markdown links
    link_pattern = re.compile(r"\[.*?\]\((?!https?:\/\/)(.*?)\)")
    for match in link_pattern.finditer(content):
        rel_target = match.group(1).split("#")[0].strip()
        if rel_target and not rel_target.startswith("mailto:"):
            target_full_path = os.path.join(skill_path, rel_target)
            if not os.path.exists(target_full_path):
                warnings.append(f"Referenced file does not exist: '{rel_target}'")

    # Root directory pollution check
    allowed_root_files = {"SKILL.md", "LICENSE", "README.md"}
    for entry in os.listdir(skill_path):
        entry_path = os.path.join(skill_path, entry)
        if os.path.isfile(entry_path) and entry not in allowed_root_files:
            warnings.append(f"Unexpected file in skill root: '{entry}'. Move documentation to references/, code to scripts/, or data to assets/.")

    # Check directory structure conventions
    for sub in ["references", "scripts", "examples", "assets", "evals"]:
        sub_p = os.path.join(skill_path, sub)
        stats[f"has_{sub}"] = os.path.isdir(sub_p)

    # Deep validation of evals/evals.json
    evals_dir = os.path.join(skill_path, "evals")
    if os.path.isdir(evals_dir):
        evals_json = os.path.join(evals_dir, "evals.json")
        if not os.path.isfile(evals_json):
            warnings.append("Directory 'evals/' exists but is missing 'evals.json'.")
        else:
            try:
                with open(evals_json, "r", encoding="utf-8") as ef:
                    eval_data = json.load(ef)
                if not isinstance(eval_data, dict):
                    issues.append("'evals/evals.json' must be a JSON object.")
                elif "evals" not in eval_data or not isinstance(eval_data["evals"], list):
                    issues.append("'evals/evals.json' must contain an 'evals' list.")
                else:
                    stats["eval_test_cases"] = len(eval_data["evals"])
                    for idx, item in enumerate(eval_data["evals"]):
                        if not isinstance(item, dict) or "prompt" not in item or "assertions" not in item:
                            issues.append(f"Eval item #{idx + 1} in 'evals.json' missing 'prompt' or 'assertions'.")
                        elif not isinstance(item["assertions"], list) or len(item["assertions"]) == 0:
                            issues.append(f"Eval item #{idx + 1} in 'evals.json' must have non-empty assertions list.")
            except Exception as e:
                issues.append(f"Failed to parse 'evals/evals.json': {str(e)}")

    # PEP 723 Python script validation in scripts/
    scripts_dir = os.path.join(skill_path, "scripts")
    if os.path.isdir(scripts_dir):
        for script_file in os.listdir(scripts_dir):
            if script_file.endswith(".py"):
                script_full = os.path.join(scripts_dir, script_file)
                try:
                    with open(script_full, "r", encoding="utf-8", errors="ignore") as sf:
                        script_head = sf.read(500)
                    if "# /// script" not in script_head:
                        warnings.append(f"Python script '{script_file}' in scripts/ does not declare PEP 723 metadata block (# /// script).")
                except Exception:
                    pass

    return {
        "valid": len(issues) == 0,
        "skill_dir": skill_dir,
        "errors": issues,
        "warnings": warnings,
        "stats": stats
    }

def main():
    args = parse_args()
    report = validate_skill(args.skill_dir)

    # Diagnostic output on stderr
    if report["valid"]:
        sys.stderr.write(f"✅ Skill '{args.skill_dir}' passed validation.\n")
    else:
        sys.stderr.write(f"❌ Skill '{args.skill_dir}' failed validation ({len(report['errors'])} errors).\n")

    for w in report["warnings"]:
        sys.stderr.write(f"  ⚠️ Warning: {w}\n")

    # Structured data on stdout
    print(json.dumps(report, indent=2))

    if not report["valid"] or (args.strict and report["warnings"]):
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
