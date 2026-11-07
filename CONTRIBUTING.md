# Contributing to AI Agent Toolkit (`CONTRIBUTING.md`)

Thank you for your interest in contributing to **`ai-agent-toolkit`**! We welcome improvements, new framework skills, infrastructure patterns, and bug fixes from the global open-source community.

---

## 1. Code of Conduct & Architectural Rigor

All contributions must reflect the depth, foresight, and rigor of a seasoned Principal Software Architect:
- **No Tutorial-Ware**: Reject simplistic, superficial happy-path examples. Code must handle error boundaries, timeouts, unsubscriptions, and concurrency safety.
- **Strict Currency**: Use current framework releases only (Angular 19+ Signals/Standalone, NestJS 11 Clean Architecture, Docker Compose v2). Obsolete patterns (e.g. Angular `NgModule`, legacy Docker `links`) are strictly prohibited.
- **Type Safety**: The use of explicit `any` types is strictly forbidden across all code, tests, and examples.
- **Zero Hallucination**: Do not introduce unverified APIs or fake library functions.

---

## 2. Authoring Guidelines

### Adding or Updating an Agent Skill
1. **Deduplication Check**: Inspect `frameworks/`, `infra/`, and `shared/` to ensure no overlapping skill exists. If one exists, enhance the existing bundle rather than creating duplicates.
2. **5-Pillar Directory Structure**:
   ```text
   [category]/[topic]/skills/
   ├── SKILL.md                          # Pillar 1 (< 500 lines, YAML frontmatter)
   ├── references/                       # Pillar 2 (authoritative guides)
   ├── scripts/                          # Pillar 3 (standalone automation tools)
   ├── assets/                           # Pillar 4 (schemas & starter templates)
   └── evals/                            # Pillar 5 (evals.json test suite)
   ```
3. **Automated Skill Validation**:
   Run the bundled skill validator before committing:
   ```bash
   uv run tools/generators/generate-skill/skills/scripts/validate_skill.py [path-to-skill]
   ```
   Must exit with code `0` (zero errors).

### Adding or Updating an Antigravity Rule
1. Place rules under `[category]/[topic]/rules/[rule-name].md`.
2. **Rule budget**: Target 6,000–8,000 characters for maintainability (toolkit convention). Antigravity limits each rule file to 24,000 UTF-8 bytes after expanding inline includes.
3. **Trigger Strategy**:
   - `trigger: model_decision` (Recommended Default for domain patterns; loaded on demand).
   - `trigger: glob` with a quoted, comma-separated string, e.g. `globs: "**/*.ts, **/*.tsx"` (filetype-specific).
   - `trigger: always_on` (Reserved strictly for universal invariants like Clean Code).
4. **Automated Rule Validation**:
   ```bash
   python3 tools/generators/generate-rule/skills/scripts/validate_rule.py [path-to-rule]
   ```
   Must exit with code `0`.

---

## 3. Local Development & Verification Workflow

1. **Clone the repository**:
   ```bash
   git clone https://github.com/muralitharan805/ai-agent-toolkit.git
   cd ai-agent-toolkit
   ```

2. **Verify Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Automated Test Suite**:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   ```

4. **Run the Whole-Ecosystem Health Audit**:
   ```bash
   python3 tools/generators/audit-agent-toolkit/skills/scripts/audit_toolkit.py .
   ```
   Inspect and resolve actionable findings before release. This health audit is a separate, manual check and is **not** an enforced CI gate.

---

## 4. Pull Request & Commit Standards

- All commits must adhere to the **Conventional Commits 1.0.0** specification:
  - Format: `<type>(<scope>): <description>`
  - Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`.
  - Imperative, lowercase subject under 72 characters (e.g. `feat(angular): add signals reactive form validation skill`).
- Create a feature branch:
  ```bash
  git checkout -b feat/add-redis-caching-skill
  git commit -m "feat(infra): add redis caching and ttl invalidation skill"
  git push origin feat/add-redis-caching-skill
  ```
- Open a Pull Request on GitHub against the `main` branch. GitHub Actions CI runs Bash syntax checks, Python compilation, unit/integration tests, representative Agent Skill validation, and Gitleaks secret scanning. The whole-ecosystem health audit above remains a manual maintainer check and is not enforced by CI.

