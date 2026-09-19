#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MANIFEST_HELPER="${SCRIPT_DIR}/toolkit_manifest.py"

MODE="workspace"
TARGET_DIR="."
TARGET_TOOL="antigravity"
FORCE=false
CLEAN=false
SYNC_ALL=false
SELECTORS=()
GLOBAL_RULE_FILES=()
START_TAG="<!-- AGENT_TOOLKIT_START -->"
END_TAG="<!-- AGENT_TOOLKIT_END -->"

CONSUMER_ROOTS=("frameworks" "infra" "domains" "shared")
DEFAULT_GLOBAL_MODULES=(
  "shared/clean-code-and-maintainability"
  "shared/thanglish-mentor-persona"
  "shared/observability-and-telemetry"
  "shared/pnpm-package-management"
  "shared/security-auditing-and-pen-testing"
  "shared/security-baseline"
  "shared/github-issue-pr-automation"
)

usage() {
  cat <<'EOF'
Usage:
  context.sh -w [selectors...] [--tool antigravity|codex|claude] [--target <project>] [--force]
  context.sh -g [selectors...] [--tool antigravity] [--force]
  context.sh -w| -g [selectors...] --clean [--force]

Scope:
  -w, --workspace           Sync into a project workspace. Default scope.
  -g, --global              Sync into the selected tool's global context.

Tool selection:
  -T, --tool, --tools NAME  antigravity (default), codex, or claude.
                            Global sync currently supports antigravity only.

Targeting:
      --target PATH         Workspace project root. Default: current directory.

Selectors:
  Pass toolkit paths, shorthand paths, parent directories, or globs.
  Quote globs so this script expands them against the toolkit catalog.

  context.sh -w 'angular/*' --target ~/work/app
  context.sh -w angular/core --tool codex --target ~/work/app
  context.sh -w frameworks/angular --target ~/work/app
  context.sh -w tooling/generate-skill --target ~/work/toolkit-dev
  context.sh -g shared/security-baseline --tool antigravity

Options:
  -a, --all                 Sync all consumer catalog roots (frameworks, infra, domains, shared).
  -p, --preset NAME         angular-spa | nestjs-api | strapi-cms | docker-dev | fullstack-app
      --clean               Remove toolkit-managed context from the selected scope.
      --force               Allow overwrite of unmanaged/modified targets; with --clean,
                            also remove locally modified toolkit-managed targets.
      --force-clean         Alias for --clean --force.
  -h, --help                Show help.
EOF
}

fail() {
  echo "Error: $*" >&2
  exit 1
}

need_value() {
  [[ $# -ge 2 && -n "${2:-}" && "${2:-}" != -* ]] || fail "Option '$1' requires a value."
}

validate_tool() {
  case "$TARGET_TOOL" in
    antigravity|codex|claude) ;;
    *) fail "Unsupported tool '$TARGET_TOOL'. Supported: antigravity, codex, claude" ;;
  esac
}

parse_preset() {
  local preset="$1"
  case "$preset" in
    angular-spa) SELECTORS+=("frameworks/angular" "infra/cloudflare" "shared") ;;
    nestjs-api) SELECTORS+=("frameworks/nestjs" "infra/postgres" "infra/redis" "shared") ;;
    strapi-cms) SELECTORS+=("frameworks/strapi-v5" "infra/postgres" "shared") ;;
    docker-dev) SELECTORS+=("infra/docker" "infra/postgres" "infra/redis" "shared") ;;
    fullstack-app) SELECTORS+=("frameworks/angular" "frameworks/nestjs" "infra/docker" "infra/postgres" "infra/redis" "shared") ;;
    *) fail "Unknown preset '$preset'." ;;
  esac
}

parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -w|--workspace)
        MODE="workspace"
        shift
        ;;
      -g|--global)
        MODE="global"
        shift
        ;;
      -T|--tool|--tools)
        need_value "$@"
        TARGET_TOOL="$2"
        shift 2
        ;;
      --target)
        need_value "$@"
        TARGET_DIR="$2"
        shift 2
        ;;
      --force)
        FORCE=true
        shift
        ;;
      --clean)
        CLEAN=true
        shift
        ;;
      --force-clean)
        CLEAN=true
        FORCE=true
        shift
        ;;
      -a|--all)
        SYNC_ALL=true
        shift
        ;;
      -p|--preset)
        need_value "$@"
        parse_preset "$2"
        shift 2
        ;;
      -s|--shared)
        SELECTORS+=("shared")
        shift
        ;;
      -f|--framework|--frameworks)
        if [[ $# -ge 2 && -n "${2:-}" && "${2:-}" != -* ]]; then
          IFS=',' read -ra values <<< "$2"
          for value in "${values[@]}"; do SELECTORS+=("frameworks/${value}"); done
          shift 2
        else
          SELECTORS+=("frameworks")
          shift
        fi
        ;;
      -i|--infra|--infras)
        if [[ $# -ge 2 && -n "${2:-}" && "${2:-}" != -* ]]; then
          IFS=',' read -ra values <<< "$2"
          for value in "${values[@]}"; do SELECTORS+=("infra/${value}"); done
          shift 2
        else
          SELECTORS+=("infra")
          shift
        fi
        ;;
      -d|--domain|--domains)
        if [[ $# -ge 2 && -n "${2:-}" && "${2:-}" != -* ]]; then
          IFS=',' read -ra values <<< "$2"
          for value in "${values[@]}"; do SELECTORS+=("domains/${value}"); done
          shift 2
        else
          SELECTORS+=("domains")
          shift
        fi
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      -*) fail "Unknown option '$1'. Use --help." ;;
      *)
        SELECTORS+=("$1")
        shift
        ;;
    esac
  done

  validate_tool
  if [[ "$MODE" == "global" && "$TARGET_DIR" != "." ]]; then
    fail "--target is workspace-only. Global destinations are tool-defined."
  fi
  if [[ "$MODE" == "global" && "$TARGET_TOOL" != "antigravity" ]]; then
    fail "Global context is currently supported only for antigravity. Use -w for ${TARGET_TOOL}."
  fi
}

setup_scope_paths() {
  if [[ "$MODE" == "workspace" ]]; then
    mkdir -p "$TARGET_DIR"
    local project_root
    project_root="$(cd "$TARGET_DIR" && pwd)"

    case "$TARGET_TOOL" in
      antigravity)
        MANIFEST_ROOT="${project_root}/.agents"
        TARGET_SKILLS_DIR="${MANIFEST_ROOT}/skills"
        TARGET_RULES_DIR="${MANIFEST_ROOT}/rules"
        TARGET_WORKFLOWS_DIR="${MANIFEST_ROOT}/workflows"
        TARGET_PLUGINS_DIR="${MANIFEST_ROOT}/plugins"
        ;;
      codex)
        MANIFEST_ROOT="${project_root}/.agents"
        TARGET_SKILLS_DIR="${MANIFEST_ROOT}/skills"
        TARGET_RULES_DIR=""
        TARGET_WORKFLOWS_DIR=""
        TARGET_PLUGINS_DIR=""
        ;;
      claude)
        MANIFEST_ROOT="${project_root}/.claude"
        TARGET_SKILLS_DIR="${MANIFEST_ROOT}/skills"
        TARGET_RULES_DIR=""
        TARGET_WORKFLOWS_DIR=""
        TARGET_PLUGINS_DIR=""
        ;;
    esac
    SCOPE_LABEL="workspace:${project_root} (${TARGET_TOOL})"
  else
    MANIFEST_ROOT="${HOME}/.gemini"
    TARGET_SKILLS_DIR="${HOME}/.gemini/antigravity/skills"
    MIRROR_SKILLS_DIR="${HOME}/.gemini/config/skills"
    TARGET_RULES_DIR=""
    TARGET_WORKFLOWS_DIR="${HOME}/.gemini/config/workflows"
    TARGET_GLOBAL_WORKFLOWS_DIR="${HOME}/.gemini/config/global_workflows"
    TARGET_PLUGINS_DIR="${HOME}/.gemini/config/plugins"
    GLOBAL_GEMINI_MD="${HOME}/.gemini/GEMINI.md"
    SCOPE_LABEL="global:${HOME}/.gemini (antigravity)"
  fi

  mkdir -p "$MANIFEST_ROOT" "$TARGET_SKILLS_DIR"
  [[ -n "${TARGET_RULES_DIR:-}" ]] && mkdir -p "$TARGET_RULES_DIR"
  [[ -n "${TARGET_WORKFLOWS_DIR:-}" ]] && mkdir -p "$TARGET_WORKFLOWS_DIR"
  [[ -n "${TARGET_PLUGINS_DIR:-}" ]] && mkdir -p "$TARGET_PLUGINS_DIR"
  [[ -n "${MIRROR_SKILLS_DIR:-}" ]] && mkdir -p "$MIRROR_SKILLS_DIR"
  [[ -n "${TARGET_GLOBAL_WORKFLOWS_DIR:-}" ]] && mkdir -p "$TARGET_GLOBAL_WORKFLOWS_DIR"
  if [[ "$MODE" == "global" ]]; then
    mkdir -p "$(dirname "$GLOBAL_GEMINI_MD")"
    touch "$GLOBAL_GEMINI_MD"
  fi
}

tool_supports_kind() {
  local kind="$1"
  if [[ "$TARGET_TOOL" == "antigravity" ]]; then
    return 0
  fi
  [[ "$MODE" == "workspace" && "$kind" == "skill" ]]
}

skip_unsupported() {
  local kind="$1"
  local name="$2"
  echo "  [${TARGET_TOOL}] ↪ skipping ${kind} '${name}' (unsupported target type for this tool/scope)."
}

strip_yaml_frontmatter() {
  local file="$1"
  awk '
    BEGIN { in_fm = 0; seen_first = 0 }
    !seen_first {
      if ($0 ~ /^[[:space:]]*$/) next
      seen_first = 1
      if ($0 ~ /^---[[:space:]]*$/) { in_fm = 1; next }
    }
    in_fm {
      if ($0 ~ /^---[[:space:]]*$/) { in_fm = 0 }
      next
    }
    { print }
  ' "$file"
}

manifest_key_for_target() {
  python3 - "$MANIFEST_ROOT" "$1" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).expanduser().resolve()
target = Path(sys.argv[2]).expanduser().resolve(strict=False)
print(target.relative_to(root).as_posix())
PY
}

manifest_status() {
  local key="$1" target="$2" source="$3"
  python3 "$MANIFEST_HELPER" status \
    --root "$MANIFEST_ROOT" \
    --key "$key" \
    --target "$target" \
    --source "$source" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])'
}

manifest_record() {
  local key="$1" target="$2" source="$3" kind="$4"
  python3 "$MANIFEST_HELPER" record \
    --root "$MANIFEST_ROOT" \
    --key "$key" \
    --target "$target" \
    --source "$source" \
    --toolkit-root "$TOOLKIT_ROOT" \
    --kind "$kind" \
    --scope "$MODE" \
    --tool "$TARGET_TOOL" >/dev/null
}

sync_managed_path() {
  local source="$1" target="$2" kind="$3" label="$4"
  local key state
  key="$(manifest_key_for_target "$target")"
  state="$(manifest_status "$key" "$target" "$source")"

  case "$state" in
    missing) echo "  [$label] + $(basename "$target")" ;;
    adoptable)
      manifest_record "$key" "$target" "$source" "$kind"
      echo "  [$label] = adopted existing identical $(basename "$target")"
      return 0
      ;;
    clean) echo "  [$label] ~ updating $(basename "$target")" ;;
    unmanaged)
      if [[ "$FORCE" != true ]]; then
        echo "  [$label] ! protected unmanaged $(basename "$target"); skipped"
        return 0
      fi
      echo "  [$label] ! force replacing unmanaged $(basename "$target")"
      ;;
    modified)
      if [[ "$FORCE" != true ]]; then
        echo "  [$label] ! local modifications detected in $(basename "$target"); skipped"
        return 0
      fi
      echo "  [$label] ! force replacing modified $(basename "$target")"
      ;;
    *) fail "Unknown manifest state '$state' for '$target'." ;;
  esac

  if [[ -d "$source" ]]; then
    rm -rf "$target"
    mkdir -p "$target"
    cp -R "$source/." "$target/"
  else
    mkdir -p "$(dirname "$target")"
    rm -f "$target"
    cp "$source" "$target"
  fi
  manifest_record "$key" "$target" "$source" "$kind"
}

sync_single_skill() {
  local skill_dir="$1"
  local custom_name="${2:-}"
  [[ -d "$skill_dir" ]] || return 0
  tool_supports_kind skill || { skip_unsupported skill "$(basename "$skill_dir")"; return 0; }

  local name="${custom_name:-$(basename "$skill_dir")}" dest
  dest="${TARGET_SKILLS_DIR}/${name}"
  sync_managed_path "$skill_dir" "$dest" skill Skill

  if [[ "$MODE" == "global" && -n "${MIRROR_SKILLS_DIR:-}" ]]; then
    sync_managed_path "$skill_dir" "${MIRROR_SKILLS_DIR}/${name}" skill Skill
  fi
}

append_global_rule() {
  local rule_file="$1"
  local existing
  for existing in "${GLOBAL_RULE_FILES[@]:-}"; do
    [[ "$existing" == "$rule_file" ]] && return 0
  done
  GLOBAL_RULE_FILES+=("$rule_file")
}

sync_single_rule() {
  local rule_file="$1"
  [[ -f "$rule_file" ]] || return 0

  if [[ "$MODE" == "global" ]]; then
    append_global_rule "$rule_file"
    return 0
  fi

  if ! tool_supports_kind rule; then
    skip_unsupported rule "$(basename "$rule_file")"
    return 0
  fi
  sync_managed_path "$rule_file" "${TARGET_RULES_DIR}/$(basename "$rule_file")" rule Rule
}

sync_single_workflow() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  if ! tool_supports_kind workflow; then
    skip_unsupported workflow "$(basename "$file")"
    return 0
  fi
  sync_managed_path "$file" "${TARGET_WORKFLOWS_DIR}/$(basename "$file")" workflow Workflow
  if [[ "$MODE" == "global" && -n "${TARGET_GLOBAL_WORKFLOWS_DIR:-}" ]]; then
    sync_managed_path "$file" "${TARGET_GLOBAL_WORKFLOWS_DIR}/$(basename "$file")" workflow Workflow
  fi
}

sync_single_plugin() {
  local plugin_dir="$1"
  [[ -d "$plugin_dir" ]] || return 0
  if ! tool_supports_kind plugin; then
    skip_unsupported plugin "$(basename "$plugin_dir")"
    return 0
  fi
  sync_managed_path "$plugin_dir" "${TARGET_PLUGINS_DIR}/$(basename "$plugin_dir")" plugin Plugin
}

is_module_dir() {
  local dir="$1"
  [[ -d "$dir/skills" || -d "$dir/rules" || -d "$dir/workflows" || -d "$dir/plugins" ]]
}

sync_module_dir() {
  local module_dir="$1"
  local module_name
  module_name="$(basename "$module_dir")"
  echo "Module: ${module_dir#"$TOOLKIT_ROOT"/}"

  if [[ -f "$module_dir/skills/SKILL.md" ]]; then
    sync_single_skill "$module_dir/skills" "$module_name"
  elif [[ -d "$module_dir/skills" ]]; then
    local s
    for s in "$module_dir"/skills/*; do
      [[ -d "$s" ]] && sync_single_skill "$s"
    done
  fi

  if [[ -d "$module_dir/rules" ]]; then
    local r
    for r in "$module_dir"/rules/*.md; do [[ -f "$r" ]] && sync_single_rule "$r"; done
  fi

  if [[ -d "$module_dir/workflows" ]]; then
    local w
    for w in "$module_dir"/workflows/*.md; do [[ -f "$w" ]] && sync_single_workflow "$w"; done
  fi

  if [[ -d "$module_dir/plugins" ]]; then
    local p
    for p in "$module_dir"/plugins/*; do [[ -d "$p" ]] && sync_single_plugin "$p"; done
  fi
}

dispatch_path() {
  local path="$1"
  if [[ -f "$path" ]]; then
    case "$(basename "$(dirname "$path")")" in
      rules) sync_single_rule "$path" ;;
      workflows) sync_single_workflow "$path" ;;
      skills)
        local skill_parent
        skill_parent="$(dirname "$path")"
        if [[ "$(basename "$skill_parent")" == "skills" ]]; then
          sync_single_skill "$skill_parent" "$(basename "$(dirname "$skill_parent")")"
        else
          sync_single_skill "$skill_parent"
        fi
        ;;
      *)
        if [[ "$(basename "$path")" == "SKILL.md" ]]; then
          sync_single_skill "$(dirname "$path")"
        else
          echo "Warning: unrecognized file '$path'; skipped."
        fi
        ;;
    esac
    return
  fi

  [[ -d "$path" ]] || { echo "Warning: '$path' does not exist; skipped."; return; }

  if [[ -f "$path/SKILL.md" ]]; then
    if [[ "$(basename "$path")" == "skills" ]]; then
      sync_single_skill "$path" "$(basename "$(dirname "$path")")"
    else
      sync_single_skill "$path"
    fi
    return
  fi
  if is_module_dir "$path"; then
    sync_module_dir "$path"
    return
  fi

  local module found=0
  while IFS= read -r module; do
    [[ -n "$module" ]] || continue
    sync_module_dir "$module"
    found=1
  done < <(
    find "$path" \
      -type d \( -name .git -o -name .agents -o -name .claude -o -name node_modules \) -prune -o \
      -type d \( -name skills -o -name rules -o -name workflows -o -name plugins \) -print 2>/dev/null \
      | sed 's|/[^/]*$||' | sort -u
  )
  [[ "$found" -eq 1 ]] || echo "Warning: no context modules found under '$path'."
}

contains_glob() {
  [[ "$1" == *'*'* || "$1" == *'?'* || "$1" == *'['* ]]
}

emit_pattern_matches() {
  local pattern="$1"
  compgen -G "$pattern" 2>/dev/null || true
}

resolve_selector() {
  local selector="${1%/}"
  local -a candidates=()
  local candidate root

  if [[ -e "$selector" ]]; then
    if [[ -d "$selector" ]]; then
      (cd "$selector" && pwd)
    else
      echo "$(cd "$(dirname "$selector")" && pwd)/$(basename "$selector")"
    fi
    return 0
  fi

  while IFS= read -r candidate; do
    [[ -e "$candidate" ]] && candidates+=("$candidate")
  done < <(emit_pattern_matches "$TOOLKIT_ROOT/$selector")

  if [[ "${#candidates[@]}" -eq 0 ]]; then
    for root in "${CONSUMER_ROOTS[@]}" tooling; do
      while IFS= read -r candidate; do
        [[ -e "$candidate" ]] && candidates+=("$candidate")
      done < <(emit_pattern_matches "$TOOLKIT_ROOT/$root/$selector")
    done
  fi

  if [[ "${#candidates[@]}" -eq 0 ]] && ! contains_glob "$selector"; then
    while IFS= read -r candidate; do
      [[ -e "$candidate" ]] && candidates+=("$candidate")
    done < <(find "$TOOLKIT_ROOT" -mindepth 1 -maxdepth 4 -name "$selector" \
      ! -path '*/.git/*' ! -path '*/.agents/*' ! -path '*/.claude/*' 2>/dev/null | sort)
  fi

  if [[ "${#candidates[@]}" -eq 0 ]]; then
    return 1
  fi

  printf '%s\n' "${candidates[@]}" | awk '!seen[$0]++'
}

sync_selectors() {
  local selector resolved matched
  for selector in "$@"; do
    matched=0
    while IFS= read -r resolved; do
      [[ -n "$resolved" ]] || continue
      matched=1
      dispatch_path "$resolved"
    done < <(resolve_selector "$selector" || true)
    [[ "$matched" -eq 1 ]] || echo "Warning: selector '$selector' matched nothing."
  done
}

sync_all_consumer_context() {
  local root
  for root in "${CONSUMER_ROOTS[@]}"; do
    [[ -d "$TOOLKIT_ROOT/$root" ]] && dispatch_path "$TOOLKIT_ROOT/$root"
  done
}

update_global_gemini_md() {
  [[ "$MODE" == "global" && "$TARGET_TOOL" == "antigravity" ]] || return 0
  [[ "${#GLOBAL_RULE_FILES[@]}" -gt 0 ]] || return 0

  local temp backup
  temp="$(mktemp)"
  backup="${GLOBAL_GEMINI_MD}.bak"
  : > "$temp"

  local rf
  for rf in "${GLOBAL_RULE_FILES[@]}"; do
    strip_yaml_frontmatter "$rf" >> "$temp"
    printf '\n\n' >> "$temp"
  done

  [[ -s "$GLOBAL_GEMINI_MD" ]] && cp "$GLOBAL_GEMINI_MD" "$backup"

  python3 - "$GLOBAL_GEMINI_MD" "$temp" "$START_TAG" "$END_TAG" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
buffer = Path(sys.argv[2]).read_text(encoding="utf-8").strip()
start, end = sys.argv[3], sys.argv[4]
existing = path.read_text(encoding="utf-8") if path.exists() else ""
block = f"{start}\n\n{buffer}\n\n{end}"
if start in existing and end in existing:
    s = existing.index(start)
    e = existing.index(end, s) + len(end)
    updated = existing[:s].rstrip() + "\n\n" + block + existing[e:]
else:
    prefix = existing.rstrip()
    updated = (prefix + "\n\n" if prefix else "") + block + "\n"
path.write_text(updated, encoding="utf-8")
PY
  rm -f "$temp"
  echo "Global rules: refreshed toolkit block in $GLOBAL_GEMINI_MD"
}

remove_global_gemini_block() {
  [[ "$MODE" == "global" && "$TARGET_TOOL" == "antigravity" ]] || return 0
  [[ -f "$GLOBAL_GEMINI_MD" ]] || return 0

  python3 - "$GLOBAL_GEMINI_MD" "$START_TAG" "$END_TAG" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
start, end = sys.argv[2], sys.argv[3]
text = path.read_text(encoding="utf-8")
if start not in text or end not in text:
    raise SystemExit(0)
backup = path.with_name(path.name + ".bak")
backup.write_text(text, encoding="utf-8")
s = text.index(start)
e = text.index(end, s) + len(end)
updated = (text[:s].rstrip() + "\n\n" + text[e:].lstrip()).strip()
path.write_text((updated + "\n") if updated else "", encoding="utf-8")
PY
  echo "Global rules: removed toolkit-managed block from $GLOBAL_GEMINI_MD"
}

normalized_source_prefix() {
  local source="$1"
  python3 - "$TOOLKIT_ROOT" "$source" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
source = Path(sys.argv[2]).resolve()
try:
    print(source.relative_to(root).as_posix())
except ValueError:
    print(str(source))
PY
}

run_cleanup() {
  local -a prefixes=()
  local selector resolved

  if [[ "${#SELECTORS[@]}" -gt 0 ]]; then
    for selector in "${SELECTORS[@]}"; do
      while IFS= read -r resolved; do
        [[ -n "$resolved" ]] && prefixes+=("$(normalized_source_prefix "$resolved")")
      done < <(resolve_selector "$selector" || true)
    done
  fi

  local -a cmd=(python3 "$MANIFEST_HELPER" clean --root "$MANIFEST_ROOT")
  [[ "$FORCE" == true ]] && cmd+=(--force)
  local prefix
  for prefix in "${prefixes[@]}"; do cmd+=(--source-prefix "$prefix"); done

  local output
  output="$("${cmd[@]}")"
  python3 - "$output" <<'PY'
import json, sys
r = json.loads(sys.argv[1])
for key in r["removed"]:
    print(f"  [Clean] - {key}")
for key in r["missing"]:
    print(f"  [Clean] = forgot missing {key}")
for key in r["modified"]:
    print(f"  [Clean] ! preserved locally modified {key}")
print(f"Cleanup complete. Remaining managed entries: {r['remaining']}")
PY

  # Global GEMINI.md is marker-managed rather than file-owned. Full global cleanup
  # removes only the toolkit block and preserves all user content.
  if [[ "$MODE" == "global" && "${#SELECTORS[@]}" -eq 0 ]]; then
    remove_global_gemini_block
  fi
}

main() {
  parse_arguments "$@"
  setup_scope_paths

  echo "AI Agent Toolkit Context"
  echo "Scope : $SCOPE_LABEL"
  echo "Mode  : $([[ "$CLEAN" == true ]] && echo clean || echo sync)"

  if [[ "$CLEAN" == true ]]; then
    run_cleanup
    exit 0
  fi

  if [[ "$SYNC_ALL" == true ]]; then
    sync_all_consumer_context
  elif [[ "${#SELECTORS[@]}" -gt 0 ]]; then
    sync_selectors "${SELECTORS[@]}"
  elif [[ "$MODE" == "global" ]]; then
    sync_selectors "${DEFAULT_GLOBAL_MODULES[@]}"
  else
    sync_selectors shared
  fi

  update_global_gemini_md
  echo "Context sync complete."
}

main "$@"
