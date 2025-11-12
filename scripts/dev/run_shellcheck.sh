#!/usr/bin/env bash
# Runs shellcheck against the repository's Bash scripts.
# Legacy RaspberryPiServer builds also relied on shellcheck; this wrapper
# falls back to the koalaman/shellcheck Docker image so developers get the same
# lint even when the host does not have shellcheck installed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

default_targets=(
  "scripts/server/toolmaster/lib/toolmaster-usb.sh"
  "scripts/server/toolmaster/tool-ingest-sync.sh"
  "scripts/server/toolmaster/tool-dist-export.sh"
  "scripts/server/toolmaster/tool-backup-export.sh"
  "scripts/server/toolmaster/tool-dist-sync.sh"
  "scripts/server/toolmaster/install_usb_services.sh"
  "scripts/dev/run_shellcheck.sh"
)

if [[ $# -gt 0 ]]; then
  targets=("$@")
else
  targets=("${default_targets[@]}")
fi

run_shellcheck() {
  local shellcheck_args=(-x)
  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck "${shellcheck_args[@]}" "$@"
    return 0
  fi

  if command -v docker >/dev/null 2>&1; then
    docker run --rm -v "${REPO_ROOT}:/work" -w /work koalaman/shellcheck:stable \
      "${shellcheck_args[@]}" "$@"
    return 0
  fi

  echo "shellcheck is not available (neither host binary nor docker). Please install shellcheck or Docker." >&2
  return 1
}

run_shellcheck "${targets[@]}"
