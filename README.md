# agent-toolkit

Central repository of reusable **skills**, **rules**, and **workflows** for AI coding agents (e.g. Google Antigravity IDE). Instead of writing agent context from scratch in every project, this toolkit lets you scaffold or sync a consistent `.agents/` directory into any repo — Angular, Node, NestJS, Strapi, Docker, or otherwise.

## Why this exists

Every project's `.agents/` folder tends to be written once and then drift — different naming, inconsistent structure, no reuse across projects. This repo centralizes that knowledge so:

- New projects get a battle-tested `.agents/` setup on day one.
- Existing projects can pull in updates without hand-copying files.
- Framework-specific knowledge (Angular, NestJS, Strapi, Docker, Postgres, Redis...) lives in one place instead of being duplicated per repo.

## Structure

```
agent-toolkit/
├── frameworks/           # Framework/language-specific agent context
│   ├── angular/
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── nestjs/
│   └── strapi-v5/
│
├── infra/                 # Infrastructure & DevOps layer context
│   ├── docker/
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── postgres/
│   │   └── skills/
│   └── redis/
│       └── skills/
│
├── shared/                # Cross-cutting, topic-based agent context
│   ├── generators/       # AI Skill, Rule, & Workflow generator workflows
│   │   └── workflows/
│   ├── git/              # Git conventions & commit standards
│   │   └── skills/
│   ├── security/         # Secret masking & OWASP rules
│   │   └── rules/
│   └── code-quality/     # Clean code & type safety standards
│       └── rules/
│
└── bin/                    # Scripts to scaffold/sync skills into real projects
    ├── scaffold-angular.sh
    ├── link-skills.sh
    └── sync-skills.sh
```

### skills/ vs rules/ vs workflows/

| Folder | Purpose | Example |
|---|---|---|
| `skills/` | "How to do X well" — reference patterns, best practices | `signal-state-management/SKILL.md` |
| `rules/` | Hard constraints the agent must always follow | "Never use `any` type", commit message format |
| `workflows/` | Step-by-step sequences for common multi-step tasks | "Add new feature module" → scaffold → route → test → barrel export |

## Usage

### 1. Scaffold a brand-new project

once you setup or run you project ( any framword). create .agents directory in you project. inside .agents directory we manage skills, rules, workflows.

### 2. Add skills to an existing project

copy the folder from  agent-toolkit/frameworks/<framword-name>/skills, rules, workflows and paste into .agents/skills, rules, workflows.

### 3. Sync updates into a project that already has copied

this repo is continuosly updated with new skills, rules, workflows. Pull the latest framework + shared skills from the toolkit and overwrites the local copies.

### 4. Generating new Skills, Rules, or Workflows with AI

This repository includes built-in AI generator workflows (supporting prompts in English, Tamil, or Thanglish):
- **Generate Skill**: `shared/generators/workflows/generate-skill.md` → Creates `[framework|infra|shared]/[topic]/skills/[skill-name]/SKILL.md`
- **Generate Rule**: `shared/generators/workflows/generate-rule.md` → Creates `[framework|infra|shared]/[topic]/rules/[rule-name].md`
- **Generate Workflow**: `shared/generators/workflows/generate-workflow.md` → Creates `[framework|infra|shared]/[topic]/workflows/[workflow-name].md`


## Adding a new framework

1. Create `frameworks/<framework-name>/{skills,rules,workflows}/`.
2. Add a `SKILL.md` per topic (frontmatter + content).
3. Add a corresponding `scaffold-<framework>.sh` in `bin/` if the framework needs its own project-init command.

## Conventions

- Directory is always `.agents/` (singular) inside consumer projects — not `.agentss/` — to match what agent IDEs (e.g. Antigravity) auto-discover.
- Each `SKILL.md` should be self-contained: one skill, one file, clear frontmatter (name, description, trigger conditions).
- Cross-cutting knowledge (git conventions, code review checklists, documentation standards) goes in `shared/`, not duplicated per framework.

## Roadmap / ideas

- [ ] Add `frameworks/nextjs/`
- [ ] Add `frameworks/java-spring-boot/`
- [ ] `bin/scaffold-nestjs.sh`
- [ ] CI check that validates every `SKILL.md` has required frontmatter
