# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Bootstrap wrapper for the canonical Problem Discovery SQLite store."""

from __future__ import annotations

import argparse
import json
import os

from discovery_db import DiscoveryDB


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Problem Discovery SQLite database")
    parser.add_argument("--db", default=os.getenv("DISCOVERY_DB_PATH", "discovery.sqlite"), help="Path to SQLite database")
    args = parser.parse_args()
    DiscoveryDB(args.db)
    print(json.dumps({"status": "BOOTSTRAPPED", "db_path": args.db}))


if __name__ == "__main__":
    main()
