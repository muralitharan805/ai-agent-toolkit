---
name: skill-authoring-standards
description: "Authoring guidelines and quality standards for creating production-ready skills, rules, and workflows in the agent-toolkit repository."
---
# Goal
Guide the agent in structuring, formatting, and authoring world-class AI agent skills, rules, and workflows that meet senior architect quality standards.

# Instructions
1. **Analyze Domain & Up-to-Date Patterns**: Before drafting any skill, rule, or workflow, identify the latest industry best practices and modern version standards for the target technology stack.
2. **Standardize Location**:
   - Framework specific → `frameworks/[framework]/[skills|rules|workflows]/`
   - Infrastructure specific → `infra/[tool]/[skills|rules|workflows]/`
   - Cross-cutting / general → `shared/[topic]/[skills|rules|workflows]/`
3. **Formulate Frontmatter**:
   - Skills: Include `name:` (kebab-case) and `description:` (third-person statement with semantic triggers).
   - Rules: Include `trigger: always_on` or `trigger: glob`, plus `description:`.
   - Workflows: Include `description:` and `trigger: manual` (or `file_change`/`pr_creation`).
4. **Draft High-Impact Content**:
   - Write clear, step-by-step logic protocols in `skills/`.
   - Write strict, unambiguous MUST / MUST NOT boundaries in `rules/`.
   - Write sequential, action-verb execution steps in `workflows/`.
5. **Include Non-Trivial Examples**: Provide real-world, production-ready code blocks for both correct and incorrect implementation patterns.

# Examples
Input: Author a skill for NestJS JWT authentication.
Output: Target path `frameworks/nestjs/skills/jwt-authentication/SKILL.md` with complete passport-jwt strategy configuration, guard implementation, error handling, and security constraints.

# Constraints
- Do NOT use outdated syntax or deprecated API methods in generated files.
- Do NOT write vague or conversational filler text in generated agent artifacts.
