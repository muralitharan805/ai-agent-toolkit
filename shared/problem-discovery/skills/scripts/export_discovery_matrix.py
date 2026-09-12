# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Export Discovery Matrix CLI & Indexer
Parses markdown discovery dossiers into a structured CSV/TSV matrix for Google Sheets and Excel analysis.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def clean_text(text: str) -> str:
    """Strip markdown formatting, brackets, asterisks, and excessive whitespace."""
    if not text:
        return ""
    text = re.sub(r"[\*\[\]`]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_discovery_file(file_path: Path) -> Dict[str, Any]:
    """Extract structured attributes from a single markdown discovery dossier."""
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    # 1. Candidate ID
    id_match = (
        re.search(r"\*\*Problem ID\*\*:\s*([^\n]+)", content)
        or re.search(r"candidate_id:\s*([^\n]+)", content)
        or re.search(r"^#\s*📋?\s*Problem Discovery Log:\s*([^\n]+)", content, re.MULTILINE)
    )
    candidate_id = id_match.group(1).strip() if id_match else file_path.stem
    candidate_id = clean_text(re.sub(r"^#\s*", "", candidate_id))

    # 2. Score
    score_match = (
        re.search(r"\*\*Score\*\*:\s*(\d+)", content)
        or re.search(r"(\d+)\s*/\s*35", content)
        or re.search(r"total_score:\s*(\d+)", content)
    )
    score = int(score_match.group(1)) if score_match else 0

    # 3. Classification
    if score >= 28:
        classification = "TIER-1 GOLD"
    elif score >= 23:
        classification = "QUALIFIED"
    else:
        classification = "REJECTED"

    # 4. Domain
    domain_match = (
        re.search(r"\*\*Domain\*\*:\s*([^\n]+)", content)
        or re.search(r"domain:\s*([^\n]+)", content)
    )
    domain = clean_text(domain_match.group(1)) if domain_match else "General B2B"

    # 5. Title
    title_match = (
        re.search(r"-\s*\*\*Title\*\*:\s*([^\n]+)", content)
        or re.search(r"^#\s*📋?\s*Problem Discovery Log:\s*([^\n]+)", content, re.MULTILINE)
        or re.search(r"Title\s*:\s*([^\n]+)", content)
        or re.search(r"\*\*What is broken\?\*\*:\s*([^\n]+)", content)
    )
    title = clean_text(title_match.group(1)) if title_match else candidate_id
    if title.startswith("PROB-") and len(title) > 20:
        title = title.split("-", 3)[-1].replace("-", " ").title()

    # 6. Target Audience / Role
    aud_match = (
        re.search(r"\*\*Target (?:Audience|role|Role)\*\*:\s*([^\n]+)", content)
        or re.search(r"\|\s*\*\*1\.?\s*Actor\*\*\s*\|\s*([^\|]+)", content)
        or re.search(r"target_role:\s*([^\n]+)", content)
    )
    target_role = clean_text(aud_match.group(1)) if aud_match else "Business Operator"

    # 7. What is Broken / Core Friction
    broken_match = (
        re.search(r"-\s*\*\*What is broken\?\*\*:\s*([^\n]+)", content)
        or re.search(r"\*\*Quote\s*/\s*Friction\*\*:\s*([^\n]+)", content)
        or re.search(r"-\s*\*Fact\*:\s*([^\n]+)", content)
    )
    broken = clean_text(broken_match.group(1)) if broken_match else ""

    # 8. Current Workaround
    workaround_match = (
        re.search(r"\*\*Current Workaround\*\*:\s*([^\n]+)", content)
        or re.search(r"-\s*\*\*Workaround Tools\*\*:\s*([^\n]+)", content)
        or re.search(r"Workaround Strength\s*\|\s*\d+\s*\|\s*([^\|\n]+)", content)
    )
    workaround = clean_text(workaround_match.group(1)) if workaround_match else "Manual Spreadsheets"

    # 9. Cost / Risk of Inaction
    risk_match = (
        re.search(r"\*\*Cost of Inaction\*\*:\s*([^\n]+)", content)
        or re.search(r"-\s*\*\*Cost of Inaction\*\*:\s*([^\n]+)", content)
        or re.search(r"\|\s*\*\*13\.?\s*Risk\*\*\s*\|\s*([^\|]+)", content)
        or re.search(r"\|\s*\*\*12\.?\s*Cost\*\*\s*\|\s*([^\|]+)", content)
    )
    risk = clean_text(risk_match.group(1)) if risk_match else ""

    # 10. Status
    status_match = (
        re.search(r"\*\*Status\*\*:\s*([^\n]+)", content)
        or re.search(r"status:\s*([^\n]+)", content)
    )
    status = clean_text(status_match.group(1)) if status_match else "EXPLORING"

    # 11. 3-Tier Wedges
    tier1_match = (
        re.search(r"Tier 1\s*(?:\([^\)]+\))?:\s*([^\n]+)", content)
        or re.search(r"Tier 1[^\n]*\n-\s*\*\*Architecture\*\*:[^\n]*\n-\s*\*\*Functionality\*\*:[^\n]*\n\s*-\s*([^\n]+)", content)
    )
    tier1 = clean_text(tier1_match.group(1)) if tier1_match else "Client-side Web Tool"

    tier2_match = (
        re.search(r"Tier 2\s*(?:\([^\)]+\))?:\s*([^\n]+)", content)
    )
    tier2 = clean_text(tier2_match.group(1)) if tier2_match else "CLI / Workflow Extension"

    tier3_match = (
        re.search(r"Tier 3\s*(?:\([^\)]+\))?:\s*([^\n]+)", content)
    )
    tier3 = clean_text(tier3_match.group(1)) if tier3_match else "Micro-SaaS ($49-$99/mo)"

    # Dimension Scores if available
    def extract_dim(pattern: str) -> str:
        m = re.search(pattern, content)
        return m.group(1).strip() if m else ""

    return {
        "candidate_id": candidate_id,
        "score": score,
        "classification": classification,
        "domain": domain,
        "title": title,
        "target_role": target_role,
        "what_is_broken": broken,
        "workaround": workaround,
        "cost_and_risk": risk,
        "tier1_free_utility": tier1,
        "tier2_micro_utility": tier2,
        "tier3_micro_saas": tier3,
        "status": status,
        "filename": file_path.name,
    }


def generate_matrix(directory: Path, output_csv: Path) -> List[Dict[str, Any]]:
    """Scan all markdown files (including archive/) in directory and write structured CSV ledger."""
    md_files = sorted(directory.rglob("*.md"))
    records = []

    for f in md_files:
        # Skip readme or index files
        if f.name.lower() in ("readme.md", "index.md"):
            continue
        try:
            item = parse_discovery_file(f)
            # Detect if file is inside an archive subdirectory
            is_archived = "archive" in f.parts or f.parent.name == "archive"
            item["folder"] = "archive" if is_archived else "active"
            if is_archived:
                item["status"] = "ARCHIVED"
            records.append(item)
        except Exception as exc:
            sys.stderr.write(f"Warning: Failed to parse {f.name}: {exc}\n")

    # Sort records: Active candidates first (sorted by score desc), followed by Archived (by score desc)
    records.sort(key=lambda x: (x["folder"] != "active", -x["score"]))

    # Add Rank
    for idx, r in enumerate(records):
        r["rank"] = idx + 1

    fieldnames = [
        "rank",
        "score",
        "classification",
        "status",
        "folder",
        "domain",
        "title",
        "target_role",
        "what_is_broken",
        "workaround",
        "cost_and_risk",
        "tier1_free_utility",
        "tier2_micro_utility",
        "tier3_micro_saas",
        "candidate_id",
        "filename",
    ]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    sys.stderr.write(f"✅ Generated Discovery Matrix ({len(records)} candidates: {sum(1 for r in records if r['folder'] == 'active')} active, {sum(1 for r in records if r['folder'] == 'archive')} archived) -> {output_csv}\n")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Export discovery log dossiers into a structured CSV for Google Sheets / Excel.")
    parser.add_argument("--dir", default="/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs", help="Directory containing markdown discovery dossiers.")
    parser.add_argument("--output", default="/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/discovery_matrix.csv", help="Output CSV file path.")
    args = parser.parse_args()

    input_dir = Path(args.dir)
    if not input_dir.exists():
        sys.stderr.write(f"Error: Directory {input_dir} does not exist.\n")
        sys.exit(1)

    out_file = Path(args.output)
    records = generate_matrix(input_dir, out_file)
    print(f"Successfully exported {len(records)} candidates to {out_file}")


if __name__ == "__main__":
    main()
