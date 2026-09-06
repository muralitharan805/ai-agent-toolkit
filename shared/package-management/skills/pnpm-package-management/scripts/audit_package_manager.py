# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_package_manager.py
------------------------
Standalone CLI automation tool to audit repositories for pnpm package manager hygiene,
stray lockfile detection (package-lock.json, yarn.lock), Corepack engine pinning,
and forbidden npm/yarn command invocations in package scripts.

Outputs structured JSON to stdout and diagnostics to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit repositories for mandatory pnpm package manager hygiene & stray lockfiles."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to repository root to audit (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any package manager violations are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class PackageManagerAuditor:
    """Audits repository files for package manager compliance."""

    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path.resolve()
        self.violations: List[Dict[str, Any]] = []
        self.passes: List[str] = []

    def audit(self) -> Dict[str, Any]:
        """Execute full package manager hygiene audit."""
        # 1. Check for stray lockfiles
        stray_lockfiles = ["package-lock.json", "yarn.lock"]
        for lockfile in stray_lockfiles:
            found_paths = list(self.root_path.rglob(lockfile))
            # Filter out node_modules
            found_paths = [p for p in found_paths if "node_modules" not in str(p)]
            for p in found_paths:
                self.violations.append({
                    "file": str(p.relative_to(self.root_path)),
                    "rule": "FORBIDDEN_STRAY_LOCKFILE",
                    "severity": "CRITICAL",
                    "message": f"Stray lockfile detected: '{lockfile}'. Delete to prevent package manager conflicts.",
                })

        if not any(v["rule"] == "FORBIDDEN_STRAY_LOCKFILE" for v in self.violations):
            self.passes.append("Zero stray npm/yarn lockfiles found in repository")

        # 2. Check for root pnpm-lock.yaml
        pnpm_lock = self.root_path / "pnpm-lock.yaml"
        if pnpm_lock.exists():
            self.passes.append("Authoritative pnpm-lock.yaml verified at root")
        else:
            # Only warn if package.json exists
            if (self.root_path / "package.json").exists():
                self.violations.append({
                    "file": "pnpm-lock.yaml",
                    "rule": "MISSING_PNPM_LOCKFILE",
                    "severity": "WARNING",
                    "message": "Root package.json exists but pnpm-lock.yaml is missing. Run 'pnpm install'.",
                })

        # 3. Check for Corepack packageManager in root package.json
        root_package_json = self.root_path / "package.json"
        if root_package_json.exists():
            try:
                pkg_data = json.loads(root_package_json.read_text(encoding="utf-8"))
                pkg_manager = pkg_data.get("packageManager", "")
                if "pnpm@" in pkg_manager:
                    self.passes.append(f"Corepack packageManager pinned: '{pkg_manager}'")
                else:
                    self.violations.append({
                        "file": "package.json",
                        "rule": "MISSING_COREPACK_ENGINE",
                        "severity": "WARNING",
                        "message": "package.json lacks pinned 'packageManager': 'pnpm@...' field.",
                    })
            except Exception as exc:
                self.violations.append({
                    "file": "package.json",
                    "rule": "INVALID_JSON",
                    "severity": "ERROR",
                    "message": f"Failed to parse package.json: {str(exc)}",
                })

        # 4. Check package.json scripts for forbidden npm/yarn commands
        package_json_files = list(self.root_path.rglob("package.json"))
        package_json_files = [p for p in package_json_files if "node_modules" not in str(p)]

        forbidden_cmd_pattern = re.compile(
            r"\b(?:npm\s+(?:install|i|run|start|test|ci)|yarn\s+(?:add|install|run|start)|npx\s+)",
            re.IGNORECASE,
        )

        for pkg_file in package_json_files:
            try:
                data = json.loads(pkg_file.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                for script_name, script_cmd in scripts.items():
                    if isinstance(script_cmd, str) and forbidden_cmd_pattern.search(script_cmd):
                        self.violations.append({
                            "file": str(pkg_file.relative_to(self.root_path)),
                            "rule": "FORBIDDEN_NPM_YARN_SCRIPT",
                            "severity": "HIGH",
                            "message": f"Script '{script_name}' invokes forbidden command: '{script_cmd}'. Use pnpm equivalents.",
                        })
            except Exception:
                pass

        critical_count = sum(1 for v in self.violations if v["severity"] == "CRITICAL")
        error_count = sum(1 for v in self.violations if v["severity"] == "ERROR")
        warning_count = sum(1 for v in self.violations if v["severity"] == "WARNING")

        return {
            "root_path": str(self.root_path),
            "passes": self.passes,
            "violations": self.violations,
            "total_violations": len(self.violations),
            "critical_count": critical_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "status": "PASSED" if (critical_count == 0 and error_count == 0) else "FAILED",
        }


def main() -> int:
    """CLI entrypoint."""
    args = parse_arguments()
    target_path = Path(args.path).resolve()

    if not target_path.exists():
        sys.stderr.write(f"❌ Target path does not exist: {target_path}\n")
        return 1

    auditor = PackageManagerAuditor(target_path)
    result = auditor.audit()

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        sys.stderr.write(f"🔍 Auditing package manager hygiene across: {target_path}\n")
        for p in result["passes"]:
            sys.stderr.write(f"  ✅ {p}\n")
        for v in result["violations"]:
            sys.stderr.write(f"  ⚠️ [{v['severity']}] {v['file']}: {v['message']}\n")
        print(json.dumps(result, indent=2))

    if args.strict and result["total_violations"] > 0:
        return 1

    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
