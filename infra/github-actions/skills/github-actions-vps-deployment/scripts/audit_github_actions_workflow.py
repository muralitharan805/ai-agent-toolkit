# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_github_actions_workflow.py
--------------------------------
Standalone CLI tool to audit GitHub Actions deployment workflows:
- Verifies SSH deployment action (appleboy/ssh-action)
- Ensures mandatory repository secrets are referenced
- Enforces Zero-VPS Compilation (up -d --pull always instead of --build)
- Checks for post-deployment disk cleanup (docker image prune -f)

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
        description="Audit GitHub Actions deployment workflow for SSH security and Zero-VPS build hygiene."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".github/workflows",
        help="Path to workflow file or .github/workflows directory (default: .github/workflows).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any workflow violations are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class WorkflowAuditor:
    """Audits GitHub Actions workflow YAML files for deployment hygiene."""

    MANDATORY_SECRETS = [
        "SERVER_HOST",
        "SERVER_USERNAME",
        "SERVER_SSH_KEY",
        "SERVER_PORT",
        "PROJECT_PATH",
    ]

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def audit(self) -> Dict[str, Any]:
        """Run all workflow checks."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        workflow_files: List[Path] = []
        if self.target_path.is_file():
            workflow_files.append(self.target_path)
        else:
            for root, _, files in os.walk(self.target_path):
                for f in files:
                    if f.endswith((".yml", ".yaml")):
                        workflow_files.append(Path(root) / f)

        if not workflow_files:
            self.violations.append({
                "type": "missing_workflow_files",
                "message": f"No YAML workflow files discovered in {self.target_path}",
                "severity": "HIGH"
            })
            return self._build_report()

        for wf in workflow_files:
            self._check_workflow(wf)

        return self._build_report()

    def _check_workflow(self, workflow_path: Path) -> None:
        """Inspect single workflow file content."""
        try:
            content = workflow_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.violations.append({
                "file": workflow_path.name,
                "type": "read_error",
                "message": str(e),
                "severity": "HIGH"
            })
            return

        # 1. Verify SSH action usage
        if "appleboy/ssh-action" in content:
            self.passes.append(f"Uses official appleboy/ssh-action in {workflow_path.name}")
        else:
            self.violations.append({
                "file": workflow_path.name,
                "type": "missing_ssh_action",
                "message": "Workflow does not use 'appleboy/ssh-action' for secure SSH deployment.",
                "severity": "HIGH"
            })

        # 2. Check for required repository secrets
        missing_secrets = []
        for sec in self.MANDATORY_SECRETS:
            pattern = rf"secrets\.{sec}"
            if not re.search(pattern, content):
                missing_secrets.append(sec)

        if not missing_secrets:
            self.passes.append(f"All 5 mandatory secrets referenced in {workflow_path.name}")
        else:
            self.violations.append({
                "file": workflow_path.name,
                "type": "missing_secrets",
                "message": f"Workflow missing references to secrets: {', '.join(missing_secrets)}",
                "severity": "HIGH",
                "missing_secrets": missing_secrets
            })

        # 3. Check for Zero-VPS Compilation (--pull always vs --build)
        if "--build" in content and "docker compose" in content:
            self.violations.append({
                "file": workflow_path.name,
                "type": "server_side_compilation",
                "message": "Workflow runs 'docker compose ... --build' on VPS. Violates Zero-VPS compilation rule. Use '--pull always'.",
                "severity": "HIGH"
            })
        elif "--pull always" in content:
            self.passes.append(f"Enforces Zero-VPS compilation with '--pull always' in {workflow_path.name}")

        # 4. Check for post-deploy disk cleanup
        if "docker image prune" in content:
            self.passes.append(f"Post-deployment image pruning verified in {workflow_path.name}")
        else:
            self.violations.append({
                "file": workflow_path.name,
                "type": "missing_image_prune",
                "message": "Workflow lacks 'docker image prune -f' cleanup step. Dangling images will exhaust server disk space.",
                "severity": "MEDIUM"
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

    auditor = WorkflowAuditor(target_path)
    report = auditor.audit()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== 🚀 GITHUB ACTIONS SSH DEPLOYMENT AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: GitHub Actions Deployment is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: GitHub Actions Deployment has Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
