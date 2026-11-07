# Script & Tool Design for Agent Skills

> Principles for designing CLI tools and executable scripts bundled in `scripts/` or referenced in skills.

## 1. One-Off Commands vs Bundled Scripts

### When to Use One-Off Commands
Use one-off commands directly in `SKILL.md` when established CLI tools already accomplish the task:
- **Python**: Use `uvx` (fast isolated environment): `uvx ruff@0.8.0 check .`
- **Node.js**: Use `pnpm dlx` or `npx`: `pnpm dlx prettier@3.2.0 --check .`
- **Deno**: Use `deno run`: `deno run --allow-read npm:eslint@9 --fix .`

**Rules for one-off commands**:
- Always pin exact versions (`tool@1.2.3`) to prevent unexpected breakage across agent runs.
- Document system prerequisites in frontmatter (`compatibility: Requires Node.js 20+ and Docker`).

### When to Bundle in `scripts/`
Move commands into `scripts/` when:
- Logic exceeds 2–3 piped commands.
- Repetitive data transformations or custom API querying are needed.
- Complex input validation or deterministic safety gates are required.

---

## 2. Self-Contained Scripts with Inline Dependencies

Do NOT require users or agents to manage a separate `package.json` or `requirements.txt` just for a helper script. Use inline dependency metadata:

### Python (PEP 723 via `uv run`)
Declare dependencies inside `# /// script` blocks. The runner (`uv` or `pipx`) auto-installs in an ephemeral virtualenv:

```python
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# requires-python = ">=3.11"
# ///

import sys
import yaml

def main():
    print("Executing self-contained validation...")

if __name__ == "__main__":
    main()
```
Run with: `uv run scripts/validate.py` or `python3 scripts/validate.py`.

### TypeScript / JavaScript (via Deno or Node)
Use Deno's native `npm:` specifiers:
```typescript
#!/usr/bin/env -S deno run --allow-read

import * as cheerio from "npm:cheerio@1.0.0";
```

---

## 3. Agentic CLI Interface Design

Agents interact with scripts through stdin, stdout, stderr, and exit codes. Follow these interface standards:

### Data to `stdout`, Diagnostics to `stderr`
- **`stdout`**: Reserved strictly for structured, parseable payloads (JSON, CSV, TSV).
- **`stderr`**: Reserved for human progress messages, logs, warnings, and diagnostic traces.
This allows the agent to pipe `stdout` into `jq` or parse it directly without string filtering bugs.

### Actionable Error Messages
Opaque errors waste turns. When input validation fails, output:
1. What went wrong.
2. What was received.
3. Allowed values / how to correct it.

```text
Error: --format must be one of: [json, csv, table]
       Received: "xml"
Usage: python3 scripts/report.py --format json <data.csv>
```

### Black-Box `--help` Introspection
Agents inspect unfamiliar tools by running `--help`. Every script MUST support `--help` or `-h` and exit with code 0, displaying concise synopsis, options, and realistic examples:

```text
Usage: scripts/validate.sh [options] <workspace-dir>

Options:
  --strict    Enforce zero-warning policy
  --json      Output machine-readable report to stdout

Examples:
  scripts/validate.sh --json ./project
```

### Idempotency
Agents frequently retry commands upon partial failures or model re-invocations.
- Ensure scripts are idempotent: *"create if not exists"* is strictly safer than *"create and fail on duplicate"*.
