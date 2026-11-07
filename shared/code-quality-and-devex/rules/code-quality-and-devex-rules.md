---
trigger: model_decision
description: "Enforces automated linting (ESLint strict), zero-debate formatting (Prettier), strict type safety (no any), pre-commit hooks (Husky/lint-staged), secret scanning (GitLeaks), and Conventional Commits."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# Code Quality, DevEx & Tooling Standards

## Description
Enforces mandatory engineering standards for automated code quality, developer experience (DevEx), and repository tooling across all services. Mandates automated strict linting (ESLint with typescript-eslint, Ruff, golangci-lint) to eliminate runtime defects, automated code formatting (Prettier, Black, gofmt) to remove style debates from code reviews, strict type-checking configuration (`strict: true` with zero `any`), staged pre-commit hooks (Husky and lint-staged) for sub-second developer feedback, pre-commit secret scanning (GitLeaks, TruffleHog) to prevent credential leakage, automated Conventional Commits validation, and one-command local environment orchestration via Docker Compose v2.

## Constraints

### 1. Automated Linting & Zero Style Debates
- Every repository MUST configure automated linters and code formatters:
  - **Node.js / TypeScript**: ESLint with `@typescript-eslint/recommended-type-checked` and Prettier.
  - **Python**: Ruff (or Flake8 + Black).
  - **Go**: `golangci-lint` and `gofmt`.
- Formatting rules MUST be enforced by automated tools; manual formatting debates during pull request code reviews are STRICTLY FORBIDDEN.
- Pull requests with unformatted code or unresolved linter errors MUST be automatically blocked by CI pipelines.

### 2. Strict Type Safety & Zero `any` Enforcement
- TypeScript configurations (`tsconfig.json`) MUST enable `strict: true`, `noImplicitAny: true`, `strictNullChecks: true`, and `noUncheckedIndexedAccess: true`.
- Using `any` as an explicit type annotation, cast, or parameter is STRICTLY FORBIDDEN. Developers must use `unknown` with runtime type narrowing, explicit interfaces, or generics.
- Python services MUST enforce strict type-checking using `mypy --strict` or `pyright`.
- Compiling code with type-checker bypasses (`@ts-ignore`, `type: ignore` without documented issue links) is prohibited.

### 3. Pre-Commit Hooks & Staged File Quality Gates
- Repositories MUST configure automated pre-commit hooks using Husky, lint-staged, or the `pre-commit` framework.
- Pre-commit hooks MUST execute only against git-staged files (`lint-staged`) to guarantee sub-second execution speed:
  1. **Linter**: Rejects commit if lint errors are introduced.
  2. **Formatter**: Auto-formats staged files or rejects if formatting is invalid.
  3. **Type Checker**: Runs `tsc --noEmit` to verify type safety across modified files.
  4. **Secret Scanner**: Scans staged diffs for leaked API keys, tokens, or private certificates.
- Committing code directly by bypassing hooks (`git commit --no-verify`) is strictly forbidden in normal development workflows.

### 4. Mandatory Conventional Commits Enforcement
- All commit messages MUST adhere to the Conventional Commits 1.0.0 specification:
  - Format: `<type>(<scope>): <description>`
  - Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`.
  - The subject line MUST be lowercase, imperative, and under 72 characters.
- Repositories MUST enforce this format at the git level using a `commit-msg` hook (e.g. `@commitlint/cli` with `@commitlint/config-conventional`).
- Commits with unstructured messages (e.g. `fixes`, `temp`, `wip`, `update`) are rejected immediately.

### 5. Pre-Commit Secret Scanning & Leak Prevention
- Every repository MUST integrate automated secret scanning tools (GitLeaks, TruffleHog, or GitHub Secret Scanning).
- Secret scanners MUST run both as a local pre-commit hook on staged changes and as a mandatory CI pull request gate.
- Hardcoding secrets, JWT private keys, database passwords, cloud credentials, or live API tokens in source code or configuration templates is STRICTLY FORBIDDEN.
- Sample configuration files (`.env.example`) MUST contain only documented placeholder strings.

### 6. One-Command Local Development Environment
- Every backend service MUST provide a self-contained, reproducible local environment orchestrated via Docker Compose v2 (`compose.yaml` or `docker-compose.yml`).
- Running `docker compose up -d` MUST launch all required backing services (PostgreSQL, Redis, RabbitMQ/Kafka, LocalStack) with pre-configured health checks.
- Backing services MUST NOT require manual host installations or multi-step manual setup procedures.

## Examples

### 1. Pre-Commit Hook Configuration (`lint-staged` & `commitlint`)
```json
// package.json configuration enforcing staged formatting, linting, and type checking
{
  "scripts": {
    "prepare": "husky",
    "typecheck": "tsc --noEmit"
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix --max-warnings=0",
      "prettier --write"
    ],
    "*.{json,md,yml,yaml}": [
      "prettier --write"
    ]
  }
}
```

### 2. Conventional Commit-Msg Hook (`commitlint.config.js`)
```javascript
// ✅ CORRECT: Enforces standardized Conventional Commit headers
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'refactor', 'test', 'chore', 'perf', 'ci', 'build'],
    ],
    'subject-case': [2, 'never', ['upper-case', 'pascal-case']],
    'header-max-length': [2, 'always', 72],
  },
};
```

### 3. Docker Compose v2 One-Command Local Backing Services
```yaml
# ✅ CORRECT: compose.yaml providing reproducible local backing services with health probes
services:
  postgres:
    image: postgres:16-alpine
    container_name: local_postgres
    environment:
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: dev_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user -d dev_db"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: local_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```
