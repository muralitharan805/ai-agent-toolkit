---
description: "Orchestrator workflow analyzing scenarios, evaluating gaps, and generating or updating modular skills, rules, and workflows in ai-agent-toolkit. Triggered by 'suite:', 'context:', or '/generate-agent-suite'."
trigger: manual
---

# Generate Agent Suite (`generate-agent-suite`)

## Persona
Act as a Principal AI Systems Architect. You specialize in analyzing complex technical scenarios (provided in English, Tamil, or Thanglish), discovering existing toolkit components (`frameworks/`, `infra/`, `shared/`, `domains/`), evaluating architectural gaps, and generating or updating an optimal combination of modular Skills (with `references/` & `evals/`), Rules, and Workflows inside `ai-agent-toolkit` without duplication.

## Task Protocol

### Step 0: Toolkit Workspace Discovery
Search `ai-agent-toolkit` (`frameworks/`, `infra/`, `shared/`, `domains/`) for existing skills, rules, or workflows related to the user's scenario or target topic:
- If a related file exists → Mark Action as **UPDATE** (merge new requirements into the existing files).
- If no related file exists → Mark Action as **CREATE** (scaffold under `frameworks/[name]`, `infra/[tool]`, `domains/[name]`, or `shared/[topic]`).

### Step 1: Architectural Need Analysis (The 3 Pillars)
Analyze the scenario against the 3 pillars:
1. **Skill Analysis**: Are there domain-specific coding patterns, library APIs, or procedural protocols required?
   - Action: CREATE or UPDATE modular skill directory `[category]/[topic]/skills/[skill-name]/`:
     - `SKILL.md`: Core instructions, progressive disclosure links, and `## Gotchas` (< 500 lines).
     - `references/[guide].md`: Scaffolds deep technical references on demand if domain has complex schemas/APIs.
     - `evals/evals.json`: Generates 2–3 realistic test prompts and objective assertions for quality verification.
     - *Optional scripts/assets*: Helper scripts (PEP 723 / stdout JSON) or schema templates if automation is needed.
2. **Rule Analysis**: Are there strict security boundaries, compliance requirements, or hard architectural constraints?
   - Action: CREATE or UPDATE `[category]/[topic]/rules/[rule-name].md` with appropriate trigger (`model_decision` for specialized features, `glob` with `globs: [...]` for file patterns, or `always_on` for universal constraints). Target 6,000–8,000 chars (split at 10,000; hard limit 12,000).
   - *If Not Needed*: Mark as skipped with a 1-sentence technical rationale.
3. **Workflow Analysis**: Is there a multi-step sequential execution process (scaffolding, migration, deployment, refactoring)?
   - Action: CREATE or UPDATE `[category]/[topic]/workflows/[workflow-name].md` (Ensuring frontmatter `description:` is strictly `<= 250 characters` with embedded shorthand triggers).
   - *If Not Needed*: Mark as skipped with a 1-sentence technical rationale.

### Step 2: Output Analysis Summary
Output a concise evaluation block before emitting file blocks:

```
=== AGENT SUITE ANALYSIS & DISCOVERY ===
Scenario: [Brief user request summary]
Target Topic Directory: [e.g., frameworks/angular, infra/docker, or shared/sample-topic]
Action Plan:
  - Skill: [UPDATE existing `...` OR CREATE new modular bundle `SKILL.md` + `references/` + `evals/`]
  - Rule: [UPDATE existing `...` OR CREATE new `...` OR SKIPPED (Rationale)]
  - Workflow: [UPDATE existing `...` OR CREATE new `...` OR SKIPPED (Rationale)]
========================================
```

### Step 3: File Generation Protocol
Output the target file locations under `ai-agent-toolkit` and complete, copy-pasteable code blocks in professional English:
1. `SKILL.md` (with YAML frontmatter `name` matching directory, imperative `description`, Gotchas)
2. `references/*.md` (if depth required)
3. `evals/evals.json` (with test cases & assertions)
4. Rule `.md` (if needed, with valid trigger)
5. Workflow `.md` (if needed, with description <= 250 chars)

### Step 4: Sync & Deployment Instructions
After generating or updating files in `ai-agent-toolkit`, provide the exact `bin/sync-context.sh` command:

- **Sync to Global Level** (`~/.gemini/antigravity/skills`, `~/.gemini/config/`):
  ```bash
  ./bin/sync-context.sh --global [category]/[topic]
  ```
- **Sync to Workspace Level** (`<target-project>/.agents/`):
  ```bash
  ./bin/sync-context.sh [category]/[topic] -w /path/to/project
  ```

## Output Constraints
- NEVER create duplicate files for topics that already have an established skill, rule, or workflow.
- Always preserve and enhance existing content when performing an update.
- Ensure all generated files follow senior principal engineer standards and zero deprecated syntax.
- Wrap rule and workflow files containing code blocks in 4-backticks (````markdown ... ````) for clean rendering.
