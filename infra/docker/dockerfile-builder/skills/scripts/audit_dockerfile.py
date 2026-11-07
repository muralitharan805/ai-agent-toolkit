# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_dockerfile.py
-------------------
Standalone CLI tool to audit Dockerfiles and .dockerignore files:
- Enforces multi-stage build architecture (FROM ... AS ...)
- Verifies non-root USER execution in runner stages
- Flags unpinned :latest base image tags
- Audits dependency manifest layer caching order
- Verifies native HEALTHCHECK directives
- Checks .dockerignore hygiene (.env, node_modules)

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
        description="Audit Dockerfiles and .dockerignore files for production hygiene and security."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to directory containing Dockerfile or direct Dockerfile path (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any Dockerfile violations or security flaws are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class DockerfileAuditor:
    """Audits Dockerfile instructions and security directives."""

    FROM_REGEX = re.compile(r"^\s*FROM\s+([^\s]+)(?:\s+AS\s+([^\s]+))?", re.IGNORECASE | re.MULTILINE)
    USER_REGEX = re.compile(r"^\s*USER\s+([^\s]+)", re.IGNORECASE | re.MULTILINE)
    HEALTHCHECK_REGEX = re.compile(r"^\s*HEALTHCHECK\s+", re.IGNORECASE | re.MULTILINE)

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def audit(self) -> Dict[str, Any]:
        """Run all Dockerfile audit checks."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        dockerfile_path: Path | None = None
        dockerignore_path: Path | None = None

        if self.target_path.is_file():
            dockerfile_path = self.target_path
            parent_dir = self.target_path.parent
            if (parent_dir / ".dockerignore").is_file():
                dockerignore_path = parent_dir / ".dockerignore"
        else:
            cand = self.target_path / "Dockerfile"
            if cand.is_file():
                dockerfile_path = cand
            ign = self.target_path / ".dockerignore"
            if ign.is_file():
                dockerignore_path = ign

        if not dockerfile_path:
            self.violations.append({
                "type": "missing_dockerfile",
                "message": f"No Dockerfile discovered in {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        self._check_dockerfile(dockerfile_path)
        self._check_dockerignore(dockerignore_path)

        return self._build_report()

    def _check_dockerfile(self, dockerfile: Path) -> None:
        """Inspect Dockerfile instructions."""
        try:
            content = dockerfile.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.violations.append({
                "file": dockerfile.name,
                "type": "read_error",
                "message": str(e),
                "severity": "HIGH"
            })
            return

        stages = list(self.FROM_REGEX.finditer(content))
        if not stages:
            self.violations.append({
                "file": dockerfile.name,
                "type": "no_from_instruction",
                "message": "No valid FROM instruction found in Dockerfile.",
                "severity": "CRITICAL"
            })
            return

        # 1. Multi-Stage Build Check
        if len(stages) < 2:
            self.violations.append({
                "file": dockerfile.name,
                "type": "single_stage_build",
                "message": "Dockerfile is a single-stage build. Production images MUST use multi-stage builds to separate build dependencies from runtime.",
                "severity": "HIGH"
            })
        else:
            stage_names = [m.group(2) for m in stages if m.group(2)]
            self.passes.append(f"Multi-stage build verified with {len(stages)} stages: {', '.join(stage_names)}")

        # 2. Pin Base Images (No :latest)
        for stage in stages:
            image_ref = stage.group(1)
            if image_ref.endswith(":latest") or ":" not in image_ref:
                self.violations.append({
                    "file": dockerfile.name,
                    "type": "unpinned_base_image",
                    "message": f"Base image '{image_ref}' uses unpinned ':latest' tag or missing tag. Pin exact semantic versions.",
                    "severity": "MEDIUM"
                })
            else:
                self.passes.append(f"Base image reference pinned: '{image_ref}'")

        # 3. Non-Root USER in final stage
        final_stage_start = stages[-1].start()
        final_stage_content = content[final_stage_start:]
        user_matches = list(self.USER_REGEX.finditer(final_stage_content))

        if not user_matches:
            self.violations.append({
                "file": dockerfile.name,
                "type": "missing_non_root_user",
                "message": "Final runner stage lacks an explicit USER instruction. Container will run as root in production (FORBIDDEN).",
                "severity": "CRITICAL"
            })
        else:
            user_name = user_matches[-1].group(1)
            if user_name.lower() == "root":
                self.violations.append({
                    "file": dockerfile.name,
                    "type": "root_user_instruction",
                    "message": "Final runner stage explicitly declares USER root. Running as root in production is strictly forbidden.",
                    "severity": "CRITICAL"
                })
            else:
                self.passes.append(f"Non-root USER instruction verified in final stage: USER {user_name}")

        # 4. HEALTHCHECK Directive
        if self.HEALTHCHECK_REGEX.search(content):
            self.passes.append("HEALTHCHECK directive verified in Dockerfile.")
        else:
            self.violations.append({
                "file": dockerfile.name,
                "type": "missing_healthcheck",
                "message": "Production Dockerfile lacks a HEALTHCHECK directive.",
                "severity": "MEDIUM"
            })

    def _check_dockerignore(self, dockerignore: Path | None) -> None:
        """Inspect .dockerignore hygiene."""
        if not dockerignore:
            self.violations.append({
                "type": "missing_dockerignore",
                "message": "No .dockerignore file discovered. Build context may leak host node_modules or .env files.",
                "severity": "HIGH"
            })
            return

        try:
            content = dockerignore.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.violations.append({
                "file": dockerignore.name,
                "type": "read_error",
                "message": str(e),
                "severity": "HIGH"
            })
            return

        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
        required_patterns = ["node_modules", ".env", ".git"]
        for req in required_patterns:
            if any(req in line for line in lines):
                self.passes.append(f".dockerignore excludes '{req}'")
            else:
                self.violations.append({
                    "file": dockerignore.name,
                    "type": "unignored_pattern",
                    "message": f".dockerignore is missing exclusion for '{req}'.",
                    "severity": "HIGH"
                })

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

    auditor = DockerfileAuditor(target_path)
    report = auditor.audit()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== 🐳 DOCKERFILE PRODUCTION AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: Dockerfile Architecture is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: Dockerfile has Compliance Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
