#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

"""
scan_duplicates.py
Scans ai-agent-toolkit for duplicate, overlapping, or fragmented skills and rules.
Identifies candidates for consolidation and safe pruning.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Set
from collections import defaultdict


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for duplicate scanning."""
    parser = argparse.ArgumentParser(
        description="Scan ai-agent-toolkit for duplicate, overlapping, or fragmented skills and rules.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/scan_duplicates.py\n"
            "  python3 scripts/scan_duplicates.py --json\n"
            "  python3 scripts/scan_duplicates.py frameworks/angular"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target_path", nargs="?", default=".", help="Path to scan (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit report as machine-readable JSON to stdout")
    return parser.parse_args()


def get_topic_cluster_key(name: str) -> str:
    """Extract primary semantic cluster key from a skill or rule name."""
    clean = name.lower().replace(".md", "")
    for suffix in ["-rules", "-rule", "-standards"]:
        if clean.endswith(suffix):
            clean = clean[:-len(suffix)]
            break
    parts = clean.split("-")
    if len(parts) >= 3 and parts[1] in {"enterprise", "cloud", "core"}:
        return f"{parts[0]}-{parts[1]}-{parts[2]}"
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return parts[0]


def scan_skills_and_rules(target_dir: str) -> Dict[str, Any]:
    """Scan directory tree and group components by topic clusters."""
    skills_by_name: Dict[str, List[str]] = defaultdict(list)
    rules_by_name: Dict[str, List[str]] = defaultdict(list)
    topic_clusters: Dict[str, List[str]] = defaultdict(list)

    for root, dirs, files in os.walk(target_dir):
        parts = root.split(os.sep)
        # Never scan generators, sync targets (.agents), or internal auxiliary directories
        if any(p in parts for p in ["shared/generators", ".agents", "evals", "references", "assets", "scripts", "examples"]):
            continue

        if "SKILL.md" in files:
            skill_name = os.path.basename(root)
            skills_by_name[skill_name].append(root)
            cluster_key = get_topic_cluster_key(skill_name)
            topic_clusters[cluster_key].append(root)

        if "rules" in parts:
            for f in files:
                if f.endswith(".md"):
                    rule_name = f[:-3]
                    rule_path = os.path.join(root, f)
                    rules_by_name[rule_name].append(rule_path)
                    cluster_key = get_topic_cluster_key(rule_name)
                    topic_clusters[cluster_key].append(rule_path)

    # Detect exact duplicates
    exact_duplicates = {
        name: paths for name, paths in {**skills_by_name, **rules_by_name}.items() if len(paths) > 1
    }

    # Detect clusters with multiple related items (consolidation candidates)
    consolidation_candidates = {
        cluster: items for cluster, items in topic_clusters.items() if len(items) > 1 and cluster not in exact_duplicates
    }

    return {
        "target": target_dir,
        "exact_duplicates": exact_duplicates,
        "consolidation_candidates": consolidation_candidates,
        "total_skills_scanned": sum(len(paths) for paths in skills_by_name.values()),
        "total_rules_scanned": sum(len(paths) for paths in rules_by_name.values()),
    }


def main() -> int:
    """Execute duplicate scan and report findings."""
    args = parse_arguments()
    target_path = os.path.abspath(args.target_path)

    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{args.target_path}' does not exist.\n")
        return 1

    report = scan_skills_and_rules(target_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        print("\n" + "=" * 56)
        print("🔍 AI AGENT TOOLKIT CONSOLIDATION & DUPLICATE SCAN")
        print("=" * 56)
        print(f"Target Directory     : {target_path}")
        print(f"Total Skills Scanned : {report['total_skills_scanned']}")
        print(f"Total Rules Scanned  : {report['total_rules_scanned']}")
        print("-" * 56)

        if report["exact_duplicates"]:
            print("🚨 EXACT DUPLICATES FOUND (Immediate Action Needed):")
            for name, paths in report["exact_duplicates"].items():
                print(f"  - '{name}':")
                for p in paths:
                    print(f"      ➔ {os.path.relpath(p, target_path)}")
        else:
            print("✅ Exact Duplicates   : Zero found (Clean)")

        if report["consolidation_candidates"]:
            print("\n📦 RELATED TOPIC CLUSTERS (Consolidation Candidates):")
            for cluster, items in sorted(report["consolidation_candidates"].items()):
                print(f"  Cluster '{cluster}' ({len(items)} items):")
                for itm in items:
                    print(f"    • {os.path.relpath(itm, target_path)}")
        else:
            print("\n✅ Topic Clusters     : Cleanly separated (No obvious fragmentation)")

        print("=" * 56 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
