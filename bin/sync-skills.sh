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
OVERWRITE=true

usage() {
  cat << EOF
Usage: $(basename "$0") --framework <framework-name> [options]

Options:
  -f, --framework <name>   Framework name (e.g., angular, nestjs, strapi-v5)
  -i, --infra <tools>      Comma-separated infra tools (e.g., docker, postgres, redis)
  -t, --target <path>      Target project root directory (default: current directory "./")
  -h, --help               Display this help message

Examples:
  $(basename "$0") --framework angular
  $(basename "$0") --framework angular --infra docker,postgres --target /path/to/my-angular-app
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

if [[ -z "$FRAMEWORK" ]]; then
  echo "Error: Missing required argument --framework <framework-name>"
  echo "Available frameworks in toolkit:"
  ls -1 "${TOOLKIT_ROOT}/frameworks" | sed 's/^/  - /'
  exit 1
fi

TARGET_AGENTS_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)/.agents"

echo "=================================================================="
echo "🚀 AI Agent Toolkit Sync Utility"
echo "=================================================================="
echo "Toolkit Source : ${TOOLKIT_ROOT}"
echo "Target Project : ${TARGET_DIR}"
echo "Framework      : ${FRAMEWORK}"
[[ -n "$INFRA_MODULES" ]] && echo "Infra Tools    : ${INFRA_MODULES}"
echo "------------------------------------------------------------------"

# Ensure destination directories exist
mkdir -p "${TARGET_AGENTS_DIR}/skills"
mkdir -p "${TARGET_AGENTS_DIR}/rules"
mkdir -p "${TARGET_AGENTS_DIR}/workflows"

# Function to copy files into target .agents
copy_category() {
  local src_dir="$1"
  local category="$2" # skills, rules, or workflows

  if [[ -d "${src_dir}/${category}" ]]; then
    if [[ "$category" == "skills" ]]; then
      # Skills are subdirectories containing SKILL.md
      for skill_dir in "${src_dir}/${category}"/*; do
        if [[ -d "$skill_dir" ]]; then
          local skill_name="$(basename "$skill_dir")"
          echo "  [Skill] Syncing ${skill_name}..."
          mkdir -p "${TARGET_AGENTS_DIR}/skills/${skill_name}"
          cp -r "${skill_dir}"/* "${TARGET_AGENTS_DIR}/skills/${skill_name}/"
        fi
      done
    else
      # Rules and Workflows are .md files
      for md_file in "${src_dir}/${category}"/*.md; do
        if [[ -f "$md_file" ]]; then
          local file_name="$(basename "$md_file")"
          echo "  [${category^}] Syncing ${file_name}..."
          cp "${md_file}" "${TARGET_AGENTS_DIR}/${category}/${file_name}"
        fi
      done
    fi
  fi
}

# 1. Sync Framework Context
FRAMEWORK_PATH="${TOOLKIT_ROOT}/frameworks/${FRAMEWORK}"
if [[ ! -d "$FRAMEWORK_PATH" ]]; then
  echo "Error: Framework '${FRAMEWORK}' not found under ${TOOLKIT_ROOT}/frameworks/"
  exit 1
fi

echo "📦 Syncing Framework Context: ${FRAMEWORK}"
copy_category "$FRAMEWORK_PATH" "skills"
copy_category "$FRAMEWORK_PATH" "rules"
copy_category "$FRAMEWORK_PATH" "workflows"

# 2. Sync Shared Context (Git, Security, Code Quality, etc.)
echo "🌐 Syncing Shared Context..."
if [[ -d "${TOOLKIT_ROOT}/shared" ]]; then
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
