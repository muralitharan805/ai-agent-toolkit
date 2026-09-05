#!/usr/bin/env bash

# ==============================================================================
# Script: sync-skills.sh
# Purpose: Syncs framework, infra, and shared skills/rules/workflows from
#          ai-agent-toolkit into a consumer project's .agents/ directory (Workspace)
#          or into ~/.gemini global customization paths (Global).
# ==============================================================================

set -e

# Determine absolute path to the ai-agent-toolkit repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET_DIR="./"
IS_GLOBAL=false
SYNC_ALL=false
FRAMEWORK=""
INFRA_MODULES=""
DOMAINS=""
SYNC_SHARED=true

# Directories in ai-agent-toolkit whose rules will be appended into ~/.gemini/GEMINI.md (Global Rules)
GEMINI_RULE_DIRS=(
  "shared/code-quality"
  "shared/communication"
  "shared/logging"
  "shared/package-management"
  "shared/security"
  "shared/git"
)

usage() {
  cat << EOF
Usage: $(basename "$0") [options]

Options:
  -g, --global             Sync context to Global Level (~/.gemini/antigravity/skills, ~/.gemini/config/)
  -t, --target <path>      Target project root directory for Workspace Level (default: current directory "./")
  -a, --all                Sync ALL frameworks, infra modules, and domain contexts
  -p, --preset <name>      Generic tech preset (e.g. angular-spa, nestjs-api, docker-dev, fullstack-app)
  -f, --framework <name>   Framework name (e.g., angular, nestjs, strapi-v5)
  -i, --infra <tools>      Comma-separated infra tools (e.g., docker, postgres, redis, cloudflare)
  -d, --domain <names>     Comma-separated domain modules (e.g. any custom directory under domains/ or shared/)
  -s, --shared             Include common shared context (enabled by default)
  -h, --help               Display this help message

Examples:
  # Workspace level sync with framework & infra:
  $(basename "$0") --framework angular --infra cloudflare --target /path/to/my-app

  # Workspace level sync with custom domain module:
  $(basename "$0") --framework nestjs --domain my-domain --target /path/to/my-backend

  # Using generic tech stack preset:
  $(basename "$0") --preset nestjs-api --target /path/to/my-api

  # Global level sync for personal machine:
  $(basename "$0") --global --shared
EOF
  exit 0
}

# Parse Command Line Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -g|--global)
      IS_GLOBAL=true
      shift 1
      ;;
    -a|--all)
      SYNC_ALL=true
      shift 1
      ;;
    -p|--preset)
      case "$2" in
        angular-spa)
          FRAMEWORK="angular"
          INFRA_MODULES="cloudflare"
          ;;
        nestjs-api)
          FRAMEWORK="nestjs"
          INFRA_MODULES="postgres,redis"
          ;;
        strapi-cms)
          FRAMEWORK="strapi-v5"
          INFRA_MODULES="postgres"
          ;;
        docker-dev)
          INFRA_MODULES="docker,postgres,redis"
          ;;
        fullstack-app)
          FRAMEWORK="angular,nestjs"
          INFRA_MODULES="docker,postgres,redis"
          ;;
        *)
          echo "Error: Unknown preset '$2'"
          exit 1
          ;;
      esac
      shift 2
      ;;
    -f|--framework)
      FRAMEWORK="$2"
      shift 2
      ;;
    -i|--infra)
      INFRA_MODULES="$2"
      shift 2
      ;;
    -d|--domain)
      DOMAINS="$2"
      shift 2
      ;;
    -s|--shared)
      SYNC_SHARED=true
      shift 1
      ;;
    -t|--target)
      TARGET_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Error: Unknown argument '$1'"
      usage
      ;;
  esac
done

if [[ "$SYNC_ALL" == true ]]; then
  # Auto-discover all frameworks, infra tools, and shared domains
  FRAMEWORK=""
  for fw_dir in "${TOOLKIT_ROOT}/frameworks"/*; do
    if [[ -d "$fw_dir" ]]; then
      fw_name="$(basename "$fw_dir")"
      if [[ -z "$FRAMEWORK" ]]; then
        FRAMEWORK="$fw_name"
      else
        FRAMEWORK="${FRAMEWORK},${fw_name}"
      fi
    fi
  done

  INFRA_MODULES=""
  for inf_dir in "${TOOLKIT_ROOT}/infra"/*; do
    if [[ -d "$inf_dir" ]]; then
      inf_name="$(basename "$inf_dir")"
      if [[ -z "$INFRA_MODULES" ]]; then
        INFRA_MODULES="$inf_name"
      else
        INFRA_MODULES="${INFRA_MODULES},${inf_name}"
      fi
    fi
  done

  DOMAINS=""
  for dom_dir in "${TOOLKIT_ROOT}/domains"/*; do
    if [[ -d "$dom_dir" ]]; then
      dom_name="$(basename "$dom_dir")"
      if [[ -z "$DOMAINS" ]]; then
        DOMAINS="$dom_name"
      else
        DOMAINS="${DOMAINS},${dom_name}"
      fi
    fi
  done
fi

## Define destination directory paths based on Scope
if [[ "$IS_GLOBAL" == true ]]; then
  TARGET_SKILLS_DIR="${HOME}/.gemini/antigravity/skills"
  TARGET_CONFIG_SKILLS_DIR="${HOME}/.gemini/config/skills"
  TARGET_RULES_DIR="${HOME}/.gemini/config/rules"
  TARGET_WORKFLOWS_DIR="${HOME}/.gemini/config/workflows"
  TARGET_GLOBAL_WORKFLOWS_DIR="${HOME}/.gemini/config/global_workflows"
  TARGET_PLUGINS_DIR="${HOME}/.gemini/config/plugins"
  GLOBAL_GEMINI_MD="${HOME}/.gemini/GEMINI.md"
  SCOPE_LABEL="Global Level (~/.gemini)"

  # Re-initialize ~/.gemini/GEMINI.md for clean sync of global rules
  mkdir -p "$(dirname "$GLOBAL_GEMINI_MD")"
  rm -f "$GLOBAL_GEMINI_MD"

  # Clean up ~/.gemini/config/rules/ so global rules are exclusively in GEMINI.md
  if [[ -d "$TARGET_RULES_DIR" ]]; then
    rm -rf "${TARGET_RULES_DIR:?}"/*
  fi
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
fi

echo "=================================================================="
echo "🚀 AI Agent Toolkit Sync Utility"
echo "=================================================================="
echo "Toolkit Source : ${TOOLKIT_ROOT}"
echo "Sync Target    : ${SCOPE_LABEL}"
[[ -n "$FRAMEWORK" ]] && echo "Frameworks     : ${FRAMEWORK}"
[[ -n "$INFRA_MODULES" ]] && echo "Infra Tools    : ${INFRA_MODULES}"
[[ -n "$DOMAINS" ]] && echo "Domain Modules : ${DOMAINS}"
echo "Shared Context : Enabled"
echo "------------------------------------------------------------------"

# Ensure destination directories exist
mkdir -p "${TARGET_SKILLS_DIR}"
mkdir -p "${TARGET_RULES_DIR}"
mkdir -p "${TARGET_WORKFLOWS_DIR}"
mkdir -p "${TARGET_PLUGINS_DIR}"
if [[ "$IS_GLOBAL" == true ]]; then
  mkdir -p "${TARGET_CONFIG_SKILLS_DIR}"
  mkdir -p "${TARGET_GLOBAL_WORKFLOWS_DIR}"
fi

# ------------------------------------------------------------------------------
# [COMMENTED OUT OLD CODE] Legacy monolithic rule upsert into ~/.gemini/GEMINI.md
# ------------------------------------------------------------------------------
# upsert_gemini_rule() {
#   local rule_file="$1"
#   local target_md="${GLOBAL_GEMINI_MD}"
# 
#   if [[ -f "$rule_file" ]]; then
#     python3 - "$rule_file" "$target_md" << 'EOF'
# import sys, os, re
# 
# rule_file = sys.argv[1]
# target_md = sys.argv[2]
# rule_id = os.path.basename(rule_file)
# 
# with open(rule_file, 'r', encoding='utf-8') as f:
#     content = f.read().strip()
# 
# if not re.search(r'<RULE\[', content):
#     content = f"<RULE[{rule_id}]>\n\n{content}\n\n</RULE[{rule_id}]>"
# 
# target_content = ""
# if os.path.exists(target_md):
#     with open(target_md, 'r', encoding='utf-8') as f:
#         target_content = f.read()
# 
# pattern = re.compile(rf'<RULE\[{re.escape(rule_id)}\]>.*?</RULE\[{re.escape(rule_id)}\]>', re.DOTALL)
# 
# if pattern.search(target_content):
#     updated = pattern.sub(lambda m: content, target_content)
# else:
#     updated = target_content.rstrip() + "\n\n" + content + "\n"
# 
# os.makedirs(os.path.dirname(os.path.abspath(target_md)), exist_ok=True)
# with open(target_md, 'w', encoding='utf-8') as f:
#     f.write(updated)
# EOF
#   fi
# }

# ------------------------------------------------------------------------------
# [COMMENTED OUT OLD CODE] Previous single-tier @mention upsert into GEMINI.md
# ------------------------------------------------------------------------------
# upsert_gemini_rule_mention() {
#   local rule_dest_file="$1"
#   local target_md="${GLOBAL_GEMINI_MD}"
# 
#   python3 - "$rule_dest_file" "$target_md" << 'EOF'
# import sys, os, re
# 
# rule_dest_file = sys.argv[1]
# target_md = sys.argv[2]
# rule_id = os.path.basename(rule_dest_file)
# mention_line = f"@{rule_dest_file}"
# 
# target_content = ""
# if os.path.exists(target_md):
#     with open(target_md, 'r', encoding='utf-8') as f:
#         target_content = f.read()
# 
# # Replace any legacy <RULE[rule_id]>...</RULE[rule_id]> block if present to clean bloat
# pattern = re.compile(rf'<RULE\[{re.escape(rule_id)}\]>.*?</RULE\[{re.escape(rule_id)}\]>', re.DOTALL)
# if pattern.search(target_content):
#     updated = pattern.sub(mention_line, target_content)
# elif mention_line not in target_content:
#     if not target_content.strip():
#         updated = f"# Global Rules\n\n{mention_line}\n"
#     else:
#         updated = target_content.rstrip() + "\n" + mention_line + "\n"
# else:
#     updated = target_content
# 
# os.makedirs(os.path.dirname(os.path.abspath(target_md)), exist_ok=True)
# with open(target_md, 'w', encoding='utf-8') as f:
#     f.write(updated)
# EOF
# }

# ------------------------------------------------------------------------------
# [COMMENTED OUT OLD CODE] Two-tier @mention / catalog upsert
# ------------------------------------------------------------------------------
# upsert_gemini_rule_entry() {
#   local src_file="$1"
#   local dest_file="$2"
#   local target_md="${GLOBAL_GEMINI_MD}"
#   local selected_rules_str="${SELECTED_GEMINI_RULES[*]}"
# 
#   python3 - "$src_file" "$dest_file" "$target_md" "$selected_rules_str" << 'EOF'
# import sys, os, re
# 
# src_file = sys.argv[1]
# dest_file = sys.argv[2]
# target_md = sys.argv[3]
# selected_rules = set(sys.argv[4].split())
# 
# file_name = os.path.basename(dest_file)
# is_selected = file_name in selected_rules
# 
# # 1. Extract description from src_file
# desc = ""
# if os.path.exists(src_file):
#     with open(src_file, 'r', encoding='utf-8') as f:
#         content = f.read()
#     if content.startswith("---"):
#         parts = content.split("---", 2)
#         if len(parts) >= 3:
#             fm = parts[1]
#             match = re.search(r'^description:\s*(["\']?)(.*?)\1$', fm, re.MULTILINE | re.DOTALL)
#             if match:
#                 desc = " ".join(match.group(2).strip().split())
#     if not desc:
#         match = re.search(r'^##\s+Description\s*\n+(.*?)(?=\n+##|\Z)', content, re.MULTILINE | re.DOTALL)
#         if match:
#             desc = " ".join(match.group(1).strip().split()[:30])
# if not desc:
#     desc = f"Rule specification for {file_name}."
# 
# # 2. Read existing target_md
# target_content = ""
# if os.path.exists(target_md):
#     with open(target_md, 'r', encoding='utf-8') as f:
#         target_content = f.read()
# 
# # Remove any legacy <RULE[file_name]>...</RULE[file_name]> block if present
# target_content = re.sub(rf'<RULE\[{re.escape(file_name)}\]>.*?</RULE\[{re.escape(file_name)}\]>\n*', '', target_content, flags=re.DOTALL)
# 
# # Parse existing core mentions and catalog entries
# core_mentions = {}
# catalog_entries = {}
# other_lines = []
# 
# for line in target_content.splitlines():
#     stripped = line.strip()
#     if stripped.startswith("@") and stripped.endswith(".md"):
#         m_path = stripped[1:].strip()
#         m_fname = os.path.basename(m_path)
#         core_mentions[m_fname] = f"@{m_path}"
#         continue
# 
#     cat_match = re.match(r'^-\s+\*\*([^*]+)\*\*:\s*(.*)$', stripped)
#     if cat_match:
#         c_fname = cat_match.group(1)
#         c_desc = cat_match.group(2)
#         catalog_entries[c_fname] = c_desc
#         continue
# 
#     if stripped in [
#         "# Antigravity Global Rules",
#         "# Global Rules",
#         "## Active Core Rules",
#         "## Available Rules Catalog (Stored in ~/.gemini/config/rules/)",
#         "The following specialized rules are available in `~/.gemini/config/rules/` and will be consulted on demand:"
#     ]:
#         continue
# 
#     if stripped:
#         other_lines.append(line)
# 
# # Route to Core Mentions or Description Catalog
# if is_selected:
#     core_mentions[file_name] = f"@{dest_file}"
#     catalog_entries.pop(file_name, None)
# else:
#     catalog_entries[file_name] = desc
#     core_mentions.pop(file_name, None)
# 
# # 3. Construct clean target document
# out = []
# if other_lines:
#     out.extend(other_lines)
#     out.append("")
# 
# out.append("# Antigravity Global Rules\n")
# out.append("## Active Core Rules")
# for fname in sorted(core_mentions.keys()):
#     out.append(core_mentions[fname])
# 
# out.append("\n## Available Rules Catalog (Stored in ~/.gemini/config/rules/)")
# out.append("The following specialized rules are available in `~/.gemini/config/rules/` and will be consulted on demand:")
# for fname in sorted(catalog_entries.keys()):
#     out.append(f"- **{fname}**: {catalog_entries[fname]}")
# 
# out.append("")
# 
# os.makedirs(os.path.dirname(os.path.abspath(target_md)), exist_ok=True)
# with open(target_md, 'w', encoding='utf-8') as f:
#     f.write("\n".join(out))
# EOF
# }

# ------------------------------------------------------------------------------
# [COMMENTED OUT OLD CODE] Legacy GEMINI.md sync helpers
# ------------------------------------------------------------------------------
# matches_gemini_rule_dir() { ... }
# upsert_gemini_rule_content() { ... }
# remove_gemini_rule_content() { ... }

# Helper to check if a directory matches GEMINI_RULE_DIRS
is_in_gemini_dirs() {
  local dir="$1"
  local rel_dir="${dir#"${TOOLKIT_ROOT}/"}"
  local base_dir="$(basename "$dir")"

  for target in "${GEMINI_RULE_DIRS[@]}"; do
    local target_clean="$(echo "$target" | sed -e 's|^/||' -e 's|/$||' -e 's|/rules$||')"
    if [[ "$rel_dir" == "$target_clean" || "$rel_dir" == "$target_clean/rules" || "$base_dir" == "$target_clean" || "$dir" == "$target" ]]; then
      return 0
    fi
  done
  return 1
}

# Helper to strip YAML frontmatter (--- ... ---) from rule files for clean GEMINI.md
strip_yaml_frontmatter() {
  local file="$1"
  awk '
    BEGIN { in_fm = 0; done_fm = 0; seen_first = 0 }
    !seen_first {
      if ($0 ~ /^[[:space:]]*$/) next
      seen_first = 1
      if ($0 ~ /^---[[:space:]]*$/) {
        in_fm = 1
        next
      }
    }
    in_fm {
      if ($0 ~ /^---[[:space:]]*$/) {
        in_fm = 0
        done_fm = 1
      }
      next
    }
    { print }
  ' "$file"
}

# Pre-flight validation helper
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

# Function to safely copy files into target locations
copy_category() {
  local src_dir="$1"
  local category="$2" # skills, rules, workflows, plugins

  if [[ -d "${src_dir}/${category}" ]]; then
    if [[ "$category" == "skills" ]]; then
      # Skills are subdirectories containing SKILL.md
      for skill_dir in "${src_dir}/${category}"/*; do
        if [[ -d "$skill_dir" ]]; then
          local skill_name="$(basename "$skill_dir")"
          local dest_skill_dir="${TARGET_SKILLS_DIR}/${skill_name}"
          validate_item "$skill_dir" "skills"
          echo "  [Skill] Syncing ${skill_name}..."
          
          # Rule 2.1: Entirely replace target item if same name exists
          rm -rf "$dest_skill_dir"
          mkdir -p "$dest_skill_dir"
          cp -r "${skill_dir}/." "${dest_skill_dir}/"

          if [[ "$IS_GLOBAL" == true ]]; then
            local dest_config_skill_dir="${TARGET_CONFIG_SKILLS_DIR}/${skill_name}"
            rm -rf "$dest_config_skill_dir"
            mkdir -p "$dest_config_skill_dir"
            cp -r "${skill_dir}/." "${dest_config_skill_dir}/"
          fi
        fi
      done
    elif [[ "$category" == "rules" ]]; then
      for md_file in "${src_dir}/${category}"/*.md; do
        if [[ -f "$md_file" ]]; then
          local file_name="$(basename "$md_file")"
          validate_item "$md_file" "rules"

          if [[ "$IS_GLOBAL" == true ]]; then
            # ------------------------------------------------------------------
            # [COMMENTED OUT OLD CODE] Legacy full-content merge into GEMINI.md
            # echo "  [Rule] Syncing ${file_name} into GEMINI.md..."
            # upsert_gemini_rule "$md_file"
            # ------------------------------------------------------------------

            # ------------------------------------------------------------------
            # [COMMENTED OUT OLD CODE] Single-tier @mention reference in GEMINI.md
            # local dest_file="${TARGET_RULES_DIR}/${file_name}"
            # echo "  [Rule] Syncing ${file_name} into ~/.gemini/config/rules/..."
            # rm -f "$dest_file"
            # cp "${md_file}" "$dest_file"
            # echo "  [Rule] Referencing @${dest_file} in GEMINI.md..."
            # upsert_gemini_rule_mention "$dest_file"
            # ------------------------------------------------------------------

            # ------------------------------------------------------------------
            # [COMMENTED OUT OLD CODE] Two-Tier @mention / Catalog Architecture
            # local dest_file="${TARGET_RULES_DIR}/${file_name}"
            # local is_selected=false
            # for sel in "${SELECTED_GEMINI_RULES[@]}"; do
            #   if [[ "$sel" == "$file_name" ]]; then
            #     is_selected=true
            #     break
            #   fi
            # done
            # rm -f "$dest_file"
            # if [[ "$is_selected" == true ]]; then
            #   cp "${md_file}" "$dest_file"
            # else
            #   sed 's/^trigger: always_on/trigger: model_decision/' "${md_file}" > "$dest_file"
            # fi
            # upsert_gemini_rule_entry "${md_file}" "${dest_file}"
            # ------------------------------------------------------------------

            # ------------------------------------------------------------------
            # [COMMENTED OUT OLD CODE] Standalone rule file copied into ~/.gemini/config/rules/
            # local dest_file="${TARGET_RULES_DIR}/${file_name}"
            # echo "  [Rule] Syncing ${file_name} into ~/.gemini/config/rules/..."
            # rm -f "$dest_file"
            # cp "${md_file}" "$dest_file"
            # ------------------------------------------------------------------

            # Direct append into ~/.gemini/GEMINI.md if directory is in GEMINI_RULE_DIRS
            if is_in_gemini_dirs "$src_dir"; then
              echo "  [Rule] Appending ${file_name} into ~/.gemini/GEMINI.md (frontmatter stripped)..."
              if [[ -s "$GLOBAL_GEMINI_MD" ]]; then
                echo "" >> "$GLOBAL_GEMINI_MD"
              fi
              strip_yaml_frontmatter "$md_file" >> "$GLOBAL_GEMINI_MD"
            fi
          else
            # Workspace Rules -> <target>/.agents/rules/*.md (Official Antigravity Spec)
            local dest_file="${TARGET_RULES_DIR}/${file_name}"
            echo "  [Rule] Syncing ${file_name}..."
            rm -f "$dest_file"
            cp "${md_file}" "$dest_file"
          fi
        fi
      done
    elif [[ "$category" == "workflows" ]]; then
      for md_file in "${src_dir}/${category}"/*.md; do
        if [[ -f "$md_file" ]]; then
          local file_name="$(basename "$md_file")"
          local dest_file="${TARGET_WORKFLOWS_DIR}/${file_name}"
          validate_item "$md_file" "workflows"
          echo "  [Workflow] Syncing ${file_name}..."
          
          # Rule 2.1: Entirely replace target workflow if same name exists
          rm -f "$dest_file"
          cp "${md_file}" "$dest_file"

          if [[ "$IS_GLOBAL" == true ]]; then
            local dest_global_file="${TARGET_GLOBAL_WORKFLOWS_DIR}/${file_name}"
            rm -f "$dest_global_file"
            cp "${md_file}" "$dest_global_file"
          fi
        fi
      done
    elif [[ "$category" == "plugins" ]]; then
      for plugin_dir in "${src_dir}/${category}"/*; do
        if [[ -d "$plugin_dir" ]]; then
          local plugin_name="$(basename "$plugin_dir")"
          local dest_plugin_dir="${TARGET_PLUGINS_DIR}/${plugin_name}"
          echo "  [Plugin] Syncing ${plugin_name}..."
          
          rm -rf "$dest_plugin_dir"
          mkdir -p "$dest_plugin_dir"
          cp -r "${plugin_dir}/." "${dest_plugin_dir}/"
        fi
      done
    fi
  fi
}

# 1. Sync Framework Contexts
if [[ -n "$FRAMEWORK" ]]; then
  IFS=',' read -ra FW_ARRAY <<< "$FRAMEWORK"
  for fw_name in "${FW_ARRAY[@]}"; do
    fw_trimmed="$(echo "$fw_name" | xargs)"
    FRAMEWORK_PATH="${TOOLKIT_ROOT}/frameworks/${fw_trimmed}"
    if [[ -d "$FRAMEWORK_PATH" ]]; then
      echo "📦 Syncing Framework Context: ${fw_trimmed}"
      copy_category "$FRAMEWORK_PATH" "skills"
      copy_category "$FRAMEWORK_PATH" "rules"
      copy_category "$FRAMEWORK_PATH" "workflows"
    else
      echo "Warning: Framework '${fw_trimmed}' not found under frameworks/. Skipping."
    fi
  done
fi

# 2. Sync Common Shared Context
if [[ "$SYNC_SHARED" == true && -d "${TOOLKIT_ROOT}/shared" ]]; then
  echo "🌐 Syncing Common Shared Context..."
  for topic_dir in "${TOOLKIT_ROOT}/shared"/*; do
    if [[ -d "$topic_dir" ]]; then
      copy_category "$topic_dir" "skills"
      copy_category "$topic_dir" "rules"
      copy_category "$topic_dir" "workflows"
    fi
  done
fi

# 3. Sync Specific Product Domain Modules
if [[ -n "$DOMAINS" ]]; then
  IFS=',' read -ra DOMAIN_ARRAY <<< "$DOMAINS"
  for domain_name in "${DOMAIN_ARRAY[@]}"; do
    domain_trimmed="$(echo "$domain_name" | xargs)"
    DOMAIN_PATH="${TOOLKIT_ROOT}/domains/${domain_trimmed}"
    
    # Fallback to shared/ if not present under domains/
    if [[ ! -d "$DOMAIN_PATH" && -d "${TOOLKIT_ROOT}/shared/${domain_trimmed}" ]]; then
      DOMAIN_PATH="${TOOLKIT_ROOT}/shared/${domain_trimmed}"
    fi

    if [[ -d "$DOMAIN_PATH" ]]; then
      echo "🎯 Syncing Domain Module Context: ${domain_trimmed}"
      copy_category "$DOMAIN_PATH" "skills"
      copy_category "$DOMAIN_PATH" "rules"
      copy_category "$DOMAIN_PATH" "workflows"
    else
      echo "Warning: Domain module '${domain_trimmed}' not found under domains/ or shared/. Skipping."
    fi
  done
fi

# 4. Sync Requested Infra Tools
if [[ -n "$INFRA_MODULES" ]]; then
  IFS=',' read -ra INFRA_ARRAY <<< "$INFRA_MODULES"
  for infra in "${INFRA_ARRAY[@]}"; do
    infra_trimmed="$(echo "$infra" | xargs)"
    INFRA_PATH="${TOOLKIT_ROOT}/infra/${infra_trimmed}"
    if [[ -d "$INFRA_PATH" ]]; then
      echo "🐳 Syncing Infra Context: ${infra_trimmed}"
      copy_category "$INFRA_PATH" "skills"
      copy_category "$INFRA_PATH" "rules"
      copy_category "$INFRA_PATH" "workflows"
    else
      echo "Warning: Infra module '${infra_trimmed}' not found in toolkit. Skipping."
    fi
  done
fi

# ------------------------------------------------------------------------------
# Global GEMINI.md Character Limit Check (Max: 12,000 chars)
# ------------------------------------------------------------------------------
if [[ "$IS_GLOBAL" == true && -f "$GLOBAL_GEMINI_MD" ]]; then
  gemini_chars="$(wc -m < "$GLOBAL_GEMINI_MD" | xargs)"
  echo "------------------------------------------------------------------"
  if [[ "$gemini_chars" -gt 12000 ]]; then
    echo "  ⚠️ [Validation Warning] ~/.gemini/GEMINI.md exceeds 12,000 chars limit (${gemini_chars} chars)!"
    echo "     Antigravity will truncate global rules exceeding 12,000 characters."
  else
    echo "  ℹ️ ~/.gemini/GEMINI.md character count: ${gemini_chars}/12,000 chars (within limit)"
  fi
fi

echo "------------------------------------------------------------------"
echo "✅ Successfully synced agent context into ${SCOPE_LABEL}"
echo "=================================================================="
