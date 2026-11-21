---
name: export-skills
description: "Packages and exports toolkit context modules into distribution-ready zip archives and raw copy-pasteable system prompts for ChatGPT Customizations (OpenAI Agent Skills) and Google Gemini Custom Skills. Employs smart synthesis to merge strict rule constraints and guards character budgets."
metadata:
  framework_version: "universal-v1"
  last_verified_date: "2026-11-21"
---

# Export Skills (`export-skills`)

## Overview
This tool packages and formats modular context bundles from `ai-agent-toolkit` (such as `shared/*`, `frameworks/*`, `domains/*`) into distribution-ready formats compatible with:
1. **ChatGPT Customizations** (OpenAI Agent Skills zip archives & Custom GPT system instructions)
2. **Google Gemini Custom Skills** (Gemini uploaded skills zip archives & Gemini system instructions)

It operates in **Dual-Mode**:
- **Zip Archives (`--mode zip` or `--mode both`)**: Full multi-file archives in `dist/skills/` including references and metadata.
- **Structured Prompts (`--mode prompt` or `--mode both`)**: Copy-pasteable XML/Markdown prompts in `dist/prompts/` equipped with an automated **Character Budget Guard** (8,000 characters limit for ChatGPT) and instant system clipboard synchronization (`--copy`).

---

## 4-Phase Packaging Lifecycle

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                          4-Phase Export Lifecycle                              │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Selector Discovery]   ──► Resolve glob/module paths to toolkit bundles
               │
  [Phase 2: Smart Synthesis]      ──► Parse frontmatter, extract & inject rule constraints
               │
  [Phase 3: Platform Formatting]  ──► Generate zip archives & structured XML prompts
               │
  [Phase 4: Output & Clipboard]   ──► Stream to dist/skills/, dist/prompts/, and clipboard
```

### Phase 1: Selector Discovery
- Evaluates input selectors (e.g. `shared/thanglish-mentor-persona`, `shared/*`, `frameworks/angular`).
- Resolves directories against toolkit roots (`shared/`, `frameworks/`, `infra/`, `domains/`, `tools/`).
- Discovers bundles containing `skills/SKILL.md`.

### Phase 2: Smart Synthesis
- Reads `skills/SKILL.md` and isolates YAML frontmatter (`name`, `description`).
- If `rules/` exists in the target bundle, extracts `## Constraints` from all `.md` rules.
- Appends an authoritative `## Mandatory Architectural & Implementation Constraints` section to the skill body.
- Sanitizes frontmatter to ensure platform compatibility.

### Phase 3: Platform Formatting & Character Budget Guard
- **ChatGPT**:
  - *Zip archive*: `<skill-name>/` directory layout containing `SKILL.md`, `agents/openai.yaml`, `assets/icon.svg`, and `references/`.
  - *Prompt*: Formatted with `<role>`, `<instructions>`, `<constraints>`, and `<knowledge_references>`. Audited against ChatGPT's 8,000 character limit for custom instructions.
- **Gemini**:
  - *Zip archive*: Places `SKILL.md` directly at root, plus `references/`.
  - *Prompt*: Formatted XML prompt optimized for Gemini system instructions.

### Phase 4: Output & Clipboard Distribution
- Writes compressed `.zip` files to `dist/skills/` (or `--out <dir>`):
  - `dist/skills/chatgpt-<skill-name>.zip`
  - `dist/skills/gemini-<skill-name>.zip`
- Writes markdown prompt files to `dist/prompts/` (or `--prompt-out <dir>`):
  - `dist/prompts/chatgpt-<skill-name>.md`
  - `dist/prompts/gemini-<skill-name>.md`
- If `--copy` / `-c` is passed, automatically synchronizes prompt text with system clipboard (`wl-copy`, `xclip`, `xsel`, `pbcopy`, or `clip.exe`).

---

## CLI Usage

### Direct Python Invocation
```bash
# Export single module in dual mode (both zip and prompt)
python3 tools/packagers/export-skills/skills/scripts/export_skills.py shared/thanglish-mentor-persona

# Export prompts only and copy directly to clipboard
python3 tools/packagers/export-skills/skills/scripts/export_skills.py shared/thanglish-mentor-persona --mode prompt --copy

# Enforce strict ChatGPT 8,000 character limit
python3 tools/packagers/export-skills/skills/scripts/export_skills.py "shared/*" --strict-budget

# Machine-readable JSON output
python3 tools/packagers/export-skills/skills/scripts/export_skills.py shared/clean-code-and-maintainability --json
```

### Integration via `context.sh`
```bash
# Export using context.sh wrapper (Dual-Mode default)
./bin/context.sh -e shared/thanglish-mentor-persona --tool both

# Shortcut to export raw prompt and copy to clipboard
./bin/context.sh -P shared/thanglish-mentor-persona -c

# Export prompt only for ChatGPT
./bin/context.sh -e 'shared/*' --tool chatgpt --mode prompt
```

---

## Gotchas

- **Root-Level Gemini Format**: Gemini expects `SKILL.md` directly at the root of the archive. Never nest `SKILL.md` inside a subfolder for Gemini exports.
- **ChatGPT Subfolder Layout**: ChatGPT requires the root of the zip archive to contain `<skill-name>/` as the parent folder for `SKILL.md`, `agents/openai.yaml`, and `assets/icon.svg`.
- **ChatGPT 8,000 Character Limit**: The Custom GPT Instructions web field allows at most 8,000 characters. Large bundles with extensive rules will trigger a `[WARN]`. Use `--no-rules` or streamline constraints when pasting into the instructions box.
- **Quote Globs**: Always quote wildcard selectors (e.g. `"shared/*"`) in the shell to prevent early shell globbing before path expansion.
- **Build Artifacts Excluded**: The `dist/` directory is ignored by git to keep repository diffs clean.
