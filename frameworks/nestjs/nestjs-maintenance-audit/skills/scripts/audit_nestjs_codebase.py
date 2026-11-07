# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit NestJS Codebase CLI Tool.

Scans an existing NestJS backend repository for architectural anti-patterns,
circular dependencies, missing request validation pipes, missing shutdown hooks,
explicit 'any' types, raw console logging, and configuration leaks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class Finding:
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    category: str  # "ARCHITECTURE", "SECURITY", "RESILIENCY", "CLEAN_CODE"
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: str = ""


@dataclass
class AuditReport:
    target_dir: str
    passed: bool
    score: int  # 0 - 100
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[Finding] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit an existing NestJS backend codebase for architectural and clean code compliance."
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=".",
        help="Path to the NestJS repository root (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero exit code if CRITICAL or HIGH findings are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON audit report to stdout.",
    )
    return parser.parse_args()


def audit_main_file(main_file: Path, findings: List[Finding]) -> None:
    if not main_file.exists():
        findings.append(
            Finding(
                severity="CRITICAL",
                category="RESILIENCY",
                title="Missing main.ts bootstrap entrypoint",
                description=f"Could not locate {main_file}. NestJS entrypoint is missing.",
                file_path=str(main_file),
                remediation="Ensure src/main.ts exists and configures the NestFactory bootstrap.",
            )
        )
        return

    content = main_file.read_text(encoding="utf-8", errors="ignore")

    # Check 1: ValidationPipe
    if "ValidationPipe" not in content or "useGlobalPipes" not in content:
        findings.append(
            Finding(
                severity="HIGH",
                category="SECURITY",
                title="Missing Global ValidationPipe",
                description="main.ts does not register a global ValidationPipe. Incoming payloads may bypass validation.",
                file_path=str(main_file),
                remediation="Add app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }))",
            )
        )
    elif "whitelist" not in content:
        findings.append(
            Finding(
                severity="MEDIUM",
                category="SECURITY",
                title="ValidationPipe Missing 'whitelist: true'",
                description="Global ValidationPipe does not explicitly enforce 'whitelist: true', allowing unvalidated extra properties.",
                file_path=str(main_file),
                remediation="Configure whitelist: true in ValidationPipe options.",
            )
        )

    # Check 2: Shutdown Hooks
    if "enableShutdownHooks" not in content:
        findings.append(
            Finding(
                severity="HIGH",
                category="RESILIENCY",
                title="Missing app.enableShutdownHooks()",
                description="main.ts lacks app.enableShutdownHooks(). SIGTERM/SIGINT signals will terminate the container without running OnModuleDestroy hooks.",
                file_path=str(main_file),
                remediation="Call app.enableShutdownHooks() in bootstrap() before app.listen().",
            )
        )

    # Check 3: Security headers (Helmet)
    if "helmet" not in content.lower():
        findings.append(
            Finding(
                severity="MEDIUM",
                category="SECURITY",
                title="Missing Helmet Security Middleware",
                description="main.ts does not use helmet() to set secure HTTP response headers.",
                file_path=str(main_file),
                remediation="Install helmet and add app.use(helmet()) in bootstrap().",
            )
        )


def audit_source_files(src_dir: Path, findings: List[Finding]) -> None:
    if not src_dir.exists():
        return

    # Regex patterns
    forward_ref_re = re.compile(r"\bforwardRef\s*\(")
    raw_console_re = re.compile(r"\bconsole\.(log|error|warn|debug|info)\s*\(")
    explicit_any_re = re.compile(r":\s*any\b|as\s+any\b|<any>")
    process_env_re = re.compile(r"\bprocess\.env\.[A-Z0-9_]+")

    for root, _, files in os.walk(src_dir):
        for f in files:
            if not f.endswith(".ts") or f.endswith(".spec.ts"):
                continue

            file_path = Path(root) / f
            relative_path = str(file_path.relative_to(src_dir.parent))
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

            is_config_or_main = (
                "config" in relative_path.lower()
                or f == "main.ts"
                or f.endswith(".config.ts")
            )

            for line_idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if clean_line.startswith("//") or clean_line.startswith("/*") or clean_line.startswith("*"):
                    continue

                # Check: forwardRef
                if forward_ref_re.search(line):
                    findings.append(
                        Finding(
                            severity="HIGH",
                            category="ARCHITECTURE",
                            title="Circular Dependency Detected (forwardRef)",
                            description="Usage of forwardRef() indicates tight coupling between modules or services.",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Decouple modules using Domain Events (@nestjs/event-emitter) or extract a shared module.",
                        )
                    )

                # Check: Raw console
                if raw_console_re.search(line):
                    findings.append(
                        Finding(
                            severity="LOW",
                            category="CLEAN_CODE",
                            title="Raw Console Logging",
                            description="Direct use of console.* in production code bypasses structured logging.",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Inject and use NestJS Logger service instead of console.log().",
                        )
                    )

                # Check: Explicit any
                if explicit_any_re.search(line):
                    findings.append(
                        Finding(
                            severity="MEDIUM",
                            category="CLEAN_CODE",
                            title="Explicit 'any' Type Detected",
                            description="Use of 'any' defeats TypeScript type safety and breaks Clean Code standards.",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Replace 'any' with specific interfaces, generics, or 'unknown' with type narrowing.",
                        )
                    )

                # Check: Direct process.env in service/controller
                if not is_config_or_main and process_env_re.search(line):
                    findings.append(
                        Finding(
                            severity="MEDIUM",
                            category="SECURITY",
                            title="Direct process.env Access in Business Logic",
                            description="Direct environment variable access bypasses configuration validation.",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Inject ConfigService to access validated environment properties.",
                        )
                    )


def audit_package_manager(target_dir: Path, findings: List[Finding]) -> None:
    package_json = target_dir / "package.json"
    pnpm_lock = target_dir / "pnpm-lock.yaml"
    npm_lock = target_dir / "package-lock.json"
    yarn_lock = target_dir / "yarn.lock"

    if package_json.exists():
        if npm_lock.exists() or yarn_lock.exists():
            findings.append(
                Finding(
                    severity="MEDIUM",
                    category="CLEAN_CODE",
                    title="Non-pnpm Lockfile Present",
                    description="package-lock.json or yarn.lock found alongside pnpm repository.",
                    file_path=str(target_dir),
                    remediation="Remove package-lock.json or yarn.lock and enforce pnpm as single authoritative package manager.",
                )
            )
        if not pnpm_lock.exists() and not (target_dir.parent / "pnpm-lock.yaml").exists():
            findings.append(
                Finding(
                    severity="LOW",
                    category="CLEAN_CODE",
                    title="Missing pnpm-lock.yaml",
                    description="pnpm-lock.yaml not found at project root.",
                    file_path=str(target_dir),
                    remediation="Run 'pnpm install' to generate a deterministic pnpm-lock.yaml.",
                )
            )


def calculate_score(findings: List[Finding]) -> int:
    deductions = {
        "CRITICAL": 30,
        "HIGH": 15,
        "MEDIUM": 8,
        "LOW": 3,
    }
    total_deduction = sum(deductions.get(f.severity, 5) for f in findings)
    return max(0, 100 - total_deduction)


def main() -> None:
    args = parse_args()
    target_dir = Path(args.target_dir).resolve()

    findings: List[Finding] = []

    # 1. Main entrypoint audit
    main_file = target_dir / "src" / "main.ts"
    audit_main_file(main_file, findings)

    # 2. Source tree audit
    audit_source_files(target_dir / "src", findings)

    # 3. Package manager audit
    audit_package_manager(target_dir, findings)

    # Calculate metrics
    crit_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    med_count = sum(1 for f in findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in findings if f.severity == "LOW")
    score = calculate_score(findings)
    passed = crit_count == 0 and (not args.strict or high_count == 0)

    report = AuditReport(
        target_dir=str(target_dir),
        passed=passed,
        score=score,
        total_findings=len(findings),
        critical_count=crit_count,
        high_count=high_count,
        medium_count=med_count,
        low_count=low_count,
        findings=findings,
    )

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        sys.stderr.write("========================================================\n")
        sys.stderr.write("🔍 NESTJS CODEBASE HEALTH & MAINTAINABILITY AUDIT\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Target Directory : {target_dir}\n")
        sys.stderr.write(f"Health Score     : {score}/100 {'✅' if score >= 80 else '⚠️'}\n")
        sys.stderr.write(f"Status           : {'PASS ✅' if passed else 'FAIL ❌'}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Critical Findings: {crit_count}\n")
        sys.stderr.write(f"High Findings    : {high_count}\n")
        sys.stderr.write(f"Medium Findings  : {med_count}\n")
        sys.stderr.write(f"Low Findings     : {low_count}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        for finding in findings:
            loc = f" ({finding.file_path}:{finding.line_number})" if finding.file_path and finding.line_number else ""
            sys.stderr.write(f"[{finding.severity}] {finding.title}{loc}\n")
            sys.stderr.write(f"  Reason : {finding.description}\n")
            sys.stderr.write(f"  Action : {finding.remediation}\n\n")
        sys.stderr.write("========================================================\n")

    if not passed and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
