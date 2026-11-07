#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

"""
Rule Validator for Antigravity Rules (`validate_rule.py`)
Enforces Antigravity rule byte limits, frontmatter syntax, valid triggers, and toolkit authoring conventions.
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any, Tuple

VALID_TRIGGERS = {"model_decision", "glob", "always_on", "manual"}
MAX_RECOMMENDED_CHARS = 8000
HARD_RULE_BYTES = 24000  # Official Antigravity rule file limit; UTF-8, after expanding includes.

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
        errors.append("PyYAML is required for reliable rule frontmatter validation (pip install PyYAML).")
    except Exception as e:
        errors.append(f"Failed to parse YAML frontmatter: {str(e)}")

    return fm, body, errors

def validate_rule_file(file_path: str) -> Dict[str, Any]:
    """Validate a single rule markdown file."""
    issues: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {
        "char_count": 0,
        "byte_count": 0,
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
    byte_count = len(content.encode("utf-8"))
    line_count = len(content.splitlines())
    stats["char_count"] = char_count
    stats["byte_count"] = byte_count
    stats["line_count"] = line_count

    # Antigravity limits each rule to 24,000 UTF-8 bytes after expanding includes.
    # The validator can check the source file, not the expanded include payload.
    if byte_count > HARD_RULE_BYTES:
        issues.append(
            f"Rule exceeds Antigravity's 24,000-byte file limit ({byte_count} UTF-8 bytes)."
        )
    if char_count > MAX_RECOMMENDED_CHARS:
        warnings.append(
            f"Rule exceeds the toolkit's recommended 8,000-character budget ({char_count} chars)."
        )
    if re.search(r"@\[[^\]]+\]\([^)]+\)", content):
        warnings.append(
            "Rule uses inline @[...] includes: expanded content size is not checked by this validator."
        )

    # Frontmatter validation
    fm, body, fm_errors = parse_frontmatter(content)
    issues.extend(fm_errors)

    if fm:
        trigger = fm.get("trigger")
        stats["trigger"] = trigger
        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            if trigger == "model_decision":
                issues.append("Field 'description' is required for model_decision rules.")
            else:
                warnings.append("A description is recommended for Antigravity rules.")
        else:
            desc_str = desc.strip()
            if len(desc_str) > 1024:
                issues.append(f"Field 'description' exceeds toolkit limit of 1024 characters ({len(desc_str)} chars).")
            if len(desc_str) < 10:
                warnings.append("Field 'description' is very short. Describe the scope and when it applies.")
        if not trigger:
            issues.append("Frontmatter missing required field: 'trigger'.")
        elif trigger not in VALID_TRIGGERS:
            issues.append(f"Invalid trigger: '{trigger}'. Must be one of: {sorted(list(VALID_TRIGGERS))}.")

        if trigger == "glob":
            globs = fm.get("globs", fm.get("glob"))  # Antigravity supports both keys.
            stats["has_globs"] = bool(globs)
            if not isinstance(globs, str) or not all(piece.strip() for piece in globs.split(",")):
                issues.append(
                    "A glob rule needs 'globs' (or 'glob') as a non-empty, comma-separated string, "
                    'e.g. globs: "**/*.ts, **/*.tsx". YAML arrays are not the documented format.'
                )

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
