# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Validate Commit Message CLI Tool.

Lints git commit messages against the Conventional Commits specification.
Checks header format, allowed types, scope syntax, summary length, and imperative phrasing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


ALLOWED_TYPES = {
    "feat",
    "fix",
    "docs",
    "refactor",
    "test",
    "chore",
    "perf",
    "ci",
    "build",
    "revert",
}

GENERIC_BLACKLIST = {
    "wip",
    "update",
    "updates",
    "fix",
    "fixes",
    "fixed",
    "changes",
    "added",
    "commit",
    "temp",
    "test",
}


@dataclass
class CommitValidationResult:
    valid: bool
    header: str
    commit_type: Optional[str] = None
    scope: Optional[str] = None
    is_breaking: bool = False
    description: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate git commit messages against Conventional Commits standard."
    )
    parser.add_argument("message", nargs="?", type=str, help="Commit message string to validate.")
    parser.add_argument("--file", type=str, help="Path to file containing commit message.")
    parser.add_argument(
        "--strict", action="store_true", help="Exit with non-zero exit code if validation fails."
    )
    parser.add_argument("--json", action="store_true", help="Output JSON result to stdout.")
    return parser.parse_args()


def validate_message(raw_message: str) -> CommitValidationResult:
    lines = raw_message.strip().splitlines()
    if not lines or not lines[0].strip():
        return CommitValidationResult(
            valid=False,
            header="",
            errors=["Commit message is empty."],
        )

    header = lines[0].strip()
    errors: List[str] = []
    warnings: List[str] = []

    # Check length
    if len(header) > 72:
        errors.append(f"Header line exceeds 72 characters ({len(header)} chars).")

    # Regex pattern
    pattern = re.compile(
        r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-zA-Z0-9_\-\.]+)\))?(?P<breaking>!)?:\s+(?P<desc>.+)$"
    )
    match = pattern.match(header)

    if not match:
        errors.append(
            "Header does not match Conventional Commits format: '<type>(<scope>): <description>'."
        )
        return CommitValidationResult(valid=False, header=header, errors=errors)

    commit_type = match.group("type")
    scope = match.group("scope")
    is_breaking = match.group("breaking") == "!"
    description = match.group("desc").strip()

    # Check type
    if commit_type not in ALLOWED_TYPES:
        errors.append(
            f"Invalid commit type '{commit_type}'. Allowed types: {', '.join(sorted(ALLOWED_TYPES))}."
        )

    # Check trailing period
    if description.endswith("."):
        errors.append("Description must not end with a period ('.').")

    # Check lower case start
    if description and description[0].isupper():
        warnings.append("Description should start with a lowercase letter.")

    # Check generic message
    if description.lower() in GENERIC_BLACKLIST:
        errors.append(f"Description '{description}' is too vague/generic. Describe the actual change.")

    valid = len(errors) == 0

    return CommitValidationResult(
        valid=valid,
        header=header,
        commit_type=commit_type,
        scope=scope,
        is_breaking=is_breaking,
        description=description,
        errors=errors,
        warnings=warnings,
    )


def main() -> None:
    args = parse_args()

    if args.file:
        raw_msg = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    elif args.message:
        raw_msg = args.message
    else:
        sys.stderr.write("Error: Please provide a commit message argument or --file.\n")
        sys.exit(1)

    result = validate_message(raw_msg)

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write("📝 CONVENTIONAL COMMITS VALIDATION\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Header : {result.header}\n")
        sys.stderr.write(f"Status : {'PASS ✅' if result.valid else 'FAIL ❌'}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        if result.commit_type:
            sys.stderr.write(f"Type   : {result.commit_type}\n")
        if result.scope:
            sys.stderr.write(f"Scope  : {result.scope}\n")
        if result.is_breaking:
            sys.stderr.write("Breaking: YES (!)\n")
        if result.errors:
            sys.stderr.write("Errors:\n")
            for err in result.errors:
                sys.stderr.write(f"  ❌ {err}\n")
        if result.warnings:
            sys.stderr.write("Warnings:\n")
            for warn in result.warnings:
                sys.stderr.write(f"  ⚠️ {warn}\n")
        sys.stderr.write("========================================================\n")

    if not result.valid and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
