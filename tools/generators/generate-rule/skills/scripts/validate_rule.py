#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

"""
Rule Validator for Antigravity Rules (`validate_rule.py`)
Enforces character limits, frontmatter syntax, valid triggers, and canonical markdown structure.
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any, Tuple

VALID_TRIGGERS = {"model_decision", "glob", "always_on", "manual"}
MAX_RECOMMENDED_CHARS = 8000
HARD_CHAR_LIMIT = 12000

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str, List[str]]:
    """Extract YAML frontmatter and body from markdown content."""
    errors = []
    fm: Dict[str, Any] = {}
    body = content

    if not content.startswith("---"):
        errors.append("Rule file must start with YAML frontmatter ('---').")
        return fm, body, errors

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("Rule file frontmatter is not properly closed with '---'.")
        return fm, body, errors

    raw_yaml = parts[1]
    body = parts[2]

    try:
        import yaml
        parsed = yaml.safe_load(raw_yaml)
        if isinstance(parsed, dict):
            fm = parsed
        else:
            errors.append("Frontmatter YAML must be an object/dictionary.")
    except ImportError:
        # Fallback simple parser if yaml not installed
        for line in raw_yaml.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "globs":
                    fm[k] = []
                elif k:
                    fm[k] = v
    except Exception as e:
        errors.append(f"Failed to parse YAML frontmatter: {str(e)}")

    return fm, body, errors

def validate_rule_file(file_path: str) -> Dict[str, Any]:
    """Validate a single rule markdown file."""
    issues: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {
        "char_count": 0,
        "line_count": 0,
        "trigger": None,
        "has_globs": False,
        "has_constraints": False,
        "has_examples": False,
    }

    if not os.path.isfile(file_path):
        return {
            "valid": False,
            "file": file_path,
            "errors": [f"File does not exist: {file_path}"],
            "warnings": [],
            "stats": stats,
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {
            "valid": False,
            "file": file_path,
            "errors": [f"Failed to read file: {str(e)}"],
            "warnings": [],
            "stats": stats,
        }

    char_count = len(content)
    line_count = len(content.splitlines())
    stats["char_count"] = char_count
    stats["line_count"] = line_count

    # Check length limits
    if char_count > HARD_CHAR_LIMIT:
        issues.append(
            f"File exceeds hard 12,000 character limit ({char_count} chars). Antigravity IDE will truncate this rule!"
        )
    elif char_count > MAX_RECOMMENDED_CHARS:
        warnings.append(
            f"File exceeds recommended 8,000 character target ({char_count} chars). Consider splitting into sub-rules."
        )

    # Frontmatter validation
    fm, body, fm_errors = parse_frontmatter(content)
    issues.extend(fm_errors)

    if fm:
        desc = fm.get("description")
        if not desc:
            issues.append("Frontmatter missing required field: 'description'.")
        else:
            desc_str = str(desc).strip()
            if len(desc_str) > 1024:
                issues.append(f"Field 'description' exceeds 1024 characters ({len(desc_str)} chars).")
            if len(desc_str) < 10:
                warnings.append("Field 'description' is very short. Describe the scope and when it applies.")

        trigger = fm.get("trigger")
        stats["trigger"] = trigger
        if not trigger:
            issues.append("Frontmatter missing required field: 'trigger'.")
        elif trigger not in VALID_TRIGGERS:
            issues.append(f"Invalid trigger: '{trigger}'. Must be one of: {sorted(list(VALID_TRIGGERS))}.")

        if trigger == "glob":
            globs = fm.get("globs")
            stats["has_globs"] = bool(globs)
            if not globs:
                issues.append("When 'trigger: glob' is set, 'globs: [...]' list is mandatory.")
            elif not isinstance(globs, list) or len(globs) == 0:
                issues.append("Field 'globs' must be a non-empty list of glob patterns.")

        if "framework_version" not in fm:
            warnings.append("Missing recommended metadata field: 'framework_version'. Prevents context drift.")
            
        if "last_verified_date" not in fm:
            warnings.append("Missing recommended metadata field: 'last_verified_date'. Helps alert on stale context.")

    # Structure checks in body
    if not re.search(r"^#\s+.+", body, re.MULTILINE):
        warnings.append("Missing primary heading (# Title).")

    if not re.search(r"^##\s+Description", body, re.MULTILINE | re.IGNORECASE):
        warnings.append("Missing '## Description' section.")

    has_constraints = bool(re.search(r"^##\s+Constraints", body, re.MULTILINE | re.IGNORECASE))
    stats["has_constraints"] = has_constraints
    if not has_constraints:
        issues.append("Missing mandatory '## Constraints' section.")

    has_examples = bool(re.search(r"^##\s+Examples", body, re.MULTILINE | re.IGNORECASE))
    stats["has_examples"] = has_examples
    if not has_examples:
        warnings.append("Missing recommended '## Examples' section.")

    # Unbalanced code blocks check
    backtick_fences = len(re.findall(r"^`{3,}", content, re.MULTILINE))
    if backtick_fences % 2 != 0:
        issues.append(f"Unbalanced code block fences detected ({backtick_fences} fences found).")

    return {
        "valid": len(issues) == 0,
        "file": file_path,
        "errors": issues,
        "warnings": warnings,
        "stats": stats,
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Antigravity rule markdown files against size, trigger, and schema standards."
    )
    parser.add_argument("target", help="Path to rule file (.md) or directory containing rule files.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    args = parser.parse_args()

    files_to_check: List[str] = []
    if os.path.isfile(args.target):
        files_to_check.append(args.target)
    elif os.path.isdir(args.target):
        for root, _, files in os.walk(args.target):
            for file in files:
                if file.endswith(".md"):
                    files_to_check.append(os.path.join(root, file))
    else:
        sys.stderr.write(f"Error: Target path '{args.target}' does not exist.\n")
        sys.exit(1)

    if not files_to_check:
        sys.stderr.write(f"No markdown files found to validate in '{args.target}'.\n")
        sys.exit(1)

    results = [validate_rule_file(f) for f in sorted(files_to_check)]
    overall_valid = all(r["valid"] for r in results)

    if args.json:
        print(json.dumps({"valid": overall_valid, "results": results}, indent=2))
    else:
        for r in results:
            rel_file = r["file"]
            if r["valid"]:
                print(f"✅ Rule '{rel_file}' passed validation.")
            else:
                print(f"❌ Rule '{rel_file}' FAILED validation:")
                for err in r["errors"]:
                    print(f"  - Error: {err}")
            for w in r["warnings"]:
                print(f"  ⚠️ Warning: {w}")

        print("\n--- Summary ---")
        passed = sum(1 for r in results if r["valid"])
        print(f"Total: {len(results)} | Passed: {passed} | Failed: {len(results) - passed}")

    sys.exit(0 if overall_valid else 1)

if __name__ == "__main__":
    main()
