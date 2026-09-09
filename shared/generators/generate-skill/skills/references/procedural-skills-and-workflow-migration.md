# Procedural Skills & Workflow Migration Guide

## Strategic Context & Deprecation Notice
Google Antigravity IDE has officially deprecated legacy Workflows (`.agents/workflows/*.md`) in favor of the **Agent Skills Open Standard** ([agentskills.io](https://agentskills.io)). Standalone workflows will be retired on **November 1, 2026**. 

In modern agent systems, multi-step sequential tasks (deployments, scaffolding, testing pipelines, migrations) are modeled as **Procedural Skills**.

---

## 1. The Two Archetypes of Agent Skills

Agent Skills are categorized into two complementary archetypes:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             AGENT SKILLS ARCHETYPES                              │
├─────────────────────────────────────────┬────────────────────────────────────────┤
│ 1. Domain Knowledge Skills              │ 2. Procedural Execution Skills         │
│ (e.g. angular-signal-state-management)   │ (e.g. deploy-angular-spa, scaffold-app)│
├─────────────────────────────────────────┼────────────────────────────────────────┤
│ • Focus: Coding patterns & API nuances  │ • Focus: Sequential task execution     │
│ • Key Elements: Decision trees, Gotchas │ • Key Elements: Step checklists, gates │
│ • Secondary: Deep references & schemas  │ • Secondary: Pre-flight & CLI scripts  │
│ • Invocation: Autonomous / Contextual   │ • Invocation: Slash commands (/<name>) │
└─────────────────────────────────────────┴────────────────────────────────────────┘
```

---

## 2. Anatomy of a Procedural Skill

A Procedural Skill organizes a complex execution trajectory into a cohesive, multi-file bundle:

```text
skills/<procedural-skill-name>/
├── SKILL.md                          # Required: Sequential checklist & execution gates (< 500 lines)
├── scripts/                          # Optional: Pre-flight checks, build validators, deployment CLIs
│   └── preflight-check.sh            # Deterministic checks (stdout JSON, stderr diagnostics)
├── references/                       # Optional: Environment variables matrix, rollback runbooks
│   └── rollback-runbook.md
├── assets/                           # Optional: Configuration templates, manifests
│   └── deployment-manifest.yaml
└── evals/                            # Required: Verification test cases
    └── evals.json                    # Evals validating successful step execution
```

---

## 3. Procedural `SKILL.md` Design Patterns

### Pattern A: Checklists for Multi-Step Progress Tracking
Procedural skills must present an explicit progress checklist so the agent tracks state across turns and avoids skipping intermediate validation gates:

````markdown
## Deployment Checklist
Progress:
- [ ] Step 1: Pre-flight validation (execute `scripts/preflight-check.sh`)
- [ ] Step 2: Clean build generation (`pnpm build`)
- [ ] Step 3: Bundle integrity audit (`scripts/verify-bundle.sh`)
- [ ] Step 4: Staging release publication
- [ ] Step 5: Post-deployment health verification
````

### Pattern B: Plan-Validate-Execute Protocol
For destructive or mutating actions (migrations, deployments, deletions), enforce intermediate verification:
1. **Plan**: Generate a dry-run execution plan.
2. **Validate**: Run a deterministic validation script against the plan.
3. **Execute**: Proceed with the live operation only when validation exits with code 0.

### Pattern C: Mandatory Error Recovery & Rollback Gates
Every procedural skill must detail what to do when a step fails:

````markdown
## Failure Recovery & Rollback
- If build fails at Step 2: Halt immediately, do not proceed to release.
- If deployment fails at Step 4: Execute rollback command `wrangler pages rollback --commit=<prev>`.
````

---

## 4. Slash Command Parity (`/<skill-name>`)

Migrating from workflows to skills preserves 100% of user slash command muscle memory:

- **Legacy Workflow Trigger**: `/deploy-angular-spa-cloudflare`
- **Modern Procedural Skill Trigger**: `/deploy-angular-spa-cloudflare`

Antigravity automatically indexes all skills located in `.agents/skills/<name>/` and makes them available in the IDE slash command autocomplete menu. Furthermore, if both a workflow and a skill exist with the identical name, **the Skill takes precedence**.

---

## 5. Workflow to Skill Migration Checklist

When converting an existing `.agents/workflows/<name>.md` into a modular skill:

1. **Directory Creation**: `mkdir -p .agents/skills/<name>/`
2. **Move File**: Move `<name>.md` to `.agents/skills/<name>/SKILL.md`
3. **Frontmatter Standardize**:
   - Set `name: <name>` (kebab-case, matches directory).
   - Set `description: [Imperative third-person statement describing process and trigger: 'Triggered by /<name>']`.
4. **Extract Scripts**: Move inline shell blocks or complex validation commands into `scripts/<helper>.sh|py`.
5. **Add Evals**: Create `evals/evals.json` with 2 realistic test prompts and assertions verifying successful execution.
6. **Archive Workflow**: Delete or archive the old `.md` file to prevent duplicate indexing.
