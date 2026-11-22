# Local Context Manager

A browser UI for the toolkit's existing workspace and global sync engine.
Context authoring runs in Codex, Antigravity, or Claude Code. See the
[Claude Code authoring setup](../../README.md#author-context-with-claude-code).

From the repository root:

```bash
python3 apps/context-manager/server.py
```

Open http://127.0.0.1:8765 and enter the local access code printed in your
terminal. Python 3.11+, Bash and the repository's existing
PyYAML dependency are required (`python3 -m pip install -r requirements.txt`).
Use `--port` to change the port, or `--state /tmp/context-projects.json` for a
disposable project registry. The default registry lives under XDG_STATE_HOME
(or ~/.local/state)/ai-agent-toolkit, never in the content repository.

1. Select **Target directory → Browse folders**, navigate to an existing project,
   choose **Use this folder**, and save it. You can
   also enter an absolute path.
2. Search the catalog and open a bundle.
3. Select **Review & sync**, choose a target directory and agent, then preview
   changes. You can use Codex, Antigravity, or Claude Code for the same directory.
4. Inspect diffs and engine output, then apply the reviewed sync.

Select **Installed context** to inspect the files tracked for a target directory
or global agent. Filter for available updates, or open a tracked bundle to
review an update or removal. Shared instruction registrations are listed
separately because the manifest tracks their sources without individual hashes.
After applying a change from this view, use **Back to installed context** to
see the refreshed inventory. The browser tab remembers the inventory selection.

To export a catalog bundle, open it and select **Download ChatGPT ZIP** or
**Download Gemini ZIP**. The existing exporter packages the bundle for the
selected platform and the browser downloads the archive.

- **ChatGPT:** In an eligible workspace, go to **Plugins → Skills → Create →
  Upload from your computer** and select the ChatGPT ZIP.
- **Gemini:** Go to **Customize → Skills → Create → Upload**, select the Gemini
  ZIP, then review and create the skill.

The context detail panel includes links to both upload guides.

For global defaults, select **Global sync** in the sidebar, choose an agent,
and review the module list and install paths. Open a catalog bundle
and switch its scope to **Global** to install just that bundle. Global sync
applies to your user account. Claude Code receives skills in project
`.claude/skills/` or its personal skills directory. Codex and Antigravity can
also receive bundled instructions. Codex reads updated instructions in a new session.

To uninstall a bundle, open **Review & sync**, choose the scope and target,
select **Remove**, and click **Preview removal**. Review the affected files
and engine output before applying. The **Global sync** sidebar shortcut can
also remove the default global bundle or **All installed toolkit context** for
the selected agent. Removing the default bundle leaves other bundles installed.
Cleanup releases the chosen agent's ownership and preserves unmanaged files
and locally modified installed files. Review the diff for any changes to the
toolkit-managed instructions block.

Workspace preview stages the agent's sync files in a temporary project.
For Claude Code it copies the skills and toolkit manifest only. Global preview
stages the configured sync destinations in a temporary home and configuration
folder. Both run the existing context.sh engine on those copies.
The temporary manifest is excluded from the displayed content diff. Apply runs
the same engine against the real destinations without --force. Locally edited and
unmanaged files are preserved according to CLI policy; inspect logs for skips.
A new preview invalidates the previous preview. Changes to the source or target
since preview require another review. Registrations persist across restarts.

The service binds only to 127.0.0.1 and checks Host, Origin, and a per-process
request token. The default launch accepts only the local GUI. Symlink
destinations are rejected.
Only consumer bundles are cataloged; toolkit authoring tools remain opt-in via CLI.

## Use the GUI on SeyaliCraft

When the hosted GUI is available at `https://seyalicraft.com/tools/context-manager`,
start the companion from the toolkit checkout:

```bash
python3 apps/context-manager/server.py --pair-with https://seyalicraft.com
```

Enter the terminal's pairing code on the page and allow browser loopback access
if prompted. Use the companion's port if it differs from 8765. The code lasts
for that companion process. The hosted GUI calls the companion directly, so
project contents and diffs do not pass through the SeyaliCraft web server.
The browser must support HTTPS-to-loopback access. The local GUI remains
available at the address printed by the companion.

For site maintenance, export the same frontend into the SeyaliCraft checkout:

```bash
python3 apps/context-manager/export_hosted_ui.py /path/to/seyalicraft-frontend/public/context-manager-app
```

The existing Angular tool route embeds those static assets. Re-export them
when the toolkit UI changes. For local Angular preview, start the companion
with `--pair-with http://localhost:4200` or
`--pair-with http://127.0.0.1:4200`. Either option accepts those two local
development addresses. Production pairing accepts only
`https://seyalicraft.com`.

Limitations: installed status is checked on open, selection change, refresh, and
after applying from the installed view. There is no background watcher,
native OS directory picker, bulk rollout, or full Markdown rendering.
External processes can still change files during a sync; avoid editing
source/target files while applying. Engine execution is serialized within the app.

See the [Context Manager overview](../../docs/CONTEXT_MANAGER.md) for its
purpose, architecture, and contributor test commands.
