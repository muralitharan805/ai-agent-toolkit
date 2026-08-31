---
trigger: always_on
description: "Enforces mandatory quality standards, YAML frontmatter GUI compatibility, strict deduplication/upserting policies, and structured directory organization across all skills, rules, and workflows in the ai-agent-toolkit repository."
---

# AI Agent Toolkit Authoring & Quality Control Rules

## Description
Enforces mandatory quality standards, YAML frontmatter GUI compatibility, strict deduplication/upserting policies, and structured directory organization across all skills, rules, and workflows in the `ai-agent-toolkit` repository.

## Constraints

### 1. Mandatory Deduplication & Upsert Policy
- Before creating a new file, search the repository (`frameworks/`, `infra/`, `shared/`) for existing files on the topic.
- If a related file exists, update and merge the new information into the existing file instead of creating duplicate files.

### 2. Strict YAML Frontmatter Rules
- **Skills**: Must include `name` (kebab-case) and `description` (third-person routing statement).
- **Workflows**: Must include `description` (with triggers in the string) and `trigger: manual`. Never use `aliases:` or unparsed YAML keys.
- **Rules**: Must include `description` and `trigger: always_on` or `trigger: glob`.

### 3. File Path & Taxonomy Structure
- Framework specific: `frameworks/<framework_name>/(skills|rules|workflows)/`
- Infrastructure specific: `infra/<tool_name>/(skills|rules|workflows)/`
- Shared/Domain specific: `shared/<topic_name>/(skills|rules|workflows)/`

### 4. Language & Quality Standards
- All written instruction text MUST use professional, technical English with non-trivial code examples.
- Code blocks MUST be production-ready and type-safe (zero `any` types).
