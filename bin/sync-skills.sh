#!/usr/bin/env bash

# ==============================================================================
# Script: sync-skills.sh
# Purpose: Copies framework, infra, and shared skills/rules/workflows from
#          ai-agent-toolkit into a consumer project's .agents/ directory.
# ==============================================================================

set -e

# Determine absolute path to the ai-agent-toolkit repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET_DIR="./"
FRAMEWORK=""
INFRA_MODULES=""
SYNC_SHARED=true

usage() {
  cat << EOF
Usage: $(basename "$0") [options]

Options:
  -f, --framework <name>   Framework name (e.g., angular, nestjs, strapi-v5)
  -i, --infra <tools>      Comma-separated infra tools (e.g., docker, postgres, redis, cloudflare)
  -s, --shared             Explicitly include shared context (enabled by default)
  -t, --target <path>      Target project root directory (default: current directory "./")
  -h, --help               Display this help message

Examples:
  $(basename "$0") --framework angular --target /path/to/app
  $(basename "$0") --shared --target /path/to/app
  $(basename "$0") --framework angular --infra docker,postgres --target /path/to/app
EOF
  exit 0
}

# Parse Command Line Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--framework)
      FRAMEWORK="$2"
      shift 2
      ;;
    -i|--infra)
      INFRA_MODULES="$2"
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

TARGET_AGENTS_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)/.agents"

echo "=================================================================="
echo "🚀 AI Agent Toolkit Sync Utility"
echo "=================================================================="
echo "Toolkit Source : ${TOOLKIT_ROOT}"
echo "Target Project : ${TARGET_DIR}"
[[ -n "$FRAMEWORK" ]] && echo "Framework      : ${FRAMEWORK}"
[[ -n "$INFRA_MODULES" ]] && echo "Infra Tools    : ${INFRA_MODULES}"
echo "Shared Context : Enabled"
echo "------------------------------------------------------------------"

# Ensure destination directories exist
mkdir -p "${TARGET_AGENTS_DIR}/skills"
mkdir -p "${TARGET_AGENTS_DIR}/rules"
mkdir -p "${TARGET_AGENTS_DIR}/workflows"

# Function to safely copy files into target .agents
copy_category() {
  local src_dir="$1"
  local category="$2" # skills, rules, or workflows

  if [[ -d "${src_dir}/${category}" ]]; then
    if [[ "$category" == "skills" ]]; then
      # Skills are subdirectories containing SKILL.md
      for skill_dir in "${src_dir}/${category}"/*; do
        if [[ -d "$skill_dir" ]]; then
          local skill_name="$(basename "$skill_dir")"
          local dest_skill_dir="${TARGET_AGENTS_DIR}/skills/${skill_name}"
          echo "  [Skill] Syncing ${skill_name}..."
          
          # Remove existing symlink or directory before copy to avoid same file errors
          rm -rf "$dest_skill_dir"
          mkdir -p "$dest_skill_dir"
          cp -r "${skill_dir}"/* "${dest_skill_dir}/"
        fi
      done
    else
      # Rules and Workflows are .md files
      for md_file in "${src_dir}/${category}"/*.md; do
        if [[ -f "$md_file" ]]; then
          local file_name="$(basename "$md_file")"
          local dest_file="${TARGET_AGENTS_DIR}/${category}/${file_name}"
          echo "  [${category^}] Syncing ${file_name}..."
          
          # Remove existing symlink or file before copy
          rm -f "$dest_file"
          cp "${md_file}" "$dest_file"
        fi
      done
    fi
  fi
}

# 1. Sync Framework Context (if specified)
if [[ -n "$FRAMEWORK" ]]; then
  FRAMEWORK_PATH="${TOOLKIT_ROOT}/frameworks/${FRAMEWORK}"
  if [[ ! -d "$FRAMEWORK_PATH" ]]; then
    echo "Error: Framework '${FRAMEWORK}' not found under ${TOOLKIT_ROOT}/frameworks/"
    exit 1
  fi

  echo "📦 Syncing Framework Context: ${FRAMEWORK}"
  copy_category "$FRAMEWORK_PATH" "skills"
  copy_category "$FRAMEWORK_PATH" "rules"
  copy_category "$FRAMEWORK_PATH" "workflows"
fi

# 2. Sync Shared Context (Git, Security, Code Quality, Package Management, etc.)
if [[ "$SYNC_SHARED" == true && -d "${TOOLKIT_ROOT}/shared" ]]; then
  echo "🌐 Syncing Shared Context..."
  for topic_dir in "${TOOLKIT_ROOT}/shared"/*; do
    if [[ -d "$topic_dir" && "$(basename "$topic_dir")" != "generators" ]]; then
      copy_category "$topic_dir" "skills"
      copy_category "$topic_dir" "rules"
      copy_category "$topic_dir" "workflows"
    fi
  done
fi

# 3. Sync Requested Infra Tools
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
echo "✅ Successfully synced agent context into ${TARGET_AGENTS_DIR}/"
echo "=================================================================="
