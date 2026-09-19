---
name: consolidate-agent-toolkit
description: "Audits ai-agent-toolkit workspace, discovers fragmented skills and rules, semantically merges them by topic, cleans up duplicates, and syncs README.md. Triggered by 'consolidate:', 'grouping:', or '/consolidate-agent-toolkit'."
---

# Consolidate Agent Toolkit (`consolidate-agent-toolkit`)

## Persona
Act as a Principal Knowledge Architect and Systems Optimizer. You specialize in auditing AI agent knowledge bases, scanning workspace files (`frameworks/`, `infra/`, `shared/`, `domains/`), identifying semantically related or fragmented skills and rules, grouping them logically into cohesive 5-pillar topic suites, merging content without data loss, and eliminating redundant duplicate files.

---

## 5-Pillar Directory Map

```text
shared/generators/skills/consolidate-agent-toolkit/
├── SKILL.md                                        # Tier 2 Core Consolidation Protocol (< 500 lines)
├── references/
│   └── merging-and-deduplication-playbook.md       # Step-by-step zero-loss merging guidelines
├── scripts/
│   └── scan_duplicates.py                          # Standalone CLI duplicate & overlap scanner (PEP 723)
└── evals/
    ├── evals.json                                  # Objective test cases for consolidation
    └── grading.json                                # Automated verification scorecard
```

---

## Authoritative Reference Grounding
Consult the bundled reference guides and tools:
- [Merging & Deduplication Playbook](references/merging-and-deduplication-playbook.md): Detailed 4-stage merge protocol ensuring zero data loss.
- [Duplicate Scanner Tool](scripts/scan_duplicates.py): Automated tool identifying duplicate file names and semantic clusters.
- [AI Toolkit Authoring Standards Rule](../../../ai-agent-toolkit/rules/ai-toolkit-authoring-rules.md): Governing rule for 5-pillar skill architecture.

---

## Task Protocol

### Phase 1: Workspace Inventory & Duplicate Scan
Execute the bundled duplicate scanning tool:

```bash
# Scan entire repository for duplicates and topic clusters:
python3 shared/generators/skills/consolidate-agent-toolkit/scripts/scan_duplicates.py

# Scan a specific framework or infrastructure directory:
python3 shared/generators/skills/consolidate-agent-toolkit/scripts/scan_duplicates.py frameworks/angular

# Machine-readable JSON output:
python3 shared/generators/skills/consolidate-agent-toolkit/scripts/scan_duplicates.py --json
```

> [!CAUTION]
> **Factory Protection**: NEVER scan, audit, merge, or delete files inside `shared/generators/`. This directory contains the toolkit's generator engines and must remain untouched.

---

### Phase 2: Consolidation Proposal & Audit Report
Before modifying any files on disk, output a structured Consolidation Proposal for user review:

```text
=== TOOLKIT CONSOLIDATION & GROUPING AUDIT ===
Target Path: [path]
Skills Scanned: [count] | Rules Scanned: [count]

Proposed Merges:
1. Absorb [secondary-skill-dir] ➔ into [master-skill-dir]
   - Reason: [Why merging makes architectural sense]
   - Unique Knowledge Preserved: [List Gotchas, templates, scripts]

Redundant Files Scheduled for Removal:
- [path/to/redundant-file-or-dir]
==============================================
```

---

### Phase 3: The Zero-Loss 5-Pillar Merge Protocol
When consolidating two skills into a single master bundle:
1. **Instructions (`SKILL.md`)**:
   - Merge procedural checklists and personas into the master `SKILL.md`.
   - Maintain the strictly enforced **< 500 lines** limit.
2. **References (`references/`)**:
   - Move deep domain guides and API specs from the secondary skill into the master `references/` folder.
   - Update relative markdown links in `SKILL.md`.
3. **Scripts (`scripts/`)**:
   - Move CLI automation tools into the master `scripts/` folder and verify execution permissions (`chmod +x`).
4. **Assets (`assets/`)**:
   - Consolidate schemas, boilerplate templates, and example outputs into `assets/`.
5. **Evals (`evals/`)**:
   - Merge test cases from secondary `evals.json` into master `evals.json`. Re-number test IDs sequentially.
6. **Gotchas Accumulation**:
   - Append all distinct edge cases and failure modes under `## Gotchas`.

---

### Phase 4: Validation & Pruning
1. Verify that all unique content has been successfully migrated to the master bundle.
2. Safely remove the empty or redundant secondary directory.
3. Validate the consolidated master bundle:
   ```bash
   python3 shared/generators/skills/generate-skill/scripts/validate_skill.py <master-skill-path>
   python3 shared/generators/skills/eval-skill/scripts/run_evals.py <master-skill-path> --save-grading
   ```
4. Sync the updated clean context using `bin/sync-context.sh`.

---

## Gotchas
- **Zero Technical Knowledge Loss**: Never delete a file without first auditing whether it contains unique Gotchas, code snippets, or assertions not present in the master bundle.
- **Factory Protection**: Files in `shared/generators/` are strictly protected from consolidation.
- **Rules Size Budget**: When merging rules, ensure the final file remains strictly under the 12,000-character IDE ceiling (target 6,000–8,000 chars).
- **Procedural Skills**: Never recreate legacy `.agents/workflows/*.md` files during consolidation. Always consolidate into Procedural Skills.
