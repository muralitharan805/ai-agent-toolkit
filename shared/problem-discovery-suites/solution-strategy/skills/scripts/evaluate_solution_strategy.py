# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Evaluates operational constraints, tests non-software sufficiency, scores solution class fit,
applies the SaaS justification gate, designs the Smallest Testable Solution (STS),
and persists the final architecture to SQLite, maintaining the master discovery view.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VALID_CONSTRAINTS = [
    "single_user_only",
    "multi_user_required",
    "local_data_only",
    "cloud_sync_required",
    "offline_capable_required",
    "browser_only_surface",
    "desktop_os_access_required",
    "mobile_surface_required",
    "scheduled_background_execution_required",
    "event_driven_trigger_required",
    "api_integrations_available",
    "realtime_latency_sensitive",
    "audit_trail_or_compliance_required",
    "recurring_commercial_wtp_validated",
    "high_domain_complexity_rules"
]

SOLUTION_CLASSES = [
    "CHECKLIST_OR_SOP",
    "STRUCTURED_SPREADSHEET",
    "MANUAL_CONCIERGE_SERVICE",
    "PROCESS_OR_POLICY_REDESIGN",
    "LOCAL_SCRIPT",
    "CLI_UTILITY",
    "DESKTOP_APP",
    "BROWSER_EXTENSION",
    "BROWSER_AUTOMATION",
    "INTEGRATION_SERVICE",
    "WEBHOOK_HANDLER",
    "INTERNAL_TOOL",
    "STATIC_SITE_OR_JAMSTACK",
    "SINGLE_USER_WEB_APP",
    "MULTI_TENANT_SAAS",
    "API_PLATFORM",
    "EMBEDDED_LIBRARY_OR_SDK"
]


def _load_discovery_db_class():
    """Load the canonical discovery-state client."""
    db_module_path = Path(__file__).resolve().parents[3] / "discovery-state" / "skills" / "scripts" / "discovery_db.py"
    spec = importlib.util.spec_from_file_location("discovery_state_db", db_module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load discovery-state client from {db_module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DiscoveryDB

def evaluate_solution_strategy(
    candidate_id: str,
    constraints: Dict[str, Any],
    non_software_input: Optional[Dict[str, Any]] = None,
    sts_input: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Apply solution-shape gates only to explicit, evidence-backed inputs."""
    if non_software_input is None:
        raise ValueError("non_software_input is required; do not invent non-software sufficiency metrics")
    if sts_input is None:
        raise ValueError("sts_input is required; the reasoning agent must preregister STS metrics instead of using generic defaults")
    if "friction_reduction_percentage" not in non_software_input:
        raise ValueError("non_software_input requires friction_reduction_percentage")
    
    # 1. Non-Software Sufficiency Evaluation
    if non_software_input and non_software_input.get("is_sufficient"):
        non_soft_class = non_software_input.get("recommended_non_software_class", "STRUCTURED_SPREADSHEET")
        friction_red = non_software_input.get("friction_reduction_percentage", 85)
        justification = non_software_input.get("justification", "Non-software solution resolves the core friction.")
        triggers = non_software_input.get("software_transition_triggers", ["Volume exceeds manual handling capacity."])
        
        return {
            "assessment_id": f"sol_{candidate_id.replace('-', '_')}",
            "candidate_id": candidate_id,
            "evaluation_date": date.today().isoformat(),
            "assessed_by": "solution-strategy-agent",
            "non_software_evaluation": {
                "is_sufficient": True,
                "recommended_non_software_class": non_soft_class,
                "friction_reduction_percentage": friction_red,
                "justification": justification,
                "software_transition_triggers": triggers
            },
            "constraints": constraints,
            "solution_class": non_soft_class,
            "saas_justification": {
                "verdict": "REJECTED",
                "multi_user_status": "NOT_APPLICABLE",
                "commercial_wtp_status": "NOT_APPLICABLE",
                "justification": "Non-software intervention eliminates >= 80% friction. Software development is rejected."
            },
            "smallest_testable_solution": sts_input or {
                "archetype": "SPREADSHEET_PILOT" if "SPREADSHEET" in str(non_soft_class) else "CONCIERGE_PILOT",
                "target_hypothesis": f"Deploying {non_soft_class} eliminates friction without custom software.",
                "estimated_build_days": 2,
                "pilot_population": "3 target operators",
                "observation_duration_days": 7,
                "success_threshold": "Operators execute workflow with zero critical errors for 7 days",
                "falsification_rule": "Operators bypass the template or manual errors persist > 20%",
                "next_step_if_passed": "Standardize non-software SOP across organization",
                "next_step_if_failed": "Re-evaluate for lightweight script automation"
            },
            "technical_operational_profile": {
                "execution_surface": "Human operator / Standard Office tools",
                "state_locality": "Local desktop / Shared drive file",
                "network_topography": "Manual file exchange or email",
                "concurrency_model": "Single-operator sequential access",
                "failure_modes": [
                    "Accidental formula deletion or template alteration",
                    "Operator omission of verification steps",
                    "Unversioned file copies causing data discrepancies"
                ]
            },
            "reversibility_tier": "TYPE_2"
        }

    # 2. Evaluate Software Solution Class
    single_user = constraints.get("single_user_only") is True
    multi_user = constraints.get("multi_user_required") is True
    local_data = constraints.get("local_data_only") is True
    cloud_sync = constraints.get("cloud_sync_required") is True
    browser_surface = constraints.get("browser_only_surface") is True
    desktop_access = constraints.get("desktop_os_access_required") is True
    bg_jobs = constraints.get("scheduled_background_execution_required") is True
    event_driven = constraints.get("event_driven_trigger_required") is True
    apis_avail = constraints.get("api_integrations_available") is True
    wtp_valid = constraints.get("recurring_commercial_wtp_validated") is True

    # Default SaaS gate verdict
    saas_verdict = "REJECTED"
    saas_multi = "NOT_APPLICABLE"
    saas_wtp = "NOT_APPLICABLE"
    saas_just = "Problem is best solved with a single-user or local utility."

    if multi_user and cloud_sync and bg_jobs and wtp_valid:
        selected_class = "MULTI_TENANT_SAAS"
        saas_verdict = "STRONG_CANDIDATE"
        saas_multi = "PROVEN"
        saas_wtp = "PROVEN"
        saas_just = "Multi-user collaboration, persistent cloud state, background jobs, and recurring WTP are all empirically verified."
    elif (apis_avail and (bg_jobs or event_driven)) and not browser_surface:
        if event_driven and not bg_jobs:
            selected_class = "WEBHOOK_HANDLER"
        else:
            selected_class = "INTEGRATION_SERVICE"
        saas_verdict = "NOT_YET_JUSTIFIED" if wtp_valid else "REJECTED"
        saas_multi = "UNPROVEN" if multi_user else "NOT_APPLICABLE"
        saas_wtp = "PROVEN" if wtp_valid else "UNPROVEN"
        saas_just = f"Headless {selected_class} satisfies automated synchronization without needing a complex multi-tenant UI."
    elif browser_surface and not apis_avail:
        selected_class = "BROWSER_EXTENSION"
        saas_verdict = "REJECTED"
        saas_just = "DOM-based workflow inside existing browser applications. Extension provides direct context."
    elif desktop_access and not single_user:
        selected_class = "INTERNAL_TOOL"
        saas_verdict = "NOT_YET_JUSTIFIED"
        saas_multi = "PROVEN" if multi_user else "UNPROVEN"
        saas_wtp = "UNPROVEN"
        saas_just = "Internal team dashboard. Public SaaS billing and multi-tenant isolation are unneeded."
    elif single_user and local_data:
        selected_class = "LOCAL_SCRIPT"
        saas_verdict = "REJECTED"
        saas_just = "Single operator working with local disk files. Zero justification for SaaS."
    elif single_user and not local_data and not multi_user:
        selected_class = "CLI_UTILITY"
        saas_verdict = "NOT_YET_JUSTIFIED"
        saas_just = "Single operator CLI utility. Multi-user collaboration unproven."
    else:
        selected_class = "LOCAL_SCRIPT"
        saas_verdict = "NOT_YET_JUSTIFIED"
        saas_just = "Simplest local script selected pending multi-user evidence."

    # 3. Formulate STS
    if not sts_input:
        if selected_class in ["LOCAL_SCRIPT", "CLI_UTILITY"]:
            sts = {
                "archetype": "LOCAL_SCRIPT_PILOT",
                "target_hypothesis": "A standalone CLI utility running locally resolves operator bottleneck in < 5 seconds.",
                "estimated_build_days": 3,
                "pilot_population": "3 target operators",
                "observation_duration_days": 10,
                "success_threshold": "Operators execute script on >= 80% of daily transactions without fatal errors",
                "falsification_rule": "Operators revert to manual process due to edge cases or CLI friction",
                "next_step_if_passed": "Refine CLI utility into standard packaged distribution",
                "next_step_if_failed": "Audit edge cases or consider GUI wrapper"
            }
        elif selected_class == "BROWSER_EXTENSION":
            sts = {
                "archetype": "THIN_EXTENSION_PROTOTYPE",
                "target_hypothesis": "An unpacked browser extension injecting an automation button eliminates DOM copy-paste friction.",
                "estimated_build_days": 4,
                "pilot_population": "5 target browser operators",
                "observation_duration_days": 14,
                "success_threshold": ">= 4 of 5 operators use the extension button daily with > 50% time saved",
                "falsification_rule": "Frequent DOM layout drift breaks parsing or operators disable extension",
                "next_step_if_passed": "Publish vetted Manifest V3 extension to Chrome Web Store",
                "next_step_if_failed": "Explore official API partnerships or headless automation"
            }
        elif selected_class in ["INTEGRATION_SERVICE", "WEBHOOK_HANDLER"]:
            sts = {
                "archetype": "NO_CODE_WORKFLOW",
                "target_hypothesis": "Automating API webhook synchronization eliminates manual data entry between systems.",
                "estimated_build_days": 3,
                "pilot_population": "2 test environments / 100 transactions",
                "observation_duration_days": 7,
                "success_threshold": "Zero missing records and 100% idempotency across 7 days",
                "falsification_rule": "API rate limits or authentication token expiry causes > 2% dropped sync events",
                "next_step_if_passed": "Implement dedicated stateless background daemon",
                "next_step_if_failed": "Re-evaluate API constraints or implement fallback queue"
            }
        else:
            sts = {
                "archetype": "CONCIERGE_PILOT",
                "target_hypothesis": "Manual concierge execution verifies customer retention and willingness to pay before software build.",
                "estimated_build_days": 2,
                "pilot_population": "3 customer accounts",
                "observation_duration_days": 14,
                "success_threshold": ">= 2 customer accounts commit to recurring subscription or renewal",
                "falsification_rule": "Customers refuse commercial commitment after experiencing manual concierge output",
                "next_step_if_passed": "Begin phased build of multi-tenant service",
                "next_step_if_failed": "Archive candidate or pivot value proposition"
            }
    else:
        sts = sts_input

    # 4. Formulate Technical Operational Profile
    if selected_class in ["LOCAL_SCRIPT", "CLI_UTILITY"]:
        profile = {
            "execution_surface": "Local terminal / shell process",
            "state_locality": "Local memory / temporary file cache / local SQLite",
            "network_topography": "Offline local processing (optional outbound API calls)",
            "concurrency_model": "Single-process synchronous execution",
            "failure_modes": [
                "Missing system runtime dependencies or environment variables",
                "Malformed local input files causing parsing termination",
                "Filesystem permission denials on local directories"
            ]
        }
    elif selected_class == "BROWSER_EXTENSION":
        profile = {
            "execution_surface": "Browser tab DOM / Extension background service worker",
            "state_locality": "chrome.storage.local / in-memory tab state",
            "network_topography": "Browser fetch requests to third-party endpoints",
            "concurrency_model": "Asynchronous event-driven callbacks",
            "failure_modes": [
                "Host web application changes DOM classes or selectors",
                "Content Security Policy (CSP) blocking script injection",
                "Manifest V3 service worker lifecycle termination during idle"
            ]
        }
    elif selected_class in ["INTEGRATION_SERVICE", "WEBHOOK_HANDLER"]:
        profile = {
            "execution_surface": "Headless background daemon / Serverless webhook function",
            "state_locality": "Transactional database for idempotency keys and state sync",
            "network_topography": "Inbound HTTPS webhook receiver + outbound REST API client",
            "concurrency_model": "Sequential queue per tenant with worker pools",
            "failure_modes": [
                "Upstream API rate limits (HTTP 429) or token expiration",
                "Network timeout during multi-step payload transformation",
                "Duplicate webhook delivery causing double-entry without idempotency key"
            ]
        }
    else:
        profile = {
            "execution_surface": "Distributed cloud application with web frontend",
            "state_locality": "Tenant-isolated relational database with read replicas",
            "network_topography": "Public HTTPS / TLS 1.3 via CDN and reverse proxy",
            "concurrency_model": "Multi-threaded web servers with async queue workers",
            "failure_modes": [
                "Cross-tenant data leakage if isolation queries are malformed",
                "Stripe billing webhook failures causing service disruption",
                "High latency on background report generation under load"
            ]
        }

    return {
        "assessment_id": f"sol_{candidate_id.replace('-', '_')}",
        "candidate_id": candidate_id,
        "evaluation_date": date.today().isoformat(),
        "assessed_by": "solution-strategy-agent",
        "non_software_evaluation": {
            "is_sufficient": False,
            "recommended_non_software_class": None,
            "friction_reduction_percentage": non_software_input["friction_reduction_percentage"],
            "justification": "Manual spreadsheets or SOPs fail under observed transaction frequency, speed, and accuracy requirements.",
            "software_transition_triggers": [
                "Execution volume exceeds manual capacity (> 2 hours/day)",
                "Error consequences cause direct financial or operational loss"
            ]
        },
        "constraints": constraints,
        "solution_class": selected_class,
        "saas_justification": {
            "verdict": saas_verdict,
            "multi_user_status": saas_multi,
            "commercial_wtp_status": saas_wtp,
            "justification": saas_just
        },
        "smallest_testable_solution": sts,
        "technical_operational_profile": profile,
        "reversibility_tier": "TYPE_2" if selected_class != "MULTI_TENANT_SAAS" else "TYPE_1"
    }


def save_solution_strategy(
    db_path: str,
    candidate_id: str,
    solution_class: str,
    solution_dict: Dict[str, Any]
) -> str:
    """Persist through the canonical discovery-state client; missing candidates are errors."""
    DiscoveryDB = _load_discovery_db_class()
    return DiscoveryDB(db_path).finalize_solution(candidate_id, solution_class, solution_dict)


def get_discovery_dashboard(
    db_path: str,
    status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Read the canonical flattened dashboard from discovery-state."""
    DiscoveryDB = _load_discovery_db_class()
    return DiscoveryDB(db_path).get_discovery_dashboard(status_filter)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluates operational constraints, scores solution classes, and finalizes candidate architecture."
    )
    parser.add_argument("--candidate-id", help="Candidate ID being evaluated")
    parser.add_argument("--constraints", help="Path to JSON file containing 15 operational constraints")
    parser.add_argument("--non-software-file", required=True, help="JSON file with evidence-backed non-software sufficiency details")
    parser.add_argument("--sts-file", required=True, help="JSON file with preregistered Smallest Testable Solution details")
    parser.add_argument("--db", help="Path to SQLite database")
    parser.add_argument("--output", help="Optional output path for SolutionAssessment JSON")
    parser.add_argument("--dashboard", action="store_true", help="Print v_discovery_dashboard table")
    parser.add_argument("--filter-status", help="Filter dashboard rows by lifecycle or validation status")

    args = parser.parse_args()

    if args.dashboard:
        if not args.db:
            sys.stderr.write("[ERROR] --db is required to query the dashboard.\n")
            sys.exit(1)
        dashboard_rows = get_discovery_dashboard(args.db, args.filter_status)
        print(json.dumps(dashboard_rows, indent=2))
        return

    if not args.candidate_id or not args.constraints:
        sys.stderr.write("[ERROR] Both --candidate-id and --constraints are required for evaluation.\n")
        parser.print_help(sys.stderr)
        sys.exit(1)

    with open(args.constraints, "r", encoding="utf-8") as f:
        constraints_data = json.load(f)

    non_soft_data = None
    if args.non_software_file:
        with open(args.non_software_file, "r", encoding="utf-8") as f:
            non_soft_data = json.load(f)

    sts_data = None
    if args.sts_file:
        with open(args.sts_file, "r", encoding="utf-8") as f:
            sts_data = json.load(f)

    assessment = evaluate_solution_strategy(
        candidate_id=args.candidate_id,
        constraints=constraints_data,
        non_software_input=non_soft_data,
        sts_input=sts_data
    )

    if args.db:
        save_solution_strategy(
            db_path=args.db,
            candidate_id=args.candidate_id,
            solution_class=assessment["solution_class"],
            solution_dict=assessment
        )

    output_json = json.dumps(assessment, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        sys.stderr.write(f"[INFO] Wrote solution assessment to {args.output}\n")

    print(output_json)


if __name__ == "__main__":
    main()
