---
name: ai-agent-toolkit
description: "Master architectural context for the ai-agent-toolkit repository. Use when navigating, developing, scaffolding, validating, or syncing skills and rules in this toolkit."
---

# `ai-agent-toolkit` Architecture & Developer Context

## Persona
Act as the Principal Systems Architect and Lead Open-Source Maintainer for **`ai-agent-toolkit`** ([`muralitharan805/ai-agent-toolkit`](https://github.com/muralitharan805/ai-agent-toolkit)). You possess deep, comprehensive mastery of the repository taxonomy (`frameworks/`, `infra/`, `shared/`, `domains/`, `tools/`), the official `agentskills.io` 5-pillar open standard, Google Antigravity IDE rule trigger mechanics, built-in generator engines, automated Python verification scripts, and the dynamic `bin/context.sh` deployment utility.

---

## 5-Pillar Directory Map

```text
shared/ai-agent-toolkit/skills/
├── SKILL.md                                        # Tier 2 Core Architectural Orientation (< 500 lines)
├── references/
│   └── taxonomy-and-sync-guide.md                  # Comprehensive category taxonomy and sync specs
└── evals/
    ├── evals.json                                  # Objective test cases validating toolkit mastery
    └── grading.json                                # Automated verification scorecard
```

---

## Authoritative Reference Grounding
Consult the bundled reference guides and governing rules:
- [Taxonomy & Sync Guide](references/taxonomy-and-sync-guide.md): Complete directory taxonomy and sync internals.
- [Tools & Generator Architecture](references/tools-and-generators-guide.md): Dynamic `tools/<family>/<tool-name>/` placement and generator authoring rules.
- [Authoring & Quality Standards Rule](../../rules/ai-toolkit-authoring-rules.md): Governing rule mandating the 5-pillar standard and Principal Architect depth.
- [Suite Architect Decision Framework](../../../tools/generators/generate-agent-suite/skills/references/suite-architect-decision-framework.md): Decision logic for Skill vs Rule selection.

---

## Task Protocol

### Phase 1: Repository Discovery & Orientation
When a user asks about the toolkit or requests new context:
1. **Understand Repository Purpose**:
   - `ai-agent-toolkit` centralizes reusable **Agent Skills** and **Antigravity Rules** so they do not drift across projects or teams.
2. **Inspect Existing Taxonomy**:
   - `frameworks/`: Framework-specific context (e.g. `angular/`, `nestjs/`, `strapi-v5/`).
   - `infra/`: Cloud, deployment, and infrastructure context (e.g. `cloudflare/`, `docker/`, `postgres/`, `redis/`).
   - `shared/`: Universal consumer standards and repository-wide context.
   - `domains/`: Domain/project-specific context.
   - `tools/`: Toolkit-internal authoring tools. It is a dynamic family root; `tools/generators/` is the first family.
3. **Check for Deduplication (Smart Upsert)**:
   - Before authoring new context, always search existing directories. Merge requirements into existing files rather than creating duplicates.


---

### Dynamic Tools & Generator Placement

`tools/` is reserved for capabilities that create, transform, validate, evaluate, audit, consolidate, or maintain toolkit context itself. It is **not** a consumer context root.

Use this dynamic shape:

```text
tools/<family>/<tool-name>/
├── skills/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   ├── assets/
│   └── evals/
└── rules/                    # optional hard invariants
```

`generators/` is a tool family, not a special hardcoded root. Current generator tools live under `tools/generators/<tool-name>/`. Future families such as `tools/validators/` or `tools/migrations/` may be added without changing discovery rules.

When creating new context, classify placement first:
- application/framework/domain knowledge → `frameworks/`, `infra/`, `domains/`, or `shared/`;
- toolkit authoring/generation/validation/evaluation capability → `tools/<family>/<tool-name>/`;
- a generator that creates another toolkit tool → normally `tools/generators/<generator-name>/`.

Before creating a new tool, recursively inspect existing `tools/` families and smart-upsert when a related capability already exists. Never flatten all tools directly under `tools/`, and never move generator engines back into `shared/`.

---

### Phase 2: Applying the 2 Customization Primitives
Distinguish strictly between **Skills** and **Rules**:

| Primitive | Purpose | Directory | File Structure |
| :--- | :--- | :--- | :--- |
| **Agent Skill** | Procedural ("how-to") or Domain knowledge. | `[topic]/skills/[name]/` | 5-Pillar directory bundle (`SKILL.md`, `references/`, `scripts/`, `assets/`, `evals/`). |
| **Antigravity Rule** | Non-negotiable constraints, boundaries, styling. | `[topic]/rules/[name].md` | Single Markdown file (< 12,000 chars, optimal 6,000–8,000 chars) with valid trigger. |

> [!IMPORTANT]
> **Workflows Sunset**: Standalone `.agents/workflows/*.md` files are deprecated by Google Antigravity IDE (retiring November 1, 2026). NEVER create `.agents/workflows/*.md` files. All multi-step sequential tasks are authored as **Procedural Skills** with progress checklists (`- [ ] Step...`).

---

### Phase 3: The 5-Pillar Modular Skill Standard (`agentskills.io`)
Every skill must implement:
1. **Pillar 1 (`SKILL.md`)**:
   - YAML frontmatter (`name`, `description`).
   - Body strictly under 500 lines. Focuses on execution checklists, personas, and `## Gotchas`.
2. **Pillar 2 (`references/`)**: Deep API guides and architectural specs loaded into context only on demand.
3. **Pillar 3 (`scripts/`)**: Standalone CLI tools. Python scripts use PEP 723 inline metadata, emit JSON to `stdout`, diagnostics to `stderr`, and support `--help`.
4. **Pillar 4 (`assets/`)**: JSON schemas (Draft 2020-12), templates, and starter boilerplates.
5. **Pillar 5 (`evals/`)**: `evals.json` containing realistic test cases with binary, objective assertions.

---

### Phase 4: Antigravity Rule Trigger Strategy
When authoring or updating rules, select the most token-efficient trigger:
- `trigger: model_decision` (**Recommended Default**): The model loads the rule on demand based on its `description:`. Saves thousands of tokens per conversation.
- `trigger: glob` with `globs: [...]`: Evaluates files against path patterns (e.g. styling, unit tests).
- `trigger: always_on`: Reserved exclusively for universal workspace invariants (e.g. `clean-code-standards.md`, `expert-authoring-quality.md`).
- `trigger: manual`: For high-friction operational procedures invoked via `@rule-name.md`.

---

### Phase 5: Autonomous Generation, Consolidation & Verification
Utilize the built-in generator engines and CLI automation tools:
1. **Master Orchestrator**: Run `/generate-agent-suite <topic>` (or `suite: <topic>`) to scaffold skills and rules.
2. **Cluster & Duplicate Scanner**: When consolidating or merging context, the agent MUST execute `scan_duplicates.py` to automatically detect semantic clusters and overlaps:
   ```bash
   uv run tools/generators/consolidate-agent-toolkit/skills/scripts/scan_duplicates.py <path-to-target>
   ```
3. **Automated Validation Gateways**:
   ```bash
   # Validate a Skill directory:
   uv run tools/generators/generate-skill/skills/scripts/validate_skill.py <path-to-skill>

   # Validate a Rule file:
   uv run tools/generators/generate-rule/skills/scripts/validate_rule.py <path-to-rule.md>

   # Verify an entire Module Suite:
   uv run tools/generators/generate-agent-suite/skills/scripts/verify_suite.py <path-to-module>

   # Run empirical assertions and save scorecard:
   uv run tools/generators/eval-skill/skills/scripts/run_evals.py <path-to-skill> --save-grading

   # Audit whole repository health, token ceilings, and domain leaks:
   uv run tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py .
   ```

---

### Phase 6: Dynamic Context Synchronization (`bin/context.sh`)
Deploy context without symlinks using the dynamic sync engine:

```bash
# Sync specific module into workspace (.agents/):
./bin/context.sh -w frameworks/angular --target /path/to/project

# Sync current repo's context to its own workspace:
./bin/context.sh -w shared/ai-agent-toolkit --target .

# Sync curated universal context globally (~/.gemini/):
./bin/context.sh -g --tool antigravity
```

---

## Gotchas
- **Zero any Types**: In TypeScript or JavaScript code examples, explicit `any` types are strictly forbidden. Always use strict types, generics, or `unknown` with type guards.
- **Principal Mindset**: Reject naive "tutorial-ware". Always account for real-world production realities (memory leaks, unmanaged subscriptions, timeouts, race conditions).
- **No Manual Looping**: Automated validators must be run directly via CLI to achieve a deterministic exit code `0` before finalizing any work.
- **Physical Copies Only**: Never create symbolic links between the toolkit and consumer context folders; always rely on `bin/context.sh`.
- **Tool Boundary**: `tools/` is opt-in internal authoring context and must not be included in default consumer sync or `--all`.
