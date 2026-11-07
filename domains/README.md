# Domains Layer (`domains/`)

This directory holds project-specific business domain rules, schemas, and skills for custom enterprise applications.

## Open-Source Security & Isolation
To protect proprietary business logic when publishing `ai-agent-toolkit` as a public open-source repository on GitHub:
- **Private by default:** `.gitignore` excludes `domains/*` except this README. New domain bundles are not automatically tracked by Git.
- **Public contributions:** After explicitly reviewing a reusable domain bundle for secrets, personal information, proprietary content, and licenses, maintainers may deliberately stage it with `git add -f domains/<reviewed-public-domain>/...`. Do not force-add private domain content.
- **Confidential content:** Keep enterprise-specific modules in private forks or locally ignored directories; review what is already tracked and the full Git history before any public release.

## Synchronization
The `bin/context.sh` sync engine automatically discovers and synchronizes domain modules into target project workspaces (`.agents/` or `.claude/`) using dynamic selector syntax:

```bash
# Sync specific domain context into target project
./bin/context.sh -w domains/<your-domain> --target ~/path/to/project
```
