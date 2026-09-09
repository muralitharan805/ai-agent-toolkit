#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
audit_angular_material.py
Audits Angular applications for Angular Material component utilization, Dark Mode default compliance,
zero-FOUC script presence, and hardcoded hex color violations in component styles.
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Any

HEX_COLOR_PATTERN = re.compile(r"""#[0-9a-fA-F]{3,8}\b""")
RAW_BUTTON_PATTERN = re.compile(r"""<button(?![^>]*\bmat-)[^>]*>""", re.IGNORECASE)
RAW_INPUT_PATTERN = re.compile(r"""<input(?![^>]*\bmatInput\b)[^>]*>""", re.IGNORECASE)
RAW_SELECT_PATTERN = re.compile(r"""<select\b[^>]*>""", re.IGNORECASE)
RAW_TABLE_PATTERN = re.compile(r"""<table(?![^>]*\bmat-table\b)[^>]*>""", re.IGNORECASE)


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for Angular Material audit."""
    parser = argparse.ArgumentParser(
        description="Audit Angular project for Material component usage, dark mode, and styling best practices.",
        epilog=(
            "Examples:\n"
            "  python3 audit_angular_material.py src/app\n"
            "  python3 audit_angular_material.py --json\n"
            "  python3 audit_angular_material.py --strict"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", nargs="?", default=".", help="Path to Angular project root or src/app (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit audit report as machine-readable JSON to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any violations are detected")
    return parser.parse_args()


def audit_material_styling(target_dir: str) -> Dict[str, Any]:
    """Inspect Angular files for Material-first compliance and theme architecture."""
    root = os.path.abspath(target_dir)

    raw_html_violations: List[Dict[str, Any]] = []
    hex_color_violations: List[Dict[str, Any]] = []

    has_theme_service = False
    has_theme_toggle = False
    has_zero_fouc_script = False

    # Check for index.html zero-FOUC script
    index_html_candidates = [
        os.path.join(root, "src", "index.html"),
        os.path.join(root, "index.html"),
        os.path.join(root, "..", "index.html"),
        os.path.join(root, "zero-fouc-script.html")
    ]
    for cand in index_html_candidates:
        if os.path.exists(cand):
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "app-theme-preference" in content or "classList.toggle('dark-theme'" in content or "classList.add('dark-theme'" in content:
                        has_zero_fouc_script = True
                        break
            except Exception:
                pass

    # Walk directory
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".angular"]]

        for filename in files:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)

            # Check ThemeService
            if filename == "theme.service.ts":
                has_theme_service = True

            # Check ThemeToggle
            if "theme-toggle" in filename:
                has_theme_toggle = True

            # Scan component SCSS files for hardcoded hex colors
            if filename.endswith(".scss"):
                # Skip root theme definition files
                if filename in ["styles.scss", "_variables.scss", "_theme.scss", "_theme-tokens.scss"]:
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as scss_file:
                        for line_num, line in enumerate(scss_file, start=1):
                            stripped = line.strip()
                            if stripped.startswith("//") or stripped.startswith("/*"):
                                continue
                            match = HEX_COLOR_PATTERN.search(line)
                            if match:
                                hex_color_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "hex": match.group(0),
                                    "snippet": stripped
                                })
                except Exception:
                    pass

            # Scan HTML templates for raw HTML tags
            if filename.endswith(".html") and filename != "zero-fouc-script.html":
                try:
                    with open(filepath, "r", encoding="utf-8") as html_file:
                        for line_num, line in enumerate(html_file, start=1):
                            if RAW_BUTTON_PATTERN.search(line):
                                raw_html_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "type": "raw <button> (Use mat-button / mat-icon-button)",
                                    "snippet": line.strip()
                                })
                            if RAW_INPUT_PATTERN.search(line):
                                raw_html_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "type": "raw <input> (Use <mat-form-field> with matInput)",
                                    "snippet": line.strip()
                                })
                            if RAW_SELECT_PATTERN.search(line):
                                raw_html_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "type": "raw <select> (Use <mat-select>)",
                                    "snippet": line.strip()
                                })
                            if RAW_TABLE_PATTERN.search(line):
                                raw_html_violations.append({
                                    "file": relpath,
                                    "line": line_num,
                                    "type": "raw <table> (Use <table mat-table>)",
                                    "snippet": line.strip()
                                })
                except Exception:
                    pass

    checkpoints = [
        {"name": "Reactive ThemeService (Signals + OS Detection)", "passed": has_theme_service},
        {"name": "Header Theme Toggle Control (<app-theme-toggle>)", "passed": has_theme_toggle},
        {"name": "Zero-FOUC Synchronous Head Script (index.html)", "passed": has_zero_fouc_script},
        {"name": "Zero Raw HTML Controls in Templates (Material First)", "passed": len(raw_html_violations) == 0},
        {"name": "Zero Hardcoded Hex Colors in Component SCSS", "passed": len(hex_color_violations) == 0}
    ]

    passed_count = sum(1 for cp in checkpoints if cp["passed"])
    score_percentage = round((passed_count / len(checkpoints)) * 100, 1)

    return {
        "target_path": root,
        "score_percentage": score_percentage,
        "is_compliant": passed_count == len(checkpoints),
        "checkpoints": checkpoints,
        "raw_html_violations": raw_html_violations,
        "hex_color_violations": hex_color_violations
    }


def main() -> int:
    """Execute audit and report findings."""
    args = parse_arguments()
    target_path = os.path.abspath(args.project_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.project_path}' does not exist.\n")
        return 1

    report = audit_material_styling(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 62)
        print("🎨  ANGULAR MATERIAL & DARK THEME COMPLIANCE AUDIT")
        print("=" * 62)
        print(f"Target Directory : {report['target_path']}")
        print(f"Compliance Score : {report['score_percentage']}%")
        print("-" * 62)

        for cp in report["checkpoints"]:
            icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            print(f"{icon} - {cp['name']}")

        if report["raw_html_violations"]:
            print(f"\n🚨 {len(report['raw_html_violations'])} RAW HTML ELEMENT VIOLATIONS:")
            for v in report["raw_html_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['type']}")

        if report["hex_color_violations"]:
            print(f"\n🚨 {len(report['hex_color_violations'])} HARDCODED HEX COLOR VIOLATIONS:")
            for v in report["hex_color_violations"]:
                print(f"  • {v['file']}:{v['line']} ➔ {v['hex']}")

        print("=" * 62 + "\n")

    if args.strict and not report["is_compliant"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
