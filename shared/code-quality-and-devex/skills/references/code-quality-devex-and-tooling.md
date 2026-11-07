# Code Quality, DevEx & Tooling Architecture Reference

## Overview
This reference establishes the engineering principles and tooling configuration for automated code quality, developer experience (DevEx), and repository governance. It details the **Automated Tooling Matrix**, **Pre-Commit Hook Pipeline (Husky + lint-staged)**, **Strict Type Safety Enforcement**, **Secret Scanning (GitLeaks)**, **Conventional Commits (commitlint)**, and **One-Command Local Environment (Docker Compose v2)**.

---

## 1. Automated Tooling Matrix by Ecosystem

| Ecosystem | Linter | Formatter | Type Checker | Secret Scanner |
| :--- | :--- | :--- | :--- | :--- |
| **Node.js / TypeScript** | ESLint (`@typescript-eslint/recommended-type-checked`) | Prettier | `tsc --noEmit` (`strict: true`) | GitLeaks / TruffleHog |
| **Python** | Ruff / Flake8 | Ruff format / Black | `mypy --strict` / `pyright` | GitLeaks / TruffleHog |
| **Go** | `golangci-lint` | `gofmt` | Native Go Compiler | GitLeaks |
| **Java** | Checkstyle / SpotBugs | `google-java-format` | Native Java Compiler | GitLeaks / Snyk |
| **.NET / C#** | Roslyn Analyzers | `dotnet format` | C# Nullable Reference Types | GitLeaks |

---

## 2. Strict Type Safety Configuration

TypeScript projects must configure `tsconfig.json` to eliminate implicit coercions and enforce explicit types:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  }
}
```

### Prohibition of `any`
- Explicit `any` annotations bypass compiler type-checking, masking critical nullability and runtime type bugs.
- **Production Standard**: Use `unknown` with user-defined type predicates (`isUser(val: unknown): val is User`), utility types (`Record<string, unknown>`), or generics.

---

## 3. Pre-Commit Hook Pipeline Architecture

Running test suites or full linting against an entire repository on every git commit degrades developer velocity. To achieve sub-second pre-commit feedback, execute tasks strictly against staged files:

```
[Developer runs: git commit -m "feat(auth): add refresh token rotation"]
                           │
                           ▼
                 [.husky/pre-commit]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
   [lint-staged on Staged Files]   [GitLeaks Staged Scan]
   ├─► Prettier auto-formatting    └─► Detect hardcoded API keys/secrets
   ├─► ESLint autofix & validation
   └─► tsc --noEmit typecheck
             │
             ▼
                 [.husky/commit-msg]
                           │
                           ▼
          [@commitlint/cli Validation]
          └─► Validate header: <type>(<scope>): <description>
                           │
                           ▼
               [Commit Saved to Git History]
```

### Husky & lint-staged Setup
```bash
# 1. Install dev dependencies with pnpm
pnpm add -D husky lint-staged @commitlint/cli @commitlint/config-conventional

# 2. Initialize Husky
pnpm exec husky init
```

`.husky/pre-commit`:
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

pnpm exec lint-staged
gitleaks protect --staged --verbose
```

`.husky/commit-msg`:
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

pnpm exec commitlint --edit "$1"
```

---

## 4. Conventional Commits 1.0.0 Specification

Commit messages must provide deterministic semantic metadata for automated changelog generation and semantic release tagging.

### Format
```text
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Allowed Types
- `feat`: A new feature introduced to the application.
- `fix`: A bug fix patching an existing issue.
- `docs`: Documentation-only modifications (README, inline TSDoc).
- `refactor`: Code changes that neither fix a bug nor add a feature.
- `perf`: Code changes that improve runtime performance or memory usage.
- `test`: Adding missing tests or correcting existing test suites.
- `chore`: Maintenance tasks, dependency bumps, or script improvements.
- `ci`: Changes to CI/CD pipelines, workflows, or build scripts.
- `build`: Changes affecting the build system or external dependencies.

---

## 5. Pre-Commit Secret Scanning with GitLeaks

GitLeaks inspects regex rules and entropy thresholds to prevent secret keys from reaching git history.

### `.gitleaks.toml` Baseline Configuration
```toml
[extend]
useDefault = true

[allowlist]
description = "Global allowlisted test mock secrets"
paths = [
  '''^\.env\.example$''',
  '''evals/.*''',
  '''test/fixtures/.*'''
]
```

---

## 6. One-Command Local Development Environment (Compose v2)

Every repository must provide a `compose.yaml` to spin up local infrastructure in a single command (`docker compose up -d`):

```yaml
services:
  database:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DATABASE_USER:-postgres}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-postgres}
      POSTGRES_DB: ${DATABASE_NAME:-dev_db}
    ports:
      - "${DATABASE_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d dev_db"]
      interval: 5s
      timeout: 3s
      retries: 5

  cache:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```
