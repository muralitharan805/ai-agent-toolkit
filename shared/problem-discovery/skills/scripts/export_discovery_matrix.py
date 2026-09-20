# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build a research ledger from Obsidian dossiers without inventing validation."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import sys
from typing import Any

FIELDS = ["rank", "score", "track", "classification", "status", "evidence_verified",
          "experiment_completed", "experiment_passed", "folder", "domain", "title",
          "target_role", "what_is_broken", "workaround", "cost_and_risk",
          "tier1_free_utility", "tier2_micro_utility", "tier3_micro_saas",
          "candidate_id", "filename"]


def _scalar(value: str) -> str:
    value = value.strip()
    try:
        decoded = json.loads(value)
        return str(decoded) if not isinstance(decoded, (dict, list)) else value
    except json.JSONDecodeError:
        return value.strip("'\"")


def _frontmatter(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---", 4)
    if end < 0:
        return {}
    result = {}
    for line in content[4:end].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, value = line.split(":", 1)
            result[k.strip()] = _scalar(value)
    return result


def _match(content: str, *patterns: str) -> str:
    for pattern in patterns:
        result = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        if result:
            return re.sub(r"[\*`]", "", result.group(1)).strip()
    return ""


def parse_discovery_file(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    fm = _frontmatter(content)
    score_text = fm.get("priority_score") or _match(content, r"\*\*TOTAL RESEARCH PRIORITY\*\*\s*\|\s*\*\*(\d+)\s*/\s*35", r"(\d+)\s*/\s*35", r"total_score:\s*(\d+)")
    score = int(score_text) if score_text.isdigit() else 0
    if not 0 <= score <= 35:
        raise ValueError(f"Invalid research score in {path}")
    status = fm.get("validation_status") or _match(content, r"\*\*Status\*\*:\s*([^\n]+)") or "UNVERIFIED"
    classification = fm.get("classification") or _match(content, r"\*\*Classification\*\*:\s*([^\n]+)")
    # An older note with score >= 28 but no experiment is never automatically promoted.
    if not classification:
        classification = ("RESEARCH PRIORITY (LEGACY / UNVERIFIED)" if score >= 23
                          else "LOW RESEARCH PRIORITY (LEGACY / UNVERIFIED)")
    # Legacy labels were derived from score alone and cannot be treated as verified findings.
    if classification in ("TIER-1 GOLD", "TIER_1_GOLD_BUILD"):
        classification = "RESEARCH PRIORITY (LEGACY / UNVERIFIED)"
    if status.upper() in ("VALIDATED", "EXPERIMENT_VALIDATED") and not (
        fm.get("evidence_verified", "").lower() == "true"
        and fm.get("experiment_completed", "").lower() == "true"
        and fm.get("experiment_passed", "").lower() == "true"
    ):
        status = "UNVERIFIED_LEGACY_CLAIM"
        classification = "RESEARCH PRIORITY (LEGACY / UNVERIFIED)"
    candidate_id = fm.get("candidate_id") or _match(content, r"\*\*Problem ID\*\*:\s*([^\n]+)") or path.stem
    title = fm.get("title") or _match(content, r"^#\s*📋?\s*Problem Discovery Log:\s*([^\n]+)", r"^#\s*Problem Discovery Log:\s*([^\n]+)") or candidate_id
    return {
        "rank": 0, "score": score,
        "track": fm.get("track", "commercial"), "classification": classification,
        "status": status, "evidence_verified": fm.get("evidence_verified", "unknown"),
        "experiment_completed": fm.get("experiment_completed", "unknown"),
        "experiment_passed": fm.get("experiment_passed", "unknown"),
        "folder": "archive" if "archive" in path.parts else "active",
        "domain": fm.get("domain") or _match(content, r"\*\*Domain\*\*:\s*([^\n]+)") or "General",
        "title": title,
        "target_role": fm.get("target_role") or _match(content, r"\*\*Target (?:Audience|role)\*\*:\s*([^\n]+)"),
        "what_is_broken": _match(content, r"\*\*What is broken\?\*\*:\s*([^\n]+)"),
        "workaround": _match(content, r"\*\*Current Workaround\*\*:\s*([^\n]+)"),
        "cost_and_risk": _match(content, r"\*\*Cost of Inaction\*\*:\s*([^\n]+)"),
        "tier1_free_utility": _match(content, r"Tier 1[^:]*:\s*([^\n]+)"),
        "tier2_micro_utility": _match(content, r"Tier 2[^:]*:\s*([^\n]+)"),
        "tier3_micro_saas": _match(content, r"Tier 3[^:]*:\s*([^\n]+)"),
        "candidate_id": candidate_id, "filename": path.name,
    }


def generate_matrix(directory: Path, output_csv: Path) -> list[dict[str, Any]]:
    """Rebuild (not append) CSV from active and archived dossiers; atomic replacement."""
    if not directory.is_dir():
        raise FileNotFoundError(f"Discovery directory does not exist: {directory}")
    records = []
    for path in sorted(directory.rglob("*.md")):
        if path.name.lower() in ("readme.md", "index.md"):
            continue
        row = parse_discovery_file(path)
        if "archive" in path.parts:
            row["status"] = "ARCHIVED"
        records.append(row)
    records.sort(key=lambda x: (x["folder"] != "active", -x["score"], x["candidate_id"]))
    for rank, record in enumerate(records, start=1):
        record["rank"] = rank
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    temp = output_csv.with_suffix(output_csv.suffix + ".tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)
        temp.replace(output_csv)
    finally:
        temp.unlink(missing_ok=True)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Export discovery dossiers into a research-priority CSV")
    parser.add_argument("--dir", required=True, help="Directory containing discovery logs (no machine-specific default)")
    parser.add_argument("--output", help="CSV output path; defaults to <dir>/discovery_matrix.csv")
    args = parser.parse_args()
    folder = Path(args.dir).expanduser()
    output = Path(args.output).expanduser() if args.output else folder / "discovery_matrix.csv"
    try:
        records = generate_matrix(folder, output)
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    print(f"Exported {len(records)} candidate(s) to {output}")


if __name__ == "__main__":
    main()
