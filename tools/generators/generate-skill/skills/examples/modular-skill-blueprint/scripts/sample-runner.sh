#!/usr/bin/env bash

# ==============================================================================
# Script: sample-runner.sh
# Purpose: Model agentic script implementing stdout/stderr separation & --help.
# ==============================================================================

set -euo pipefail

usage() {
  cat << EOF
Usage: $(basename "$0") [options]

Options:
  --check          Run pre-flight diagnostic checks
  --action <act>   Action to perform: execute, dry-run (default: execute)
  --target <file>  Target file to process
  -h, --help       Show this help message

Examples:
  $(basename "$0") --check
  $(basename "$0") --action execute --target sample.txt
EOF
  exit 0
}

ACTION="execute"
TARGET=""
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      CHECK_ONLY=true
      shift 1
      ;;
    --action)
      ACTION="$2"
      shift 2
      ;;
    --target)
      TARGET="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      >&2 echo "Error: Unknown argument '$1'"
      usage
      ;;
  esac
done

if [[ "$CHECK_ONLY" == true ]]; then
  >&2 echo "🔍 [Diagnostics] Checking local dependencies: bash, python3, git... OK"
  echo '{"status": "ready", "checks": "passed"}'
  exit 0
fi

>&2 echo "🚀 [Diagnostics] Processing target '${TARGET}' with action '${ACTION}'..."

# Structured output to stdout
cat << EOF
{
  "status": "success",
  "action": "${ACTION}",
  "target": "${TARGET}",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
