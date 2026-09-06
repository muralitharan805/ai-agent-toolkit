#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Audit Angular Forms Utility (`audit_angular_forms.py`)
Scans Angular projects for enterprise reactive forms anti-patterns:
- Untyped forms (UntypedFormGroup, UntypedFormControl, new FormGroup without generic)
- Form subscription memory leaks (valueChanges/statusChanges without takeUntilDestroyed)
- Template error spaghetti (inline .hasError or .errors checking instead of centralized presenters)
- Explicit 'any' in form definitions
- Legacy [(ngModel)] in feature component templates
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, List, Any

UNTYPED_FORM_PATTERN = re.compile(r'\b(UntypedFormGroup|UntypedFormControl|UntypedFormArray|UntypedFormBuilder)\b')
BARE_NEW_FORM_PATTERN = re.compile(r'new\s+(FormGroup|FormControl|FormArray)\s*\(')
STREAM_LEAK_PATTERN = re.compile(r'\.(valueChanges|statusChanges)\s*\.\s*subscribe\s*\(')
ANY_FORM_PATTERN = re.compile(r'(FormControl|FormGroup|FormArray)<any>')
TEMPLATE_ERROR_PATTERN = re.compile(r'(\.hasError\(|\.errors\s*&&|\.errors\?\.)')
NGMODEL_PATTERN = re.compile(r'\[\(ngModel\)\]')

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit an Angular project for Reactive Forms enterprise architectural compliance.",
        epilog="Examples:\n  python3 audit_angular_forms.py src/app\n  python3 audit_angular_forms.py src/app --json",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target_dir", help="Path to the Angular source directory (e.g. src/app).")
    parser.add_argument("--json", action="store_true", help="Emit report in machine-readable JSON format to stdout.")
    parser.add_argument("--strict", action="store_true", help="Treat any warning or violation as a non-zero exit code.")
    return parser.parse_args()

def scan_file(file_path: str) -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    is_ts = file_path.endswith(".ts")
    is_html = file_path.endswith(".html")

    if not (is_ts or is_html):
        return violations

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to read {file_path}: {str(e)}\n")
        return violations

    for idx, line in enumerate(lines, start=1):
        clean_line = line.strip()
        if clean_line.startswith("//") or clean_line.startswith("<!--"):
            continue

        if is_ts:
            # 1. Untyped form declarations
            if UNTYPED_FORM_PATTERN.search(clean_line):
                violations.append({
                    "file": file_path,
                    "line": idx,
                    "type": "untyped_form_class",
                    "severity": "high",
                    "message": "Usage of legacy untyped form class. Use strictly typed Reactive Forms with NonNullableFormBuilder.",
                    "snippet": clean_line[:120]
                })

            if BARE_NEW_FORM_PATTERN.search(clean_line) and "<" not in clean_line:
                violations.append({
                    "file": file_path,
                    "line": idx,
                    "type": "untyped_instantiation",
                    "severity": "high",
                    "message": "Form instantiated without explicit generic type. Use FormBuilder.nonNullable or generic type.",
                    "snippet": clean_line[:120]
                })

            # 2. Form subscription leak
            if STREAM_LEAK_PATTERN.search(clean_line) and "takeUntilDestroyed" not in clean_line:
                # Check preceding lines for takeUntilDestroyed
                start_context = max(0, idx - 4)
                context_block = "".join(lines[start_context:idx])
                if "takeUntilDestroyed" not in context_block and "toSignal" not in context_block:
                    violations.append({
                        "file": file_path,
                        "line": idx,
                        "type": "unmanaged_form_subscription",
                        "severity": "critical",
                        "message": "Form stream subscription without takeUntilDestroyed(). Potential memory leak hazard.",
                        "snippet": clean_line[:120]
                    })

            # 3. Explicit any in form generic
            if ANY_FORM_PATTERN.search(clean_line):
                violations.append({
                    "file": file_path,
                    "line": idx,
                    "type": "form_any_generic",
                    "severity": "high",
                    "message": "Usage of 'any' type in form generic parameter is strictly forbidden.",
                    "snippet": clean_line[:120]
                })

        if is_html:
            # 4. Template error boilerplate
            if TEMPLATE_ERROR_PATTERN.search(clean_line):
                violations.append({
                    "file": file_path,
                    "line": idx,
                    "type": "template_error_spaghetti",
                    "severity": "medium",
                    "message": "Inline error checking logic detected. Use centralized FormErrorComponent or pipe.",
                    "snippet": clean_line[:120]
                })

            # 5. [(ngModel)] in templates
            if NGMODEL_PATTERN.search(clean_line):
                violations.append({
                    "file": file_path,
                    "line": idx,
                    "type": "ng_model_detected",
                    "severity": "medium",
                    "message": "Two-way [(ngModel)] binding detected. Prefer Reactive Forms for domain features.",
                    "snippet": clean_line[:120]
                })

    return violations

def run_audit(target_dir: str) -> Dict[str, Any]:
    abs_target = os.path.abspath(target_dir)
    report: Dict[str, Any] = {
        "target": abs_target,
        "valid": True,
        "scanned_files": 0,
        "total_violations": 0,
        "violations_by_severity": {"critical": 0, "high": 0, "medium": 0},
        "violations": []
    }

    if not os.path.exists(abs_target):
        report["valid"] = False
        report["error"] = f"Directory not found: {abs_target}"
        return report

    for root, dirs, files in os.walk(abs_target):
        # Exclude node_modules, dist, .git
        if any(ignored in root.split(os.sep) for ignored in ["node_modules", ".git", "dist", ".angular"]):
            continue

        for f in files:
            if f.endswith(".ts") or f.endswith(".html"):
                # Ignore spec files for template checks
                if f.endswith(".spec.ts"):
                    continue
                file_path = os.path.join(root, f)
                report["scanned_files"] += 1
                file_violations = scan_file(file_path)
                if file_violations:
                    report["violations"].extend(file_violations)

    report["total_violations"] = len(report["violations"])
    for v in report["violations"]:
        sev = v.get("severity", "medium")
        if sev in report["violations_by_severity"]:
            report["violations_by_severity"][sev] += 1

    if report["violations_by_severity"]["critical"] > 0 or report["violations_by_severity"]["high"] > 0:
        report["valid"] = False

    return report

def main() -> None:
    args = parse_arguments()
    report = run_audit(args.target_dir)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=======================================================")
        print("🔍 Angular Forms Architecture Audit Report")
        print("=======================================================")
        print(f"Target: {report['target']}")
        print(f"Scanned Files: {report.get('scanned_files', 0)}")
        print(f"Total Violations: {report.get('total_violations', 0)}")
        print(f"  - Critical: {report['violations_by_severity']['critical']}")
        print(f"  - High:     {report['violations_by_severity']['high']}")
        print(f"  - Medium:   {report['violations_by_severity']['medium']}")
        print("-------------------------------------------------------")

        if report["violations"]:
            for idx, v in enumerate(report["violations"], start=1):
                print(f"{idx}. [{v['severity'].upper()}] {v['type']} in {v['file']}:{v['line']}")
                print(f"   Reason: {v['message']}")
                print(f"   Code:   {v['snippet']}")
                print()
        else:
            print("✅ Zero Angular Forms anti-patterns found! Clean enterprise compliance.")
        print("=======================================================")

    is_failure = not report["valid"] or (args.strict and report["total_violations"] > 0)
    sys.exit(1 if is_failure else 0)

if __name__ == "__main__":
    main()
