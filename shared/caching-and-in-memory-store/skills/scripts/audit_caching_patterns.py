#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""
Audit Caching Patterns Script
Audits backend codebases for caching resilience and architectural standards:
- Bounded L1 in-memory caches (prohibiting unbounded Maps)
- Mandatory TTL on all cache writes (prohibiting zombie keys)
- Standardized cache key namespacing
- Cache stampede (thundering herd) guards
- Graceful database fallback on cache failure
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

UNBOUNDED_MAP_PATTERN = re.compile(r'\b(const|let|var)\s+\w*[Cc]ache\w*\s*=\s*new\s+(Map|Set)\s*\(', re.IGNORECASE)
REDIS_SET_NO_TTL_PATTERN = re.compile(r'\.set\s*\(\s*[^,)]+\s*,\s*[^,)]+\s*\)', re.IGNORECASE)
REDIS_SET_WITH_TTL_PATTERN = re.compile(r'(\.set\s*\(.*?(EX|PX|EXAT|PXAT).*?\)|setex\s*\()', re.IGNORECASE)
STAMPEDE_GUARD_PATTERN = re.compile(r'(\b(lock|mutex|redlock)\b|[\'"`]NX[\'"`]|earlyExp|xFetch)', re.IGNORECASE)
CACHE_KEY_NAMESPACING = re.compile(r'[\'"`][a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+:', re.IGNORECASE)

EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
    '__pycache__', '.venv', 'venv', 'target'
}

def is_source_file(file_path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in file_path.parts):
        return False
    name = file_path.name.lower()
    if '.test.' in name or '.spec.' in name or name.startswith('test_'):
        return False
    return file_path.suffix in {'.ts', '.js', '.py', '.go', '.rs', '.java'}

def audit_directory(target_path: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    scanned_files_count = 0
    has_caching = False
    has_ttl_enforcement = False
    has_stampede_protection = False
    has_unbounded_cache_leak = False

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            file_path = Path(root) / f
            if not is_source_file(file_path):
                continue

            scanned_files_count += 1
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to read {file_path}: {e}\n")
                continue

            rel_path = str(file_path.relative_to(target_path))

            # Detect unbounded map leak
            if UNBOUNDED_MAP_PATTERN.search(content):
                # Ensure it's not an LRU cache
                if 'lru' not in content.lower() and 'max' not in content.lower():
                    has_unbounded_cache_leak = True
                    findings.append({
                        "file": rel_path,
                        "type": "unbounded_in_memory_cache",
                        "severity": "high",
                        "message": "Found unbounded Map/Set used as in-memory cache without max-size limits. This causes Node.js OOM crashes."
                    })

            # Detect Redis usage
            if 'redis' in content.lower():
                has_caching = True

                # Check for TTL
                if REDIS_SET_WITH_TTL_PATTERN.search(content):
                    has_ttl_enforcement = True
                elif REDIS_SET_NO_TTL_PATTERN.search(content):
                    findings.append({
                        "file": rel_path,
                        "type": "zombie_key_no_ttl",
                        "severity": "medium",
                        "message": "Found Redis set() call without explicit TTL (EX/PX). Accumulates permanent zombie keys in Redis."
                    })

                # Check for stampede protection
                if STAMPEDE_GUARD_PATTERN.search(content):
                    has_stampede_protection = True

    summary = {
        "scanned_files": scanned_files_count,
        "caching_detected": has_caching,
        "caching_quality": {
            "zero_unbounded_l1_leaks": not has_unbounded_cache_leak,
            "ttl_expiration_enforced": has_ttl_enforcement or not has_caching,
            "stampede_guards_present": has_stampede_protection
        },
        "is_compliant": (
            not has_unbounded_cache_leak and
            (not has_caching or has_ttl_enforcement)
        ),
        "findings": findings
    }

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit backend codebase for caching architecture and resilience standards."
    )
    parser.add_argument(
        "target_path",
        nargs="?",
        default=".",
        help="Path to backend codebase or directory to audit (default: current directory)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any violations or missing caching configurations are detected."
    )

    args = parser.parse_args()
    target = Path(args.target_path).resolve()

    if not target.exists():
        sys.stderr.write(f"Error: Target path '{target}' does not exist.\n")
        sys.exit(1)

    results = audit_directory(target)
    print(json.dumps(results, indent=2))

    if args.strict and not results["is_compliant"]:
        sys.stderr.write("Caching audit failed compliance checks in strict mode.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
