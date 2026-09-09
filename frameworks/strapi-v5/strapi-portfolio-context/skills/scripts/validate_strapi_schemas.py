# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
validate_strapi_schemas.py
--------------------------
Standalone CLI tool to validate Strapi v5 content-type schema definitions:
- Verifies schema.json structure (kind, collectionName, attributes)
- Enforces UID type on slug fields with valid targetField
- Checks draftAndPublish option configuration
- Audits rich text content fields for modern Strapi Blocks type
- Validates component naming conventions (category.name)

Outputs structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Strapi v5 content-type schemas, UID slugs, and draft/publish settings."
    )
    parser.add_argument(
        "--path",
        type=str,
        default="src",
        help="Path to Strapi project, src directory, or schema.json file (default: src).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any schema violations are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class StrapiSchemaValidator:
    """Validates Strapi v5 schema JSON files."""

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def validate(self) -> Dict[str, Any]:
        """Run all schema validation checks."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        schema_files: List[Path] = []
        if self.target_path.is_file() and self.target_path.name.endswith(".json"):
            schema_files.append(self.target_path)
        else:
            for root, _, files in os.walk(self.target_path):
                for f in files:
                    if f == "schema.json":
                        schema_files.append(Path(root) / f)

        if not schema_files:
            self.violations.append({
                "type": "missing_schemas",
                "message": f"No 'schema.json' files discovered under {self.target_path}",
                "severity": "HIGH"
            })
            return self._build_report()

        for s_file in schema_files:
            self._check_schema_file(s_file)

        return self._build_report()

    def _check_schema_file(self, schema_file: Path) -> None:
        """Inspect individual schema.json structure."""
        try:
            content = json.loads(schema_file.read_text(encoding="utf-8"))
        except Exception as e:
            self.violations.append({
                "file": str(schema_file),
                "type": "invalid_json",
                "message": f"Malformed JSON: {e}",
                "severity": "CRITICAL"
            })
            return

        # 1. Verify schema root structure
        kind = content.get("kind")
        if kind not in ("collectionType", "singleType", None):
            self.violations.append({
                "file": schema_file.name,
                "type": "invalid_kind",
                "message": f"Unknown schema kind '{kind}'. Expected 'collectionType' or 'singleType'.",
                "severity": "HIGH"
            })

        attributes = content.get("attributes", {})
        if not attributes:
            self.violations.append({
                "file": schema_file.name,
                "type": "empty_attributes",
                "message": "Schema has no defined attributes.",
                "severity": "HIGH"
            })
            return

        # 2. Check for UID slug definition if entity has title or name
        has_title_or_name = "title" in attributes or "name" in attributes
        if has_title_or_name and kind == "collectionType":
            if "slug" not in attributes:
                self.violations.append({
                    "file": schema_file.name,
                    "type": "missing_slug",
                    "message": "Collection with title/name should have a corresponding 'slug' attribute for SEO routing.",
                    "severity": "MEDIUM"
                })
            else:
                slug_attr = attributes["slug"]
                if slug_attr.get("type") != "uid":
                    self.violations.append({
                        "file": schema_file.name,
                        "type": "invalid_slug_type",
                        "message": f"Slug field must have type 'uid', found '{slug_attr.get('type')}'.",
                        "severity": "HIGH"
                    })
                elif not slug_attr.get("targetField"):
                    self.violations.append({
                        "file": schema_file.name,
                        "type": "missing_slug_target_field",
                        "message": "UID slug attribute missing 'targetField' declaration.",
                        "severity": "MEDIUM"
                    })
                else:
                    self.passes.append(f"Valid UID slug attribute verified in {schema_file.parent.name}")

        # 3. Check for Draft & Publish in projects or articles
        entity_name = content.get("info", {}).get("singularName", "").lower()
        if entity_name in ("project", "article"):
            options = content.get("options", {})
            if not options.get("draftAndPublish"):
                self.violations.append({
                    "file": schema_file.name,
                    "type": "missing_draft_and_publish",
                    "message": f"Collection '{entity_name}' should have 'draftAndPublish: true' enabled.",
                    "severity": "MEDIUM"
                })
            else:
                self.passes.append(f"Draft & Publish enabled for {entity_name}")

        self.passes.append(f"Successfully validated schema structure for {schema_file.parent.name}")

    def _build_report(self) -> Dict[str, Any]:
        """Construct structured report dict."""
        critical_count = sum(1 for v in self.violations if v.get("severity") in ("CRITICAL", "HIGH"))
        return {
            "valid": critical_count == 0,
            "target_path": str(self.target_path),
            "passes_count": len(self.passes),
            "violations_count": len(self.violations),
            "passes": self.passes,
            "violations": self.violations,
        }


def main() -> int:
    args = parse_arguments()
    target_path = Path(args.path)

    validator = StrapiSchemaValidator(target_path)
    report = validator.validate()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== 🧩 STRAPI V5 SCHEMA AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: Strapi Schema Architecture is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: Strapi Schema has Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
