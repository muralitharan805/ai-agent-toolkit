#!/usr/bin/env bash

# ==============================================================================
# Script: sync-skills.sh (Legacy Compatibility Wrapper)
# Note: Renamed to bin/sync-context.sh to reflect complete context synchronization.
#       This wrapper transparently forwards all arguments to bin/sync-context.sh.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/sync-context.sh" "$@"
