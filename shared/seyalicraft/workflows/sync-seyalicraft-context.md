---
description: "Workflow to synchronize Seyalicraft ecosystem context, product suite details, and project rules into a target workspace. Triggered by 'seyalicraft:', 'sync-seyalicraft:', or '/sync-seyalicraft-context'."
trigger: manual
---

# Sync Seyalicraft Context Workflow

This workflow synchronizes Seyalicraft master context, product domain architectures, and engineering standards from `ai-agent-toolkit` into any target Seyalicraft project directory.

## Step 1: Verify Target Directory

1. Ensure target directory exists and is a Seyalicraft repository (e.g. `seyalicraft-frontend`, `nidhiflow-frontend`, `nidhiflow-backend`).
2. Verify `bin/sync-skills.sh` script is available in `ai-agent-toolkit`.

## Step 2: Execute Sync Script

Run the synchronization command from `ai-agent-toolkit`:

```bash
./bin/sync-skills.sh --shared --target /path/to/target-seyalicraft-project
```

## Step 3: Verify Sync Result

1. Check that `.agents/skills/seyalicraft-ecosystem-context/SKILL.md` exists in target workspace.
2. Check that `.agents/rules/seyalicraft-project-standards.md` exists in target workspace.
3. Verify that the AI Agent in the target workspace re-indexes the `.agents/` folder.
