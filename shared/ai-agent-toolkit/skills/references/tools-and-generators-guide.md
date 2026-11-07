# Tools & Generator Architecture Guide

## Purpose

`tools/` contains toolkit-internal capabilities used to create, transform, validate, evaluate, audit, consolidate, migrate, or maintain agent context. It is intentionally separate from consumer context roots.

## Dynamic Hierarchy

```text
tools/
└── <family>/
    └── <tool-name>/
        ├── skills/
        │   ├── SKILL.md
        │   ├── references/
        │   ├── scripts/
        │   ├── assets/
        │   └── evals/
        └── rules/              # optional
```

`generators/` is the first family, not a hardcoded special case. Discovery must recurse through `tools/` so additional families can be introduced without changing the context resolver.

## Placement Decision

Use this decision order before creating anything:

1. Search all existing consumer roots and `tools/` for overlap.
2. If the capability teaches an application agent how to work with a framework, platform, domain, or general engineering standard, place it under `frameworks/`, `infra/`, `domains/`, or `shared/`.
3. If the capability primarily operates on the toolkit or produces toolkit context, place it under `tools/<family>/<tool-name>/`.
4. If the capability generates skills, rules, prompts, suites, or other context bundles, prefer `tools/generators/<tool-name>/`.
5. If no existing family fits, create a semantically named family instead of forcing the tool into `generators/`.

## Generator Contract

A generator tool must:

- discover the correct output taxonomy before writing;
- smart-upsert existing related context instead of duplicating it;
- emit or modify the standard module structure;
- keep deep guidance in references and deterministic work in scripts;
- provide objective eval scenarios;
- state exact validator commands;
- avoid hardcoded lists of existing tool names;
- never assume generated output belongs under `tools/` solely because the generator itself lives there.

## Example

A request to create a new generator that scaffolds API contract context should produce something like:

```text
tools/generators/generate-api-contract-context/
├── skills/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   ├── assets/
│   └── evals/
└── rules/                    # only if generator-specific invariants are needed
```

But when that generator runs for a NestJS API, its generated consumer context would normally belong under a consumer root, for example:

```text
frameworks/nestjs/nestjs-api-contracts/
├── skills/
└── rules/
```

## Sync Boundary

`tools/` is excluded from default consumer sync and `--all`. Internal tool context is installed only when explicitly selected:

```bash
./bin/context.sh -w tools/generators/generate-skill --target /path/to/toolkit-dev
```

## Validation

Use the generators and validators from the tools hierarchy:

```bash
uv run tools/generators/generate-skill/skills/scripts/validate_skill.py <skill-path>
uv run tools/generators/generate-rule/skills/scripts/validate_rule.py <rule-path>
uv run tools/generators/generate-agent-suite/skills/scripts/verify_suite.py <module-path>
```
