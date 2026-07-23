---
name: skill-authoring-standards
description: "Authoring guidelines, deduplication logic, and quality standards for creating or updating production-ready skills, rules, and workflows in the agent-toolkit repository."
---
# Goal
Guide the agent in structuring, formatting, deduplicating, and authoring world-class AI agent skills, rules, and workflows that meet senior architect quality standards.

# Instructions
1. **Existing File Discovery & Upsert**: Before creating any file, check if a related skill, rule, or workflow already exists under `frameworks/`, `infra/`, `shared/`, or `.agents/`. If found, enhance and merge new data into the existing file instead of creating a duplicate.
2. **Analyze Domain & Up-to-Date Patterns**: Identify the latest industry best practices and modern version standards for the target technology stack.
3. **Standardize Location**:
   - Framework specific → `frameworks/[framework]/[skills|rules|workflows]/`
   - Infrastructure specific → `infra/[tool]/[skills|rules|workflows]/`
   - Cross-cutting / general → `shared/[topic]/[skills|rules|workflows]/`
4. **Formulate Frontmatter**:
   - Skills: Include `name:` (kebab-case) and `description:` (third-person statement with semantic triggers).
   - Rules: Include `trigger: always_on` or `trigger: glob`, plus `description:`.
   - Workflows: Include `description:` and `trigger: manual` (or `file_change`/`pr_creation`).
5. **Draft High-Impact Content**:
   - Write clear, step-by-step logic protocols in `skills/`.
   - Write strict, unambiguous MUST / MUST NOT boundaries in `rules/`.
   - Write sequential, action-verb execution steps in `workflows/`.
6. **Include Non-Trivial Examples**: Provide real-world, production-ready code blocks for both correct and incorrect implementation patterns.

# Examples
Input: Update NestJS authentication skill with refresh token rotation.
Output: Target existing file `frameworks/nestjs/skills/jwt-authentication/SKILL.md` and append refresh token logic protocols and security constraints.

# Constraints
- Do NOT create duplicate files for topics that already have an established skill, rule, or workflow.
- Do NOT overwrite existing valuable instructions when updating a file; merge new enhancements cleanly.
- Do NOT use outdated syntax or deprecated API methods in generated files.
