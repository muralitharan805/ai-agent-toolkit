#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

"""
audit_resume_text.py
Standalone CLI tool to analyze resume files (.md, .txt, or Word .docx) line-by-line
for ATS parsing compatibility, section completeness, duty-style phrasing,
quantifiable metrics, core technical keywords, page margins, font sizes,
header/footer placement traps, and cross-section duplication (Experience vs Projects).
Outputs structured JSON to stdout and diagnostic progress to stderr.
"""

import sys
import os
import re
import json
import zipfile
import argparse
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple

STANDARD_HEADINGS = [
    r"professional summary|summary|about me",
    r"technical skills|skills|core competencies",
    r"professional experience|experience|work history|employment",
    r"key projects|projects|selected projects",
    r"education|academic background",
]

WEAK_PHRASES = [
    r"\bresponsible for\b",
    r"\bworked on\b",
    r"\bassisted with\b",
    r"\bhelped to\b",
    r"\bhandled\b",
    r"\bduties included\b",
    r"\btasked with\b",
    r"\bparticipated in\b",
    r"\binvolved in\b",
]

# Numbers alone (e.g. "Angular 18" or "Node 20") are not impact evidence.
# Treat detectable units and candidate placeholders as quantitative evidence.
METRIC_PATTERN = re.compile(
    r"(?ix)(?:"
    r"\b\d+(?:\.\d+)?\s*(?:%|ms|milliseconds?|seconds?|minutes?|hours?|days?|"
    r"users?|customers?|requests?|rps|qps|records?|items?|queries?|"
    r"endpoints?|services?|transactions?)(?!\w)"
    r"|\b\d+(?:\.\d+)?\s*x\b"
    r"|\b(?:p50|p90|p95|p99)\b"
    r"|\[\s*(?:X|Y|\d+(?:\.\d+)?)\s*(?:%|ms|users?|requests?|rps|records?)\s*\]"
    r")"
)

# A qualitative outcome is acceptable when the candidate cannot verify a metric.
# A keyword match is a hint, not proof that the claimed result occurred.
OUTCOME_PATTERN = re.compile(
    r"\b(?:improv\w*|reduc\w*|eliminat\w*|prevent\w*|automat\w*|"
    r"streamlin\w*|stabiliz\w*|accelerat\w*|resolv\w*|enabl\w*|"
    r"decreas\w*|increas\w*|secur\w*|simplif\w*|optim\w*|"
    r"unblock\w*|reliab\w*|scal\w*|saved?|faster)\b",
    re.IGNORECASE,
)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "using", "used", "via", "across", "through", "while", "built", "engineered",
    "developed", "implemented", "designed", "architected", "system", "application"
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit resume (.md, .txt, or .docx) line-by-line for ATS compatibility, typography, and duplication."
    )
    parser.add_argument("file_path", help="Path to resume file (.md, .txt, or .docx)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON (default)")
    parser.add_argument("--line-by-line", action="store_true", help="Print detailed line-by-line diagnostic report")
    parser.add_argument(
        "--target-keywords",
        default="",
        help="Optional comma-separated job requirements, e.g. 'Angular,PostgreSQL,AWS'. "
             "If omitted, role-keyword scoring is skipped.",
    )
    return parser.parse_args()

def extract_content(file_path: str) -> List[str]:
    """Reads content line-by-line from markdown, txt, or word .docx."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".docx":
        lines = []
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for p in tree.iterfind(".//w:p", ns):
                is_bullet = p.find(".//w:numPr", ns) is not None
                texts = [t.text for t in p.iterfind(".//w:t", ns) if t.text]
                line_str = "".join(texts).strip()
                if line_str:
                    if is_bullet and not re.match(r"^[\s*•\-]+", line_str):
                        line_str = f"- {line_str}"
                    lines.append(line_str)
            return lines
        except Exception as e:
            sys.stderr.write(f"Error reading .docx file: {e}\n")
            sys.exit(1)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return [l.rstrip("\r\n") for l in f.readlines()]

def audit_docx_layout(file_path: str) -> Dict[str, Any]:
    """Inspects Word document XML for margins, micro-fonts, and header/footer traps."""
    layout_report = {
        "is_docx": False,
        "margins_in_inches": {},
        "font_sizes_pt": [],
        "min_font_pt": None,
        "max_font_pt": None,
        "header_footer_trap": False,
        "layout_issues": [],
        "standards": {
            "recommended_margin_in": "0.5 to 0.75 in",
            "recommended_body_font_pt": "10 to 11 pt (min 9.5 pt)",
            "recommended_heading_font_pt": "12 to 14 pt",
            "recommended_line_spacing": "1.1x to 1.15x",
        }
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".docx":
        return layout_report

    layout_report["is_docx"] = True
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            # 1. Inspect margins in word/document.xml
            if "word/document.xml" in z.namelist():
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                
                # Check pgMar (dxa units: 1440 dxa = 1 inch)
                pg_mar = tree.find(".//w:pgMar", ns)
                if pg_mar is not None:
                    margins = {}
                    for side in ["top", "bottom", "left", "right"]:
                        val = pg_mar.attrib.get(f"{{{ns['w']}}}{side}") or pg_mar.attrib.get(side)
                        if val and val.isdigit():
                            inch_val = round(int(val) / 1440.0, 2)
                            margins[side] = inch_val
                            if inch_val < 0.5:
                                layout_report["layout_issues"].append(
                                    f"Margin risk: {side} margin is {inch_val} in (< 0.5 in). Text near edges may be cropped in OCR scanning."
                                )
                            elif inch_val > 1.0:
                                layout_report["layout_issues"].append(
                                    f"Margin warning: {side} margin is {inch_val} in (> 1.0 in). Wastes 1-page visual space."
                                )
                    layout_report["margins_in_inches"] = margins

                # Check font sizes (half-point units: 20 val = 10 pt)
                font_sizes = []
                for sz in tree.iterfind(".//w:sz", ns):
                    val = sz.attrib.get(f"{{{ns['w']}}}val") or sz.attrib.get("val")
                    if val and val.isdigit():
                        pt = int(val) / 2.0
                        font_sizes.append(pt)
                
                if font_sizes:
                    unique_sizes = sorted(list(set(font_sizes)))
                    layout_report["font_sizes_pt"] = unique_sizes
                    layout_report["min_font_pt"] = min(font_sizes)
                    layout_report["max_font_pt"] = max(font_sizes)
                    if layout_report["min_font_pt"] < 9.5:
                        layout_report["layout_issues"].append(
                            f"Micro-font risk: Minimum font size is {layout_report['min_font_pt']} pt (< 9.5 pt). May fail OCR text parsing or strain recruiter readability."
                        )

            # 2. Check for Header / Footer Traps
            contact_pattern = re.compile(
                r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|\+?\d{10,}|\blinkedin\b|\bgithub\b)",
                re.IGNORECASE
            )
            for fname in z.namelist():
                if fname.startswith("word/header") or fname.startswith("word/footer"):
                    h_xml = z.read(fname)
                    h_tree = ET.fromstring(h_xml)
                    texts = [t.text for t in h_tree.iterfind(".//w:t", ns) if t.text]
                    h_text = " ".join(texts)
                    if contact_pattern.search(h_text):
                        layout_report["header_footer_trap"] = True
                        layout_report["layout_issues"].append(
                            f"Contact-info extraction risk: Word '{os.path.basename(fname)}' contains contact details in a header/footer. Some parsers omit these fields; place contact info in the document body."
                        )
                        break

    except Exception as e:
        layout_report["layout_issues"].append(f"Layout inspection error: {e}")

    return layout_report

def detect_heading(line: str) -> str:
    """Recognize only standalone section headings, not body sentences."""
    clean = re.sub(r"^\s*#{1,6}\s*", "", line).strip()
    clean = clean.strip("*_ ").rstrip(":").strip()
    headings = [
        "Professional Summary", "Technical Skills", "Professional Experience",
        "Key Projects", "Education",
    ]
    for canonical, pattern in zip(headings, STANDARD_HEADINGS):
        if re.fullmatch(pattern, clean, re.IGNORECASE):
            return canonical
    return ""


def detect_section(line: str, current_section: str) -> str:
    return detect_heading(line) or current_section

def analyze_resume_lines(lines: List[str], file_path: str = "", target_keywords: List[str] = None) -> Dict[str, Any]:
    total_lines = len(lines)
    full_text = "\n".join(lines)
    char_count = len(full_text)

    # 1. Section Headings Check (full-line matches prevent false positives)
    canonical_headings = [
        "Professional Summary", "Technical Skills", "Professional Experience",
        "Key Projects", "Education",
    ]
    detected = {detect_heading(line) for line in lines}
    matched_headings = [heading for heading in canonical_headings if heading in detected]
    missing_headings = [heading for heading in canonical_headings if heading not in detected]

    # 2. Line-by-Line Inspection
    current_section = "Header / Contact Info"
    line_audits: List[Dict[str, Any]] = []
    weak_bullets_count = 0
    weak_impact_bullets_count = 0
    quantified_bullets_count = 0
    total_bullets = 0
    impact_bullets_count = 0
    bullets_needing_outcome_count = 0

    for idx, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line:
            continue

        current_section = detect_section(line, current_section)
        # Bullet must start with bullet symbol followed by whitespace (- item, * item, • item)
        is_bullet = bool(re.match(r"^(?:[\s]*[-•]\s+|\s*\*\s+)\w+", line))
        
        issues = []
        improvement_hint = None
        verdict = "PASS"

        if is_bullet:
            total_bullets += 1
            b_lower = line.lower()
            
            # Check for duty-style weak phrasing
            matched_weak = [pat for pat in WEAK_PHRASES if re.search(pat, b_lower)]
            if matched_weak:
                weak_bullets_count += 1
                if current_section in ["Professional Experience", "Key Projects"]:
                    weak_impact_bullets_count += 1
                clean_weak = matched_weak[0].replace(r"\b", "")
                issues.append(f"Duty-style passive phrasing detected: '{clean_weak}'")
                improvement_hint = f"Replace '{clean_weak}' with an active engineering verb (e.g., 'Architected', 'Engineered', 'Optimized') following Action + Tech + Problem + Outcome."
                verdict = "REPLACE_WEAK_VERB"

            # Evaluate engineering/project impact without requiring fabricated metrics.
            if current_section in ["Professional Experience", "Key Projects"]:
                impact_bullets_count += 1
                has_metric = bool(METRIC_PATTERN.search(line))
                has_outcome = bool(OUTCOME_PATTERN.search(line))
                if has_metric:
                    quantified_bullets_count += 1
                elif not has_outcome:
                    bullets_needing_outcome_count += 1
                    issues.append(
                        "No explicit outcome found (verified metric or qualitative result)."
                    )
                    if not improvement_hint:
                        improvement_hint = (
                            "Explain the observed outcome; quantify it only if evidenced."
                        )
                        verdict = "NEEDS_OUTCOME"

            # Check formatting risk on bullet
            if "|" in line:
                issues.append("Table pipe delimiter detected inside bullet; may fail ATS column parsing.")
                verdict = "FORMATTING_RISK"

        is_heading = bool(detect_heading(line))
        
        line_audits.append({
            "line_number": idx,
            "section": current_section,
            "type": "heading" if is_heading else ("bullet" if is_bullet else "text"),
            "text": line,
            "verdict": verdict,
            "issues": issues,
            "improvement_hint": improvement_hint,
        })

    # 2.5 Cross-Section Duplication Detection (Professional Experience vs Key Projects)
    exp_bullets = [
        item for item in line_audits 
        if item["section"] == "Professional Experience" and item["type"] == "bullet"
    ]
    proj_bullets = [
        item for item in line_audits 
        if item["section"] == "Key Projects" and item["type"] == "bullet"
    ]

    duplication_warnings = []
    for pb in proj_bullets:
        p_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", pb["text"].lower())) - STOP_WORDS
        if not p_words:
            continue
        for eb in exp_bullets:
            e_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", eb["text"].lower())) - STOP_WORDS
            if not e_words:
                continue
            common_words = p_words & e_words
            union = p_words | e_words
            jaccard = len(common_words) / len(union) if union else 0.0

            # Trigger duplication risk if Jaccard >= 0.35 or >= 4 common tech/domain words
            if jaccard >= 0.35 or len(common_words) >= 4:
                shared_kw_str = ", ".join(sorted(list(common_words))[:5])
                dup_msg = (
                    f"Duplication Risk: Content overlaps heavily with Experience L{eb['line_number']:03d} "
                    f"(Shared keywords: {shared_kw_str})."
                )
                pb["issues"].append(dup_msg)
                pb["verdict"] = "DUPLICATION_RISK"
                pb["improvement_hint"] = (
                    f"Decouple focus: Highlight deep architecture or vector algorithms in Projects, "
                    f"and keep scale/metrics in Experience L{eb['line_number']:03d}."
                )
                duplication_warnings.append({
                    "project_line": pb["line_number"],
                    "experience_line": eb["line_number"],
                    "shared_keywords": sorted(list(common_words)),
                    "project_text": pb["text"],
                    "experience_text": eb["text"],
                })
                break

    # 3. Target-role keyword coverage: opt-in; never score against a fixed tech stack.
    requested_keywords = list(dict.fromkeys(
        keyword.strip() for keyword in (target_keywords or []) if keyword.strip()
    ))
    found_keywords, missing_keywords = [], []
    for keyword in requested_keywords:
        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
        if re.search(pattern, full_text, re.IGNORECASE):
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    # 4. ATS Formatting & Layout Inspection
    formatting_risks = []
    # Pipe-separated contact lines are not markdown tables.
    if re.search(r"(?m)^\s*\|[^\n]*\|[^\n]*\|\s*$|^\s*:?-{3,}:?\s*\|\s*:?-{3,}:?", full_text):
        formatting_risks.append("Detected markdown table formatting; tables often fail to parse sequentially in legacy ATS.")
    if total_lines > 120:
        formatting_risks.append(f"Resume length ({total_lines} lines) may exceed optimal 1-page visual budget.")

    # Inspect document layout (margins, font size, header traps) if docx
    layout_audit = audit_docx_layout(file_path) if file_path else {"is_docx": False, "layout_issues": []}
    if layout_audit.get("layout_issues"):
        formatting_risks.extend(layout_audit["layout_issues"])

    # 5. Keep ATS text structure separate from content effectiveness.
    # Both values are transparent *heuristics*, never measured ATS pass rates.
    required_missing = [
        h for h in ["Professional Experience", "Education"] if h in missing_headings
    ]
    ats_score = 100 - (len(required_missing) * 12)
    ats_score -= min(40, len(formatting_risks) * 10)
    ats_score = max(0, min(100, ats_score))

    content_score = 100
    if impact_bullets_count:
        content_score -= round(35 * weak_impact_bullets_count / impact_bullets_count)
        content_score -= round(40 * bullets_needing_outcome_count / impact_bullets_count)
    content_score -= min(25, len(duplication_warnings) * 8)
    content_score = max(0, min(100, content_score))

    keyword_coverage = (
        round(100 * len(found_keywords) / len(requested_keywords))
        if requested_keywords else None
    )

    flagged_lines = [la for la in line_audits if la["verdict"] != "PASS"]

    return {
        "score": ats_score,  # Backward-compatible alias for ATS readability ONLY.
        "scores": {
            "ats_readability": ats_score,
            "content_evidence": content_score,
            "target_keyword_coverage": keyword_coverage,
        },
        "scoring_method": "Heuristic linting only; not a real ATS parser or hiring probability.",
        "stats": {
            "char_count": char_count,
            "line_count": total_lines,
            "total_bullets": total_bullets,
            "impact_bullets_count": impact_bullets_count,
            "bullets_needing_outcome_count": bullets_needing_outcome_count,
            "quantified_bullets_count": quantified_bullets_count,
            "weak_bullets_count": weak_bullets_count,
            "weak_impact_bullets_count": weak_impact_bullets_count,
            "duplication_warnings_count": len(duplication_warnings),
            "flagged_lines_count": len(flagged_lines),
        },
        "headings": {
            "required_for_lint": ["Professional Experience", "Education"],
            "found": matched_headings,
            "missing": missing_headings,
        },
        "keywords": {
            "source": "user_supplied" if requested_keywords else "not_provided",
            "found": found_keywords,
            "missing": missing_keywords,
        },
        "layout_and_typography": layout_audit,
        "duplication_warnings": duplication_warnings,
        "flagged_lines": flagged_lines,
        "line_by_line_audit": line_audits,
        "formatting_risks": formatting_risks,
    }

def main():
    args = parse_args()
    if not os.path.exists(args.file_path):
        sys.stderr.write(f"Error: File '{args.file_path}' not found.\n")
        sys.exit(1)

    lines = extract_content(args.file_path)
    requested_keywords = [term.strip() for term in args.target_keywords.split(",") if term.strip()]
    results = analyze_resume_lines(lines, args.file_path, requested_keywords)
    
    sys.stderr.write(
        f"Audited '{args.file_path}' ({results['stats']['line_count']} lines): "
        f"ATS Readability {results['score']}/100 | Content Evidence {results['scores']['content_evidence']}/100 | Flagged Lines: {results['stats']['flagged_lines_count']} "
        f"| Duplication: {results['stats']['duplication_warnings_count']}\n"
    )

    if args.line_by_line:
        print(f"\n{'='*70}")
        print(f"LINE-BY-LINE AUDIT REPORT: {args.file_path}")
        print(f"ATS readability heuristic: {results['score']}/100")
        print(f"Content evidence heuristic: {results['scores']['content_evidence']}/100")
        if results["scores"]["target_keyword_coverage"] is not None:
            print(f"Target keyword coverage: {results['scores']['target_keyword_coverage']}%")
        print("These are linting heuristics, not a real ATS pass probability.")
        print(f"{'='*70}\n")

        # Layout & Typography Summary
        layout = results["layout_and_typography"]
        if layout.get("is_docx"):
            print("📐 LAYOUT & TYPOGRAPHY INSPECTION (.docx):")
            print(f"  - Margins: {layout.get('margins_in_inches')}")
            print(f"  - Font Sizes Detected: {layout.get('font_sizes_pt')} pt (Min: {layout.get('min_font_pt')} pt)")
            print(f"  - Header/Footer Trap: {'⚠️ YES (Contact info inside header/footer!)' if layout.get('header_footer_trap') else '✅ Clean (In body)'}")
            if layout.get("layout_issues"):
                for issue in layout["layout_issues"]:
                    print(f"    ⚠️ {issue}")
            print()
        else:
            print("📐 LAYOUT STANDARDS (Markdown / General):")
            print("  - Recommended Margins: 0.5 in (12.7 mm) to 0.75 in (19 mm)")
            print("  - Recommended Body Font: 10 pt – 11 pt (Calibri, Arial, Inter)")
            print("  - Recommended Line Spacing: 1.1x – 1.15x with 2–3pt after bullets")
            print("  - Header/Footer Trap: Avoid putting contact info in Word/PDF headers\n")

        # Cross-Section Duplication Summary
        if results["duplication_warnings"]:
            print("🔁 CROSS-SECTION DUPLICATION WARNINGS (Experience vs Projects):")
            for dw in results["duplication_warnings"]:
                print(f"  ⚠️ Project L{dw['project_line']:03d} overlaps with Experience L{dw['experience_line']:03d}")
                print(f"     Shared Keywords: {', '.join(dw['shared_keywords'])}")
                print(f"     Project Bullet: \"{dw['project_text']}\"")
                print(f"     Experience Bullet: \"{dw['experience_text']}\"")
            print()

        for item in results["line_by_line_audit"]:
            status_icon = "✅" if item["verdict"] == "PASS" else "⚠️"
            print(f"L{item['line_number']:03d} [{item['section']}] {status_icon} {item['verdict']}")
            print(f"     \"{item['text']}\"")
            for iss in item["issues"]:
                print(f"     -> Issue: {iss}")
            if item["improvement_hint"]:
                print(f"     -> Action: {item['improvement_hint']}")
            print()
    else:
        # Default JSON output
        print(json.dumps(results, indent=2))

    sys.exit(0)

if __name__ == "__main__":
    main()
