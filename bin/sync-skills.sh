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
fi

## Define destination directory paths based on Scope
if [[ "$IS_GLOBAL" == true ]]; then
  TARGET_SKILLS_DIR="${HOME}/.gemini/antigravity/skills"
  TARGET_RULES_DIR="${HOME}/.gemini/config/rules"
  TARGET_WORKFLOWS_DIR="${HOME}/.gemini/config/workflows"
  TARGET_PLUGINS_DIR="${HOME}/.gemini/config/plugins"
  GLOBAL_GEMINI_MD="${HOME}/.gemini/GEMINI.md"
  SCOPE_LABEL="Global Level (~/.gemini)"
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

# Helper function to upsert rules ONLY into ~/.gemini/GEMINI.md for global sync
upsert_gemini_rule() {
  local rule_file="$1"
  local target_md="${GLOBAL_GEMINI_MD}"

  if [[ -f "$rule_file" ]]; then
    python3 - "$rule_file" "$target_md" << 'EOF'
import sys, os, re

rule_file = sys.argv[1]
target_md = sys.argv[2]
rule_id = os.path.basename(rule_file)

with open(rule_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

if not re.search(r'<RULE\[', content):
    content = f"<RULE[{rule_id}]>\n\n{content}\n\n</RULE[{rule_id}]>"

target_content = ""
if os.path.exists(target_md):
    with open(target_md, 'r', encoding='utf-8') as f:
        target_content = f.read()

pattern = re.compile(rf'<RULE\[{re.escape(rule_id)}\]>.*?</RULE\[{re.escape(rule_id)}\]>', re.DOTALL)

if pattern.search(target_content):
    updated = pattern.sub(lambda m: content, target_content)
else:
    updated = target_content.rstrip() + "\n\n" + content + "\n"

os.makedirs(os.path.dirname(os.path.abspath(target_md)), exist_ok=True)
with open(target_md, 'w', encoding='utf-8') as f:
    f.write(updated)
EOF
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
          echo "  [Skill] Syncing ${skill_name}..."
          
          # Rule 2.1: Entirely replace target item if same name exists
          rm -rf "$dest_skill_dir"
          mkdir -p "$dest_skill_dir"
          cp -r "${skill_dir}/." "${dest_skill_dir}/"
        fi
      done
    elif [[ "$category" == "rules" ]]; then
      for md_file in "${src_dir}/${category}"/*.md; do
        if [[ -f "$md_file" ]]; then
          local file_name="$(basename "$md_file")"

          if [[ "$IS_GLOBAL" == true ]]; then
            # Global Rules -> ~/.gemini/GEMINI.md ONLY (Official Antigravity Spec)
            echo "  [Rule] Syncing ${file_name} into GEMINI.md..."
            upsert_gemini_rule "$md_file"
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
          echo "  [Workflow] Syncing ${file_name}..."
          
          # Rule 2.1: Entirely replace target workflow if same name exists
          rm -f "$dest_file"
          cp "${md_file}" "$dest_file"
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

echo "------------------------------------------------------------------"
echo "✅ Successfully synced agent context into ${SCOPE_LABEL}"
echo "=================================================================="
