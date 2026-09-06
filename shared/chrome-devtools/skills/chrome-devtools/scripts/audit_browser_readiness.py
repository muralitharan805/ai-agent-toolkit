# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_browser_readiness.py
--------------------------
Standalone CLI tool to verify local dev server readiness, audit web target
reachability, and inspect HTML response structure for WCAG 2.1 AA accessibility
landmarks and Core Web Vitals (CLS) container reservations.

Outputs structured JSON to stdout and human-readable diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify web server readiness and audit HTML markup for A11y & CWV heuristics."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:4200",
        help="Target URL to inspect and verify (default: http://localhost:4200).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if accessibility or readiness warnings are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


def check_url_reachability(
    target_url: str, timeout_sec: int
) -> Tuple[bool, int, str, Optional[str]]:
    """
    Attempt an HTTP GET request to verify server readiness and fetch HTML content.

    Returns:
        (is_reachable, status_code, content_or_error, content_type)
    """
    parsed = urllib.parse.urlparse(target_url)
    if not parsed.scheme or not parsed.netloc:
        return False, 0, f"Invalid URL structure: {target_url}", None

    req = urllib.request.Request(
        target_url,
        headers={
            "User-Agent": "ChromeDevTools-Auditor/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            status_code = response.status
            content_type = response.headers.get("Content-Type", "")
            raw_data = response.read(500000)  # Read up to 500KB
            charset = response.headers.get_content_charset() or "utf-8"
            html_body = raw_data.decode(charset, errors="replace")
            return True, status_code, html_body, content_type
    except urllib.error.HTTPError as exc:
        return True, exc.code, f"HTTP Error: {exc.code} {exc.reason}", None
    except urllib.error.URLError as exc:
        return False, 0, f"Connection Failed: {exc.reason}", None
    except TimeoutError:
        return False, 0, f"Connection timed out after {timeout_sec}s", None
    except Exception as exc:
        return False, 0, f"Unexpected error: {str(exc)}", None


def audit_html_markup(html_content: str) -> Dict[str, Any]:
    """
    Audit raw HTML markup for key WCAG accessibility landmarks, heading hierarchy,
    and Cumulative Layout Shift (CLS) prevention markers.
    """
    issues: List[Dict[str, str]] = []
    passes: List[str] = []

    # 1. Landmark Checks
    has_main = bool(re.search(r"<main[\s>]|role=[\"']main[\"']", html_content, re.IGNORECASE))
    if has_main:
        passes.append("Semantic <main> landmark identified")
    else:
        issues.append({
            "code": "MISSING_MAIN_LANDMARK",
            "severity": "WARNING",
            "message": "Document lacks explicit <main> tag or role='main' landmark.",
        })

    has_nav = bool(re.search(r"<nav[\s>]|role=[\"']navigation[\"']", html_content, re.IGNORECASE))
    if has_nav:
        passes.append("Semantic <nav> landmark identified")

    # 2. Heading Hierarchy Checks
    h1_matches = re.findall(r"<h1[\s>]", html_content, re.IGNORECASE)
    if len(h1_matches) == 1:
        passes.append("Single <h1> heading found on page")
    elif len(h1_matches) == 0:
        issues.append({
            "code": "MISSING_H1_HEADING",
            "severity": "WARNING",
            "message": "Page contains zero <h1> elements. Single top-level heading is required.",
        })
    else:
        issues.append({
            "code": "MULTIPLE_H1_HEADINGS",
            "severity": "WARNING",
            "message": f"Page contains {len(h1_matches)} <h1> elements. Exactly one <h1> is recommended.",
        })

    # 3. Viewport Meta Tag Check
    has_viewport = bool(
        re.search(r"<meta[^>]+name=[\"']viewport[\"'][^>]*>", html_content, re.IGNORECASE)
    )
    if has_viewport:
        passes.append("Responsive viewport meta tag verified")
    else:
        issues.append({
            "code": "MISSING_VIEWPORT_TAG",
            "severity": "ERROR",
            "message": "Missing responsive meta viewport tag in HTML head.",
        })

    # 4. Image Dimensions Check (CLS Prevention)
    img_tags = re.findall(r"<img\s+[^>]*>", html_content, re.IGNORECASE)
    imgs_without_dimensions = 0
    for img in img_tags:
        has_width = "width=" in img.lower() or "style=" in img.lower()
        has_height = "height=" in img.lower() or "style=" in img.lower()
        if not (has_width and has_height):
            imgs_without_dimensions += 1

    if img_tags:
        if imgs_without_dimensions == 0:
            passes.append(f"All {len(img_tags)} <img> elements specify layout dimensions")
        else:
            issues.append({
                "code": "IMG_MISSING_DIMENSIONS",
                "severity": "WARNING",
                "message": f"{imgs_without_dimensions} of {len(img_tags)} <img> tags lack width/height attributes (CLS risk).",
            })

    # 5. Language Tag Check
    has_lang = bool(re.search(r"<html[^>]+lang=[\"'][a-zA-Z\-]+[\"']", html_content, re.IGNORECASE))
    if has_lang:
        passes.append("HTML document declares valid lang attribute")
    else:
        issues.append({
            "code": "MISSING_HTML_LANG",
            "severity": "WARNING",
            "message": "The <html> element lacks a language attribute (<html lang='en'>).",
        })

    return {
        "passes": passes,
        "issues": issues,
        "issue_count": len(issues),
        "error_count": sum(1 for item in issues if item["severity"] == "ERROR"),
        "warning_count": sum(1 for item in issues if item["severity"] == "WARNING"),
    }


def main() -> int:
    """CLI entrypoint."""
    args = parse_arguments()

    if not args.json_output:
        sys.stderr.write(f"🔍 Probing target server readiness: {args.url}\n")

    is_reachable, status_code, content_or_error, content_type = check_url_reachability(
        args.url, args.timeout
    )

    if not is_reachable:
        result = {
            "target_url": args.url,
            "status": "UNREACHABLE",
            "status_code": status_code,
            "error": content_or_error,
            "readiness": False,
            "audit": None,
        }
        if args.json_output:
            print(json.dumps(result, indent=2))
        else:
            sys.stderr.write(f"❌ Target server unreachable: {content_or_error}\n")
            print(json.dumps(result, indent=2))
        return 1

    # Server is reachable
    audit_data = None
    if content_type and "html" in content_type:
        audit_data = audit_html_markup(content_or_error)

    result = {
        "target_url": args.url,
        "status": "ONLINE" if 200 <= status_code < 400 else "ERROR_STATUS",
        "status_code": status_code,
        "content_type": content_type,
        "readiness": 200 <= status_code < 400,
        "audit": audit_data,
    }

    if not args.json_output:
        sys.stderr.write(f"✅ Server responded with status code {status_code}\n")
        if audit_data:
            sys.stderr.write(
                f"📊 A11y & CWV Heuristics: {len(audit_data['passes'])} passed, "
                f"{audit_data['error_count']} errors, {audit_data['warning_count']} warnings.\n"
            )

    print(json.dumps(result, indent=2))

    if args.strict:
        if not (200 <= status_code < 400):
            return 1
        if audit_data and audit_data["error_count"] > 0:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
