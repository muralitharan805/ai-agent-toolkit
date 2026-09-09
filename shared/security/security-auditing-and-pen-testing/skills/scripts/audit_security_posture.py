# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Audit Security Posture CLI Tool.

Scans project codebases for security anti-patterns, hardcoded secrets,
SQL injection patterns, insecure client-side token storage, missing security headers,
CORS misconfigurations, and dependency lockfile hygiene.
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
class SecurityFinding:
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    category: str  # "SECRETS", "INJECTION", "AUTH", "CONFIG", "SUPPLY_CHAIN"
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: str = ""


@dataclass
class SecurityAuditReport:
    target_dir: str
    passed: bool
    security_score: int  # 0 - 100
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[SecurityFinding] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit project repository for security posture, secrets hygiene, and OWASP compliance."
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=".",
        help="Path to repository root (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero exit code if CRITICAL or HIGH security findings exist.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON audit report to stdout.",
    )
    return parser.parse_args()


def audit_git_and_env(target_dir: Path, findings: List[SecurityFinding]) -> None:
    gitignore_path = target_dir / ".gitignore"
    env_path = target_dir / ".env"
    env_example_path = target_dir / ".env.example"

    # Check 1: .env in .gitignore
    if gitignore_path.exists():
        gi_content = gitignore_path.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"^\s*\.?env(\.local)?\b", gi_content, re.MULTILINE):
            findings.append(
                SecurityFinding(
                    severity="HIGH",
                    category="SECRETS",
                    title=".env not excluded in .gitignore",
                    description="The .gitignore file does not explicitly ignore .env files, risking secret credential exposure.",
                    file_path=str(gitignore_path),
                    remediation="Add '.env' and '.env.*' to .gitignore.",
                )
            )

    # Check 2: .env.example parity
    if env_path.exists() and not env_example_path.exists():
        findings.append(
            SecurityFinding(
                severity="MEDIUM",
                category="SECRETS",
                title="Missing .env.example template",
                description="Project contains a .env file but lacks a documented .env.example for newcomer setup.",
                file_path=str(target_dir),
                remediation="Create a .env.example file with placeholder values and descriptive comments for every required variable.",
            )
        )

    # Check 3: Real secrets in .env.example
    if env_example_path.exists():
        example_lines = env_example_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(example_lines, start=1):
            if re.search(r"(sk_live_[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|xoxb-[a-zA-Z0-9]{20,})", line):
                findings.append(
                    SecurityFinding(
                        severity="CRITICAL",
                        category="SECRETS",
                        title="Real API key detected in .env.example",
                        description="Live API token pattern found in public .env.example file.",
                        file_path=str(env_example_path),
                        line_number=idx,
                        remediation="Replace real API credentials with placeholder values (e.g. 'your_api_key_here').",
                    )
                )


def audit_source_code(src_dir: Path, findings: List[SecurityFinding]) -> None:
    if not src_dir.exists():
        return

    # Patterns
    secret_key_re = re.compile(
        r"""(?i)(['"]?)(?:api_?key|jwt_?secret|private_?key|auth_?secret)\1\s*[:=]\s*['"]([a-zA-Z0-9_\-]{16,})['"]"""
    )
    raw_sql_re = re.compile(r"""(\$queryRawUnsafe|\.query)\s*\(\s*`[^`]*\$\{""")
    localstorage_token_re = re.compile(
        r"""localStorage\.(setItem|getItem)\s*\(\s*['"](token|refreshToken|access_token|jwt)['"]"""
    )
    cors_wildcard_re = re.compile(r"""origin\s*:\s*['"]\*['"]""")
    helmet_re = re.compile(r"""\bhelmet\s*\(""")

    for root, _, files in os.walk(src_dir):
        for f in files:
            if not f.endswith((".ts", ".js", ".mjs")):
                continue
            if f.endswith(".spec.ts") or f.endswith(".test.ts"):
                continue

            file_path = Path(root) / f
            relative_path = str(file_path.relative_to(src_dir.parent))
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

            # Inspect main.ts specifically
            if f == "main.ts":
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if not helmet_re.search(content):
                    findings.append(
                        SecurityFinding(
                            severity="MEDIUM",
                            category="CONFIG",
                            title="Missing Helmet Security Middleware in main.ts",
                            description="Entrypoint does not register Helmet HTTP security headers.",
                            file_path=relative_path,
                            remediation="Install helmet and add 'app.use(helmet())' in bootstrap().",
                        )
                    )

            for line_idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if clean_line.startswith("//") or clean_line.startswith("/*") or clean_line.startswith("*"):
                    continue

                # Check 1: Hardcoded secrets
                match_secret = secret_key_re.search(line)
                if match_secret:
                    val = match_secret.group(2)
                    if not val.startswith("your_") and not val.startswith("test_") and not val.startswith("replace_"):
                        findings.append(
                            SecurityFinding(
                                severity="HIGH",
                                category="SECRETS",
                                title="Potential Hardcoded Secret / Key Detected",
                                description=f"Found potential raw credential assigned to variable in source code.",
                                file_path=relative_path,
                                line_number=line_idx,
                                remediation="Load credentials from environment variables using ConfigService or process.env.",
                            )
                        )

                # Check 2: SQL Injection concatenation
                if raw_sql_re.search(line):
                    findings.append(
                        SecurityFinding(
                            severity="CRITICAL",
                            category="INJECTION",
                            title="Potential SQL Injection via String Interpolation",
                            description="Direct interpolation detected inside query statement.",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Use parameterized queries, prepared statements, or ORM query builder methods.",
                        )
                    )

                # Check 3: Insecure token storage in frontend
                if localstorage_token_re.search(line):
                    findings.append(
                        SecurityFinding(
                            severity="MEDIUM",
                            category="AUTH",
                            title="Insecure Token Storage in Browser localStorage",
                            description="Tokens stored in localStorage are vulnerable to XSS exfiltration.",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Store refresh tokens in HTTP-Only, SameSite cookies.",
                        )
                    )

                # Check 4: CORS wildcard
                if cors_wildcard_re.search(line) and "enableCors" in line:
                    findings.append(
                        SecurityFinding(
                            severity="MEDIUM",
                            category="CONFIG",
                            title="Permissive Wildcard CORS Configuration",
                            description="CORS is configured with wildcard origin ('*').",
                            file_path=relative_path,
                            line_number=line_idx,
                            remediation="Restrict CORS origin to validated domain whitelist.",
                        )
                    )


def audit_package_manager(target_dir: Path, findings: List[SecurityFinding]) -> None:
    npm_lock = target_dir / "package-lock.json"
    yarn_lock = target_dir / "yarn.lock"
    pnpm_lock = target_dir / "pnpm-lock.yaml"

    if npm_lock.exists() or yarn_lock.exists():
        findings.append(
            SecurityFinding(
                severity="MEDIUM",
                category="SUPPLY_CHAIN",
                title="Non-pnpm Lockfile Present",
                description="package-lock.json or yarn.lock found. May cause non-deterministic builds.",
                file_path=str(target_dir),
                remediation="Delete package-lock.json or yarn.lock and enforce pnpm.",
            )
        )


def calculate_score(findings: List[SecurityFinding]) -> int:
    deductions = {"CRITICAL": 35, "HIGH": 20, "MEDIUM": 10, "LOW": 3}
    total_deduction = sum(deductions.get(f.severity, 5) for f in findings)
    return max(0, 100 - total_deduction)


def main() -> None:
    args = parse_args()
    target_dir = Path(args.target_dir).resolve()

    findings: List[SecurityFinding] = []

    # 1. Environment and git check
    audit_git_and_env(target_dir, findings)

    # 2. Source code audit
    audit_source_code(target_dir / "src", findings)

    # 3. Supply chain lockfile check
    audit_package_manager(target_dir, findings)

    crit_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    med_count = sum(1 for f in findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in findings if f.severity == "LOW")
    score = calculate_score(findings)
    passed = crit_count == 0 and (not args.strict or high_count == 0)

    report = SecurityAuditReport(
        target_dir=str(target_dir),
        passed=passed,
        security_score=score,
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
        sys.stderr.write("🛡️  PROJECT SECURITY & POSTURE AUDIT REPORT\n")
        sys.stderr.write("========================================================\n")
        sys.stderr.write(f"Target Directory : {target_dir}\n")
        sys.stderr.write(f"Security Score   : {score}/100 {'✅' if score >= 80 else '⚠️'}\n")
        sys.stderr.write(f"Audit Status     : {'PASS ✅' if passed else 'FAIL ❌'}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        sys.stderr.write(f"Critical Findings: {crit_count}\n")
        sys.stderr.write(f"High Findings    : {high_count}\n")
        sys.stderr.write(f"Medium Findings  : {med_count}\n")
        sys.stderr.write(f"Low Findings     : {low_count}\n")
        sys.stderr.write("--------------------------------------------------------\n")
        for f in findings:
            loc = f" ({f.file_path}:{f.line_number})" if f.file_path and f.line_number else ""
            sys.stderr.write(f"[{f.severity}] {f.title}{loc}\n")
            sys.stderr.write(f"  Category: {f.category}\n")
            sys.stderr.write(f"  Reason  : {f.description}\n")
            sys.stderr.write(f"  Fix     : {f.remediation}\n\n")
        sys.stderr.write("========================================================\n")

    if not passed and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
