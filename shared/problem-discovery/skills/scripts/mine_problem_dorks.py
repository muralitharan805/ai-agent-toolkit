# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Advanced Problem Dorking & Live Complaint Mining CLI.

Discovers operational pain points, manual glue-work, and unmanaged workflows
by synthesizing:
1. 5-stream precision search dorks (Community, Filetypes, Job Postings, Software Gaps, Regional).
2. Live public API complaint mining (Hacker News Algolia, GitHub Issues, Reddit JSON).

Adheres to agentskills.io 5-pillar modular architecture and emits clean JSON or Markdown.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any

# Standard timeout for external API requests in seconds
REQUEST_TIMEOUT_SECONDS = 8

# Common user-agent string for polite public API requests
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; AgentToolkitProblemMiner/1.0; +https://agentskills.io)"


@dataclass
class ComplaintSignal:
    """Represents an observed real-world complaint or friction signal."""
    source: str
    title: str
    url: str
    excerpt: str
    author_or_actor: str = ""
    timestamp: str = ""
    relevance_hint: str = ""


@dataclass
class DorkMatrix:
    """Categorized Google and forum search dorks across 5 research streams."""
    community: list[str] = field(default_factory=list)
    filetypes: list[str] = field(default_factory=list)
    job_postings: list[str] = field(default_factory=list)
    software_gaps: list[str] = field(default_factory=list)
    regional_grievances: list[str] = field(default_factory=list)


@dataclass
class MiningResult:
    """Consolidated result payload containing search dorks and live signals."""
    domain: str
    operator: str
    region: str
    track: str
    dorks: DorkMatrix
    live_signals: list[ComplaintSignal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def clean_html_text(raw_html: str) -> str:
    """Strips HTML tags and unescapes entities from raw comment text."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    return " ".join(text.split())


def fetch_hn_algolia_complaints(query: str, limit: int = 8) -> list[ComplaintSignal]:
    """Fetches real practitioner comments discussing pain points from Hacker News via Algolia API."""
    signals: list[ComplaintSignal] = []
    # Search comments matching the target query directly
    encoded = urllib.parse.urlencode({"query": query, "tags": "comment", "hitsPerPage": limit})
    url = f"https://hn.algolia.com/api/v1/search?{encoded}"

    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                hits = payload.get("hits", [])
                for hit in hits:
                    comment_body = clean_html_text(hit.get("comment_text", ""))
                    if not comment_body:
                        continue
                    excerpt = comment_body[:300] + ("..." if len(comment_body) > 300 else "")
                    story_id = hit.get("story_id")
                    item_id = hit.get("objectID")
                    comment_url = f"https://news.ycombinator.com/item?id={item_id}" if item_id else ""
                    signals.append(
                        ComplaintSignal(
                            source="Hacker News (Algolia API)",
                            title=hit.get("story_title") or f"Comment on HN story #{story_id}",
                            url=comment_url,
                            excerpt=excerpt,
                            author_or_actor=hit.get("author", ""),
                            timestamp=hit.get("created_at", ""),
                            relevance_hint="Practitioner discussion on workflow / tools",
                        )
                    )
    except Exception as exc:
        sys.stderr.write(f"[WARNING] HN Algolia fetch failed for '{query}': {exc}\n")

    return signals


def fetch_github_issue_complaints(query: str, limit: int = 8) -> list[ComplaintSignal]:
    """Fetches public GitHub issues discussing missing features or manual workarounds."""
    signals: list[ComplaintSignal] = []
    search_term = f'"{query}" "manual workaround" OR "currently not supported" in:title,body is:issue'
    encoded = urllib.parse.urlencode({"q": search_term, "per_page": limit, "sort": "relevance"})
    url = f"https://api.github.com/search/issues?{encoded}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/vnd.github.v3+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                items = payload.get("items", [])
                for item in items:
                    raw_body = item.get("body") or ""
                    clean_body = " ".join(raw_body.split())
                    excerpt = clean_body[:280] + ("..." if len(clean_body) > 280 else "")
                    signals.append(
                        ComplaintSignal(
                            source="GitHub Issues API",
                            title=item.get("title", ""),
                            url=item.get("html_url", ""),
                            excerpt=excerpt,
                            author_or_actor=item.get("user", {}).get("login", ""),
                            timestamp=item.get("created_at", ""),
                            relevance_hint="Issue reporting technical limitation / manual workaround",
                        )
                    )
    except Exception as exc:
        sys.stderr.write(f"[WARNING] GitHub Issues fetch failed for '{query}': {exc}\n")

    return signals


def fetch_reddit_public_complaints(query: str, limit: int = 8) -> list[ComplaintSignal]:
    """Fetches public Reddit complaints using the public JSON search endpoint."""
    signals: list[ComplaintSignal] = []
    search_term = f'"{query}" (spreadsheet OR workaround OR "takes hours" OR "frustrating")'
    encoded = urllib.parse.urlencode({"q": search_term, "limit": limit, "sort": "relevance"})
    url = f"https://www.reddit.com/search.json?{encoded}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                children = payload.get("data", {}).get("children", [])
                for child in children:
                    data = child.get("data", {})
                    selftext = data.get("selftext", "")
                    clean_text = " ".join(selftext.split())
                    excerpt = clean_text[:280] + ("..." if len(clean_text) > 280 else "")
                    permalink = data.get("permalink", "")
                    full_url = f"https://reddit.com{permalink}" if permalink else ""
                    signals.append(
                        ComplaintSignal(
                            source=f"Reddit (r/{data.get('subreddit', 'all')})",
                            title=data.get("title", ""),
                            url=full_url,
                            excerpt=excerpt or "(Post content in title)",
                            author_or_actor=data.get("author", ""),
                            timestamp="",
                            relevance_hint=f"Score: {data.get('score', 0)} | Comments: {data.get('num_comments', 0)}",
                        )
                    )
    except Exception as exc:
        sys.stderr.write(f"[WARNING] Reddit JSON fetch failed for '{query}': {exc}\n")

    return signals


def generate_precision_dorks(domain: str, operator: str, region: str, track: str) -> DorkMatrix:
    """Generates 5-stream targeted search dorks using the Atomic Search Unit methodology."""
    target = f'"{domain}"' if " " in domain else domain
    actor_clause = f'"{operator}"' if operator else ""

    # Stream 1: Community & Practitioner Complaints
    community = [
        f'site:reddit.com {target} {actor_clause} "takes hours"'.strip(),
        f'site:reddit.com {target} "every month I have to"'.strip(),
        f'site:reddit.com {target} "manually enter" spreadsheet'.strip(),
        f'site:reddit.com {target} "there must be a better way" OR "tired of"'.strip(),
        f'site:news.ycombinator.com "Ask HN" {target} "how do you manage"'.strip(),
    ]

    # Stream 2: Public Filetypes (SOPs, Templates, Spreadsheets)
    filetypes = [
        f'filetype:xlsx template {target} reconciliation'.strip(),
        f'filetype:xlsx template {target} tracking OR audit'.strip(),
        f'filetype:pdf "standard operating procedure" {target} "manually"'.strip(),
        f'filetype:docx checklist {target} "step by step"'.strip(),
        f'{target} "submit" "portal" "Excel" "download CSV" "upload" "manually"'.strip(),
    ]

    # Stream 3: Job Postings Hunting Paid Human Glue-Work
    job_postings = [
        f'site:linkedin.com/jobs {target} "manually reconcile"'.strip(),
        f'site:indeed.com {target} "maintain spreadsheets" "weekly report"'.strip(),
        f'site:naukri.com {target} "data entry" "multiple systems"'.strip(),
        f'site:indeed.com {target} "job description" "copy paste" OR "re-key"'.strip(),
    ]

    # Stream 4: Software Gaps & Negative Reviews
    software_gaps = [
        f'site:g2.com {target} "doesn\'t support"'.strip(),
        f'site:capterra.com {target} "too expensive" OR "cons"'.strip(),
        f'site:community.shopify.com {target} "manual workaround"'.strip(),
        f'site:wordpress.org/support/topic/ {target} "export" "manually"'.strip(),
        f'site:github.com/issues {target} "feature request" "export CSV"'.strip(),
    ]

    # Stream 5: Regional Grievances & Local Context
    regional: list[str] = []
    region_norm = region.lower().strip()
    if region_norm in ("in", "tn", "tamil nadu", "india"):
        regional = [
            f'"{domain}" "Tamil Nadu" grievance report PDF',
            f'site:tn.gov.in "{domain}" "G.O." delay OR penalty',
            f'"{domain}" complaint application process Chennai OR Coimbatore',
            f'site:consumercomplaints.in "{domain}" delay OR refund',
            f'"{domain}" tender manual record system India',
            f'site:arappor.org "{domain}" OR tender audit',
        ]
    elif region_norm in ("uk", "united kingdom", "england"):
        regional = [
            f'site:gov.uk "{domain}" statutory guidance compliance',
            f'site:propertyindustryeye.com "{domain}" delay OR fall-through',
            f'site:estateagenttoday.co.uk "{domain}" compliance penalty',
            f'site:reddit.com/r/HousingUK "{domain}" delay',
        ]
    elif region_norm in ("us", "usa", "united states"):
        regional = [
            f'site:sec.gov "{domain}" compliance disclosure',
            f'site:irs.gov "{domain}" reporting requirements',
            f'site:reddit.com/r/smallbusiness "{domain}" IRS OR state filing delay',
        ]
    else:
        regional = [
            f'"{domain}" "standard operating procedure" grievance PDF',
            f'"{domain}" regulatory compliance penalty delay',
            f'site:reddit.com "{domain}" government portal broken',
        ]

    return DorkMatrix(
        community=community,
        filetypes=filetypes,
        job_postings=job_postings,
        software_gaps=software_gaps,
        regional_grievances=regional,
    )


def render_markdown_output(result: MiningResult) -> str:
    """Renders human-readable categorized Markdown report for terminal and IDE display."""
    lines: list[str] = []
    lines.append(f"# Problem Discovery Deep Search & Dork Report")
    lines.append(f"**Domain:** `{result.domain}` | **Region:** `{result.region}` | **Operator:** `{result.operator or 'General'}` | **Track:** `{result.track}`\n")

    # Section 1: Live Fetched Signals
    lines.append(f"## 1. Live Public Complaints & Practitioner Signals ({len(result.live_signals)} found)")
    if result.live_signals:
        for idx, sig in enumerate(result.live_signals, start=1):
            lines.append(f"### Signal {idx}: [{sig.source}] {sig.title}")
            if sig.url:
                lines.append(f"- **URL:** {sig.url}")
            if sig.author_or_actor:
                lines.append(f"- **Author / Actor:** `{sig.author_or_actor}`")
            if sig.relevance_hint:
                lines.append(f"- **Context:** {sig.relevance_hint}")
            lines.append(f"- **Raw Excerpt:**\n  > *\"{sig.excerpt}\"*\n")
    else:
        lines.append("_No live API signals fetched (or live fetch was disabled)._\n")

    # Section 2: 5-Stream Search Dorks
    lines.append("## 2. Precision 5-Stream Search Dorks (Copy & Paste to Google)")
    
    lines.append("### Stream A: Community & Reddit Pain Phrases")
    for d in result.dorks.community:
        lines.append(f"- `{d}`")

    lines.append("\n### Stream B: Public SOPs, Spreadsheets & Templates")
    for d in result.dorks.filetypes:
        lines.append(f"- `{d}`")

    lines.append("\n### Stream C: Job Postings Hunting Paid Glue-Work")
    for d in result.dorks.job_postings:
        lines.append(f"- `{d}`")

    lines.append("\n### Stream D: Software Gaps & Negative Reviews")
    for d in result.dorks.software_gaps:
        lines.append(f"- `{d}`")

    lines.append(f"\n### Stream E: Regional Context & Grievances ({result.region.upper()})")
    for d in result.dorks.regional_grievances:
        lines.append(f"- `{d}`")

    lines.append("\n---\n*Generated by `mine_problem_dorks.py` adhering to agentskills.io standard.*")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    """Builds the CLI argument parser with comprehensive help."""
    parser = argparse.ArgumentParser(
        description="Mine operational friction and generate precision search dorks for problem discovery."
    )
    parser.add_argument(
        "--domain",
        "-d",
        required=True,
        help="Target industry, workflow, or domain (e.g. 'textile export', 'welfare appeal', 'estate agency').",
    )
    parser.add_argument(
        "--operator",
        "-o",
        default="",
        help="Target persona or operational role (e.g. 'merchandiser', 'accountant', 'citizen').",
    )
    parser.add_argument(
        "--region",
        "-r",
        default="in",
        help="Geographic or regulatory region: 'in' (India/TN), 'uk', 'us', or 'any' (default: 'in').",
    )
    parser.add_argument(
        "--track",
        "-t",
        default="all",
        choices=["commercial", "free_utility", "all"],
        help="Target discovery track: 'commercial' (WTP), 'free_utility', or 'all' (default: 'all').",
    )
    parser.add_argument(
        "--no-live-fetch",
        action="store_true",
        help="Disable live API querying (HN, GitHub, Reddit) and emit dorks only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON to stdout instead of Markdown.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    sys.stderr.write(f"[INFO] Mining dorks and complaints for domain='{args.domain}', region='{args.region}'...\n")

    # 1. Generate 5-stream precision dorks
    dorks = generate_precision_dorks(
        domain=args.domain,
        operator=args.operator,
        region=args.region,
        track=args.track,
    )

    # 2. Live fetch complaints if enabled
    live_signals: list[ComplaintSignal] = []
    if not args.no_live_fetch:
        sys.stderr.write("[INFO] Querying Hacker News Algolia API...\n")
        hn_signals = fetch_hn_algolia_complaints(args.domain, limit=6)
        live_signals.extend(hn_signals)

        sys.stderr.write("[INFO] Querying GitHub Issues Search API...\n")
        gh_signals = fetch_github_issue_complaints(args.domain, limit=5)
        live_signals.extend(gh_signals)

        sys.stderr.write("[INFO] Querying Reddit Public JSON Search...\n")
        reddit_signals = fetch_reddit_public_complaints(args.domain, limit=5)
        live_signals.extend(reddit_signals)

    result = MiningResult(
        domain=args.domain,
        operator=args.operator,
        region=args.region,
        track=args.track,
        dorks=dorks,
        live_signals=live_signals,
        metadata={
            "live_fetched_count": len(live_signals),
            "dorks_generated_count": (
                len(dorks.community)
                + len(dorks.filetypes)
                + len(dorks.job_postings)
                + len(dorks.software_gaps)
                + len(dorks.regional_grievances)
            ),
        },
    )

    # 3. Output payload
    if args.json:
        # Convert dataclasses to dict
        output_dict = {
            "domain": result.domain,
            "operator": result.operator,
            "region": result.region,
            "track": result.track,
            "metadata": result.metadata,
            "live_signals": [asdict(s) for s in result.live_signals],
            "dorks": asdict(result.dorks),
        }
        sys.stdout.write(json.dumps(output_dict, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(render_markdown_output(result) + "\n")


if __name__ == "__main__":
    main()
