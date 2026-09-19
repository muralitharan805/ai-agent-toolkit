#!/usr/bin/env bash
# Legacy compatibility wrapper. New interface: bin/context.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

translated=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -w|--workspace|-t|--target)
      if [[ $# -lt 2 || -z "${2:-}" || "${2:-}" == -* ]]; then
        echo "Error: legacy '$1' requires a workspace target path." >&2
        exit 1
      fi
      translated+=("-w" "--target" "$2")
      shift 2
      ;;
    --agent)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "Error: --agent requires a value." >&2
        exit 1
      fi
      translated+=("--tool" "$2")
      shift 2
      ;;
    *)
      translated+=("$1")
      shift
      ;;
  esac
done

exec "${SCRIPT_DIR}/context.sh" "${translated[@]}"
