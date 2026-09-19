# Skill Best Practices & Gotchas Pattern

> Authoring principles derived from real-world agent execution and the Agent Skills Open Standard.

## 1. Grounding in Real Expertise
A common failure mode in AI-generated skills is generic, shallow advice:
- *Generic (Bad)*: "Handle errors appropriately and follow REST best practices."
- *Expertise-Grounded (Good)*: "Catch `PrismaClientKnownRequestError` with code `P2002` and map to `ConflictException` ('Email already registered')."

Effective skills capture:
- Project-specific conventions and non-obvious API schemas.
- Recurring reviewer feedback and hard lessons from incident post-mortems.
- Production-grade edge cases and explicit failure recoveries.

---

## 2. Spending Context Wisely
Once a skill activates, every token in `SKILL.md` directly competes with the user's conversation history and active tools for attention.

### Add What the Agent Lacks, Omit What It Knows
- Do NOT explain basic concepts (e.g., what a JWT is, how HTTP GET works, or what a relational database is).
- DO provide proprietary business rules, domain schemas, specific library quirks, and project directory mappings.
- Ask: *"Would a senior software engineer or modern LLM get this wrong without being told?"* If no, remove it.

### Design Coherent, Composable Units
- Scope skills like functions: each skill should encapsulate one coherent domain or lifecycle.
- Avoid "do everything" monolithic skills. Instead of `backend-fullstack-dev`, separate into `nestjs-module-authoring`, `postgres-multi-schema-architecture`, and `caching-strategies`.

---

## 3. Calibrating Control: Specificity vs Freedom

### Match Specificity to Fragility
- **Give freedom** when multiple approaches are valid and the task tolerates variation (e.g., code refactoring, styling tweaks). Explain the *why* rather than prescribing rigid single lines.
- **Be strictly prescriptive** when operations are fragile, destructive, or have exact sequence dependencies (e.g., database schema migrations, production deployments, financial ledgers).

### Provide Defaults, Not Menus
- Do NOT present 5 alternatives as equal choices: *"You can use Jest, Vitest, Mocha, Jasmine, or AVA..."*
- DO pick a strong, opinionated default and mention alternatives with explicit escape hatches:
  ```markdown
  Use Vitest as the primary test runner:
  `pnpm vitest run`
  For legacy projects requiring Jest, pass the `--jest` flag.
  ```

### Procedures Over Declarations
- Teach the agent *how to approach* the problem class systematically, not just what the end result looked like on one specific run.

---

## 4. The High-Value "Gotchas" Section

The highest-leverage section in any skill is `## Gotchas`. This section collects non-obvious traps, hidden gotchas, and environment quirks that defy reasonable assumptions:

```markdown
## Gotchas

- The `users` table uses soft deletes. All queries MUST include `WHERE deleted_at IS NULL` or results will include deactivated accounts.
- In Prisma, `Decimal` types serialize as strings in JSON responses. Helper `serializeDecimal()` must be applied in controllers.
- The `/health` endpoint returns 200 even if Redis is unreachable; always inspect `/health/readiness` for full cluster state.
```

Whenever an agent makes a mistake during real-world task execution, capture the correction as a new bullet point in the `## Gotchas` section.

---

## 5. Concrete Output Format Templates
Agents adhere to structure significantly better when shown concrete markdown or JSON templates rather than descriptive prose:

```markdown
## Output Report Structure
When generating the analysis, adhere to this format:

```markdown
# [Domain] Security Audit Report
- Target Service: [service-name]
- Severity: [HIGH | MEDIUM | LOW]

### Identified Vulnerabilities
1. **[CVE or OWASP Category]**: [Concise description]
   - *Remediation*: [Actionable code snippet]
```
```
