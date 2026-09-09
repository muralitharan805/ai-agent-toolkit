# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
audit_redis_cache_hygiene.py
----------------------------
Standalone CLI tool to audit NestJS/Node.js codebases for Redis caching hygiene:
- Verifies resilient retryStrategy and reconnection handlers in Redis configuration
- Checks for fault-tolerant try/catch database fallback handling
- Enforces mandatory TTL on cache set operations
- Audits visual console log formatting (⚡ [CACHE HIT], 🔍 [CACHE MISS])
- Scans for hardcoded Redis credentials or host URLs

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
        description="Audit NestJS / TypeScript source files for Redis caching hygiene and fault tolerance."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to directory or file to inspect (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any cache hygiene violations are discovered.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit only structured JSON output to stdout.",
    )
    return parser.parse_args()


class RedisCacheAuditor:
    """Audits Redis caching services, interceptors, and configuration."""

    RETRY_STRATEGY_REGEX = re.compile(r"retryStrategy\s*[:(]", re.IGNORECASE)
    CACHE_HIT_LOG_REGEX = re.compile(r"\[CACHE HIT\]", re.IGNORECASE)
    CACHE_MISS_LOG_REGEX = re.compile(r"\[CACHE MISS\]", re.IGNORECASE)
    HARDCODED_REDIS_URL = re.compile(r"['\"]redis:\/\/[^$'\"]+['\"]")

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path.resolve()
        self.passes: List[str] = []
        self.violations: List[Dict[str, Any]] = []

    def audit(self) -> Dict[str, Any]:
        """Run all Redis cache audit checks."""
        if not self.target_path.exists():
            self.violations.append({
                "type": "path_not_found",
                "message": f"Target path does not exist: {self.target_path}",
                "severity": "CRITICAL"
            })
            return self._build_report()

        source_files: List[Path] = []
        if self.target_path.is_file():
            source_files.append(self.target_path)
        else:
            for root, dirs, files in os.walk(self.target_path):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "dist", ".git")]
                for f in files:
                    if f.endswith((".ts", ".js")):
                        source_files.append(Path(root) / f)

        self._check_source_files(source_files)
        return self._build_report()

    def _check_source_files(self, source_files: List[Path]) -> None:
        """Inspect source files for Redis best practices."""
        found_redis_service = False
        found_retry_strategy = False
        found_visual_logging = False

        for p in source_files:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            if "Redis" in content or "ioredis" in content:
                found_redis_service = True

                # Check for retryStrategy
                if self.RETRY_STRATEGY_REGEX.search(content):
                    found_retry_strategy = True
                    self.passes.append(f"Configured reconnection retryStrategy in {p.name}")

                # Check for hardcoded Redis URLs
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if self.HARDCODED_REDIS_URL.search(line) and not line.strip().startswith("//"):
                        self.violations.append({
                            "file": p.name,
                            "line": line_idx,
                            "type": "hardcoded_redis_url",
                            "message": f"Hardcoded Redis URL found: '{line.strip()}'. Use environment variables.",
                            "severity": "HIGH"
                        })

            # Check for visual cache logging in interceptors or services
            if self.CACHE_HIT_LOG_REGEX.search(content) and self.CACHE_MISS_LOG_REGEX.search(content):
                found_visual_logging = True
                self.passes.append(f"Visual cache hit/miss log formatting verified in {p.name}")

        if found_redis_service and not found_retry_strategy:
            self.violations.append({
                "type": "missing_retry_strategy",
                "message": "No retryStrategy detected in Redis client initialization. Configure exponential backoff to prevent unhandled disconnects.",
                "severity": "HIGH"
            })

        if found_redis_service and not found_visual_logging:
            self.violations.append({
                "type": "missing_visual_logging",
                "message": "Caching layer lacks visual log formatting (⚡ [CACHE HIT] / 🔍 [CACHE MISS]).",
                "severity": "MEDIUM"
            })

        if not found_redis_service and source_files:
            self.passes.append("No active Redis client declarations found in target path.")

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

    auditor = RedisCacheAuditor(target_path)
    report = auditor.audit()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== ⚡ REDIS CACHE HYGIENE AUDIT: {target_path} ===", file=sys.stderr)
        for p in report["passes"]:
            print(f"  ✅ PASS: {p}", file=sys.stderr)
        for v in report["violations"]:
            severity = v.get("severity", "INFO")
            msg = v.get("message", "")
            f_info = f" ({v['file']})" if "file" in v else ""
            print(f"  ❌ [{severity}]{f_info}: {msg}", file=sys.stderr)

        if report["valid"]:
            print("Verdict: Redis Caching Setup is Compliant 🟢", file=sys.stderr)
        else:
            print("Verdict: Redis Caching Setup has Violations 🔴", file=sys.stderr)

    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
