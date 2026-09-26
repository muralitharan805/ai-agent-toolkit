# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
FTS5 Full-Text Search CLI tool for Problem Discovery State.
Enables instant keyword and semantic-token search across runs, candidates, and collected evidence signals.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def search_discovery(db_path: str, query: str, entity_type: str | None = None) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        if entity_type:
            cursor.execute("""
                SELECT entity_id, entity_type, title_or_issue, body_text, rank
                FROM discovery_fts
                WHERE discovery_fts MATCH ? AND entity_type = ?
                ORDER BY rank
            """, (query, entity_type.upper()))
        else:
            cursor.execute("""
                SELECT entity_id, entity_type, title_or_issue, body_text, rank
                FROM discovery_fts
                WHERE discovery_fts MATCH ?
                ORDER BY rank
            """, (query,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Full-Text Search across Problem Discovery SQLite database.")
    parser.add_argument("query", help="Search query string (supports FTS5 syntax, e.g., 'reconciliation OR dispute')")
    parser.add_argument("--db", default="discovery.sqlite", help="Path to SQLite database")
    parser.add_argument("--type", choices=["RUN", "CANDIDATE", "SIGNAL"], help="Filter by entity type")

    args = parser.parse_args()

    results = search_discovery(args.db, args.query, args.type)
    sys.stderr.write(f"[INFO] Found {len(results)} matches for query '{args.query}'\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
