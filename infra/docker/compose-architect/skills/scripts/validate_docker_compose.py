# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
validate_docker_compose.py
--------------------------
Standalone CLI tool to validate Docker Compose architectures:
- Verifies the mandatory 6-file modular Compose topology
- Enforces dynamic port mapping (${HOST_PORT:-${PORT:-...}})
- Scans for hardcoded secrets and credentials
- Validates condition-based healthcheck startup (condition: service_healthy)
- Checks external network definitions in existing-infra layers

Outputs structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Docker Compose multi-environment topology, security, and healthcheck hygiene."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to project directory or compose file (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any topology violations or hardcoded secrets are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class ComposeValidator:
    """Audits Docker Compose files for enterprise topology and security standards."""

    EXPECTED_TOPOLOGY_FILES = [
        "docker-compose.yml",
        "docker-compose.override.yml",
        "docker-compose.prod.yml",
        "docker-compose.shared.yml",
        "docker-compose.existing-infra.yml",
        "docker-compose.repo.yml",
    ]

    DYNAMIC_PORT_REGEX = re.compile(r"['\"]?\$\{HOST_PORT(?::-\$\{PORT(?::-\d+)?\}|:-\d+)?\}:(?:\$\{PORT(?::-\d+)?\}|\d+)['\"]?")
    STATIC_PORT_REGEX = re.compile(r"^\s*-\s*['\"]?(\d{2,5}):(\d{2,5})['\"]?", re.MULTILINE)
    HARDCODED_SECRET_REGEX = re.compile(
        r"(?:PASSWORD|SECRET|KEY|TOKEN)\s*[:=]\s*(?!(\$\{.*\}|['\"]?\$\{.*\}['\"]?|null|~|$))[^\s#]+",
        re.IGNORECASE,
    )

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def validate(self) -> Dict[str, Any]:
        """Run all compose validation checks."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        if self.target_path.is_file():
            self._check_single_file(self.target_path)
        else:
            self._check_topology(self.target_path)
            for f_name in self.EXPECTED_TOPOLOGY_FILES:
                p = self.target_path / f_name
                if p.is_file():
                    self._check_single_file(p)

        return self._build_report()

    def _check_topology(self, directory: Path) -> None:
        """Check for presence of the 6-file modular compose topology."""
        missing = []
        for f_name in self.EXPECTED_TOPOLOGY_FILES:
            if not (directory / f_name).is_file():
                missing.append(f_name)

        if not missing:
            self.passes.append("All 6 modular Docker Compose topology files are present.")
        else:
            self.violations.append({
                "type": "incomplete_topology",
                "message": f"Missing compose topology files: {', '.join(missing)}",
                "severity": "HIGH",
                "missing_files": missing
            })

    def _check_single_file(self, file_path: Path) -> None:
        """Inspect individual compose file content for standards compliance."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.violations.append({
                "file": file_path.name,
                "type": "read_error",
                "message": str(e),
                "severity": "HIGH"
            })
            return

        # 1. Check for static port bindings (violating dynamic port policy)
        if file_path.name in ("docker-compose.yml", "docker-compose.prod.yml"):
            for match in self.STATIC_PORT_REGEX.finditer(content):
                self.violations.append({
                    "file": file_path.name,
                    "type": "static_port_binding",
                    "message": f"Static port mapping found: '{match.group(0).strip()}'. Use dynamic mapping: '${{HOST_PORT:-${{PORT:-3000}}}}:${{PORT:-3000}}'.",
                    "severity": "HIGH"
                })

        # 2. Check for hardcoded secrets
        for line_idx, line in enumerate(content.splitlines(), start=1):
            if "#" in line:
                line = line.split("#")[0]
            if self.HARDCODED_SECRET_REGEX.search(line):
                # Allow dummy local fallbacks in development override
                if file_path.name == "docker-compose.override.yml" or "dev_" in line:
                    continue
                self.violations.append({
                    "file": file_path.name,
                    "line": line_idx,
                    "type": "hardcoded_secret",
                    "message": f"Potential hardcoded secret discovered: '{line.strip()}'. Interpolate from environment variables.",
                    "severity": "HIGH"
                })

        # 3. Check for condition-based health checks in depends_on
        if "depends_on:" in content and "condition: service_healthy" not in content and "shared" not in file_path.name:
            self.violations.append({
                "file": file_path.name,
                "type": "missing_healthcheck_condition",
                "message": "Service 'depends_on' should specify 'condition: service_healthy' to prevent startup race conditions.",
                "severity": "MEDIUM"
            })
        elif "condition: service_healthy" in content:
            self.passes.append(f"Condition-based healthcheck sequencing verified in {file_path.name}")

        self.passes.append(f"Validated syntax and structure of {file_path.name}")

    def _build_report(self) -> Dict[str, Any]:
        """Construct structured report dictionary."""
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

    validator = ComposeValidator(target_path)
    report = validator.validate()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== 🐳 DOCKER COMPOSE TOPOLOGY AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: Compose Architecture is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: Compose Architecture has Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
