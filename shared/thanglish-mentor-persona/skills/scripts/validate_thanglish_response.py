# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
validate_thanglish_response.py
------------------------------
Standalone CLI automation tool to audit Thanglish and English assistant responses
for Latin-font exclusivity (zero Tamil Unicode characters), calibrated 7-point / 6-point
response envelope presence, and pedagogical curiosity triggers.

Outputs structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit assistant responses for Thanglish font exclusivity, response envelope, and curiosity triggers."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--text",
        type=str,
        help="Literal response text string to audit.",
    )
    group.add_argument(
        "--file",
        type=str,
        help="Path to file containing response text to audit.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any violations or missing envelope sections are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


def audit_response_content(text: str) -> Dict[str, Any]:
    """Audit response text for Tamil script characters, response envelope, and curiosity triggers."""
    violations: List[Dict[str, str]] = []
    passes: List[str] = []

    # 1. Check for Tamil Unicode characters (\u0B80 - \u0BFF)
    tamil_char_pattern = re.compile(r"[\u0B80-\u0BFF]")
    tamil_matches = tamil_char_pattern.findall(text)
    if tamil_matches:
        violations.append({
            "code": "TAMIL_UNICODE_FOUND",
            "severity": "CRITICAL",
            "message": f"Found {len(tamil_matches)} Tamil Unicode script characters. Thanglish mode requires Latin/English font exclusively.",
        })
    else:
        passes.append("Zero Tamil Unicode characters found (Latin/English font exclusively)")

    # 2. Check for Response Envelope Sections (Supports Calibrated 7-Point or Classic 6-Point)
    # 7-point targets:
    # 1. What is happening
    # 2. Why it happens / Why it is happening
    # 3. What actually matters
    # 4. Recommended approach
    # 5. How to execute it / How to implement it
    # 6. What could go wrong / Things to watch out for
    # 7. Professional judgment / Professional recommendation
    has_what_happens = bool(re.search(r"\b1\.\s*What\s+is\s+happening\b", text, re.IGNORECASE))
    has_why_happens = bool(re.search(r"\b2\.\s*Why\s+it\s+(?:happens|is\s+happening)\b", text, re.IGNORECASE))
    has_what_matters = bool(re.search(r"\b(?:3\.\s*)?What\s+actually\s+matters\b", text, re.IGNORECASE))
    has_recommended = bool(re.search(r"\b(?:\d\.\s*)?Recommended\s+approach\b", text, re.IGNORECASE))
    has_execution = bool(re.search(r"\b(?:\d\.\s*)?How\s+to\s+(?:implement|execute)\s+it\b", text, re.IGNORECASE))
    has_risks = bool(re.search(r"\b(?:\d\.\s*)?(?:Things\s+to\s+watch\s+out\s+for|What\s+could\s+go\s+wrong)\b", text, re.IGNORECASE))
    has_judgment = bool(re.search(r"\b(?:\d\.\s*)?Professional\s+(?:recommendation|judgment)\b", text, re.IGNORECASE))

    envelope_checks = [
        ("What is happening", has_what_happens),
        ("Why it happens", has_why_happens),
        ("Recommended approach", has_recommended),
        ("How to execute/implement it", has_execution),
        ("What could go wrong / Things to watch out for", has_risks),
        ("Professional judgment / recommendation", has_judgment),
    ]

    missing_sections = [name for name, present in envelope_checks if not present]

    if has_what_matters:
        passes.append("Calibrated Section: 'What actually matters' verified")

    for name, present in envelope_checks:
        if present:
            passes.append(f"Envelope section verified: '{name}'")

    if missing_sections:
        violations.append({
            "code": "INCOMPLETE_RESPONSE_ENVELOPE",
            "severity": "HIGH",
            "message": f"Missing {len(missing_sections)} core envelope sections: {', '.join(missing_sections)}",
        })

    # 3. Check for Curiosity Trigger
    has_curiosity = bool(
        re.search(r"\bCuriosity\s+Trigger\b|\bCuriosity\b", text, re.IGNORECASE)
    )
    if has_curiosity:
        passes.append("Inspirational curiosity trigger present at conclusion")
    else:
        violations.append({
            "code": "MISSING_CURIOSITY_TRIGGER",
            "severity": "MEDIUM",
            "message": "Response lacks concluding curiosity trigger to inspire deeper learning.",
        })

    critical_count = sum(1 for v in violations if v["severity"] == "CRITICAL")
    high_count = sum(1 for v in violations if v["severity"] == "HIGH")

    return {
        "text_length_chars": len(text),
        "passes": passes,
        "violations": violations,
        "violation_count": len(violations),
        "is_latin_exclusive": len(tamil_matches) == 0,
        "has_full_envelope": len(missing_sections) == 0,
        "has_what_matters_section": has_what_matters,
        "has_curiosity_trigger": has_curiosity,
        "status": "PASSED" if (critical_count == 0 and high_count == 0) else "FAILED",
    }


def main() -> int:
    """CLI entrypoint."""
    args = parse_arguments()

    if args.file:
        file_p = Path(args.file).resolve()
        if not file_p.exists():
            sys.stderr.write(f"❌ Target file does not exist: {file_p}\n")
            return 1
        content = file_p.read_text(encoding="utf-8", errors="replace")
    else:
        content = args.text or ""

    audit_result = audit_response_content(content)

    if args.json_output:
        print(json.dumps(audit_result, indent=2))
    else:
        sys.stderr.write(
            f"🔍 Thanglish & Response Envelope Audit: {audit_result['text_length_chars']} chars scanned\n"
        )
        for p in audit_result["passes"]:
            sys.stderr.write(f"  ✅ {p}\n")
        for v in audit_result["violations"]:
            sys.stderr.write(f"  ⚠️ [{v['severity']}] {v['code']}: {v['message']}\n")
        print(json.dumps(audit_result, indent=2))

    if args.strict and audit_result["violation_count"] > 0:
        return 1

    return 0 if audit_result["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
