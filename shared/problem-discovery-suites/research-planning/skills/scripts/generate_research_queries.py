#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
generate_research_queries.py
Deterministic query generator and SQLite runner helper for the Research Planning Skill.
Generates targeted queries across 5 search categories using the Atomic Search Unit standard.
Outputs structured JSON to stdout and diagnostics to stderr.
"""

import sys
import os
import re
import json
import sqlite3
import argparse
from typing import Dict, List, Any, Optional

CATEGORIES = ("community", "filetypes", "jobs", "software_gaps", "regional")

def clean_str(val: Optional[str]) -> str:
    """Strips whitespace and quotes from a string value."""
    if not val:
        return ""
    return val.strip().strip('"').strip("'")

def generate_stream_queries(
    domain: str,
    operator: Optional[str] = None,
    workflow: Optional[str] = None,
    friction: Optional[str] = None,
    region: Optional[str] = "any",
    category: Optional[str] = "all"
) -> Dict[str, List[str]]:
    """Generates source-specific search queries using atomic search units."""
    dom = clean_str(domain)
    target = f'"{dom}"' if " " in dom else dom
    op = clean_str(operator)
    actor_clause = f'"{op}"' if op else ""
    wf = clean_str(workflow)
    wf_clause = f'"{wf}"' if wf else ""
    fric = clean_str(friction)

    results: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES}

    # 1. Community & Practitioner Discussions
    community_queries = [
        f'site:reddit.com {target} {actor_clause} "takes hours"'.strip(),
        f'site:reddit.com {target} {wf_clause} "every month I have to"'.strip(),
        f'site:reddit.com {target} {actor_clause} "manually enter" spreadsheet'.strip(),
        f'site:reddit.com {target} {wf_clause} "there must be a better way" OR "tired of"'.strip(),
        f'site:news.ycombinator.com "Ask HN" {target} "how do you manage"'.strip(),
    ]
    if fric:
        community_queries.append(f'site:reddit.com {target} {actor_clause} "{fric}"'.strip())
    results["community"] = [re.sub(r'\s+', ' ', q) for q in community_queries]

    # 2. Public Filetypes & SOPs
    filetypes_queries = [
        f'filetype:xlsx template {target} {wf_clause} reconciliation'.strip(),
        f'filetype:xlsx template {target} tracking OR audit'.strip(),
        f'filetype:pdf "standard operating procedure" {target} "manually"'.strip(),
        f'filetype:docx checklist {target} "step by step"'.strip(),
        f'{target} {wf_clause} "submit" "portal" "Excel" "download CSV" "upload" "manually"'.strip(),
    ]
    results["filetypes"] = [re.sub(r'\s+', ' ', q) for q in filetypes_queries]

    # 3. Job Postings Hunting Glue-Work
    jobs_queries = [
        f'site:linkedin.com/jobs {target} {actor_clause} "manually reconcile"'.strip(),
        f'site:indeed.com {target} {actor_clause} "maintain spreadsheets" "weekly report"'.strip(),
        f'site:naukri.com {target} {actor_clause} "data entry" "multiple systems"'.strip(),
        f'site:indeed.com {target} "job description" "copy paste" OR "re-key"'.strip(),
    ]
    results["jobs"] = [re.sub(r'\s+', ' ', q) for q in jobs_queries]

    # 4. Software Gaps & Negative Reviews
    software_queries = [
        f'site:g2.com {target} "doesn\'t support"'.strip(),
        f'site:capterra.com {target} "too expensive" OR "cons"'.strip(),
        f'site:community.shopify.com {target} "manual workaround"'.strip(),
        f'site:wordpress.org/support/topic/ {target} "export" "manually"'.strip(),
        f'site:github.com/issues {target} "feature request" "export CSV"'.strip(),
    ]
    if wf:
        software_queries.append(f'site:g2.com {target} "{wf}" "workaround"'.strip())
    results["software_gaps"] = [re.sub(r'\s+', ' ', q) for q in software_queries]

    # 5. Regional Grievances & Local Context
    reg_clean = clean_str(region).lower()
    regional_queries: List[str] = []
    if reg_clean in ("in", "tn", "tamil nadu", "india"):
        regional_queries = [
            f'"{dom}" "Tamil Nadu" grievance report PDF',
            f'site:tn.gov.in "{dom}" "G.O." delay OR penalty',
            f'"{dom}" complaint application process Chennai OR Coimbatore',
            f'site:consumercomplaints.in "{dom}" delay OR refund',
            f'"{dom}" tender manual record system India',
        ]
    elif reg_clean in ("uk", "united kingdom", "england"):
        regional_queries = [
            f'site:gov.uk "{dom}" statutory guidance compliance',
            f'site:propertyindustryeye.com "{dom}" delay OR fall-through',
            f'site:estateagenttoday.co.uk "{dom}" compliance penalty',
            f'site:reddit.com/r/HousingUK "{dom}" delay',
        ]
    elif reg_clean in ("us", "usa", "united states"):
        regional_queries = [
            f'site:sec.gov "{dom}" compliance disclosure',
            f'site:regulations.gov "{dom}" public comment backlog',
            f'site:bbb.org "{dom}" complaint delay',
        ]
    else:
        regional_queries = [
            f'"{dom}" statutory compliance penalty report PDF',
            f'"{dom}" operational audit delay findings',
            f'"{dom}" complaint portal backlog',
        ]
    results["regional"] = [re.sub(r'\s+', ' ', q) for q in regional_queries]

    # Filter by category if requested
    cat_clean = clean_str(category).lower()
    if cat_clean and cat_clean != "all" and cat_clean in results:
        return {cat_clean: results[cat_clean]}

    return results

def init_sqlite_run(
    db_path: str,
    research_id: str,
    original_request: str,
    domain: str,
    scope_type: str = "BROAD",
    geography: Optional[str] = None,
    plan_dict: Optional[Dict[str, Any]] = None
) -> None:
    """Initializes a research run record in the SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_runs (
                research_id         TEXT PRIMARY KEY,
                original_request    TEXT NOT NULL,
                domain              TEXT NOT NULL,
                scope_type          TEXT DEFAULT 'BROAD',
                geography           TEXT,
                current_stage       TEXT NOT NULL DEFAULT 'PLANNED',
                status              TEXT NOT NULL DEFAULT 'ACTIVE',
                plan_json           TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        plan_str = json.dumps(plan_dict, indent=2) if plan_dict else None
        cursor.execute("""
            INSERT OR REPLACE INTO research_runs (
                research_id, original_request, domain, scope_type, geography, current_stage, status, plan_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'PLANNED', 'ACTIVE', ?, CURRENT_TIMESTAMP)
        """, (research_id, original_request, domain, scope_type, geography, plan_str))
        conn.commit()
        sys.stderr.write(f"[INFO] Initialized SQLite research run: {research_id} in {db_path}\n")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic query generator for the Research Planning Skill.",
        epilog="Examples:\n  python3 generate_research_queries.py --domain 'ecommerce logistics' --operator 'warehouse clerk'\n  python3 generate_research_queries.py --json-input plan.json"
    )
    parser.add_argument("--domain", help="Target domain or industry sector")
    parser.add_argument("--operator", help="Specific operational worker role")
    parser.add_argument("--workflow", help="Target operational workflow")
    parser.add_argument("--friction", help="Hypothesized or reported friction")
    parser.add_argument("--region", default="any", help="Geographic region anchor (default: any)")
    parser.add_argument("--category", choices=["all", "community", "filetypes", "jobs", "software_gaps", "regional"], default="all", help="Filter by search category")
    parser.add_argument("--json-input", help="Path to input JSON file or raw JSON string")
    parser.add_argument("--json", action="store_true", default=True, help="Emit output as JSON (default: True)")
    parser.add_argument("--sqlite-db", help="Path to SQLite database to save research_run")
    parser.add_argument("--run-id", help="Research run identifier (e.g. RUN-2026-001)")

    args = parser.parse_args()

    # Input parsing
    if args.json_input:
        try:
            if os.path.isfile(args.json_input):
                with open(args.json_input, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(args.json_input)
            domain = data.get("domain", "")
            operator = data.get("operator")
            workflow = data.get("workflow")
            friction = data.get("friction")
            region = data.get("region", "any")
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to parse --json-input: {e}\n")
            sys.exit(1)
    else:
        if not args.domain:
            sys.stderr.write("[ERROR] Argument --domain is required when --json-input is not provided.\n")
            sys.exit(1)
        domain = args.domain
        operator = args.operator
        workflow = args.workflow
        friction = args.friction
        region = args.region

    queries = generate_stream_queries(
        domain=domain,
        operator=operator,
        workflow=workflow,
        friction=friction,
        region=region,
        category=args.category
    )

    output = {
        "domain": domain,
        "operator": operator,
        "workflow": workflow,
        "region": region,
        "category_filter": args.category,
        "query_count": sum(len(q_list) for q_list in queries.values()),
        "queries": queries
    }

    if args.sqlite_db and args.run_id:
        init_sqlite_run(
            db_path=args.sqlite_db,
            research_id=args.run_id,
            original_request=f"Automated query generation for domain: {domain}",
            domain=domain,
            geography=region if region != "any" else None,
            plan_dict=output
        )

    sys.stdout.write(json.dumps(output, indent=2) + "\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
