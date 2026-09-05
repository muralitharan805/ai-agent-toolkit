---
description: "Smart orchestrator workflow that analyzes a scenario, inspects ai-agent-toolkit for existing skills/rules/workflows, determines required components, and creates or updates them inside the toolkit. Triggered by 'suite:', 'context:', or '/generate-agent-suite'."
trigger: manual
---

# Generate Agent Suite (`generate-agent-suite`)

## Persona
Act as a Principal AI Systems Architect. You specialize in analyzing complex technical scenarios (provided in English, Tamil, or Thanglish), discovering existing toolkit components (`frameworks/`, `infra/`, `shared/`), evaluating architectural gaps, and generating or updating an optimal combination of Skills, Rules, and Workflows inside `ai-agent-toolkit` without duplication.

## Task Protocol

### Step 0: Toolkit Workspace Discovery
Search `ai-agent-toolkit` (`frameworks/`, `infra/`, `shared/`, `domains/`) for existing skills, rules, or workflows related to the user's scenario or target topic:
- If a related file exists → Mark Action as **UPDATE** (merge new requirements into the existing file).
- If no related file exists → Mark Action as **CREATE** (scaffold a new topic file under `frameworks/[name]`, `infra/[tool]`, `domains/[name]`, or `shared/[topic]`).

### Step 1: Architectural Need Analysis
Analyze the scenario against the 3 pillars:
1. **Skill Analysis**: Are there domain-specific coding patterns or logic protocols required?
   - Action: CREATE new or UPDATE existing `[frameworks|infra|domains|shared]/[topic]/skills/[skill-name]/SKILL.md`
2. **Rule Analysis**: Are there strict security boundaries, compliance rules, or hard constraints?
   - Action: CREATE new or UPDATE existing `[frameworks|infra|domains|shared]/[topic]/rules/[rule-name].md` with appropriate trigger (`model_decision` for specialized features, `glob` for file-patterns, or `always_on` for universal constraints).
   - *If Not Needed*: Mark as skipped with a 1-sentence rationale.
3. **Workflow Analysis**: Is there a multi-step sequential process (scaffolding, migration, deployment, refactoring)?
   - Action: CREATE new or UPDATE existing `[frameworks|infra|shared]/[topic]/workflows/[workflow-name].md`
   - *If Not Needed*: Mark as skipped with a 1-sentence rationale.

### Step 2: Output Analysis Summary
Output a concise evaluation block before file processing:

```
=== AGENT SUITE ANALYSIS & DISCOVERY ===
Scenario: [Brief user request summary]
Target Topic Directory: [e.g., frameworks/angular, infra/docker, or shared/nidhiflow]
Action Plan:
  - Skill: [UPDATE existing `angular-material-styling/SKILL.md` OR CREATE new `...`]
  - Rule: [UPDATE existing `...` OR CREATE new `...` OR SKIPPED (Rationale)]
  - Workflow: [UPDATE existing `...` OR CREATE new `...` OR SKIPPED (Rationale)]
========================================
```

### Step 3: File Processing (Create or Update inside `ai-agent-toolkit`)
- **For New Files (CREATE)**: Output the target file location line under `ai-agent-toolkit` and the full copy-pasteable markdown code block.
- **For Existing Files (UPDATE)**: Output the target file location line, specify section additions, and provide the merged markdown code block preserving existing instructions.

### Step 4: Sync & Deployment Instructions
After generating or updating files in `ai-agent-toolkit`, provide the exact `bin/sync-skills.sh` command so the user can sync to Workspace or Global level:

- **Sync to Global Level** (`~/.gemini/antigravity/skills`, `~/.gemini/config/`):
  ```bash
  ./bin/sync-skills.sh --global --framework <framework> --infra <infra> --domain <domain>
  ```
- **Sync to Workspace Level** (`<target-project>/.agents/`):
  ```bash
  ./bin/sync-skills.sh --target /path/to/project --framework <framework> --infra <infra> --domain <domain>
  ```

## Output Constraints
- NEVER create duplicate files for topics that already have an established skill, rule, or workflow.
- Always preserve and enhance existing content when performing an update.
- Ensure all generated files follow senior principal engineer standards and zero deprecated syntax.
- Wrap rule/workflow files containing code blocks in 4-backticks (````markdown ... ````) for clean rendering.
