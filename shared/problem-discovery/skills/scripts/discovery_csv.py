#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Score candidate JSON and maintain ONE CSV ledger; no Markdown files are generated.

This is a CSV snapshot of the scorer's results, not independent validation of claims.
Artifact paths/URLs are references; sensitive evidence stays outside the CSV/repo.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

from score_problem_candidate import evaluate_candidate, parse_candidate_dict

DIMENSIONS = ("frequency", "severity", "workaround", "wtp", "decision_maker", "feasibility", "discrepancy")
JSON_FIELDS = ("evidence_sources", "evidence_artifacts", "evidence_records", "workflow_14_nodes",
               "stop_checks_triggered", "experiment", "solution_constraints", "smallest_solution")
FIELDS = ("candidate_id", "problem_title", "domain", "track", "rank", "total_score",
          "classification", "status", "evidence_level", "evidence_verified",
          "experiment_completed", "experiment_passed", *DIMENSIONS, *JSON_FIELDS,
          "recommended_action", "research_notes", "updated_at")


def _json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _safe_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or any(c in value for c in "\n\r\x00"):
        raise ValueError("Every candidate needs a nonblank, single-line id")
    # Spreadsheet applications can interpret leading formula characters as executable formulas.
    if value.lstrip().startswith(("=", "+", "-", "@")):
        raise ValueError("Candidate id must not start with a spreadsheet formula character")
    return value.strip()


def _safe_cell(value: Any) -> str:
    text = str(value if value is not None else "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def make_row(payload: dict[str, Any], defaults: argparse.Namespace) -> dict[str, str]:
    result = evaluate_candidate(**parse_candidate_dict(payload, defaults))
    result_id = _safe_id(result.candidate_id)
    evaluation = asdict(result)
    row = {column: "" for column in FIELDS}
    row.update({"candidate_id": result_id, "problem_title": _safe_cell(result.problem_title),
                "domain": _safe_cell(result.domain), "track": result.track,
                "total_score": str(result.total_score), "classification": result.classification,
                "status": result.status, "evidence_level": str(result.evidence_level),
                "evidence_verified": str(result.evidence_verified).lower(),
                "experiment_completed": str(result.experiment_completed).lower(),
                "experiment_passed": str(result.experiment_passed).lower(),
                "recommended_action": _safe_cell(result.recommended_action),
                "research_notes": _safe_cell(payload.get("research_notes", "")),
                "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    for dimension in DIMENSIONS:
        row[dimension] = str(result.scores[dimension])
    for column in JSON_FIELDS:
        value = payload.get(column) if column in ("evidence_records", "workflow_14_nodes", "solution_constraints") else evaluation.get(column)
        row[column] = _json_cell(value)
    return row


def write_ledger(csv_path: Path, candidate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Upsert by candidate_id, preserve unrelated rows, and atomically replace the CSV."""
    if not candidate_rows:
        raise ValueError("At least one candidate is required")
    ids = [row["candidate_id"] for row in candidate_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate candidate IDs in this batch; refusing ambiguous updates")
    existing: dict[str, dict[str, str]] = {}
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != list(FIELDS):
                raise ValueError(f"Existing CSV has an incompatible schema: {csv_path}. Back it up and migrate separately; existing data will not be overwritten.")
            for row in reader:
                key = _safe_id(row["candidate_id"])
                if key in existing:
                    raise ValueError(f"Duplicate existing candidate ID {key!r}; refusing to overwrite")
                existing[key] = row
    for row in candidate_rows:
        old = existing.get(row["candidate_id"])
        # Keep analyst-entered notes unless the new JSON explicitly includes replacements.
        if old and not row["research_notes"]:
            row["research_notes"] = old["research_notes"]
        existing[row["candidate_id"]] = row
    ordered = sorted(existing.values(), key=lambda row: (-int(row["total_score"]), row["candidate_id"]))
    for position, row in enumerate(ordered, 1):
        row["rank"] = str(position)  # Rank reflects research priority only, never validation.
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=".discovery-matrix-", suffix=".tmp", dir=csv_path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise")
            writer.writeheader()
            writer.writerows(ordered)
        os.replace(temp_name, csv_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return ordered


def main() -> None:
    parser = argparse.ArgumentParser(description="CSV-first problem discovery: one row per candidate, no per-candidate Markdown")
    parser.add_argument("--input-json", required=True, help="One candidate object or array of candidates")
    parser.add_argument("--output", default="discovery_matrix.csv", help="Single CSV ledger (default: ./discovery_matrix.csv)")
    parser.add_argument("--json", action="store_true", help="Print JSON summary as well as writing CSV")
    args = parser.parse_args()
    try:
        raw = json.loads(Path(args.input_json).expanduser().read_text(encoding="utf-8"))
        batch = raw if isinstance(raw, list) else [raw]
        if not batch or not all(isinstance(item, dict) for item in batch):
            raise ValueError("Input must be one candidate object or a nonempty array of candidate objects")
        defaults = argparse.Namespace(id="CANDIDATE-001", title="Operational Problem Candidate", domain="General",
                                      track="commercial", evidence_level=1)
        rows = [make_row(payload, defaults) for payload in batch]
        output_path = Path(args.output).expanduser()
        ledger = write_ledger(output_path, rows)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    result = {"csv": str(output_path), "updated": len(rows), "total_candidates": len(ledger),
              "candidate_ids": [row["candidate_id"] for row in rows], "markdown_generated": False}
    print(json.dumps(result, ensure_ascii=False) if args.json else
          f"Updated {len(rows)} candidate(s) in {output_path} ({len(ledger)} total); no Markdown generated.")


if __name__ == "__main__":
    main()
