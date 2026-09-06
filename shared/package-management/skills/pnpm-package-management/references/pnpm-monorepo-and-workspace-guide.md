# pnpm Monorepo & Workspace Orchestration Guide

## 1. Monorepo Workspace Configuration (`pnpm-workspace.yaml`)

`pnpm` provides first-class, lightning-fast monorepo workspace orchestration without requiring heavy third-party task runners like Lerna. A monorepo workspace is defined by declaring `pnpm-workspace.yaml` in the root repository directory:

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'frameworks/*'
  - 'shared/*'
```

---

## 2. Workspace Filtering Syntax (`--filter`)

The `--filter` selector enables granular targeting of specific packages, their dependencies, or their dependents:

| Command | Behavior |
| :--- | :--- |
| `pnpm --filter @org/web-app build` | Executes `build` script exclusively inside `@org/web-app`. |
| `pnpm --filter @org/web-app... build` | Builds `@org/web-app` AND all of its internal workspace dependencies first. |
| `pnpm --filter ...@org/core build` | Builds `@org/core` AND all packages that depend on `@org/core`. |
| `pnpm --filter ...[origin/main] test` | Runs tests only in packages modified between current branch and `origin/main`. |
| `pnpm -r run build` | Recursively executes `build` across every workspace package in topological order. |

---

## 3. Internal Workspace Protocol Linking (`workspace:*`)

When declaring dependencies between packages inside the same monorepo, always use the `workspace:*` or `workspace:^` protocol in `package.json`:

```json
{
  "name": "@org/web-app",
  "version": "1.0.0",
  "dependencies": {
    "@org/ui-kit": "workspace:*",
    "@org/shared-utils": "workspace:^"
  }
}
```

### Benefits of the Workspace Protocol
1. **Zero Symlink Drift**: Guarantees that local packages always link to the active source code in the monorepo during development.
2. **Publish-Time Resolution**: When publishing packages to an npm registry via `pnpm publish`, `pnpm` automatically replaces `workspace:*` with the exact SemVer release version (e.g. `1.2.0`).

---

## 4. Parallelized & Topological Script Execution

By default, `pnpm -r` respects the dependency graph between packages, ensuring dependencies are built before their consumers:

```bash
# Execute build across all packages topologically with concurrency
pnpm -r --workspace-concurrency 4 run build

# Run unit tests across all packages in parallel
pnpm -r --parallel test
```
