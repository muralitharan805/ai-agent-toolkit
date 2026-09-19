---
name: modular-skill-blueprint
description: A reference model skill demonstrating the 4-pillar directory structure (SKILL.md, references, scripts, assets, evals) and 3-tier progressive disclosure. Use as a structural blueprint when generating new skills.
compatibility: Requires Bash, Python 3.9+, and jq.
---

# Modular Skill Blueprint

This skill serves as the canonical reference implementation of an Agent Skill adhering to the Agent Skills Open Standard and Google Antigravity IDE.

---

## 1. Quick Start Workflow

Follow this procedure when executing domain tasks:

1. **Verify Environment Prerequisites**:
   Run the bundled diagnostic runner:
   ```bash
   bash scripts/sample-runner.sh --check
   ```
2. **Apply Domain Logic**:
   - For standard workflows, apply the core procedure below.
   - For complex edge cases, review [Deep Domain Guide](references/domain-guide.md).
3. **Format Output**:
   Structure all responses against the schema defined in [Output Schema](assets/output-schema.json).

---

## 2. Progressive Disclosure Pointers

Depending on the specific sub-task, inspect the following focused reference guides on demand:

- **Technical Architecture & Invariants**: [references/domain-guide.md](references/domain-guide.md)
- **Output Schema Definition**: [assets/output-schema.json](assets/output-schema.json)
- **Quality Assurance & Verification**: [evals/evals.json](evals/evals.json)

---

## 3. Gotchas

- **Idempotency**: All scripts must be run with safe defaults; re-running must not create duplicate entities.
- **Environment Isolation**: Always execute commands from the project root rather than assuming current working directory is inside subfolders.
- **JSON Formatting**: Always output clean, unescaped JSON on stdout; send progress messages to stderr.

---

## 4. Script Execution Interface

Run the bundled automation helper:
```bash
bash scripts/sample-runner.sh --action execute --target sample.txt
```
To inspect available options, run `bash scripts/sample-runner.sh --help`.
