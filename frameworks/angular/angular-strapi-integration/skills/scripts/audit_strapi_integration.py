#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
audit_strapi_integration.py
Audits Angular applications consuming Strapi CMS APIs for:
- Type-safe Strapi client service with TransferState
- Standalone StrapiMediaPipe for dynamic URL resolution
- Zero hardcoded localhost URLs in source files
- Zero hardcoded content in component templates
- Proactive schema prompt template availability
- Zero explicit 'any' annotations in CMS models and services
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

ANY_TYPE_PATTERN = re.compile(r""":\s*any\b|\bas\s+any\b|<any>""")
HARDCODED_LOCALHOST_PATTERN = re.compile(r"""['"`]https?://localhost:1337['"`]""")
HARDCODED_HTML_TEXT_PATTERN = re.compile(r"""<(h[1-6]|p|span|button|a)\b[^>]*>([A-Za-z0-9\s,.'"-]{20,})</\1>""")


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for Strapi integration audit."""
    parser = argparse.ArgumentParser(
        description="Audit Angular project for Strapi CMS zero-hardcoding compliance and best practices.",
        epilog=(
            "Examples:\n"
            "  python3 audit_strapi_integration.py src/app\n"
            "  python3 audit_strapi_integration.py --json\n"
            "  python3 audit_strapi_integration.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to Angular project root or src (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are detected")
    return parser.parse_args()


def audit_strapi_integration(target_dir: str) -> Dict[str, Any]:
    """Inspect Angular project files for Strapi zero-hardcoding and architectural compliance."""
    root = os.path.abspath(target_dir)

    hardcoded_url_violations: List[Dict[str, Any]] = []
    hardcoded_text_violations: List[Dict[str, Any]] = []
    any_type_violations: List[Dict[str, Any]] = []

    has_strapi_service = False
    has_media_pipe = False
    has_transfer_state = False
    has_proactive_prompt = False

    # Check for proactive prompt template asset
    prompt_candidates = [
        os.path.join(root, "proactive-schema-prompt.md"),
        os.path.join(root, "assets", "proactive-schema-prompt.md"),
        os.path.join(root, "docs", "proactive-schema-prompt.md")
    ]
    for cand in prompt_candidates:
        if os.path.exists(cand):
            has_proactive_prompt = True
            break

    # Walk directory to analyze services, pipes, templates, models
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]

        for filename in files:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)

            # Check Strapi Service
            if "strapi" in filename.lower() and "service" in filename.lower() and filename.endswith(".ts"):
                has_strapi_service = True
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        if "TransferState" in f.read():
                            has_transfer_state = True
                except Exception:
                    pass

            # Check Strapi Media Pipe
            if "strapi-media" in filename.lower() and filename.endswith(".ts"):
                has_media_pipe = True

            # Scan TypeScript files for hardcoded localhost and any types
            if filename.endswith(".ts") and not filename.endswith(".spec.ts"):
                try:
                    with open(filepath, "r", encoding="utf-8") as ts_file:
                        for line_num, line in enumerate(ts_file, start=1):
                            stripped = line.strip()
                            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                                continue

                            # Hardcoded localhost:1337 outside of default fallback factory
                            if HARDCODED_LOCALHOST_PATTERN.search(line) and "factory:" not in line:
                                hardcoded_url_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "snippet": stripped
                                })

                            # Explicit any annotations
                            if ANY_TYPE_PATTERN.search(line):
                                any_type_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "snippet": stripped
                                })
                except Exception:
                    pass

            # Scan HTML templates for hardcoded static text strings
            if filename.endswith(".html"):
                try:
                    with open(filepath, "r", encoding="utf-8") as html_file:
                        for line_num, line in enumerate(html_file, start=1):
                            stripped = line.strip()
                            if stripped.startswith("<!--") or "{{" in stripped or "@" in stripped:
                                continue

                            match = HARDCODED_HTML_TEXT_PATTERN.search(stripped)
                            if match:
                                hardcoded_text_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "text": match.group(2).strip(),
                                    "snippet": stripped
                                })
                except Exception:
                    pass

    checkpoints = [
        {"name": "Strapi Client Service (Type-safe API consumer)", "passed": has_strapi_service},
        {"name": "SSR Hydration Caching (TransferState integration)", "passed": has_transfer_state},
        {"name": "Dynamic Media Resolution (StrapiMediaPipe presence)", "passed": has_media_pipe},
        {"name": "Proactive Schema Prompt Template Available", "passed": has_proactive_prompt},
        {"name": "Zero Hardcoded Localhost API URLs in Source Code", "passed": len(hardcoded_url_violations) == 0},
        {"name": "Zero Hardcoded Text Strings in HTML Templates", "passed": len(hardcoded_text_violations) == 0},
        {"name": "Strict Type Safety (Zero explicit 'any' annotations)", "passed": len(any_type_violations) == 0}
    ]

    passed_count = sum(1 for cp in checkpoints if cp["passed"])
    score_percentage = round((passed_count / len(checkpoints)) * 100, 1)

    return {
        "target_path": root,
        "score_percentage": score_percentage,
        "is_compliant": passed_count == len(checkpoints),
        "checkpoints": checkpoints,
        "hardcoded_url_violations": hardcoded_url_violations,
        "hardcoded_text_violations": hardcoded_text_violations,
        "any_type_violations": any_type_violations
    }


def main() -> int:
    """Execute audit and report findings."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_strapi_integration(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 66)
        print("🚀  ANGULAR & STRAPI CMS ZERO-HARDCODING AUDIT")
        print("=" * 66)
        print(f"Target Directory : {report['target_path']}")
        print(f"Compliance Score : {report['score_percentage']}%")
        print("-" * 66)

        for cp in report["checkpoints"]:
            icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            print(f"{icon} - {cp['name']}")

        if report["hardcoded_url_violations"]:
            print(f"\n🚨 {len(report['hardcoded_url_violations'])} HARDCODED LOCALHOST URLS:")
            for v in report["hardcoded_url_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['snippet']}")

        if report["hardcoded_text_violations"]:
            print(f"\n🚨 {len(report['hardcoded_text_violations'])} HARDCODED HTML TEXT VIOLATIONS:")
            for v in report["hardcoded_text_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['text']}")

        if report["any_type_violations"]:
            print(f"\n🚨 {len(report['any_type_violations'])} EXPLICIT 'ANY' TYPE VIOLATIONS:")
            for v in report["any_type_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['snippet']}")

        print("=" * 66 + "\n")

    if args.strict and not report["is_compliant"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
