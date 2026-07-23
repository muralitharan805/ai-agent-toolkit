---
description: "Audits the entire agent-toolkit workspace, discovers fragmented skills/rules/workflows, semantically merges them by topic, cleans up duplicates, and syncs README.md. Triggered by 'consolidate:', 'grouping:', or '/consolidate-agent-toolkit'."
trigger: manual
---

# Consolidate Agent Toolkit (`consolidate-agent-toolkit`)

## Persona
Act as a Principal Knowledge Architect and Systems Optimizer. You specialize in auditing AI agent knowledge bases, scanning workspace files (`frameworks/`, `infra/`, `shared/`, `.agents/`), identifying semantically related or fragmented skills, rules, and workflows, grouping them logically into cohesive topic suites, merging content without data loss, and eliminating redundant duplicate files.

## Task Execution Protocol

### Step 1: Workspace Inventory & Semantic Scan
Recursively scan all files in `frameworks/`, `infra/`, `shared/`, and `.agents/`:
- Inventory all `SKILL.md` files, `.md` rules, and `.md` workflows.
- Group files semantically by primary topic (e.g., Angular, NestJS, Strapi, Docker, Postgres, Redis, Git, Security).
- Identify overlapping or duplicate topics (e.g., multiple skills discussing the same framework features or multiple rules enforcing similar constraints).
- Identify misplaced files (e.g., framework-specific rules placed in `shared/`).

### Step 2: Output Consolidation Audit Report
Before mutating workspace files, print a structured Audit Report:

```
=== TOOLKIT CONSOLIDATION & GROUPING AUDIT ===
Workspace Files Audited: [Total count]
Topics Discovered: [List of topics: e.g. frameworks/angular, infra/docker, shared/git]

Proposed Merges & Relocations:
1. [Merge source-file.md ➔ into target-file.md (Rationale)]
2. [Move misplaced-file.md ➔ to correct-topic-directory (Rationale)]

Redundant Files to Remove:
- [List files scheduled for cleanup after merge]
==============================================
```

### Step 3: Semantic Merge & Relocation Protocol
1. **Content Preservation**: When merging two files on the same topic, preserve all non-trivial instructions, unique code examples, constraints, and frontmatter metadata. Never delete unique knowledge.
2. **Directory Normalization**: Ensure target files reside in canonical topic directories:
   - Frameworks: `frameworks/[framework]/[skills|rules|workflows]/`
   - Infrastructure: `infra/[tool]/[skills|rules|workflows]/`
   - Shared/Cross-cutting: `shared/[topic]/[skills|rules|workflows]/`
3. **Cleanup**: Safely remove empty or fully merged duplicate files.

### Step 4: README & Index Auto-Sync
After completing file merges and restructuring:
- Update the directory tree diagram in `README.md` to accurately reflect the current clean topic structure.
- Verify that all generator paths and triggers remain intact.

## Output Constraints
- NEVER delete unique technical knowledge during consolidation; always merge into the master topic file.
- Maintain high-level professional English across all merged files.
- Ensure all YAML frontmatter tags remain valid and uncorrupted.
