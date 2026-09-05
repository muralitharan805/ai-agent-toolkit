#!/usr/bin/env bash

# ==============================================================================
# Script: sync-context.sh
# Purpose: Universal dynamic synchronization utility for AI Agent Toolkit.
#          Syncs skills, rules, and workflows into project workspace (.agents/)
#          or into system global customization paths (~/.gemini/).
# Architecture: Zero-hardcoding dynamic discovery & universal path routing.
# ==============================================================================

set -e

# Base toolkit root resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Global Defaults & State Flags
TARGET_DIR="./"
IS_GLOBAL=false
SYNC_ALL=false
SELECTORS=()
GLOBAL_RULES_BUFFER=""
START_TAG="<!-- AGENT_TOOLKIT_START -->"
END_TAG="<!-- AGENT_TOOLKIT_END -->"

# Default curated rules for global sync when no specific selector is provided
DEFAULT_GLOBAL_RULE_DIRS=(
  "shared/code-quality"
  "shared/communication"
  "shared/logging"
  "shared/package-management"
  "shared/security"
  "shared/git"
)

# ------------------------------------------------------------------------------
# CLI Help & Usage
# ------------------------------------------------------------------------------
usage() {
  cat << EOF
Usage: $(basename "$0") [scope] [options] [path-or-selector...]

Scope Identifiers:
  -w, --workspace <path>    Target project directory for Workspace Level (.agents/) [Default: ./]
  -t, --target <path>       Alias for --workspace
  -g, --global              Sync to machine Global Level (~/.gemini/)

Selectors & Options:
  -a, --all                 Dynamically discover and sync ALL categories and modules
  -s, --shared              Sync shared common context
  -f, --frameworks [names]  Framework(s) to sync (e.g. angular, nestjs). Omit value to sync all.
  -i, --infra [tools]       Infra module(s) to sync (e.g. docker, postgres). Omit value to sync all.
  -d, --domains [names]     Domain module(s) to sync (e.g. nidhiflow). Omit value to sync all.
  -p, --preset <name>       Preset bundle (e.g. angular-spa, nestjs-api, docker-dev, fullstack-app)
  -h, --help                Display this help message

Universal Path Routing (Zero Hardcoding):
  You can pass ANY relative path or module name directly as an argument:
  1. Category Level:       $(basename "$0") shared -w /path/to/project
  2. Module Level:         $(basename "$0") frameworks/angular -w /path/to/project
  3. Single Skill:         $(basename "$0") frameworks/angular/skills/angular-enterprise-scaffolding -w /path/to/project
  4. Single Rule:          $(basename "$0") shared/code-quality/rules/no-any-type.md -w /path/to/project
  5. Single Workflow:      $(basename "$0") shared/git/workflows/github-feature-workflow.md -w /path/to/project
  6. Global Rules Sync:    $(basename "$0") shared/code-quality shared/communication --global

EOF
  exit 0
}

# ------------------------------------------------------------------------------
# Argument Parser
# ------------------------------------------------------------------------------
parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -g|--global)
        IS_GLOBAL=true
        shift 1
        ;;
      -w|--workspace|-t|--target)
        TARGET_DIR="$2"
        shift 2
        ;;
      -a|--all)
        SYNC_ALL=true
        shift 1
        ;;
      -s|--shared)
        SELECTORS+=("shared")
        shift 1
        ;;
      -f|--framework|--frameworks)
        if [[ -n "$2" && "$2" != -* ]]; then
          IFS=',' read -ra FW_ITEMS <<< "$2"
          for item in "${FW_ITEMS[@]}"; do SELECTORS+=("frameworks/$(echo "$item" | xargs)"); done
          shift 2
        else
          SELECTORS+=("frameworks")
          shift 1
        fi
        ;;
      -i|--infra|--infras)
        if [[ -n "$2" && "$2" != -* ]]; then
          IFS=',' read -ra INF_ITEMS <<< "$2"
          for item in "${INF_ITEMS[@]}"; do SELECTORS+=("infra/$(echo "$item" | xargs)"); done
          shift 2
        else
          SELECTORS+=("infra")
          shift 1
        fi
        ;;
      -d|--domain|--domains)
        if [[ -n "$2" && "$2" != -* ]]; then
          IFS=',' read -ra DOM_ITEMS <<< "$2"
          for item in "${DOM_ITEMS[@]}"; do SELECTORS+=("domains/$(echo "$item" | xargs)"); done
          shift 2
        else
          SELECTORS+=("domains")
          shift 1
        fi
        ;;
      -p|--preset)
        parse_preset "$2"
        shift 2
        ;;
      -h|--help)
        usage
        ;;
      -*)
        echo "Error: Unknown option '$1'"
        usage
        ;;
      *)
        SELECTORS+=("$1")
        shift 1
        ;;
    esac
  done
}

parse_preset() {
  local preset="$1"
  case "$preset" in
    angular-spa)
      SELECTORS+=("frameworks/angular" "infra/cloudflare" "shared")
      ;;
    nestjs-api)
      SELECTORS+=("frameworks/nestjs" "infra/postgres" "infra/redis" "shared")
      ;;
    strapi-cms)
      SELECTORS+=("frameworks/strapi-v5" "infra/postgres" "shared")
      ;;
    docker-dev)
      SELECTORS+=("infra/docker" "infra/postgres" "infra/redis" "shared")
      ;;
    fullstack-app)
      SELECTORS+=("frameworks/angular" "frameworks/nestjs" "infra/docker" "infra/postgres" "infra/redis" "shared")
      ;;
    *)
      echo "Error: Unknown preset '$preset'"
      exit 1
      ;;
  esac
}

# ------------------------------------------------------------------------------
# Scope Configuration
# ------------------------------------------------------------------------------
setup_scope_paths() {
  if [[ "$IS_GLOBAL" == true ]]; then
    TARGET_SKILLS_DIR="${HOME}/.gemini/antigravity/skills"
    TARGET_CONFIG_SKILLS_DIR="${HOME}/.gemini/config/skills"
    TARGET_WORKFLOWS_DIR="${HOME}/.gemini/config/workflows"
    TARGET_GLOBAL_WORKFLOWS_DIR="${HOME}/.gemini/config/global_workflows"
    TARGET_PLUGINS_DIR="${HOME}/.gemini/config/plugins"
    GLOBAL_GEMINI_MD="${HOME}/.gemini/GEMINI.md"
    SCOPE_LABEL="Global Level (~/.gemini)"

    mkdir -p "$(dirname "$GLOBAL_GEMINI_MD")"
    touch "$GLOBAL_GEMINI_MD"

    GLOBAL_RULES_BUFFER="$(mktemp)"
    trap 'rm -f "$GLOBAL_RULES_BUFFER"' EXIT

    mkdir -p "${TARGET_SKILLS_DIR}" "${TARGET_CONFIG_SKILLS_DIR}" "${TARGET_WORKFLOWS_DIR}" "${TARGET_GLOBAL_WORKFLOWS_DIR}" "${TARGET_PLUGINS_DIR}"
  else
    if [[ ! -d "$TARGET_DIR" ]]; then
      mkdir -p "$TARGET_DIR"
    fi
    TARGET_AGENTS_DIR="$(cd "$TARGET_DIR" && pwd)/.agents"
    TARGET_SKILLS_DIR="${TARGET_AGENTS_DIR}/skills"
    TARGET_RULES_DIR="${TARGET_AGENTS_DIR}/rules"
    TARGET_WORKFLOWS_DIR="${TARGET_AGENTS_DIR}/workflows"
    TARGET_PLUGINS_DIR="${TARGET_AGENTS_DIR}/plugins"
    SCOPE_LABEL="Workspace Level (${TARGET_DIR}/.agents)"

    mkdir -p "${TARGET_SKILLS_DIR}" "${TARGET_RULES_DIR}" "${TARGET_WORKFLOWS_DIR}" "${TARGET_PLUGINS_DIR}"
  fi
}

# ------------------------------------------------------------------------------
# Content Parsers & Formatters
# ------------------------------------------------------------------------------
strip_yaml_frontmatter() {
  local file="$1"
  awk '
    BEGIN { in_fm = 0; done_fm = 0; seen_first = 0 }
    !seen_first {
      if ($0 ~ /^[[:space:]]*$/) next
      seen_first = 1
      if ($0 ~ /^---[[:space:]]*$/) { in_fm = 1; next }
    }
    in_fm {
      if ($0 ~ /^---[[:space:]]*$/) { in_fm = 0; done_fm = 1 }
      next
    }
    { print }
  ' "$file"
}

validate_item() {
  local item_path="$1"
  local category="$2"

  if [[ "$category" == "skills" ]]; then
    local skill_md="${item_path}/SKILL.md"
    if [[ -f "$skill_md" ]]; then
      if ! grep -q "^description:" "$skill_md"; then
        echo "  ⚠️ [Validation Warning] $(basename "$item_path")/SKILL.md is missing 'description:' frontmatter!"
      fi
    else
      echo "  ⚠️ [Validation Warning] Skill '$(basename "$item_path")' is missing SKILL.md!"
    fi
  elif [[ "$category" == "rules" || "$category" == "workflows" ]]; then
    if [[ -f "$item_path" ]]; then
      local char_count
      char_count="$(wc -m < "$item_path" | xargs)"
      if [[ "$char_count" -gt 12000 ]]; then
        echo "  ⚠️ [Validation Warning] $(basename "$item_path") exceeds 12,000 chars limit (${char_count} chars)!"
      fi
    fi
  fi
}

# ------------------------------------------------------------------------------
# Granular Item Sync Handlers
# ------------------------------------------------------------------------------
sync_single_skill() {
  local skill_dir="$1"
  if [[ ! -d "$skill_dir" ]]; then return 0; fi

  local skill_name="$(basename "$skill_dir")"
  validate_item "$skill_dir" "skills"

  local dest_dir="${TARGET_SKILLS_DIR}/${skill_name}"
  if [[ -d "$dest_dir" ]]; then
    echo "  [Skill] 🔄 Replacing existing ${skill_name}..."
    rm -rf "$dest_dir"
  else
    echo "  [Skill] ➕ Adding ${skill_name}..."
  fi
  mkdir -p "$dest_dir"
  cp -r "${skill_dir}/." "${dest_dir}/"

  if [[ "$IS_GLOBAL" == true ]]; then
    local config_dest="${TARGET_CONFIG_SKILLS_DIR}/${skill_name}"
    if [[ -d "$config_dest" ]]; then
      rm -rf "$config_dest"
    fi
    mkdir -p "$config_dest"
    cp -r "${skill_dir}/." "${config_dest}/"
  fi
}

sync_single_rule() {
  local rule_file="$1"
  if [[ ! -f "$rule_file" ]]; then return 0; fi

  local file_name="$(basename "$rule_file")"
  validate_item "$rule_file" "rules"

  if [[ "$IS_GLOBAL" == true ]]; then
    echo "  [Rule] 📦 Staging ${file_name} for GEMINI.md..."
    if [[ -s "$GLOBAL_RULES_BUFFER" ]]; then
      echo "" >> "$GLOBAL_RULES_BUFFER"
    fi
    strip_yaml_frontmatter "$rule_file" >> "$GLOBAL_RULES_BUFFER"
  else
    local dest_file="${TARGET_RULES_DIR}/${file_name}"
    if [[ -f "$dest_file" ]]; then
      echo "  [Rule] 🔄 Replacing existing ${file_name}..."
      rm -f "$dest_file"
    else
      echo "  [Rule] ➕ Adding ${file_name}..."
    fi
    cp "$rule_file" "$dest_file"
  fi
}

sync_single_workflow() {
  local wf_file="$1"
  if [[ ! -f "$wf_file" ]]; then return 0; fi

  local file_name="$(basename "$wf_file")"
  validate_item "$wf_file" "workflows"

  local dest_file="${TARGET_WORKFLOWS_DIR}/${file_name}"
  if [[ -f "$dest_file" ]]; then
    echo "  [Workflow] 🔄 Replacing existing ${file_name}..."
    rm -f "$dest_file"
  else
    echo "  [Workflow] ➕ Adding ${file_name}..."
  fi
  cp "$wf_file" "$dest_file"

  if [[ "$IS_GLOBAL" == true ]]; then
    local dest_global="${TARGET_GLOBAL_WORKFLOWS_DIR}/${file_name}"
    if [[ -f "$dest_global" ]]; then
      rm -f "$dest_global"
    fi
    cp "$wf_file" "$dest_global"
  fi
}

sync_single_plugin() {
  local plugin_dir="$1"
  if [[ ! -d "$plugin_dir" ]]; then return 0; fi

  local plugin_name="$(basename "$plugin_dir")"
  local dest_dir="${TARGET_PLUGINS_DIR}/${plugin_name}"
  if [[ -d "$dest_dir" ]]; then
    echo "  [Plugin] 🔄 Replacing existing ${plugin_name}..."
    rm -rf "$dest_dir"
  else
    echo "  [Plugin] ➕ Adding ${plugin_name}..."
  fi
  mkdir -p "$dest_dir"
  cp -r "${plugin_dir}/." "${dest_dir}/"
}

# ------------------------------------------------------------------------------
# Module Sync Engine
# ------------------------------------------------------------------------------
sync_module_dir() {
  local module_dir="$1"
  if [[ ! -d "$module_dir" ]]; then return 0; fi

  local module_name="$(basename "$module_dir")"
  local parent_name="$(basename "$(dirname "$module_dir")")"
  echo "📦 Syncing Module: ${parent_name}/${module_name}"

  # 1. Sync Skills
  if [[ -d "${module_dir}/skills" ]]; then
    for s_dir in "${module_dir}/skills"/*; do
      if [[ -d "$s_dir" ]]; then sync_single_skill "$s_dir"; fi
    done
  fi

  # 2. Sync Rules
  if [[ -d "${module_dir}/rules" ]]; then
    for r_file in "${module_dir}/rules"/*.md; do
      if [[ -f "$r_file" ]]; then sync_single_rule "$r_file"; fi
    done
  fi

  # 3. Sync Workflows
  if [[ -d "${module_dir}/workflows" ]]; then
    for w_file in "${module_dir}/workflows"/*.md; do
      if [[ -f "$w_file" ]]; then sync_single_workflow "$w_file"; fi
    done
  fi

  # 4. Sync Plugins
  if [[ -d "${module_dir}/plugins" ]]; then
    for p_dir in "${module_dir}/plugins"/*; do
      if [[ -d "$p_dir" ]]; then sync_single_plugin "$p_dir"; fi
    done
  fi
}

is_module_dir() {
  local dir="$1"
  [[ -d "${dir}/skills" || -d "${dir}/rules" || -d "${dir}/workflows" || -d "${dir}/plugins" ]]
}

# ------------------------------------------------------------------------------
# Dynamic Path Resolution & Classifier (Zero Hardcoding)
# ------------------------------------------------------------------------------
resolve_selector_path() {
  local input="$1"
  input="${input%/}"

  if [[ -e "$input" ]]; then
    echo "$(cd "$(dirname "$input")" 2>/dev/null && pwd)/$(basename "$input")"
    return 0
  fi

  if [[ -e "${TOOLKIT_ROOT}/${input}" ]]; then
    local parent_dir
    parent_dir="$(dirname "${TOOLKIT_ROOT}/${input}")"
    echo "$(cd "$parent_dir" 2>/dev/null && pwd)/$(basename "${TOOLKIT_ROOT}/${input}")"
    return 0
  fi

  local fuzzy_match
  fuzzy_match="$(find "${TOOLKIT_ROOT}" -mindepth 1 -maxdepth 3 -name "$input" ! -path '*/.*' 2>/dev/null | head -n 1)"
  if [[ -n "$fuzzy_match" && -e "$fuzzy_match" ]]; then
    echo "$fuzzy_match"
    return 0
  fi

  return 1
}

dispatch_path() {
  local path="$1"

  if [[ -f "$path" ]]; then
    local parent_dir_name
    parent_dir_name="$(basename "$(dirname "$path")")"
    case "$parent_dir_name" in
      rules)
        sync_single_rule "$path"
        ;;
      workflows)
        sync_single_workflow "$path"
        ;;
      skills)
        sync_single_skill "$(dirname "$path")"
        ;;
      *)
        if [[ "$(basename "$path")" == "SKILL.md" ]]; then
          sync_single_skill "$(dirname "$path")"
        else
          echo "Warning: Unrecognized file type '${path}'. Skipping."
        fi
        ;;
    esac
    return 0
  fi

  if [[ -d "$path" ]]; then
    if [[ -f "${path}/SKILL.md" ]]; then
      sync_single_skill "$path"
      return 0
    fi

    if is_module_dir "$path"; then
      sync_module_dir "$path"
      return 0
    fi

    # It is a category or parent directory (e.g. shared, frameworks, or new category)
    local found_modules=0
    for sub in "${path}"/*; do
      if [[ -d "$sub" ]] && is_module_dir "$sub"; then
        sync_module_dir "$sub"
        found_modules=1
      fi
    done

    if [[ "$found_modules" -eq 0 ]]; then
      echo "Warning: No modules containing skills/rules/workflows found under '${path}'."
    fi
    return 0
  fi

  echo "Warning: Path '${path}' could not be resolved. Skipping."
}

# ------------------------------------------------------------------------------
# Top-Level Dynamic Discovery
# ------------------------------------------------------------------------------
sync_all_dynamically() {
  echo "🌐 Dynamically Discovering All Modules across Toolkit..."
  for top_dir in "${TOOLKIT_ROOT}"/*; do
    if [[ -d "$top_dir" ]]; then
      local base_top
      base_top="$(basename "$top_dir")"
      case "$base_top" in
        bin|.*|node_modules|scratch)
          continue
          ;;
        *)
          dispatch_path "$top_dir"
          ;;
      esac
    fi
  done
}

# ------------------------------------------------------------------------------
# Global GEMINI.md Tagged Block Updater
# ------------------------------------------------------------------------------
update_global_gemini_md() {
  if [[ "$IS_GLOBAL" != true || ! -s "$GLOBAL_RULES_BUFFER" ]]; then
    return 0
  fi

  echo "🌐 Refreshing ~/.gemini/GEMINI.md with tagged toolkit block..."

  # Safety backup if existing file has content
  if [[ -s "$GLOBAL_GEMINI_MD" ]]; then
    cp "$GLOBAL_GEMINI_MD" "${GLOBAL_GEMINI_MD}.bak"
  fi

  python3 -c "
import sys

gemini_path = sys.argv[1]
buffer_path = sys.argv[2]
start_tag = sys.argv[3]
end_tag = sys.argv[4]

with open(buffer_path, 'r', encoding='utf-8') as f:
    toolkit_rules = f.read().strip()

replacement_block = f'{start_tag}\n\n{toolkit_rules}\n\n{end_tag}'

try:
    with open(gemini_path, 'r', encoding='utf-8') as f:
        existing = f.read()
except FileNotFoundError:
    existing = ''

if start_tag in existing and end_tag in existing:
    s_idx = existing.find(start_tag)
    e_idx = existing.find(end_tag) + len(end_tag)
    updated = existing[:s_idx] + replacement_block + existing[e_idx:]
else:
    marker = '# Clean Code & Maintainability Standards'
    if marker in existing:
        prefix = existing[:existing.find(marker)].rstrip()
        updated = (prefix + '\n\n' if prefix else '') + replacement_block + '\n'
    else:
        user_content = existing.strip()
        updated = (user_content + '\n\n' if user_content else '') + replacement_block + '\n'

with open(gemini_path, 'w', encoding='utf-8') as f:
    f.write(updated)
" "$GLOBAL_GEMINI_MD" "$GLOBAL_RULES_BUFFER" "$START_TAG" "$END_TAG"

  echo "  [Global] ✅ Toolkit rules block refreshed inside ~/.gemini/GEMINI.md (backup: ~/.gemini/GEMINI.md.bak)"
}

# ------------------------------------------------------------------------------
# Main Dispatcher
# ------------------------------------------------------------------------------
main() {
  parse_arguments "$@"
  setup_scope_paths

  echo "=================================================================="
  echo "🚀 AI Agent Toolkit Dynamic Sync Utility"
  echo "=================================================================="
  echo "Toolkit Source : ${TOOLKIT_ROOT}"
  echo "Sync Target    : ${SCOPE_LABEL}"
  echo "------------------------------------------------------------------"

  if [[ "$SYNC_ALL" == true ]]; then
    sync_all_dynamically
  elif [[ "${#SELECTORS[@]}" -gt 0 ]]; then
    for selector in "${SELECTORS[@]}"; do
      local resolved
      if resolved="$(resolve_selector_path "$selector")"; then
        dispatch_path "$resolved"
      else
        echo "Warning: Selector '${selector}' could not be found under toolkit. Skipping."
      fi
    done
  else
    if [[ "$IS_GLOBAL" == true ]]; then
      echo "🌐 Syncing Curated Universal Global Context..."
      for default_dir in "${DEFAULT_GLOBAL_RULE_DIRS[@]}"; do
        local resolved
        if resolved="$(resolve_selector_path "$default_dir")"; then
          dispatch_path "$resolved"
        fi
      done
    else
      # Default workspace action when no selector given: sync shared context
      echo "🌐 Syncing Common Shared Context (Default)..."
      local shared_resolved
      if shared_resolved="$(resolve_selector_path "shared")"; then
        dispatch_path "$shared_resolved"
      fi
    fi
  fi

  if [[ "$IS_GLOBAL" == true ]]; then
    update_global_gemini_md

    if [[ -f "$GLOBAL_GEMINI_MD" ]]; then
      local gemini_chars
      gemini_chars="$(wc -m < "$GLOBAL_GEMINI_MD" | xargs)"
      echo "------------------------------------------------------------------"
      if [[ "$gemini_chars" -gt 12000 ]]; then
        echo "  ⚠️ [Validation Warning] ~/.gemini/GEMINI.md exceeds 12,000 chars limit (${gemini_chars} chars)!"
        echo "     Antigravity will truncate global rules exceeding 12,000 characters."
      else
        echo "  ℹ️ ~/.gemini/GEMINI.md character count: ${gemini_chars}/12,000 chars (within limit)"
      fi
    fi
  fi

  echo "------------------------------------------------------------------"
  echo "✅ Successfully synced agent context into ${SCOPE_LABEL}"
  echo "=================================================================="
}

main "$@"
