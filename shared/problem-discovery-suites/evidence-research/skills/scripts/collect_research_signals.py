#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
collect_research_signals.py
Deterministic search execution and signal collection dispatcher for the Evidence Research Skill.
Ingests a ResearchPlan, executes queries across authorized adapters (HN, GitHub, Reddit),
normalizes raw results, deduplicates canonical sources, and records to SQLite.
"""

import sys
import os
import re
import json
import sqlite3
import argparse
import importlib.util
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

DEFAULT_USER_AGENT = "ai-agent-toolkit/1.0 (ResearchEvidenceCollector; +https://github.com/muralitharan805/ai-agent-toolkit)"
REQUEST_TIMEOUT_SECONDS = 10

def _load_discovery_db_class():
    """Load the canonical discovery-state client without making suite directories import packages."""
    candidates = [
        Path(__file__).resolve().parents[3] / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path(__file__).resolve().parents[2] / "discovery-state" / "scripts" / "discovery_db.py",
        Path(__file__).resolve().parents[3] / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path(__file__).resolve().parents[4] / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path.cwd() / "shared" / "problem-discovery-suites" / "discovery-state" / "skills" / "scripts" / "discovery_db.py",
        Path.cwd() / ".agents" / "skills" / "discovery-state" / "scripts" / "discovery_db.py",
    ]
    for db_module_path in candidates:
        if db_module_path.exists():
            spec = importlib.util.spec_from_file_location("discovery_state_db", db_module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.DiscoveryDB
    raise RuntimeError(f"Unable to load discovery-state client from candidates: {[str(p) for p in candidates]}")

def clean_html_text(text: str) -> str:
    """Removes HTML tags and normalizes whitespace."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = clean.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#x27;", "'")
    return " ".join(clean.split())

def adapt_query_for_algolia(query: str) -> str:
    """Adapts a query for Hacker News Algolia keyword search."""
    cleaned = re.sub(r'site:\S+', '', query)
    cleaned = re.sub(r'filetype:\S+', '', cleaned)
    cleaned = cleaned.replace('"', '').replace(' OR ', ' ')
    return " ".join(cleaned.split())

def adapt_query_for_github(query: str) -> str:
    """Adapts a query for GitHub issues search."""
    cleaned = re.sub(r'site:\S+', '', query)
    cleaned = re.sub(r'filetype:\S+', '', cleaned)
    terms = [t.strip().replace('"', '') for t in cleaned.split() if t.strip()]
    keyword_clause = " ".join(terms[:4])
    return f'{keyword_clause} in:title,body is:issue'

def adapt_query_for_reddit(query: str) -> str:
    """Adapts a query for Reddit public search."""
    cleaned = re.sub(r'site:\S+', '', query)
    cleaned = re.sub(r'filetype:\S+', '', cleaned)
    terms = [t.strip().replace('"', '') for t in cleaned.split() if t.strip()]
    return " ".join(terms[:5])

def fetch_hn_signals(query: str, limit: int = 5) -> Dict[str, Any]:
    """Fetches discussions from Hacker News via Algolia API."""
    adapted = adapt_query_for_algolia(query)
    encoded = urllib.parse.urlencode({"query": adapted, "tags": "comment", "hitsPerPage": limit})
    url = f"https://hn.algolia.com/api/v1/search?{encoded}"

    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                hits = payload.get("hits", [])
                results = []
                for hit in hits:
                    comment_body = clean_html_text(hit.get("comment_text", ""))
                    if not comment_body:
                        continue
                    item_id = hit.get("objectID")
                    results.append({
                        "raw_result_id": f"HN-{item_id}",
                        "source_platform": "HACKERNEWS",
                        "source_url": f"https://news.ycombinator.com/item?id={item_id}" if item_id else "",
                        "title": hit.get("story_title") or f"Comment on HN item #{item_id}",
                        "excerpt": comment_body[:300] + ("..." if len(comment_body) > 300 else ""),
                        "author": hit.get("author", ""),
                        "published_at": hit.get("created_at"),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "inspection_status": "SNIPPET_ONLY"
                    })
                return {"status": "COMPLETED", "executed_query": adapted, "results": results, "error": None}
            return {"status": "FAILED", "executed_query": adapted, "results": [], "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "FAILED", "executed_query": adapted, "results": [], "error": str(e)}

def fetch_github_signals(query: str, limit: int = 5) -> Dict[str, Any]:
    """Fetches public GitHub issues discussing friction."""
    adapted = adapt_query_for_github(query)
    encoded = urllib.parse.urlencode({"q": adapted, "per_page": limit, "sort": "relevance"})
    url = f"https://api.github.com/search/issues?{encoded}"

    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                items = payload.get("items", [])
                results = []
                for item in items:
                    raw_body = clean_html_text(item.get("body") or "")
                    results.append({
                        "raw_result_id": f"GH-{item.get('id')}",
                        "source_platform": "GITHUB",
                        "source_url": item.get("html_url", ""),
                        "title": item.get("title", ""),
                        "excerpt": raw_body[:300] + ("..." if len(raw_body) > 300 else ""),
                        "author": item.get("user", {}).get("login", ""),
                        "published_at": item.get("created_at"),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "inspection_status": "SNIPPET_ONLY"
                    })
                return {"status": "COMPLETED", "executed_query": adapted, "results": results, "error": None}
            return {"status": "FAILED", "executed_query": adapted, "results": [], "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "FAILED", "executed_query": adapted, "results": [], "error": str(e)}

def fetch_reddit_signals(query: str, limit: int = 5) -> Dict[str, Any]:
    """Fetches public Reddit discussions via public search endpoint."""
    adapted = adapt_query_for_reddit(query)
    encoded = urllib.parse.urlencode({"q": adapted, "limit": limit, "sort": "relevance"})
    url = f"https://www.reddit.com/search.json?{encoded}"

    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                children = payload.get("data", {}).get("children", [])
                results = []
                for child in children:
                    data = child.get("data", {})
                    selftext = clean_html_text(data.get("selftext", "") or data.get("title", ""))
                    permalink = data.get("permalink", "")
                    full_url = f"https://reddit.com{permalink}" if permalink else ""
                    results.append({
                        "raw_result_id": f"RD-{data.get('id')}",
                        "source_platform": "REDDIT",
                        "source_url": full_url,
                        "title": data.get("title", ""),
                        "excerpt": selftext[:300] + ("..." if len(selftext) > 300 else ""),
                        "author": data.get("author", ""),
                        "published_at": datetime.fromtimestamp(data.get("created_utc", 0), timezone.utc).isoformat() if data.get("created_utc") else None,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "inspection_status": "SNIPPET_ONLY"
                    })
                return {"status": "COMPLETED", "executed_query": adapted, "results": results, "error": None}
            return {"status": "FAILED", "executed_query": adapted, "results": [], "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "FAILED", "executed_query": adapted, "results": [], "error": str(e)}

def execute_plan_searches(
    plan: Dict[str, Any],
    providers: List[str],
    no_live_fetch: bool = False
) -> Dict[str, Any]:
    """Iterates through all research streams and search queries in a plan."""
    streams = plan.get("research_streams", [])
    research_run_id = plan.get("research_id") or "RUN-DEFAULT-001"
    run_status = "COMPLETED"
    run_limitations: List[str] = []
    stream_results: List[Dict[str, Any]] = []
    canonical_signals_map: Dict[str, Dict[str, Any]] = {}
    signal_counter = 1

    for stream in streams:
        stream_id = stream.get("stream_id", "RS-001")
        stream_name = stream.get("name", "Research Stream")
        queries = stream.get("search_queries", [])
        if not queries and "search_strategy" in stream:
            queries = [s.get("query") for s in stream.get("search_strategy", []) if s.get("query")]

        query_execution_records = []
        collected_signals = []

        for q_idx, original_query in enumerate(queries, start=1):
            query_id = f"{stream_id}-Q{q_idx:03d}"
            provider_runs = []

            for prov in providers:
                if no_live_fetch:
                    provider_runs.append({
                        "provider": prov,
                        "executed_query": original_query,
                        "status": "SKIPPED_UNAVAILABLE",
                        "result_count": 0,
                        "error": "Live fetch disabled"
                    })
                    run_status = "COMPLETED_WITH_GAPS"
                    continue

                res: Dict[str, Any] = {"status": "SKIPPED_UNAVAILABLE", "executed_query": original_query, "results": [], "error": "Provider not configured"}
                if prov == "hackernews":
                    res = fetch_hn_signals(original_query)
                elif prov == "github":
                    res = fetch_github_signals(original_query)
                elif prov == "reddit":
                    res = fetch_reddit_signals(original_query)

                status = res.get("status", "FAILED")
                if status != "COMPLETED":
                    run_status = "COMPLETED_WITH_GAPS"
                    run_limitations.append(f"Provider {prov} returned {status} for {query_id}: {res.get('error')}")

                provider_runs.append({
                    "provider": prov,
                    "executed_query": res.get("executed_query", original_query),
                    "status": status,
                    "result_count": len(res.get("results", [])),
                    "error": res.get("error")
                })

                # Deduplicate and register signals
                for raw_res in res.get("results", []):
                    url = raw_res.get("source_url")
                    if not url:
                        continue
                    if url in canonical_signals_map:
                        canonical = canonical_signals_map[url]
                        if query_id not in canonical["query_ids"]:
                            canonical["query_ids"].append(query_id)
                        if raw_res["raw_result_id"] not in canonical["raw_result_ids"]:
                            canonical["raw_result_ids"].append(raw_res["raw_result_id"])
                    else:
                        sig_id = f"SIG-{research_run_id}-{signal_counter:03d}"
                        signal_counter += 1
                        canonical = {
                            "signal_id": sig_id,
                            "raw_result_ids": [raw_res["raw_result_id"]],
                            "query_ids": [query_id],
                            "stream_id": stream_id,
                            "source": {
                                "platform": raw_res.get("source_platform", "WEB"),
                                "url": url,
                                "title": raw_res.get("title", ""),
                                "published_at": raw_res.get("published_at"),
                                "retrieved_at": raw_res.get("retrieved_at"),
                                "inspection_status": raw_res.get("inspection_status", "SNIPPET_ONLY")
                            },
                            "actor": {
                                "role": stream.get("operator", {}).get("title") if isinstance(stream.get("operator"), dict) else None,
                                "role_is_self_reported": False
                            },
                            "observation": {
                                "reported_issue": raw_res.get("excerpt", ""),
                                "reported_workaround": None,
                                "reported_frequency": None,
                                "reported_impact": None
                            },
                            "evidence": {
                                "classification": "UNASSESSED",
                                "independently_corroborated": False,
                                "human_audited_primary_evidence": False,
                                "verification_status": "UNVERIFIED"
                            },
                            "unknowns": ["Direct primary source inspection pending"]
                        }
                        canonical_signals_map[url] = canonical
                        collected_signals.append(canonical)

            query_execution_records.append({
                "query_id": query_id,
                "original_query": original_query,
                "provider_runs": provider_runs
            })

        stream_results.append({
            "stream_id": stream_id,
            "name": stream_name,
            "research_questions": stream.get("research_questions", []),
            "query_execution": query_execution_records,
            "signals": collected_signals,
            "alternative_evidence": [],
            "unknowns": plan.get("unknowns", []),
            "next_verification": [
                "Inspect full source content for accessible permalinks",
                "Verify actor authenticity and operational context"
            ]
        })

    return {
        "schema_version": "1.0",
        "research_run_id": research_run_id,
        "original_request": plan.get("original_request", ""),
        "scope": plan.get("scope", {}),
        "status": run_status if not no_live_fetch else "COMPLETED_WITH_GAPS",
        "research_results": stream_results,
        "research_limitations": run_limitations,
        "next_action": "EVALUATE_RESEARCH_SIGNALS"
    }

def save_signals_to_sqlite(db_path: str, signals_payload: Dict[str, Any]) -> int:
    """Persist normalized signals through the canonical discovery-state client."""
    research_id = signals_payload.get("research_run_id", "RUN-DEFAULT-001")
    signals: List[Dict[str, Any]] = []
    for stream in signals_payload.get("research_results", []):
        for sig in stream.get("signals", []):
            normalized = dict(sig)
            normalized["stream_id"] = stream.get("stream_id")
            signals.append(normalized)

    DiscoveryDB = _load_discovery_db_class()
    db = DiscoveryDB(db_path)
    count = db.save_evidence_signals(research_id, signals)
    sys.stderr.write(f"[INFO] Persisted {count} signals for {research_id} through discovery-state\n")
    return count

def main():
    parser = argparse.ArgumentParser(
        description="Search execution and signal collection dispatcher for Evidence Research.",
        epilog="Examples:\n  python3 collect_research_signals.py --input plan.json --output signals.json\n  python3 collect_research_signals.py --sqlite-db data/discovery.db --run-id RUN-2026-001"
    )
    parser.add_argument("--input", help="Path to input ResearchPlan JSON file or inline string")
    parser.add_argument("--output", help="Path to output ResearchSignals JSON file")
    parser.add_argument("--sqlite-db", "--db", default=os.getenv("DISCOVERY_DB_PATH", "discovery.sqlite"), help="Path to SQLite database to read plan or persist signals")
    parser.add_argument("--run-id", help="Research run identifier")
    parser.add_argument("--providers", default="hackernews,github,reddit", help="Comma-separated provider adapters")
    parser.add_argument("--no-live-fetch", action="store_true", help="Execute in offline/mock mode without network calls")
    parser.add_argument("--json", action="store_true", default=True, help="Emit output JSON to stdout")

    args = parser.parse_args()

    plan: Optional[Dict[str, Any]] = None

    # Load from SQLite or input file
    db_path = args.sqlite_db
    if args.run_id and not args.input and db_path and os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT plan_json FROM research_runs WHERE research_id = ?", (args.run_id,))
            row = cursor.fetchone()
            if not row or not row[0]:
                sys.stderr.write(f"[ERROR] No plan_json found for run {args.run_id} in {db_path}\n")
                sys.exit(1)
            plan = json.loads(row[0])
        finally:
            conn.close()
    elif args.input:
        try:
            if os.path.isfile(args.input):
                with open(args.input, "r", encoding="utf-8") as f:
                    plan = json.load(f)
            else:
                plan = json.loads(args.input)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load --input: {e}\n")
            sys.exit(1)
    else:
        sys.stderr.write("[ERROR] Either --input or both --sqlite-db (valid db file) and --run-id must be provided.\n")
        sys.exit(1)

    providers = [p.strip().lower() for p in args.providers.split(",") if p.strip()]
    signals_output = execute_plan_searches(plan, providers, no_live_fetch=args.no_live_fetch)

    if db_path and os.path.exists(db_path):
        save_signals_to_sqlite(db_path, signals_output)

    formatted_json = json.dumps(signals_output, indent=2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_json + "\n")
            sys.stderr.write(f"[INFO] Saved signals to {args.output}\n")
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to write --output file: {e}\n")
            sys.exit(1)

    sys.stdout.write(formatted_json + "\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
