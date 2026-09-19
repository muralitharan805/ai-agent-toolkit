#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///

"""
run_evals.py
Evaluation suite validator for Agent Skills (agentskills.io open standard).
Validates eval definitions and performs only deterministic checks that this runner
can actually verify. Semantic assertions are reported as not_evaluated rather than
being treated as passes.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for evaluation execution."""
    parser = argparse.ArgumentParser(
        description="Run or validate Agent Skill evaluation test cases and assertions.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/run_evals.py path/to/skill\n"
            "  python3 scripts/run_evals.py path/to/skill --json\n"
            "  python3 scripts/run_evals.py path/to/skill --save-grading\n"
            "  python3 scripts/run_evals.py path/to/skill --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("skill_dir", help="Path to the target skill directory")
    parser.add_argument("--json", action="store_true", help="Emit report as machine-readable JSON to stdout")
    parser.add_argument("--save-grading", action="store_true", help="Save report to <skill-dir>/evals/grading.json")
    parser.add_argument("--output", help="Explicit path to output grading JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Validate test cases without evaluating live files")
    parser.add_argument("--strict", action="store_true", help="Fail if any warning or non-critical issue is found")
    return parser.parse_args()


def log_diagnostic(message: str) -> None:
    """Print diagnostic messages to stderr."""
    sys.stderr.write(f"[eval-runner] {message}\n")
    sys.stderr.flush()


def load_evals_file(evals_path: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Load and parse the evals.json test suite file."""
    errors: List[str] = []
    if not os.path.isfile(evals_path):
        errors.append(f"Missing required evaluation suite: {evals_path}")
        return None, errors

    try:
        with open(evals_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
            if not isinstance(data, dict):
                errors.append("Root of evals.json must be a JSON object.")
                return None, errors
            return data, errors
    except json.JSONDecodeError as err:
        errors.append(f"Invalid JSON in evals.json: {err}")
        return None, errors


def validate_test_cases(evals_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """Validate schema conformance and integrity of test cases."""
    errors: List[str] = []
    warnings: List[str] = []
    test_cases: List[Dict[str, Any]] = []

    evals_list = evals_data.get("evals")
    if not isinstance(evals_list, list) or len(evals_list) == 0:
        errors.append("Field 'evals' must be a non-empty array of test cases.")
        return test_cases, errors, warnings

    seen_ids = set()
    for index, item in enumerate(evals_list):
        if not isinstance(item, dict):
            errors.append(f"evals[{index}] must be a JSON object.")
            continue

        test_id = item.get("id")
        if test_id is None:
            errors.append(f"evals[{index}] is missing required field 'id'.")
        elif test_id in seen_ids:
            errors.append(f"Duplicate test ID '{test_id}' detected at evals[{index}].")
        else:
            seen_ids.add(test_id)

        prompt = item.get("prompt")
        if not prompt or not isinstance(prompt, str):
            errors.append(f"evals[{index}] (id: {test_id}) is missing required string 'prompt'.")

        expected = item.get("expected_output")
        if not expected or not isinstance(expected, str):
            errors.append(f"evals[{index}] (id: {test_id}) is missing required string 'expected_output'.")

        assertions = item.get("assertions")
        if not isinstance(assertions, list) or len(assertions) == 0:
            errors.append(f"evals[{index}] (id: {test_id}) must have a non-empty 'assertions' array.")
        else:
            for assertion_index, assertion in enumerate(assertions):
                if not isinstance(assertion, str) or not assertion.strip():
                    errors.append(
                        f"evals[{index}] assertion[{assertion_index}] must be a non-empty string."
                    )

        test_cases.append(item)

    if len(test_cases) < 2:
        warnings.append("Recommended to include at least 2 test cases in evals suite.")

    return test_cases, errors, warnings


def evaluate_files_presence(
    workspace_root: str,
    target_files: List[str],
) -> Tuple[bool, List[str]]:
    """Check whether expected output files exist on the filesystem."""
    missing_files: List[str] = []
    for relative_path in target_files:
        full_path = os.path.join(workspace_root, relative_path)
        if not os.path.exists(full_path):
            missing_files.append(relative_path)
    return len(missing_files) == 0, missing_files


def run_evaluation(
    skill_dir: str,
    test_cases: List[Dict[str, Any]],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Execute evaluation and construct structured grading report."""
    workspace_root = os.getcwd()
    skill_name = os.path.basename(os.path.abspath(skill_dir).rstrip("/"))
    if skill_name == "skills":
        skill_name = os.path.basename(os.path.dirname(os.path.abspath(skill_dir).rstrip("/")))

    evaluated_cases: List[Dict[str, Any]] = []
    total_assertions = 0
    verified_assertions = 0
    failed_assertions = 0
    not_evaluated_assertions = 0

    for item in test_cases:
        test_id = item.get("id")
        test_name = item.get("name", f"Test Case #{test_id}")
        assertions = item.get("assertions", [])
        expected_files = item.get("files", [])

        case_assertions_total = len(assertions)
        total_assertions += case_assertions_total

        details: List[Dict[str, Any]] = []
        case_verified = 0
        case_failed = 0
        case_not_evaluated = 0

        files_ok, missing_files = evaluate_files_presence(workspace_root, expected_files)

        for assertion_text in assertions:
            is_file_assertion = "file" in assertion_text.lower() or "scaffold" in assertion_text.lower()

            if dry_run:
                status = "not_evaluated"
                evidence = "Dry-run mode validates suite structure only."
                remediation = None
            elif is_file_assertion and expected_files:
                if files_ok:
                    status = "verified"
                    evidence = "All declared expected files are present."
                    remediation = None
                else:
                    status = "failed"
                    evidence = f"Expected files missing: {', '.join(missing_files)}"
                    remediation = "Ensure scaffolding step outputs all declared files."
            else:
                status = "not_evaluated"
                evidence = (
                    "This assertion requires an agent run or a dedicated deterministic grader; "
                    "the local suite validator cannot verify it."
                )
                remediation = "Run this case through a real agent-eval harness with an assertion-specific grader."

            if status == "verified":
                case_verified += 1
                verified_assertions += 1
            elif status == "failed":
                case_failed += 1
                failed_assertions += 1
            else:
                case_not_evaluated += 1
                not_evaluated_assertions += 1

            details.append({
                "assertion": assertion_text,
                "status": status,
                "evidence": evidence,
                "remediation": remediation,
            })

        if case_failed:
            case_status = "failed"
        elif case_not_evaluated:
            case_status = "not_evaluated"
        else:
            case_status = "verified"

        evaluated_cases.append({
            "id": test_id,
            "name": test_name,
            "status": case_status,
            "assertions_total": case_assertions_total,
            "assertions_verified": case_verified,
            "assertions_failed": case_failed,
            "assertions_not_evaluated": case_not_evaluated,
            "details": details,
        })

    if failed_assertions:
        verdict = "failed"
    elif not_evaluated_assertions:
        verdict = "not_evaluated"
    else:
        verdict = "verified"

    deterministic_coverage_percent = (
        0 if total_assertions == 0 else round(((verified_assertions + failed_assertions) / total_assertions) * 100)
    )

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "skill_name": skill_name,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluator": "eval-suite-validator v1.1.0",
        "verdict": verdict,
        "deterministic_coverage_percent": deterministic_coverage_percent,
        "benchmark": None,
        "summary": {
            "total_test_cases": len(test_cases),
            "verified_test_cases": sum(1 for tc in evaluated_cases if tc["status"] == "verified"),
            "failed_test_cases": sum(1 for tc in evaluated_cases if tc["status"] == "failed"),
            "not_evaluated_test_cases": sum(1 for tc in evaluated_cases if tc["status"] == "not_evaluated"),
            "total_assertions": total_assertions,
            "verified_assertions": verified_assertions,
            "failed_assertions": failed_assertions,
            "not_evaluated_assertions": not_evaluated_assertions,
        },
        "test_cases": evaluated_cases,
    }


def format_visual_scorecard(report: Dict[str, Any], skill_dir: str) -> str:
    """Format evaluation-suite validation results."""
    summary = report["summary"]
    verdict = report["verdict"].upper()

    lines = [
        f"=== AGENT SKILL EVAL SUITE REPORT: {report['skill_name']} ===",
        f"Skill Directory       : {skill_dir}",
        f"Total Test Cases      : {summary['total_test_cases']}",
        f"Total Assertions      : {summary['total_assertions']}",
        f"Deterministic Coverage: {report['deterministic_coverage_percent']}%",
        "",
        "Important: semantic assertions are NOT auto-passed.",
        "They remain NOT_EVALUATED until a real agent run or dedicated grader verifies them.",
        "",
    ]

    for tc in report["test_cases"]:
        lines.append(f"Test Case #{tc['id']}: {tc['name']} [{tc['status'].upper()}]")
        for d in tc["details"]:
            lines.append(f"  - [{d['status'].upper()}] {d['assertion']}")
            if d.get("remediation") and d["status"] != "verified":
                lines.append(f"    Remediation: {d['remediation']}")
        lines.append("")

    lines.extend([
        f"Verified Assertions    : {summary['verified_assertions']}",
        f"Failed Assertions      : {summary['failed_assertions']}",
        f"Not Evaluated          : {summary['not_evaluated_assertions']}",
        f"Overall Verdict        : {verdict}",
        "=" * 54,
    ])
    return "\n".join(lines)

def save_grading_report(report: Dict[str, Any], target_path: str) -> None:
    """Persist grading report to specified output path."""
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)
        file_handle.write("\n")
    log_diagnostic(f"Grading report saved to: {target_path}")


def main() -> int:
    """Main CLI entrypoint."""
    args = parse_arguments()
    skill_path = os.path.abspath(args.skill_dir)

    if not os.path.isdir(skill_path):
        log_diagnostic(f"Error: Target path '{args.skill_dir}' is not a directory.")
        return 1

    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        log_diagnostic(f"Error: Missing SKILL.md in '{args.skill_dir}'.")
        return 1

    evals_path = os.path.join(skill_path, "evals", "evals.json")
    evals_data, load_errors = load_evals_file(evals_path)
    if load_errors:
        for err in load_errors:
            log_diagnostic(f"Error: {err}")
        return 1

    test_cases, val_errors, val_warnings = validate_test_cases(evals_data)
    if val_errors:
        for err in val_errors:
            log_diagnostic(f"Error: {err}")
        return 1

    for warn in val_warnings:
        log_diagnostic(f"Warning: {warn}")

    if args.strict and val_warnings:
        log_diagnostic("Strict mode enabled: failing due to warnings.")
        return 1

    report = run_evaluation(skill_path, test_cases, dry_run=args.dry_run)

    if args.output:
        save_grading_report(report, args.output)
    elif args.save_grading:
        grading_path = os.path.join(skill_path, "evals", "grading.json")
        save_grading_report(report, grading_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        sys.stdout.write(format_visual_scorecard(report, args.skill_dir) + "\n")

    return 1 if report["verdict"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
