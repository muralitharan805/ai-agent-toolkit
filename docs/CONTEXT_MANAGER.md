# Context Manager

Context Manager is a local browser UI for managing reusable AI agent context.
Use it to browse the toolkit, see what your projects already use, and review
changes before syncing context into Codex, Antigravity, or Claude Code.

The toolkit repository is the source for Skills, Rules, and their supporting
files. Contributors author and validate context in the repository. Context
Manager handles the next step: getting that context into the projects and
agents that need it.

## What you can do

| Feature | What it does |
| --- | --- |
| Browse the context library | Search and filter bundles by category, then open a bundle to read its instructions. |
| Save target directories | Browse to an existing folder or enter an absolute path. Choose Codex, Antigravity, or Claude Code for each sync operation. The same folder can support multiple agents. |
| Install, update, and remove context | Review file diffs and instructions changes before applying them to a target directory. |
| Manage global context | Install the curated defaults or a specific bundle for an agent. Remove a single bundle, the defaults, or all toolkit-managed global context for that agent. |
| Inspect installed context | See tracked entries for a directory or global agent, filter for available updates, and open the review screen for a bundle. |
| Export skill ZIPs | Download ChatGPT or Gemini skill packages. The bundle details include upload instructions for each platform. |

## Get started

From the root of a cloned toolkit repository, run:

```bash
python3 apps/context-manager/server.py
```

Open [Context Manager](http://127.0.0.1:8765/) and enter the local access code
printed in your terminal. The app requires Python 3.11+, Bash, and PyYAML.
The [GUI usage guide](../apps/context-manager/README.md) includes
installation and configuration options.

For a first sync, choose **Target directory**, save an existing project folder,
and open a bundle in the library. In **Review & sync**, pick the directory and
agent, preview the diff, and apply it. Use **Installed context** to see the
result and return later to review updates or removal.

To create or update source bundles in Claude Code, follow the
[authoring setup](../README.md#author-context-with-claude-code) and invoke
`/generate-agent-suite` from the toolkit checkout.

## How it works

The local Python server serves a plain HTML, CSS, and JavaScript frontend. The
GUI calls [`bin/context.sh`](../bin/context.sh) for sync, cleanup, and ZIP
export, so the GUI and CLI use the same installation rules.

- **Preview and apply.** Preview runs against temporary copies of the relevant
  destination files. Apply checks that the source and destination still match
  the preview, then runs the operation against the real destination.
- **Installed status.** The [manifest helper](../bin/toolkit_manifest.py) records
  where context came from, its installed hash, and which agents own it. The GUI
  compares that record with the current source and destination. A changed target
  appears as **Locally modified**. An unchanged target with a newer source
  appears as **Update available**. Rules merged into a shared instructions file
  appear as **Instructions registered**.
- **Selective removal.** Cleanup uses manifest ownership to preserve unmanaged
  files, locally modified installed files, and shared files still owned by
  another agent. Review the diff for changes to toolkit-managed instruction
  blocks.
- **Local state.** Saved directory paths live in a JSON registry under
  `${XDG_STATE_HOME:-$HOME/.local/state}/ai-agent-toolkit/` by default. Install
  records stay in the manifests at the destinations, so the GUI can read
  contexts installed through the CLI too.

The companion listens on loopback. Local workspace access and sync operations
stay on the machine running the companion. The same GUI can be hosted on
SeyaliCraft and paired with the companion using a process-specific code.
See the [hosted setup](../apps/context-manager/README.md#use-the-gui-on-seyalicraft).

## ZIP export

The [existing packager](../tools/packagers/export-skills/skills/scripts/export_skills.py)
generates separate archives for ChatGPT and Gemini. ChatGPT archives put
`SKILL.md` in a named skill folder. Gemini archives put it at the archive
root. Both formats include available reference files and fold bundled rule
constraints into `SKILL.md` by default. Authored scripts and assets remain in
the source bundle.

Upload availability depends on the target product and account. See the
[ChatGPT Skills guide](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
and the
[Gemini Skills guide](https://support.google.com/gemini/answer/17094296?co=GENIE.Platform%3DDesktop&hl=en)
for supported import options.

## Contributing

The app lives in [`apps/context-manager/`](../apps/context-manager/README.md).
See [`server.py`](../apps/context-manager/server.py) for the local API and
[`static/app.js`](../apps/context-manager/static/app.js) for the UI flows.
Use disposable targets when testing changes to sync or removal.

```bash
python3 -m unittest discover -s tests -p test_context_manager.py -v
python3 -m unittest discover -s tests -p test_toolkit_manifest.py -v
python3 -m unittest discover -s tests -p test_export_skills.py -v
```

The Context Manager tests use loopback networking for HTTP checks.
