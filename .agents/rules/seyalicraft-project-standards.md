# Seyalicraft Enterprise Engineering Standards

## Description
Enforces mandatory standards, domain naming conventions (`seyalicraft.com`), repository commit scoping, zero `any` policy, pnpm package manager usage, and security rules across all Seyalicraft repositories and product suites.

## Constraints

### 1. Mandatory Root Domain & Subdomain Conventions
- All production endpoints, environment configs, and CORS policies MUST align with `seyalicraft.com` domains:
  - Main Portal: `seyalicraft.com`
  - NidhiFlow: `nidhiflow.seyalicraft.com` / `api.nidhiflow.seyalicraft.com`
  - CivicPath: `civicpath.seyalicraft.com` / `api.civicpath.seyalicraft.com`

### 2. Git Conventional Commit Scoping
- All commit messages across Seyalicraft repositories MUST follow conventional commits with explicit product scope:
  - `feat(nidhiflow-frontend): add EMI amortization chart component`
  - `fix(nidhiflow-backend): enforce double-entry ledger balance check`
  - `chore(seyalicraft-portal): update dependencies via pnpm`

### 3. Package Manager & Script Rules
- All Seyalicraft repositories MUST strictly use `pnpm` (`pnpm install`, `pnpm add`, `pnpm run dev`).
- `npm` or `yarn` lockfiles MUST NOT be committed to Git.

### 4. Zero Hardcoded Secrets & Environment Isolation
- Secrets (JWT secrets, DB connection strings, API keys) MUST be loaded exclusively via environment variables (`process.env`).
- Never hardcode credentials in code files or git-tracked configs.

### 5. Type Safety & API Documentation
- Explicit type annotations MUST be used throughout (`any` is forbidden).
- Public classes, services, and endpoints MUST have JSDoc/TSDoc comments detailing purpose, parameters, and exceptions.
