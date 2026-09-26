"""CSV is a self-contained discovery ledger; no dossier files are created."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "shared/problem-discovery/skills/scripts/discovery_csv.py"


@unittest.skipUnless(SCRIPT.exists(), "legacy monolithic problem-discovery CSV suite was removed")
class CsvFirstTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.output = self.folder / "discovery_matrix.csv"
        self.input = self.folder / "input.json"

    def run_cli(self, candidates, expect=0):
        self.input.write_text(json.dumps(candidates), encoding="utf-8")
        process = subprocess.run([sys.executable, str(SCRIPT), "--input-json", str(self.input),
                                  "--output", str(self.output), "--json"],
                                 text=True, capture_output=True)
        self.assertEqual(process.returncode, expect, process.stderr)
        return process

    def read_rows(self):
        with self.output.open(encoding="utf-8", newline="") as source:
            return list(csv.DictReader(source))

    def test_single_file_upsert_and_ranking(self):
        alpha = {"id": "PROB-A", "title": "Reconcile dispatch notes", "domain": "Logistics",
                 "track": "commercial", "evidence_level": 5,
                 "scores": {"frequency": 5, "severity": 5, "workaround": 5, "wtp": 5,
                            "decision_maker": 5, "feasibility": 5, "discrepancy": 5},
                 "research_notes": "Follow up with operators"}
        beta = {"id": "PROB-B", "title": "Repair batch mismatch", "domain": "Manufacturing",
                "track": "commercial", "evidence_level": 1,
                "scores": {"frequency": 4, "severity": 4, "workaround": 4, "wtp": 4,
                           "decision_maker": 4, "feasibility": 4, "discrepancy": 4},
                "experiment_outcome": "great success", "evidence_sources": ["https://example.org/report"]}
        result = json.loads(self.run_cli([alpha, beta]).stdout)
        self.assertEqual(result["total_candidates"], 2)
        self.assertFalse(result["markdown_generated"])
        self.assertEqual({file.name for file in self.folder.iterdir()}, {"input.json", "discovery_matrix.csv"})
        rows = self.read_rows()
        self.assertEqual([row["candidate_id"] for row in rows], ["PROB-B", "PROB-A"])
        self.assertEqual(rows[0]["status"], "UNVERIFIED")
        self.assertEqual(rows[0]["total_score"], "28")
        self.assertEqual(rows[1]["total_score"], "0")
        self.assertEqual(rows[0]["evidence_verified"], "false")
        self.assertEqual(json.loads(rows[0]["evidence_sources"]), ["https://example.org/report"])
        self.run_cli({**alpha, "evidence_level": 1})
        rows = self.read_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["candidate_id"], "PROB-A")
        self.assertEqual(rows[0]["research_notes"], "Follow up with operators")
        self.assertEqual([row["rank"] for row in rows], ["1", "2"])

    def test_incompatible_existing_csv_is_not_overwritten(self):
        self.output.write_text("candidate_id,legacy_notes\nPROB-A,important\n", encoding="utf-8")
        before = self.output.read_bytes()
        self.run_cli({"id": "PROB-A"}, expect=2)
        self.assertEqual(before, self.output.read_bytes())

    def test_ambiguous_ids_do_not_modify_previous_ledger(self):
        self.run_cli({"id": "PROB-A"})
        before = self.output.read_bytes()
        self.run_cli([{"id": "PROB-A"}, {"id": "PROB-A"}], expect=2)
        self.assertEqual(before, self.output.read_bytes())

    def test_spreadsheet_formula_protection(self):
        self.run_cli({"id": "=HYPERLINK(\"bad\")"}, expect=2)
        self.run_cli({"id": "PROB-SAFE", "title": "=cmd"})
        self.assertEqual(self.read_rows()[0]["problem_title"], "'=cmd")


if __name__ == "__main__":
    unittest.main()
