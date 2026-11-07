# Release Verification — Consumer and Authoring Journeys

This checklist verifies what a developer experiences **after cloning** this toolkit. The command-line lifecycle is automatically tested in CI using the Angular Forms catalog module. On 2026-11-07, a developer reported successful Antigravity skill/rule discovery, Angular form generation, and production build; the build log was not independently retained. Codex and Claude Code workspace sync were tested without the corresponding agents installed; **real agent invocation remains unverified for those two tools**.

> **Safety:** Use a disposable target project for manual checks. Never use `--force` or `--force-clean` on a real workspace unless you intentionally want to discard local changes. Do not run the global (`-g`) flow as part of the workspace smoke test.

## 1. Prerequisites

- A fresh clone/checkout of the intended release candidate (not a working tree with pre-existing `.agents/` or `.claude/` files).
- Bash, Python 3.11 or newer, and Git for the toolkit.
- Antigravity, Codex, or Claude Code installed separately **if testing actual agent behavior**.
- An optional disposable Angular project for verifying actual code generation. The sync itself does **not** require Angular or Node.js.

From the toolkit repository root:

```bash
bash -n bin/context.sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## 2. Sync an existing context to a fresh workspace

Set `TARGET` to a **new temporary directory**. Do not use the toolkit repository as the consumer target.

```bash
TARGET="$(mktemp -d)"
./bin/context.sh -w frameworks/angular/angular-enterprise-forms \
  --tool antigravity --target "$TARGET"

test -f "$TARGET/.agents/skills/angular-enterprise-forms/SKILL.md"
test -f "$TARGET/.agents/rules/angular-enterprise-forms-rules.md"
test -f "$TARGET/.agents/.toolkit-manifest.json"
```

Expected: Angular Forms skill + rules copied into `.agents/` with an ownership manifest. Re-running the same `context.sh` command should succeed without modifying the skill's contents or damaging user-owned files.

For an equivalent fresh **Codex** workspace, use `--tool codex`; expect `.agents/skills/angular-enterprise-forms/SKILL.md` and **no copied Antigravity rule**.

For a fresh **Claude Code** workspace, use `--tool claude`; expect `.claude/skills/angular-enterprise-forms/SKILL.md` and **no copied Antigravity rule**.

## 3. Verify safe re-sync and cleanup

In **the disposable target only**:

1. Re-run the identical workspace sync command. Confirm the skill is still installed.
2. Add a local note to the installed skill's `SKILL.md`.
3. Re-run sync without `--force`; verify the note remains, and the CLI reports a local modification.
4. Run `./bin/context.sh -w frameworks/angular/angular-enterprise-forms --tool antigravity --target "$TARGET" --clean`; verify the modified skill remains but unmodified managed rules are cleaned.
5. Only in the disposable target, run the same command using `--force-clean`; verify the modified toolkit-owned skill is removed. Unmanaged project files must remain untouched.

The automated counterpart is `tests/test_consumer_lifecycle_e2e.py`; it additionally verifies selective cleanup of an Angular module leaves a separate shared toolkit module installed.

## 4. Verify shared Antigravity + Codex skill ownership

Only run this in a **disposable** consumer directory. Both tools use `.agents/skills/`; the manifest records each owner in `tools`, instead of treating the most recent `tool` as the only owner.

```bash
TARGET="$(mktemp -d)"
./bin/context.sh -w frameworks/angular/angular-enterprise-forms --tool antigravity --target "$TARGET"
./bin/context.sh -w frameworks/angular/angular-enterprise-forms --tool codex --target "$TARGET"
jq '.managed["skills/angular-enterprise-forms"].tools' "$TARGET/.agents/.toolkit-manifest.json"
# Expected: ["antigravity", "codex"]

./bin/context.sh -w frameworks/angular/angular-enterprise-forms --tool codex --target "$TARGET" --clean
test -f "$TARGET/.agents/skills/angular-enterprise-forms/SKILL.md"
test -f "$TARGET/.agents/rules/angular-enterprise-forms-rules.md"
jq '.managed["skills/angular-enterprise-forms"].tools' "$TARGET/.agents/.toolkit-manifest.json"
# Expected: ["antigravity"]
```

Now the last owner can clean its own skill. Reverse-order cleanup (Antigravity then Codex) is covered by automated tests too.

**Existing workspaces migrated from the previous manifest format:** First update the toolkit, then re-run non-cleaning sync for **both** Antigravity and Codex before cleaning either. Older manifests contain only the last recorded `tool`; they cannot automatically reconstruct an earlier owner's interest. This registration step is required once for any previously shared workspace.

## 5. Verify real AI agent consumption (manual sign-off)

Repeat Step 2 against a **disposable real Angular application**, then open that **application workspace** in the relevant tool:

| Tool | Verify |
| --- | --- |
| Google Antigravity | Workspace skill appears under `.agents/skills/`; relevant Angular rules under `.agents/rules/` |
| OpenAI Codex | Workspace skill appears under `.agents/skills/`; Antigravity rules are not installed |
| Claude Code | Workspace skill appears under `.claude/skills/`; Antigravity rules are not installed |

Ask the agent to **use the installed `angular-enterprise-forms` skill** and implement a small typed reactive form with validation. Confirm the agent can access the installed skill and its references, creates correct app code, and that the Angular project's own build/tests pass.

If the agent doesn't discover the skill, record the IDE version, the workspace path, and what the agent actually reported. Do **not** mark this step passed solely because the files exist. Different coding agents may require a distinct skill-invocation syntax; do not assume `/generate-agent-suite` works verbatim everywhere.

## 6. Optional toolkit authoring journey (manual sign-off)

The ordinary consumer journey does **not** require installing authoring skills. To test authoring, open the toolkit repository in an agent and run:

```bash
./bin/context.sh -w \
  tools/generators/generate-agent-suite \
  tools/generators/generate-skill \
  tools/generators/generate-rule \
  shared/ai-agent-toolkit \
  --tool antigravity --target .
```

Confirm the four skill bundles appear in `.agents/skills/`. Ask the agent to review an existing toolkit module, e.g. `frameworks/angular/angular-enterprise-forms/`, without inventing a new duplicate. Verify actual source changes if requested, review the diff, run the skill/suite validators, and sync only after validation. Clean up any unintentional test changes before release.

The companion-skill installation and relative reference links are automatically covered by `tests/test_authoring_bootstrap.py`. AI model behavior itself is **not** automatically verified.

## 7. Final release sign-off

Status recorded **2026-11-07** against fresh root commit `20ac3ff76543189d45343f97be2fdb37515d4637`.

- [x] CI: Bash syntax, Python compilation, 75 unit/integration tests, representative skill validation, and Gitleaks — passed on the new private repository ([run 42382807463](https://github.com/muralitharan805/ai-agent-toolkit/actions/runs/42382807463)).
- [x] Antigravity consumer: skill and rule sync, discovery, and file reading — independently evidenced by reported command/agent output; Angular form generation and production build — **developer-reported success without retained build logs**.
- [x] Codex workspace skill sync — passed; Antigravity-specific rules correctly skipped. **Real Codex agent use not tested** (CLI unavailable).
- [x] Claude Code workspace skill sync — passed; Antigravity-specific rules correctly skipped. **Real Claude agent use not tested** (CLI unavailable).
- [ ] Full Codex consumer agent smoke test — requires Codex agent installation.
- [ ] Full Claude Code consumer agent smoke test — requires Claude Code installation.
- [ ] Optional `generate-agent-suite` authoring smoke test — requires actual agent invocation if advertised as agent-tested.
- [ ] Manual provenance/sign-off for all first-party source and third-party redistribution rights; attribution and automated checks do not establish authorship of every file.
- [x] Fresh repository history: one root commit with zero parents, separate from original private history; 650 files, no historical `evals/grading.json` reports or unverified backend guides.
- [x] Secret checks: Gitleaks CI passed, developer's local no-Git directory scan found no leaks, and temporary tracked-file preflight scanned for private project names, credential-shaped strings and publisher identifiers. No scan guarantees the absence of secrets or private information.
- [x] Public identity details in README, LICENSE and SECURITY.md — developer approved for publication.
- [x] Documentation distinguishes deterministic evaluation checks from unverified agent/benchmark assertions.

**Scope of verification:** The source snapshot and its one new commit have been checked; any additional untracked local files or future changes require separate review. A green CI does not validate actual behavior in every IDE. Keep `ai-agent-toolkit-internal` and its Git history private and separate.
