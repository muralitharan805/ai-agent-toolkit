#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

"""
Suite Verification Engine (`verify_suite.py`)
Validates an entire generated agent suite (all skills and rules within a topic/module directory)
by coordinating validate_skill.py and validate_rule.py.
"""

import sys
import os
import json
import argparse
import subprocess
from typing import Dict, List, Any

def find_generator_root() -> str:
    """Find the root path of shared/generators."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # From shared/generators/skills/generate-agent-suite/scripts -> shared/generators
    return os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

def verify_suite(target_path: str) -> Dict[str, Any]:
    """Inspect and validate all skills and rules in target path."""
    gen_root = find_generator_root()
    validate_skill_script = os.path.join(gen_root, "skills", "generate-skill", "scripts", "validate_skill.py")
    validate_rule_script = os.path.join(gen_root, "skills", "generate-rule", "scripts", "validate_rule.py")

    results: Dict[str, Any] = {
        "target": target_path,
        "valid": True,
        "skills": [],
        "rules": [],
        "summary": {
            "total_skills": 0,
            "passed_skills": 0,
            "total_rules": 0,
            "passed_rules": 0,
        }
    }

    if not os.path.exists(target_path):
        results["valid"] = False
        results["error"] = f"Target path does not exist: {target_path}"
        return results

    # 1. Discover skills (directories containing SKILL.md, excluding examples)
    skill_dirs: List[str] = []
    if os.path.isfile(os.path.join(target_path, "SKILL.md")):
        skill_dirs.append(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            parts = root.split(os.sep)
            if "examples" in parts:
                continue
            if "SKILL.md" in files:
                skill_dirs.append(root)

    # 2. Discover rules (.md files in rules/ directory or root rules)
    rule_files: List[str] = []
    for root, dirs, files in os.walk(target_path):
        # Exclude skill directories and internal subdirectories
        parts = root.split(os.sep)
        if any(p in parts for p in ["evals", "references", "examples", "assets", "scripts"]):
            continue
        # Also avoid treating SKILL.md or README.md as rules
        for f in files:
            if f.endswith(".md") and f != "SKILL.md" and f != "README.md":
                # Ensure it's in a rules/ folder or has frontmatter trigger
                if "rules" in parts:
                    rule_files.append(os.path.join(root, f))

    # 3. Validate Skills
    for s_dir in sorted(skill_dirs):
        results["summary"]["total_skills"] += 1
        cmd = [sys.executable, validate_skill_script, s_dir]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        is_pass = proc.returncode == 0
        if is_pass:
            results["summary"]["passed_skills"] += 1
        else:
            results["valid"] = False

        results["skills"].append({
            "path": s_dir,
            "valid": is_pass,
            "output": proc.stdout.strip(),
            "errors": proc.stderr.strip(),
        })

    # 4. Validate Rules
    for r_file in sorted(rule_files):
        results["summary"]["total_rules"] += 1
        cmd = [sys.executable, validate_rule_script, r_file]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        is_pass = proc.returncode == 0
        if is_pass:
            results["summary"]["passed_rules"] += 1
        else:
            results["valid"] = False

        results["rules"].append({
            "file": r_file,
            "valid": is_pass,
            "output": proc.stdout.strip(),
            "errors": proc.stderr.strip(),
        })

    return results

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify an entire Agent Suite (validating all skills and rules in target module)."
    )
    parser.add_argument("target", help="Path to suite directory or topic module (e.g. frameworks/angular).")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    args = parser.parse_args()

    results = verify_suite(args.target)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n=======================================================")
        print(f"🔍 Agent Suite Verification: {results['target']}")
        print(f"=======================================================")

        if results["skills"]:
            print("\n📦 SKILLS AUDIT:")
            for s in results["skills"]:
                status = "✅ PASS" if s["valid"] else "❌ FAIL"
                print(f"  [{status}] {s['path']}")
                if not s["valid"]:
                    print(f"      {s['output']}")

        if results["rules"]:
            print("\n📜 RULES AUDIT:")
            for r in results["rules"]:
                status = "✅ PASS" if r["valid"] else "❌ FAIL"
                print(f"  [{status}] {r['file']}")
                if not r["valid"]:
                    print(f"      {r['output']}")

        summary = results["summary"]
        print(f"\n-------------------------------------------------------")
        print(f"📊 SUITE SCORECARD:")
        print(f"   Skills: {summary['passed_skills']}/{summary['total_skills']} Passed")
        print(f"   Rules:  {summary['passed_rules']}/{summary['total_rules']} Passed")
        print(f"   Overall Status: {'✅ SUITE VALIDATED' if results['valid'] else '❌ SUITE HAS ISSUES'}")
        print(f"=======================================================\n")

    sys.exit(0 if results["valid"] else 1)

if __name__ == "__main__":
    main()
